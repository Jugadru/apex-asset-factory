"""Execute bounded native UV atlas QA on original vehicle requests, no promotion."""
import argparse
import json
import os
from pathlib import Path
import sys
from asset_factory.build import build, HERE, digest
from asset_factory.stage_pbr import stage

CASES={"2012":((0,256,11804),(1,256,6844),(2,256,4252)),
       "gt":((0,256,15080),(2,512,4904)),
       "endurance":((0,256,15116),)}

def logs(w):
    for path in sorted(w.glob("*.log")):
        text=path.read_text(errors="replace")
        print(f"--- {path.name} ---\n{text[-20000:]}",flush=True)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--family",choices=CASES,required=True)
    p.add_argument("--blender",required=True);p.add_argument("--godot",required=True)
    p.add_argument("--workspace",required=True)
    args=p.parse_args()
    w=Path(args.workspace).resolve();w.mkdir(exist_ok=False)
    request=HERE/f"demo_wheel_{args.family}.json"
    results=[];failed=False
    for lod,size,triangles in CASES[args.family]:
        src=w/f"lod{lod}-source";dst=w/f"lod{lod}-atlas"
        result={"family":args.family,"lod":lod,"texture_size":size,"expected_triangles":triangles,"status":"FAIL"}
        try:
            a=build(request,args.blender,args.godot,src,derived_lod=lod)
            result["source"]=a
            if a["status"]!="BUILT":raise ValueError("original build failed")
            source_sha=digest(src/"staging/asset.glb")
            # LOD0 A/B render captures remain ephemeral. No asset publication.
            baseline=w/f"lod{lod}-baseline"
            old=stage(src,source_sha,args.blender,args.godot,baseline,size,True,True,True) if lod==0 else None
            if old is not None:
                result["baseline"]=old
                if old["status"]!="PASS":raise ValueError("baseline PBR failed")
            r=stage(src,source_sha,args.blender,args.godot,dst,size,lod==0,True,True,True,2048)
            result["atlas"]=r
            if r["status"]!="PASS":raise ValueError("atlas native stage failed")
            if r["asset"]["triangles"]!=triangles:raise ValueError("historical triangle count drift")
            if old is not None:
                if old["asset"]["maps"]!=r["asset"]["maps"]:raise ValueError("PBR map regression")
                result["capture_hash_equal"]=digest(baseline/"staging/capture.png")==digest(dst/"staging/capture.png")
                result["visual_review"]="NOT_RUN"
            result["status"]="PASS"
        except Exception as exc:
            failed=True;result["error"]=str(exc)
            for d in (src,w/f"lod{lod}-baseline",dst):
                if d.exists():logs(d)
        finally:
            results.append(result)
            print("APEX_NATIVE_ATLAS_CASE "+json.dumps(result,sort_keys=True,allow_nan=False),flush=True)
    print("APEX_NATIVE_ATLAS_SUMMARY "+json.dumps({"family":args.family,"revision":os.getenv("GITHUB_SHA"),"cases":[{"lod":r["lod"],"status":r["status"]} for r in results],"status":"FAIL" if failed else "PASS","physical_gpu":"NOT_RUN","promotion":"BLOCKED"}),flush=True)
    return int(failed)

if __name__=="__main__":sys.exit(main())
