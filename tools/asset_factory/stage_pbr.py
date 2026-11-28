"""Run the opt-in PBR enrichment and native staging checks against an original build receipt."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from asset_factory.build import HERE, ROOT, read_request, digest, dump
from asset_factory.material_factory import generate, require, MAX_BYTES
from asset_factory.secure_run import run
from asset_factory.uv_repair import repair
from apex_lab_graphics import inspect as inspect_png


def source_contract(source,source_sha,size):
    source=Path(source).absolute()
    require(source.resolve()==source and source.is_dir(),"regular source workspace required")
    for rel in ("request.json","report.json","registry.json","staging/asset.glb"):
        p=source/rel;require(p.resolve()==p and p.is_file() and p.stat().st_size<=MAX_BYTES,"invalid source file")
    req=read_request(source/"request.json");base=json.loads((source/"report.json").read_text());reg=json.loads((source/"registry.json").read_text())
    asset=source/"staging/asset.glb"
    require(req["schema"] in (7,8) and type(size) is int and size in (256,512) and size<=req["texture_max_px"],"schema 7/8 and texture budget required")
    require(base["status"]==reg["status"]=="BUILT" and base["promotion"]==reg["promotion"]=="BLOCKED" and reg["license"]==req["license"]=="ORIGINAL","source not original staged build")
    require(reg["id"]==req["id"] and reg["version"]==req["version"] and reg["request_sha256"]==digest(source/"request.json") and reg["asset"]["sha256"]==base["asset"]["sha256"]==source_sha==digest(asset),"source receipt mismatch")
    require(type(base["derived_lod"]) is int and base["derived_lod"] in (0,1,2) and base["derived_lod"]==reg["derived_lod"] and all(base["stages"].get(k)=="PASS" for k in ("plan","export","structural_validation","godot_import")),"source stages incomplete")
    return req,base,asset


def stage(source,source_sha,blender,godot,workspace,size=256,capture=False,repair_uv=False,normal_maps=False):
    source=Path(source).absolute();w=Path(workspace).absolute()
    require(not w.exists() and not w.is_symlink() and ROOT not in w.resolve().parents and w.resolve()!=ROOT and source.resolve() not in w.resolve().parents,"new external workspace required")
    w=w.resolve();w.mkdir()
    report={"factory_version":"0.3.0.2","status":"FAIL","promotion":"BLOCKED","manual_review":"NOT_RUN","physical_gpu":"NOT_RUN","game_integration":"NOT_RUN","stages":{k:"NOT_RUN" for k in ("source","textures","blender_import","godot_import","capture")}}
    if repair_uv:report["stages"]={k:"NOT_RUN" for k in ("source","uv_repair","textures","blender_import","godot_import","capture")}
    try:
        require(type(repair_uv) is bool and type(normal_maps) is bool,"invalid repair/normal option")
        require(not normal_maps or repair_uv,"normal maps require explicit UV repair")
        req,base,asset=source_contract(source,source_sha,size)
        report.update(source_id=req["id"],source_version=req["version"],source_lod=base["derived_lod"],source_report_sha256=digest(source/"report.json"));report["stages"]["source"]="PASS"
        staging=w/"staging";staging.mkdir();target=staging/"asset.glb"
        material_source,material_sha=asset,source_sha
        if repair_uv:
            material_source=w/"repaired.glb"
            report["uv_repair"]=repair(asset,material_source,source_sha,req["triangle_budget"])
            material_sha=report["uv_repair"]["sha256"];report["stages"]["uv_repair"]="PASS"
        report["asset"]=generate(material_source,material_sha,target,req["triangle_budget"],size,normal_maps);report["stages"]["textures"]="PASS"
        if repair_uv:require(report["asset"]["uv_degenerate_triangles"]==0,"repaired PBR UV regression")
        require(report["asset"]["triangles"]==base["asset"]["mesh_triangles"] and report["asset"]["materials"]==base["asset"]["materials"],"source counts mismatch")
        expected=report["asset"]["materials"]
        b=str(Path(blender).resolve(strict=True));g=str(Path(godot).resolve(strict=True))
        report["blender"]=run([b,"--version"],w,w/"blender-version.log",15).splitlines()[0];report["godot"]=run([g,"--version"],w,w/"godot-version.log",15).strip()
        require(report["blender"].startswith("Blender 5.3.") and report["godot"].startswith("4.7.2."),"unsupported runtime")
        log=run([b,"--background","--factory-startup","--python-exit-code","1","--python",str(HERE/"pbr_blender.py"),"--",str(target),str(expected),str(size)]+(["--uv-clean"] if repair_uv else [])+(["--normal-maps"] if normal_maps else []),w,w/"blender-import.log",120)
        require("APEX_PBR_BLENDER PASS" in log,"Blender material import failed")
        if repair_uv:require(f"APEX_UV_BLENDER PASS {report['asset']['triangles']}" in log.splitlines(),"Blender UV count mismatch")
        if normal_maps:require("APEX_TANGENT_BLENDER PASS" in log,"Blender tangent gate")
        report["stages"]["blender_import"]="PASS"
        (staging/"project.godot").write_text('[application]\nconfig/name="APEX PBR Staging"\n[display]\nwindow/size/viewport_width=960\nwindow/size/viewport_height=540\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n')
        for name in ("pbr_godot.gd","staging.gd"):shutil.copyfile(HERE/name,staging/name)
        log=run([g,"--headless","--path",str(staging),"--editor","--import"],w,w/"godot-import.log",120)
        require(not any(s in log for s in ("ERROR:","SCRIPT ERROR","Parse Error:")),"Godot import errors")
        log=run([g,"--headless","--path",str(staging),"--script","res://pbr_godot.gd","--",str(expected),str(size)]+(["--uv-clean"] if repair_uv else [])+(["--normal-maps"] if normal_maps else []),w,w/"godot-test.log",60)
        require("APEX_PBR_GODOT PASS" in log and "ERROR:" not in log,"Godot PBR fixture failed")
        if repair_uv:require(f"APEX_UV_GODOT PASS {report['asset']['triangles']}" in log.splitlines(),"Godot UV count mismatch")
        if normal_maps:require("APEX_TANGENT_GODOT PASS" in log,"Godot tangent gate")
        report["stages"]["godot_import"]="PASS"
        if capture:
            log=run((["xvfb-run","-a"] if shutil.which("xvfb-run") else [])+[g,"--path",str(staging),"--rendering-method","gl_compatibility","--audio-driver","Dummy","--script","res://staging.gd","--","--capture"],w,w/"godot-capture.log",60)
            require("ERROR:" not in log,"capture error");report["capture"]=inspect_png(staging/"capture.png",960,540);report["stages"]["capture"]="PASS"
        require(digest(target)==report["asset"]["sha256"] and digest(asset)==source_sha and digest(material_source)==material_sha,"asset changed during staging")
        report["status"]="PASS"
    except (ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError) as exc:
        report["error"]=str(exc)
        for k,v in report["stages"].items():
            if v=="NOT_RUN":report["stages"][k]="FAIL";break
    finally:dump(w/"pbr-report.json",report)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("source");p.add_argument("--source-sha256",required=True);p.add_argument("--blender",required=True);p.add_argument("--godot",required=True);p.add_argument("--workspace",required=True);p.add_argument("--size",type=int,choices=(256,512),default=256);p.add_argument("--capture",action="store_true")
    p.add_argument("--repair-uv",action="store_true")
    p.add_argument("--normal-maps",action="store_true")
    a=p.parse_args();r=stage(a.source,a.source_sha256,a.blender,a.godot,a.workspace,a.size,a.capture,a.repair_uv,a.normal_maps);print(json.dumps(r,indent=2));return 0 if r["status"]=="PASS" else 1

if __name__=="__main__":sys.exit(main())
