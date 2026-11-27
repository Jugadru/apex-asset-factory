"""Transactional local content-addressed registry; no network or publication."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys

from asset_factory.build import read_request
from asset_factory.validate_glb import inspect, MAX_BYTES

SHA = re.compile(r"[0-9a-f]{64}")
REV = re.compile(r"[0-9a-f]{40}")
ID = re.compile(r"[a-z0-9][a-z0-9_-]{0,63}")
VER = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")
ROOT = Path(__file__).resolve().parents[2]


def check(ok, message):
    if not ok:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode("utf-8")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_bytes(path, limit):
    p = Path(path)
    check(p.is_file() and not p.is_symlink(), "regular input file required")
    with p.open("rb") as f:
        data=f.read(limit+1)
    check(0 < len(data) <= limit, "input size limit")
    return data


def read_json(path, limit=1024*1024):
    def unique(pairs):
        d={}
        for k,v in pairs:
            check(k not in d,"duplicate JSON key")
            d[k]=v
        return d
    def bad(v):
        raise ValueError("nonfinite JSON constant")
    return json.loads(read_bytes(path,limit),object_pairs_hook=unique,parse_constant=bad)


def identity(id, version):
    check(type(id) is str and ID.fullmatch(id), "invalid asset id")
    check(type(version) is str and len(version)<=32 and VER.fullmatch(version), "invalid asset version")


def outside_repo(p):
    p=Path(p).absolute()
    check(not p.is_symlink(),"symlink path")
    p=p.resolve()
    check(p!=ROOT and ROOT not in p.parents,"registry/workspace outside checkout required")
    return p


def connect(path,create=True):
    p=outside_repo(path)
    check(p.parent.is_dir(),"registry parent missing")
    if not create:
        check(p.is_file(),"registry does not exist")
    c=sqlite3.connect(p.as_uri()+("?mode=rwc" if create else "?mode=rw"),uri=True,timeout=10,isolation_level=None)
    c.row_factory=sqlite3.Row
    try:
        c.execute("PRAGMA foreign_keys=ON")
        c.execute("PRAGMA busy_timeout=10000")
        c.executescript("""
        CREATE TABLE IF NOT EXISTS blobs (
            digest TEXT PRIMARY KEY, body BLOB NOT NULL
        );
        CREATE TABLE IF NOT EXISTS assets (
            id TEXT NOT NULL, version TEXT NOT NULL, digest TEXT NOT NULL REFERENCES blobs(digest),
            request_sha TEXT NOT NULL, request_json TEXT NOT NULL,
            report_json TEXT NOT NULL, revision TEXT NOT NULL,
            PRIMARY KEY(id,version)
        );
        CREATE TABLE IF NOT EXISTS events (
            seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT NOT NULL, version TEXT NOT NULL,
            kind TEXT NOT NULL, detail TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(id,version) REFERENCES assets(id,version)
        );
        CREATE TABLE IF NOT EXISTS reservations (
            seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT NOT NULL, version TEXT NOT NULL,
            request_sha TEXT NOT NULL, revision TEXT NOT NULL,
            kind TEXT NOT NULL CHECK(kind IN ('RESERVED','RELEASED','CONSUMED')),
            reason TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS reservations_lookup ON reservations(id,version,seq);
        CREATE TRIGGER IF NOT EXISTS reservations_no_update BEFORE UPDATE ON reservations BEGIN SELECT RAISE(ABORT,'immutable reservation'); END;
        CREATE TRIGGER IF NOT EXISTS reservations_no_delete BEFORE DELETE ON reservations BEGIN SELECT RAISE(ABORT,'immutable reservation'); END;
        CREATE TRIGGER IF NOT EXISTS assets_no_update BEFORE UPDATE ON assets BEGIN SELECT RAISE(ABORT,'immutable asset'); END;
        CREATE TRIGGER IF NOT EXISTS assets_no_delete BEFORE DELETE ON assets BEGIN SELECT RAISE(ABORT,'immutable asset'); END;
        CREATE TRIGGER IF NOT EXISTS blobs_no_update BEFORE UPDATE ON blobs BEGIN SELECT RAISE(ABORT,'immutable blob'); END;
        CREATE TRIGGER IF NOT EXISTS blobs_no_delete BEFORE DELETE ON blobs BEGIN SELECT RAISE(ABORT,'immutable blob'); END;
        CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT,'immutable event'); END;
        CREATE TRIGGER IF NOT EXISTS events_no_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT,'immutable event'); END;
        """)
        return c
    except BaseException:
        c.close()
        raise


def event(c,id,version,kind,detail):
    c.execute("INSERT INTO events(id,version,kind,detail) VALUES(?,?,?,?)",
              (id,version,kind,canonical(detail).decode()))


def verified_revision():
    head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True,timeout=10).strip()
    dirty=subprocess.check_output(["git","status","--porcelain","--untracked-files=all"],cwd=ROOT,text=True,timeout=10)
    check(REV.fullmatch(head) and not dirty.strip(),"clean tracked git checkout required")
    return head


def reservation_latest(c,id,version):
    return c.execute("SELECT * FROM reservations WHERE id=? AND version=? ORDER BY seq DESC LIMIT 1",(id,version)).fetchone()


def reservation_event(c,id,version,req_hash,revision,kind,reason):
    c.execute("INSERT INTO reservations(id,version,request_sha,revision,kind,reason) VALUES(?,?,?,?,?,?)",
              (id,version,req_hash,revision,kind,reason))


def reserve_in_transaction(c,id,version,req_hash,revision):
    prev=reservation_latest(c,id,version)
    if prev and prev["kind"]=="RESERVED":
        check((prev["request_sha"],prev["revision"])==(req_hash,revision),"reservation conflict")
        return "EXISTS"
    check(not prev or prev["kind"]!="CONSUMED","version already consumed")
    reservation_event(c,id,version,req_hash,revision,"RESERVED","reserve before build")
    return "RESERVED"


def reserve(db,request_path,revision=None):
    request=read_request(Path(request_path))
    id,version=request["id"],request["version"]
    identity(id,version)
    revision=revision or verified_revision()
    check(type(revision) is str and REV.fullmatch(revision),"invalid source revision")
    req_hash=sha(canonical(request))
    c=connect(db)
    try:
        c.execute("BEGIN IMMEDIATE")
        check(not c.execute("SELECT 1 FROM assets WHERE id=? AND version=?",(id,version)).fetchone(),"version already registered")
        status=reserve_in_transaction(c,id,version,req_hash,revision)
        c.commit()
        return {"status":status,"id":id,"version":version,"request_sha256":req_hash,"revision":revision}
    except BaseException:
        c.rollback();raise
    finally:c.close()


def release_reservation(db,request_path,reason,revision=None):
    request=read_request(Path(request_path))
    id,version=request["id"],request["version"]
    identity(id,version)
    revision=revision or verified_revision()
    check(type(revision) is str and REV.fullmatch(revision),"invalid source revision")
    check(type(reason) is str and 1<=len(reason.strip())<=500,"release reason required")
    req_hash=sha(canonical(request))
    c=connect(db,create=False)
    try:
        c.execute("BEGIN IMMEDIATE")
        prev=reservation_latest(c,id,version)
        check(prev and prev["kind"]=="RESERVED" and (prev["request_sha"],prev["revision"])==(req_hash,revision),"matching reservation required")
        reservation_event(c,id,version,req_hash,revision,"RELEASED",reason)
        c.commit()
        return {"status":"RELEASED","id":id,"version":version}
    except BaseException:
        c.rollback();raise
    finally:c.close()


def reservations(db,id,version):
    identity(id,version)
    c=connect(db,create=False)
    try:
        return [dict(x) for x in c.execute("SELECT * FROM reservations WHERE id=? AND version=? ORDER BY seq",(id,version))]
    finally:c.close()


def register(db,workspace,revision=None):
    # Revision override is for explicit offline receipts/tests; not cryptographic provenance.
    revision=revision or verified_revision()
    check(type(revision) is str and REV.fullmatch(revision),"invalid source revision")
    w=outside_repo(workspace)
    request=read_request(w/"request.json")
    id,version=request["id"],request["version"]
    identity(id,version)
    check(request["license"]=="ORIGINAL","original assets only")
    report=read_json(w/"report.json")
    check(type(report.get("derived_lod",0)) is int and report.get("derived_lod",0)==0,"derived LOD cannot register as primary asset")
    check(report.get("status")=="BUILT" and report.get("promotion")=="BLOCKED" and report.get("approval")=="PENDING","candidate report required")
    check(all(report.get("stages",{}).get(k)=="PASS" for k in ("plan","export","structural_validation","godot_import")),"incomplete build evidence")
    glb=w/"staging"/"asset.glb"
    check(glb.resolve()==glb,"unsafe GLB path")
    qa=inspect(glb,request["triangle_budget"])[0]
    raw=read_bytes(glb,MAX_BYTES)
    digest=sha(raw)
    check(qa["sha256"]==digest==report.get("asset",{}).get("sha256"),"asset changed or report mismatch")
    req=canonical(request)
    c=connect(db)
    try:
        c.execute("BEGIN IMMEDIATE")
        previous=c.execute("SELECT * FROM assets WHERE id=? AND version=?",(id,version)).fetchone()
        if previous:
            check((previous["digest"],previous["request_sha"],previous["revision"])==(digest,sha(req),revision),"immutable id/version conflict")
            c.commit()
            return {"status":"EXISTS","id":id,"version":version,"sha256":digest,"promotion":"BLOCKED"}
        reserve_in_transaction(c,id,version,sha(req),revision)
        c.execute("INSERT OR IGNORE INTO blobs VALUES (?,?)",(digest,raw))
        check(sha(c.execute("SELECT body FROM blobs WHERE digest=?",(digest,)).fetchone()[0])==digest,"blob integrity mismatch")
        c.execute("INSERT INTO assets VALUES (?,?,?,?,?,?,?)",(id,version,digest,sha(req),req.decode(),canonical(report).decode(),revision))
        event(c,id,version,"REGISTERED",{"sha256":digest,"revision":revision,"qa":qa,"provenance":"local receipt; not signed"})
        reservation_event(c,id,version,sha(req),revision,"CONSUMED","asset registered")
        c.commit()
        return {"status":"REGISTERED","id":id,"version":version,"sha256":digest,"promotion":"BLOCKED"}
    except BaseException:
        c.rollback()
        raise
    finally:
        c.close()


def lookup(c,id,version):
    identity(id,version)
    row=c.execute("SELECT * FROM assets WHERE id=? AND version=?",(id,version)).fetchone()
    check(row is not None,"unknown asset/version")
    return row


def list_assets(db):
    c=connect(db,create=False)
    try:
        return [dict(r) for r in c.execute("""SELECT id,version,digest AS sha256,request_sha,revision,
          EXISTS(SELECT 1 FROM events e WHERE e.id=a.id AND e.version=a.version AND e.kind='REVOKED') AS revoked
          FROM assets a ORDER BY id,version""")]
    finally:
        c.close()


def history(db,id,version):
    c=connect(db,create=False)
    try:
        lookup(c,id,version)
        return [dict(r) for r in c.execute("SELECT * FROM events WHERE id=? AND version=? ORDER BY seq",(id,version))]
    finally:
        c.close()


def revoke(db,id,version,reason):
    check(type(reason) is str and 1<=len(reason.strip())<=500,"revocation reason required")
    c=connect(db,create=False)
    try:
        c.execute("BEGIN IMMEDIATE")
        lookup(c,id,version)
        check(not c.execute("SELECT 1 FROM events WHERE id=? AND version=? AND kind='REVOKED'",(id,version)).fetchone(),"already revoked")
        event(c,id,version,"REVOKED",{"reason":reason})
        c.commit()
    except BaseException:
        c.rollback()
        raise
    finally:
        c.close()
    return {"status":"REVOKED","id":id,"version":version,"promotion":"BLOCKED"}


def audit(db):
    c=connect(db,create=False)
    try:
        check(c.execute("PRAGMA integrity_check").fetchone()[0]=="ok","SQLite integrity error")
        check(not c.execute("PRAGMA foreign_key_check").fetchall(),"registry foreign keys")
        for r in c.execute("SELECT digest,body FROM blobs"):
            check(sha(r["body"])==r["digest"],"blob integrity mismatch")
        for row in c.execute("SELECT * FROM assets"):
            check(sha(row["request_json"].encode())==row["request_sha"],"request integrity mismatch")
            request=json.loads(row["request_json"])
            report=json.loads(row["report_json"])
            identity(row["id"],row["version"])
            check(request["id"]==row["id"] and request["version"]==row["version"] and request["license"]=="ORIGINAL","registry request identity")
            check(report["asset"]["sha256"]==row["digest"] and REV.fullmatch(row["revision"]),"registry report identity")
            check(c.execute("SELECT count(*) FROM events WHERE id=? AND version=? AND kind='REGISTERED'",(row["id"],row["version"])).fetchone()[0]==1,"registry registration event")
        return {"status":"PASS","assets":c.execute("SELECT count(*) FROM assets").fetchone()[0],
                "events":c.execute("SELECT count(*) FROM events").fetchone()[0]}
    finally:
        c.close()


def select_version(db,id,version,reason):
    """Record explicit rollback/selection without modifying or copying assets."""
    check(type(reason) is str and 1<=len(reason.strip())<=500,"selection reason required")
    c=connect(db,create=False)
    try:
        c.execute("BEGIN IMMEDIATE")
        row=lookup(c,id,version)
        check(not c.execute("SELECT 1 FROM events WHERE id=? AND version=? AND kind='REVOKED'",(id,version)).fetchone(),"asset revoked")
        event(c,id,version,"SELECTED",{"reason":reason,"sha256":row["digest"]})
        c.commit()
        return {"status":"SELECTED","id":id,"version":version,"sha256":row["digest"],"game_integration":"NOT_RUN"}
    except BaseException:
        c.rollback()
        raise
    finally:c.close()


def current(db,id):
    check(type(id) is str and ID.fullmatch(id),"invalid asset id")
    c=connect(db,create=False)
    try:
        row=c.execute("SELECT version,detail FROM events WHERE id=? AND kind='SELECTED' ORDER BY seq DESC LIMIT 1",(id,)).fetchone()
        if row is None:return {"status":"NOT_SELECTED","id":id}
        asset=lookup(c,id,row["version"])
        revoked=c.execute("SELECT 1 FROM events WHERE id=? AND version=? AND kind='REVOKED'",(id,row["version"])).fetchone()
        return {"status":"REVOKED" if revoked else "SELECTED","id":id,"version":row["version"],
                "sha256":asset["digest"],"game_integration":"NOT_RUN"}
    finally:c.close()


def backup(db,destination):
    """SQLite consistent online snapshot, no overwrite; audit destination."""
    src=outside_repo(db)
    dst=outside_repo(destination)
    check(src!=dst and not dst.exists() and dst.parent.is_dir(),"new backup path required")
    audit(src)
    c=connect(src,create=False)
    fd=None
    created=False
    try:
        fd=os.open(dst,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        created=True
        os.close(fd);fd=None
        target=sqlite3.connect(dst)
        try:c.backup(target)
        finally:target.close()
        result=audit(dst)
        digest=hashlib.sha256()
        with dst.open("rb") as handle:
            for chunk in iter(lambda:handle.read(1024*1024),b""):
                digest.update(chunk)
        result["backup_sha256"]=digest.hexdigest()
        return result
    except BaseException:
        if created:dst.unlink(missing_ok=True)
        raise
    finally:
        if fd is not None:os.close(fd)
        c.close()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db",required=True)
    subs=p.add_subparsers(dest="command",required=True)
    subs.add_parser("register").add_argument("workspace")
    subs.add_parser("reserve").add_argument("request")
    rel=subs.add_parser("release-reservation");rel.add_argument("request");rel.add_argument("reason")
    subs.add_parser("list")
    subs.add_parser("audit")
    subs.add_parser("backup").add_argument("destination")
    subs.add_parser("current").add_argument("id")
    for name in ("history","revoke","select","reservations"):
        sub=subs.add_parser(name)
        sub.add_argument("id");sub.add_argument("version")
        if name in ("revoke","select"):sub.add_argument("reason")
    a=p.parse_args()
    try:
        result={"register":lambda:register(a.db,a.workspace),"reserve":lambda:reserve(a.db,a.request),
                "release-reservation":lambda:release_reservation(a.db,a.request,a.reason),
                "reservations":lambda:reservations(a.db,a.id,a.version),"list":lambda:list_assets(a.db),
                "audit":lambda:audit(a.db),"history":lambda:history(a.db,a.id,a.version),
                "revoke":lambda:revoke(a.db,a.id,a.version,a.reason),
                "select":lambda:select_version(a.db,a.id,a.version,a.reason),
                "current":lambda:current(a.db,a.id),"backup":lambda:backup(a.db,a.destination)}[a.command]()
    except (ValueError,OSError,sqlite3.Error,subprocess.SubprocessError,KeyError,TypeError) as exc:
        print(json.dumps({"status":"FAIL","error":str(exc),"promotion":"BLOCKED"}))
        return 1
    print(json.dumps(result,indent=2))
    return 0


if __name__=="__main__":
    sys.exit(main())
