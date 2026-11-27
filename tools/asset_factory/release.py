"""Owner-signed, local-only candidate packaging. No network, merge or publication."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from asset_factory import registry as r

APPROVAL_FIELDS={"schema","decision","owner","id","version","sha256","request_sha256",
                 "revision","license","rights_evidence","review_evidence","scope"}


def statement(row,rights,review):
    for value in (rights,review):
        r.check(type(value) is str and 1<=len(value.strip())<=1000,"evidence required")
    return {"schema":1,"decision":"APPROVE_LOCAL_INTEGRATION_PACKAGE","owner":"Jugadru",
            "id":row["id"],"version":row["version"],"sha256":row["digest"],
            "request_sha256":row["request_sha"],"revision":row["revision"],
            "license":"ORIGINAL","rights_evidence":rights,"review_evidence":review,
            "scope":"LOCAL_ONLY_NO_PUBLICATION"}


def verify_signature(approval,signature,key,expected_key_sha):
    r.check(type(expected_key_sha) is str and r.SHA.fullmatch(expected_key_sha),"trusted key fingerprint required")
    key_bytes=r.read_bytes(key,16384)
    r.check(r.sha(key_bytes)==expected_key_sha,"public key fingerprint mismatch")
    body=r.read_bytes(approval,16384)
    sig=r.read_bytes(signature,1024)
    # Snapshot bytes before verification so all verified data is exactly what is consumed.
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp)
        for name,data in (("key.pem",key_bytes),("approval.json",body),("signature.bin",sig)):
            (p/name).write_bytes(data)
        completed=subprocess.run(["/usr/bin/openssl","pkeyutl","-verify","-pubin","-inkey",str(p/"key.pem"),
                          "-rawin","-in",str(p/"approval.json"),"-sigfile",str(p/"signature.bin")],
                          capture_output=True,timeout=10,check=False)
        r.check(completed.returncode==0,"approval signature invalid")
        obj=r.read_json(p/"approval.json",16384)
    r.check(type(obj) is dict and set(obj)==APPROVAL_FIELDS and type(obj["schema"]) is int and obj["schema"]==1,"approval schema")
    return obj,body,sig


def make_statement(db,id,version,rights,review):
    c=r.connect(db,create=False)
    try:
        return statement(r.lookup(c,id,version),rights,review)
    finally:c.close()


def package(db,id,version,approval,signature,key,expected_key_sha,out):
    obj,body,sig=verify_signature(approval,signature,key,expected_key_sha)
    out=r.outside_repo(out)
    r.check(not out.exists() and out.parent.is_dir(),"new output directory required")
    c=r.connect(db,create=False)
    created=False
    try:
        c.execute("BEGIN IMMEDIATE")
        row=r.lookup(c,id,version)
        r.check(obj==statement(row,obj["rights_evidence"],obj["review_evidence"]),"approval does not bind this asset")
        r.check(not c.execute("SELECT 1 FROM events WHERE id=? AND version=? AND kind='REVOKED'",(id,version)).fetchone(),"asset revoked")
        raw=c.execute("SELECT body FROM blobs WHERE digest=?",(row["digest"],)).fetchone()[0]
        r.check(r.sha(raw)==row["digest"],"blob integrity mismatch")
        manifest={"schema":1,"status":"LOCAL_PACKAGE","id":id,"version":version,
                  "asset":{"file":"asset.glb","sha256":row["digest"],"bytes":len(raw)},
                  "source_revision":row["revision"],"request_sha256":row["request_sha"],
                  "approval_sha256":r.sha(body),"signature_sha256":r.sha(sig),
                  "trusted_key_sha256":expected_key_sha,"publication":"BLOCKED",
                  "game_integration":"NOT_RUN","license":"ORIGINAL"}
        out.mkdir(mode=0o700)
        created=True
        for name,data in (("asset.glb",raw),("approval.json",body),("approval.sig",sig),
                          ("manifest.json",r.canonical(manifest)+b"\n")):
            with (out/name).open("xb") as f:f.write(data)
        event={"manifest_sha256":r.sha((out/"manifest.json").read_bytes()),"key_sha256":expected_key_sha}
        r.event(c,id,version,"PACKAGED",event)
        c.commit()
        return manifest
    except BaseException:
        c.rollback()
        if created:
            # Only remove our own fixed paths; never a pre-existing directory.
            for name in ("manifest.json","asset.glb","approval.json","approval.sig"):
                (out/name).unlink(missing_ok=True)
            out.rmdir()
        raise
    finally:c.close()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db",required=True)
    sub=p.add_subparsers(dest="cmd",required=True)
    s=sub.add_parser("statement")
    s.add_argument("id");s.add_argument("version");s.add_argument("--rights",required=True);s.add_argument("--review",required=True)
    s=sub.add_parser("package")
    s.add_argument("id");s.add_argument("version")
    for arg in ("approval","signature","key","key-sha256","out"):
        s.add_argument("--"+arg,required=True)
    a=p.parse_args()
    try:
        if a.cmd=="statement":
            result=make_statement(a.db,a.id,a.version,a.rights,a.review)
        else:
            result=package(a.db,a.id,a.version,a.approval,a.signature,a.key,a.key_sha256,a.out)
        print(json.dumps(result,indent=2))
        return 0
    except (ValueError,OSError,subprocess.SubprocessError,TypeError,KeyError) as exc:
        print(json.dumps({"status":"FAIL","error":str(exc),"publication":"BLOCKED"}))
        return 1


if __name__=="__main__":
    sys.exit(main())
