"""Build isolated procedural LOD0/1/2 sets and test distance switching in Godot."""
import argparse
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys

from asset_factory.build import build, read_request, dump, digest, HERE, ROOT
from asset_factory.secure_run import run
from asset_factory.validate_glb import inspect
from asset_factory.lod_policy import level_for_distance

DISTANCES=[0,26,29,72,74,68,66,23,21,100,0]


def compare_levels(reports):
    if type(reports) is not list or len(reports)!=3:
        raise ValueError("three completed LOD reports required")
    counts=[]
    required=("plan","export","structural_validation","godot_import")
    for i,r in enumerate(reports):
        if type(r) is not dict or r.get("status")!="BUILT" or type(r.get("derived_lod")) is not int or r["derived_lod"]!=i:
            raise ValueError("invalid LOD report")
        if r.get("promotion")!="BLOCKED" or any(r.get("stages",{}).get(k)!="PASS" for k in required):
            raise ValueError("incomplete staging evidence")
        count=r["asset"]["mesh_triangles"]
        fixture=r["godot_fixture"]
        size=fixture["size"]
        if type(count) is not int or count<=0 or type(fixture["meshes"]) is not int or fixture["meshes"]<=0:
            raise ValueError("invalid LOD counts")
        if type(size) is not list or len(size)!=3 or any(type(v) not in (int,float) or not math.isfinite(v) or v<=0 for v in size):
            raise ValueError("invalid LOD dimensions")
        if type(r["asset"]["materials"]) is not int or r["asset"]["materials"]<=0:
            raise ValueError("invalid material count")
        counts.append(count)
    if not 0<counts[2]<counts[1]<counts[0] or counts[1]>.90*counts[0] or counts[2]>.75*counts[0]:
        raise ValueError("LOD triangle reduction target not met")
    base=reports[0]["godot_fixture"]
    for r in reports:
        fixture=r["godot_fixture"]
        if fixture["meshes"]!=base["meshes"] or any(abs(x-y)>.005*y for x,y in zip(fixture["size"],base["size"])):
            raise ValueError("LOD component count or envelope drift")
        if r["asset"]["materials"]!=reports[0]["asset"]["materials"]:
            raise ValueError("LOD material count drift")
    return counts


def document_contract(doc):
    """Compare semantic identity, not exporter ordering or triangle topology."""
    nodes=doc["nodes"];materials=doc["materials"]
    names=[n.get("name") for n in nodes]
    mat_names=[m.get("name") for m in materials]
    for values in (names,mat_names):
        if any(type(v) is not str or not v for v in values) or len(set(values))!=len(values):
            raise ValueError("LOD missing or duplicate component/material name")
    signature={}
    for node in nodes:
        primitives=doc["meshes"][node["mesh"]]["primitives"]
        if not primitives:
            raise ValueError("LOD empty component")
        signature[node["name"]]={
            "matrix":node.get("matrix"),
            "translation":node.get("translation",[0,0,0]),
            "rotation":node.get("rotation",[0,0,0,1]),
            "scale":node.get("scale",[1,1,1]),
            "children":sorted(names[i] for i in node.get("children",[])),
            "materials":sorted({mat_names[p["material"]] for p in primitives}),
        }
    return {"nodes":signature,"materials":dict(zip(mat_names,materials)),
            "roots":sorted(names[i] for i in doc["scenes"][doc["scene"]]["nodes"])}


def compare_documents(docs):
    if len(docs)!=3:
        raise ValueError("three inspected LOD documents required")
    contracts=[document_contract(d) for d in docs]
    if any(c!=contracts[0] for c in contracts[1:]):
        raise ValueError("LOD component identity, transform, hierarchy or material drift")


def verify_level_receipt(result,report,request_sha,actual_request_sha):
    if request_sha!=actual_request_sha or result["sha256"]!=report["asset"]["sha256"] or result["triangles"]!=report["asset"]["mesh_triangles"]:
        raise ValueError("LOD inspected asset or request differs from build report")


def build_set(request,blender,godot,workspace,capture=False):
    r=read_request(Path(request))
    if r["schema"] not in (2,3,4,5,6,7,8):
        raise ValueError("LOD set requires modular request schema 2–8")
    w=Path(workspace).absolute()
    if w.exists() or w.is_symlink() or ROOT in w.resolve().parents or w.resolve()==ROOT:
        raise ValueError("new workspace outside repository required")
    w=w.resolve();w.mkdir()
    manifest={"schema":1,"factory_version":"0.2.4.1","id":r["id"],"version":r["version"],"status":"FAIL",
              "promotion":"BLOCKED","manual_review":"NOT_RUN","physical_gpu":"NOT_RUN","game_integration":"NOT_RUN",
              "thresholds_m":[25,70],"hysteresis_m":3,"levels":[],"switch_test":"NOT_RUN","identity_contract":"NOT_RUN"}
    try:
        dump(w/"request.json",r)
        manifest["request_sha256"]=digest(w/"request.json")
        reports=[];docs=[]
        stage=w/"switch";stage.mkdir()
        for level in range(3):
            loc=w/f"lod{level}"
            report=build(w/"request.json",blender,godot,loc,capture,derived_lod=level)
            reports.append(report)
            if report["status"]!="BUILT":raise ValueError(f"LOD{level} build failed: "+str(report.get("error")))
            asset=loc/"staging/asset.glb"
            result,doc,_=inspect(asset,r["triangle_budget"])
            verify_level_receipt(result,report,manifest["request_sha256"],digest(loc/"request.json"))
            docs.append(doc)
            shutil.copyfile(asset,stage/f"lod{level}.glb")
            manifest["levels"].append({"level":level,"asset":f"lod{level}/staging/asset.glb","sha256":result["sha256"],
                  "triangles":result["triangles"],"bytes":result["bytes"],"report_sha256":digest(loc/"report.json")})
        counts=compare_levels(reports)
        compare_documents(docs)
        manifest["identity_contract"]="PASS"
        for row in manifest["levels"]:row["triangle_ratio"]=row["triangles"]/counts[0]
        shutil.copyfile(HERE/"lod_switch.gd",stage/"lod_switch.gd")
        shutil.copyfile(w/"lod0/staging/project.godot",stage/"project.godot")
        g=str(Path(godot).resolve(strict=True))
        log=run([g,"--headless","--path",str(stage),"--editor","--import"],w,w/"switch-import.log",120)
        if any(s in log for s in ("ERROR:","SCRIPT ERROR","Parse Error:")):raise ValueError("LOD switch import errors")
        log=run([g,"--headless","--path",str(stage),"--script","res://lod_switch.gd"],w,w/"switch-test.log",60)
        marker=next((line[9:] for line in log.splitlines() if line.startswith("APEX_LOD ")),None)
        if marker is None or "ERROR:" in log:raise ValueError("LOD switch fixture failed")
        observed=json.loads(marker)
        expected=[];level=0
        for distance in DISTANCES:
            level=level_for_distance(distance,level);expected.append(level)
        if observed!={"status":"PASS","distances_m":DISTANCES,"levels":expected,"visible_roots":1}:raise ValueError("LOD switch result mismatch")
        manifest["switch_test"]=observed
        manifest["status"]="PASS"
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as exc:
        manifest["error"]=str(exc)
    finally:dump(w/"lod-manifest.json",manifest)
    return manifest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("request");p.add_argument("--blender",required=True);p.add_argument("--godot",required=True)
    p.add_argument("--workspace",required=True);p.add_argument("--capture",action="store_true")
    a=p.parse_args()
    try:result=build_set(a.request,a.blender,a.godot,a.workspace,a.capture)
    except (ValueError,OSError) as exc:result={"status":"FAIL","error":str(exc)}
    print(json.dumps(result,indent=2));return 0 if result["status"]=="PASS" else 1

if __name__=="__main__":sys.exit(main())
