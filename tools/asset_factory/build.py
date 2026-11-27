"""Asset Factory 0.2.4.1: isolated original vehicle build, no promotion."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
from apex_foundation import plan
from apex_asset_build import inspect_glb
from asset_factory.validate_glb import inspect as inspect_advanced
from asset_factory.secure_run import run
from apex_lab_graphics import inspect as inspect_png

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def dump(path, data):
    with path.open("x", encoding="utf-8") as f:
        json.dump(data, f, sort_keys=True, indent=2, allow_nan=False)
        f.write("\n")

def validate(value, schema, field="$"):
    # Strict subset used by the bundled JSON Schema; no external dependency.
    def fail():
        raise ValueError("invalid request: " + field)
    if "const" in schema and (type(value) is not type(schema["const"]) or value != schema["const"]):
        fail()
    if "enum" in schema and (type(value) is not int or value not in schema["enum"]):
        fail()
    kind = schema.get("type")
    if kind == "object":
        if type(value) is not dict or set(value) != set(schema["required"]):
            fail()
        for k,v in value.items():
            validate(v, schema["properties"][k], field+"."+k)
    elif kind == "array":
        if type(value) is not list or not schema["minItems"] <= len(value) <= schema["maxItems"]:
            fail()
        for v in value:
            validate(v, schema["items"], field+"[]")
    elif kind == "string":
        if type(value) is not str or not schema.get("minLength",0) <= len(value) <= schema.get("maxLength",100) or not value.strip():
            fail()
        if "pattern" in schema and not re.fullmatch(schema["pattern"], value):
            fail()
    elif kind in ("integer","number"):
        if type(value) not in ((int,) if kind == "integer" else (int,float)):
            fail()
        if not schema["minimum"] <= value <= schema["maximum"] or not math.isfinite(value):
            fail()
    elif kind is not None:
        fail()

def read_request(path):
    def unique(pairs):
        out = {}
        for key,value in pairs:
            if key in out:
                raise ValueError("duplicate JSON key: "+key)
            out[key] = value
        return out
    if path.is_symlink() or not path.is_file():
        raise ValueError("regular request required")
    if path.stat().st_size > 65536:
        raise ValueError("request too large")
    with path.open("rb") as f:
        raw = f.read(65537)
    if len(raw) > 65536:
        raise ValueError("request too large")
    r = json.loads(raw, object_pairs_hook=unique, parse_constant=lambda s: (_ for _ in ()).throw(ValueError("nonfinite JSON constant: "+s)))
    schema_name = {2:"request_v2.schema.json",3:"request_v3.schema.json",4:"request_v4.schema.json",5:"request_v5.schema.json",6:"request_v6.schema.json",7:"request_v7.schema.json",8:"request_v8.schema.json"}.get(r["schema"],"request.schema.json") if type(r) is dict and type(r.get("schema")) is int else "request.schema.json"
    validate(r, json.loads((HERE/schema_name).read_text()))
    return r

def inspect_attributes(path, budget, layout=None):
    result = inspect_glb(path, budget)
    result["advanced_validation"], doc, decoded = inspect_advanced(path, budget)
    if layout is not None:
        if any(p["kind"] == "wheel_mesh" for p in layout):
            from asset_factory.wheel_detail import verify_wheel_details
            result["detailed_wheels"] = verify_wheel_details(doc,decoded,layout)
        else:
            from asset_factory.modular_qa import verify_wheels
            result["modular_wheels"] = verify_wheels(doc, decoded, layout)
        if any(p.get("shape") == "open_tub" for p in layout):
            from asset_factory.detail_qa import verify_details
            result["detail_geometry"] = verify_details(doc,decoded,layout)
        if any(p["name"] == "BodyShell" for p in layout):
            from asset_factory.closed_wheel_qa import verify_closed_wheel
            result["closed_wheel_geometry"] = verify_closed_wheel(doc,decoded,layout)
    raw = path.read_bytes()
    n = struct.unpack_from("<I", raw, 12)[0]
    data = json.loads(raw[20:20+n])
    names = {node.get("name") for node in data.get("nodes", [])}
    wheels = {"Wheel_"+s+"_"+a for s in ("L","R") for a in ("F","R")}
    if not wheels <= names:
        raise ValueError("wheel nodes missing")
    for mesh in data["meshes"]:
        for p in mesh["primitives"]:
            if not {"POSITION","NORMAL","TEXCOORD_0"} <= p["attributes"].keys():
                raise ValueError("mesh attributes missing")
            if type(p.get("material")) is not int or not 0 <= p["material"] < len(data.get("materials", [])):
                raise ValueError("material missing")
    if data.get("images") or data.get("textures"):
        raise ValueError("v0.1.0 supports untextured materials only")
    result.update({"wheel_nodes":sorted(wheels),"materials":len(data["materials"]),
                   "attribute_presence":"PASS","textures":0})
    return result

def build(request, blender, godot, workspace, capture=False, derived_lod=0):
    r = read_request(Path(request))
    if type(derived_lod) is not int or derived_lod not in (0,1,2) or (derived_lod and r["schema"]==1):
        raise ValueError("LOD variants require schema 2–8 and level 0–2")
    generator = {1:"vehicle.py",2:"modular_vehicle.py",3:"era_vehicle.py",4:"detail_vehicle.py",5:"closed_wheel_vehicle.py",6:"advanced_body_vehicle.py",7:"wheel_detail_vehicle.py",8:"openwheel_detail_vehicle.py"}[r["schema"]]
    w = Path(workspace).absolute()
    if w.exists() or w.is_symlink() or ROOT in w.resolve().parents or w.resolve() == ROOT:
        raise ValueError("new workspace outside repository required")
    w = w.resolve()
    w.mkdir()
    report = {"factory_version":"0.2.4.1","derived_lod":derived_lod,"status":"FAIL","approval":"PENDING",
              "promotion":"BLOCKED","stages":{k:"NOT_RUN" for k in ("plan","export","structural_validation","godot_import","capture")}}
    try:
        dump(w/"request.json",r)
        legacy = {"schema":1,"jobs":[{"id":r["id"],"kind":"car","era":r["era"],
                  "source":None,"approved":True,"license":"ORIGINAL",
                  "output":"staging/asset.glb","triangle_budget":r["triangle_budget"],
                  "texture_max_px":r["texture_max_px"]}]}
        dump(w/"foundation-job.json", legacy)
        planned = plan(w/"foundation-job.json")
        dump(w/"plan.json",planned)
        if planned["jobs"][0]["status"] != "PLANNED":
            raise ValueError("Foundation blocked request")
        if r["schema"] in (2,3,4,5,6,7,8):
            if r["schema"] == 8:
                from asset_factory.openwheel_detail import design, validate_layout
            elif r["schema"] == 7:
                from asset_factory.wheel_detail import design, validate_layout
            elif r["schema"] == 6:
                from asset_factory.advanced_body_layout import design, validate_layout
            elif r["schema"] == 5:
                from asset_factory.closed_wheel_layout import design, validate_layout
            elif r["schema"] == 4:
                from asset_factory.detail_layout import design, validate_layout
            elif r["schema"] == 3:
                from asset_factory.era_layout import design, validate_layout
            else:
                from asset_factory.modular_layout import design, validate_layout
            layout = design(r,derived_lod) if r["schema"] in (6,7,8) else design(r)
            report["layout"] = validate_layout(layout,r)
            dump(w/"component-layout.json",layout)
        report["stages"]["plan"]="PASS"
        b = str(Path(blender).resolve(strict=True))
        g = str(Path(godot).resolve(strict=True))
        report["blender"] = run([b,"--version"],w,w/"blender-version.log",15).splitlines()[0]
        report["godot"] = run([g,"--version"],w,w/"godot-version.log",15).strip()
        if not report["blender"].startswith("Blender 5.3.") or not report["godot"].startswith("4.7.2."):
            raise ValueError("unsupported runtime")
        stage = w/"staging"
        stage.mkdir()
        asset = stage/"asset.glb"
        run([b,"--background","--factory-startup","--python-exit-code","1","--python",
             str(HERE/generator),"--","--request",str(w/"request.json"),"--output",str(asset)]+(["--derived-lod",str(derived_lod)] if derived_lod else []),
            w,w/"blender.log",180)
        report["stages"]["export"]="PASS"
        report["asset"] = inspect_attributes(asset,r["triangle_budget"],layout if r["schema"] in (2,3,4,5,6,7,8) else None)
        report["stages"]["structural_validation"]="PASS"
        (stage/"project.godot").write_text('[application]\nconfig/name="APEX Asset Staging"\n[display]\nwindow/size/viewport_width=960\nwindow/size/viewport_height=540\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n')
        shutil.copyfile(HERE/"staging.gd",stage/"staging.gd")
        import_log = run([g,"--headless","--path",str(stage),"--editor","--import"],w,w/"godot-import.log",120)
        if any(s in import_log for s in ("SCRIPT ERROR","ERROR:","Parse Error:")):
            raise ValueError("Godot editor import errors")
        output = run([g,"--headless","--path",str(stage),"--script","res://staging.gd"],w,w/"godot-test.log",60)
        marker = next((line[12:] for line in output.splitlines() if line.startswith("APEX_IMPORT ")),None)
        if marker is None or any(s in output for s in ("SCRIPT ERROR","ERROR:")):
            raise ValueError("Godot import fixture failed")
        info = json.loads(marker)
        expected = [r["dimensions_m"][k] for k in ("width","height","length")]
        if info["meshes"] < 4 or len(info["size"]) != 3 or any(abs(x-y) > .02*y for x,y in zip(info["size"],expected)):
            raise ValueError("Godot dimensions or mesh count invalid")
        report["godot_fixture"] = info
        report["asset"]["godot_import"]="PASS"
        report["stages"]["godot_import"]="PASS"
        if capture:
            prefix = ["xvfb-run","-a"] if shutil.which("xvfb-run") else []
            capture_log = run(prefix+[g,"--path",str(stage),"--rendering-method","gl_compatibility",
                        "--audio-driver","Dummy","--script","res://staging.gd","--","--capture"],w,w/"godot-capture.log",60)
            if any(s in capture_log for s in ("SCRIPT ERROR","ERROR:")):
                raise ValueError("Godot capture errors")
            report["capture"] = inspect_png(stage/"capture.png",960,540)
            report["stages"]["capture"]="PASS"
        else:
            report["stages"]["capture"]="NOT_RUN"
        report["status"]="BUILT"
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as exc:
        report["error"]=str(exc)
        stage_key = next((k for k,v in report["stages"].items() if v=="NOT_RUN"),None)
        if stage_key:
            report["stages"][stage_key]="FAIL"
    finally:
        report["stages"]["manual_review"]="NOT_RUN"
        report["stages"]["promotion"]="BLOCKED"
        dump(w/"report.json",report)
        dump(w/"registry.json",{"schema":1,"id":r["id"],"version":r["version"],
              "author":r["author"],"license":r["license"],"origin":"original procedural",
              "request_sha256":digest(w/"request.json"),"dependencies":[],
              "generator_sha256":digest(HERE/generator),
              "derived_lod":derived_lod,
              "generator_dependencies":({name:digest(HERE/name) for name in (["modular_layout.py","modular_qa.py","lod_policy.py"]+(["era_layout.py"] if r["schema"] in (3,4,5,6,7,8) else [])+(["detail_layout.py","detail_qa.py"] if r["schema"] in (4,8) else [])+(["closed_wheel_layout.py","closed_wheel_qa.py"] if r["schema"] in (5,6,7) else [])+(["advanced_body_layout.py"] if r["schema"] in (6,7) else [])+(["wheel_detail.py","advanced_body_layout.py","closed_wheel_layout.py","closed_wheel_qa.py"] if r["schema"] == 8 else (["wheel_detail.py"] if r["schema"] == 7 else []))+(["openwheel_detail.py"] if r["schema"] == 8 else []))} if r["schema"] in (2,3,4,5,6,7,8) else {}),"asset":report.get("asset"),
              "status":report["status"],"history":[{"version":r["version"],"status":report["status"]}],
              "approval":"PENDING","promotion":"BLOCKED"})
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("request")
    p.add_argument("--blender",required=True)
    p.add_argument("--godot",required=True)
    p.add_argument("--workspace",required=True)
    p.add_argument("--capture",action="store_true")
    a=p.parse_args()
    report=build(a.request,a.blender,a.godot,a.workspace,a.capture)
    print(json.dumps(report,indent=2))
    return 0 if report["status"]=="BUILT" else 1

if __name__=="__main__":
    sys.exit(main())
