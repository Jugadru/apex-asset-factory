"""Non-executing Lab handoff receipts; no dispatch, no secrets, no remote authorization."""
import argparse
import json
from pathlib import Path
import sys
from asset_factory import registry as r

REPO="Jugadru/apex-asset-factory"
FOUNDATION="f878b09aa5d66ef7d8302b2d94aa2a8d7db9c59b"


def handoff(request_path,revision,job_id):
    r.check(type(revision) is str and r.REV.fullmatch(revision),"exact revision required")
    r.check(type(job_id) is str and r.ID.fullmatch(job_id),"invalid job id")
    request=r.read_request(Path(request_path))
    return {"schema":1,"job_id":job_id,"repository":REPO,"revision":revision,
            "foundation_snapshot":FOUNDATION,"capability":"asset.build.original",
            "request_sha256":r.sha(r.canonical(request)),"status":"PLANNED",
            "execution_authority":"NONE","dispatch":"BLOCKED","publication":"BLOCKED"}


def validate_receipt(plan,receipt):
    # Validates correlation only. A receipt does not authenticate an agent or prove execution.
    required={"schema","job_id","repository","revision","request_sha256","status","evidence_sha256","evidence_url"}
    r.check(type(plan) is dict and plan.get("repository")==REPO and plan.get("capability")=="asset.build.original" and plan.get("execution_authority")=="NONE","invalid handoff")
    r.check(type(receipt) is dict and set(receipt)==required and type(receipt["schema"]) is int and receipt["schema"]==1,"receipt schema")
    for k in ("job_id","repository","revision","request_sha256"):
        r.check(receipt[k]==plan[k],"receipt mismatch: "+k)
    r.check(receipt["status"] in ("PASS","FAIL","BLOCKED","NOT_RUN","INCONCLUSIVE"),"receipt status")
    r.check(type(receipt["evidence_sha256"]) is str and r.SHA.fullmatch(receipt["evidence_sha256"]),"evidence hash")
    r.check(type(receipt["evidence_url"]) is str and receipt["evidence_url"].startswith("https://github.com/"+REPO+"/actions/runs/") and receipt["evidence_url"].split("/")[-1].isdigit(),"expected Actions run link")
    return {"status":"CORRELATED","reported_status":receipt["status"],"authenticated":False,
            "evidence_verified":False,"dispatch":"BLOCKED","publication":"BLOCKED"}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest="cmd",required=True)
    s=sub.add_parser("plan");s.add_argument("request");s.add_argument("--revision",required=True);s.add_argument("--job-id",required=True)
    s=sub.add_parser("receipt");s.add_argument("plan");s.add_argument("receipt")
    a=p.parse_args()
    try:
        if a.cmd=="plan":result=handoff(a.request,a.revision,a.job_id)
        else:result=validate_receipt(r.read_json(a.plan),r.read_json(a.receipt))
        print(json.dumps(result,indent=2));return 0
    except (ValueError,OSError,TypeError,KeyError) as exc:
        print(json.dumps({"status":"FAIL","error":str(exc)}));return 1


if __name__=="__main__":
    sys.exit(main())
