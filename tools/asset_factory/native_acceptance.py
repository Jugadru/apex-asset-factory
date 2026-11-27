"""Opt-in native acceptance harness: two seeds, two repeats each, no publication."""
import argparse
import json
from pathlib import Path
import sys

from asset_factory import registry as r
from asset_factory.build import build, read_request, dump, HERE
from asset_factory.validate_glb import compare


def acceptance(blender,godot,workspace,capture=False):
    work=r.outside_repo(workspace)
    work.mkdir(mode=0o700)
    summary={"schema":1,"status":"FAIL","revision":None,"runs":[],"comparisons":[],
             "physical_gpu":"NOT_RUN","manual_review":"NOT_RUN","promotion":"BLOCKED"}
    try:
        summary["revision"]=r.verified_revision()
        base=read_request(HERE/"demo.json")
        for seed in (2012,2027):
            request=dict(base,seed=seed)
            req=work/f"request-{seed}.json"
            dump(req,request)
            locations=[]
            for repeat in (1,2):
                loc=work/f"seed-{seed}-run-{repeat}"
                report=build(req,blender,godot,loc,capture)
                summary["runs"].append({"seed":seed,"repeat":repeat,"report":loc.name+"/report.json",
                                        "status":report["status"],"report_sha256":r.sha((loc/"report.json").read_bytes())})
                r.check(report["status"]=="BUILT","native build failed")
                locations.append(loc/"staging"/"asset.glb")
            result=compare(*locations,budget=request["triangle_budget"])
            summary["comparisons"].append(dict(result,seed=seed))
            r.check(result["status"]=="PASS","numeric repeatability failed")
        summary["status"]="PASS"
    except Exception as exc:
        summary["error"]=str(exc)
    finally:
        dump(work/"acceptance.json",summary)
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--blender",required=True);p.add_argument("--godot",required=True)
    p.add_argument("--workspace",required=True);p.add_argument("--capture",action="store_true")
    a=p.parse_args()
    try:res=acceptance(a.blender,a.godot,a.workspace,a.capture)
    except (ValueError,OSError) as exc:res={"status":"FAIL","error":str(exc)}
    print(json.dumps(res,indent=2));return 0 if res["status"]=="PASS" else 1


if __name__=="__main__":
    sys.exit(main())
