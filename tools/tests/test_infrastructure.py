import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from asset_factory import registry as r, release, bridge, secure_run, native_acceptance
from test_advanced_validator import fixture, encode


class InfrastructureTest(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.db=self.root/"registry.sqlite"
        self.work=self.root/"work"
        self.work.mkdir()
        (self.work/"staging").mkdir()
        self.req=json.loads((r.ROOT/"tools/asset_factory/demo.json").read_text())
        (self.work/"request.json").write_bytes(r.canonical(self.req))
        self.id=self.req["id"]
        self.ver=self.req["version"]
        self.rev="a"*40
        self.doc,self.raw=fixture()
        self.write_asset()

    def write_asset(self):
        raw=encode(self.doc,self.raw)
        (self.work/"staging/asset.glb").write_bytes(raw)
        report={"status":"BUILT","approval":"PENDING","promotion":"BLOCKED",
                "stages":dict.fromkeys(("plan","export","structural_validation","godot_import"),"PASS"),
                "asset":{"sha256":r.sha(raw)}}
        (self.work/"report.json").write_bytes(r.canonical(report))
        return r.sha(raw)

    def register(self):
        return r.register(self.db,self.work,self.rev)

    def test_derived_lod_cannot_replace_primary(self):
        p=self.work/"report.json"
        obj=json.loads(p.read_text())
        for level in (1,2,True,"0"):
            p.write_bytes(r.canonical(dict(obj,derived_lod=level)))
            with self.assertRaisesRegex(ValueError,"derived LOD"):
                self.register()
        p.write_bytes(r.canonical(dict(obj,derived_lod=0)))
        self.assertEqual(self.register()["status"],"REGISTERED")

    def test_registry_idempotence_and_history(self):
        a=self.register()
        self.assertEqual(a["status"],"REGISTERED")
        self.assertEqual(self.register()["status"],"EXISTS")
        self.assertEqual(r.list_assets(self.db)[0]["sha256"],a["sha256"])
        self.assertEqual(r.audit(self.db),{"status":"PASS","assets":1,"events":1})
        r.revoke(self.db,self.id,self.ver,"test")
        self.assertEqual([x["kind"] for x in r.history(self.db,self.id,self.ver)],["REGISTERED","REVOKED"])
        self.assertEqual(r.list_assets(self.db)[0]["revoked"],1)
        with self.assertRaises(ValueError):r.revoke(self.db,self.id,self.ver,"again")

    def test_backup_restore_and_explicit_rollback(self):
        self.register()
        r.select_version(self.db,self.id,self.ver,"initial selection")
        self.req["version"]="0.1.1"
        (self.work/"request.json").write_bytes(r.canonical(self.req))
        self.doc["materials"][0]["pbrMetallicRoughness"]["roughnessFactor"]=0.7
        self.write_asset()
        self.register()
        r.select_version(self.db,self.id,"0.1.1","new version")
        r.select_version(self.db,self.id,self.ver,"explicit rollback")
        self.assertEqual(r.current(self.db,self.id)["version"],self.ver)
        backup=self.root/"snapshot.sqlite"
        self.assertEqual(r.backup(self.db,backup)["assets"],2)
        self.assertEqual(r.current(backup,self.id),r.current(self.db,self.id))
        restored=self.root/"restored.sqlite"
        r.backup(backup,restored)
        r.revoke(restored,self.id,self.ver,"test")
        self.assertEqual(r.current(restored,self.id)["status"],"REVOKED")
        self.assertEqual(r.current(self.db,self.id)["status"],"SELECTED")
        with self.assertRaises(ValueError):r.backup(self.db,backup)
        with self.assertRaises(ValueError):r.audit(self.root/"missing.sqlite")
        with self.assertRaises(ValueError):r.select_version(restored,self.id,self.ver,"revoked")

    def test_prebuild_reservation_conflict_and_release(self):
        request=self.work/"request.json"
        self.assertEqual(r.reserve(self.db,request,self.rev)["status"],"RESERVED")
        self.assertEqual(r.reserve(self.db,request,self.rev)["status"],"EXISTS")
        alt=self.root/"alternative.json"
        alt.write_bytes(r.canonical(dict(self.req,seed=999)))
        with self.assertRaisesRegex(ValueError,"conflict"):r.reserve(self.db,alt,self.rev)
        with self.assertRaisesRegex(ValueError,"matching reservation"):r.release_reservation(self.db,alt,"wrong",self.rev)
        with self.assertRaisesRegex(ValueError,"conflict"):r.register(self.db,self.work,"b"*40)
        r.release_reservation(self.db,request,"failed initial build",self.rev)
        self.assertEqual(r.reserve(self.db,request,self.rev)["status"],"RESERVED")
        self.assertEqual(self.register()["status"],"REGISTERED")
        self.assertEqual([x["kind"] for x in r.reservations(self.db,self.id,self.ver)],["RESERVED","RELEASED","RESERVED","CONSUMED"])
        with self.assertRaises(ValueError):r.reserve(self.db,request,self.rev)
        with self.assertRaises(ValueError):r.release_reservation(self.db,request,"too late",self.rev)
        c=r.connect(self.db)
        try:
            with self.assertRaises(sqlite3.IntegrityError):c.execute("DELETE FROM reservations")
        finally:c.close()

    def test_concurrent_same_id(self):
        # Initialize schema before competing writers; transaction serializes inserts.
        r.connect(self.db).close()
        with ThreadPoolExecutor(max_workers=4) as pool:
            statuses=list(pool.map(lambda _:self.register()["status"],range(4)))
        self.assertEqual(statuses.count("REGISTERED"),1)
        self.assertEqual(statuses.count("EXISTS"),3)
        self.assertEqual(r.audit(self.db)["events"],1)

    def test_conflict_and_sql_immutability(self):
        self.register()
        self.doc["materials"][0]["pbrMetallicRoughness"]["roughnessFactor"]=0.7
        self.write_asset()
        with self.assertRaisesRegex(ValueError,"conflict"):self.register()
        c=r.connect(self.db)
        try:
            for sql in ("DELETE FROM assets","UPDATE assets SET revision='bad'","DELETE FROM blobs","DELETE FROM events"):
                with self.assertRaises(sqlite3.IntegrityError):c.execute(sql)
        finally:c.close()
        self.assertEqual(r.audit(self.db)["assets"],1)

    def test_tamper_or_incomplete(self):
        p=self.work/"report.json"
        obj=json.loads(p.read_text())
        obj["stages"]["godot_import"]="NOT_RUN"
        p.write_bytes(r.canonical(obj))
        with self.assertRaisesRegex(ValueError,"incomplete"):self.register()
        self.write_asset()
        p.write_bytes(p.read_bytes().replace(b'"sha256":"',b'"sha256":"x'))
        with self.assertRaisesRegex(ValueError,"mismatch"):self.register()

    def test_signature_and_package(self):
        self.register()
        # Ephemeral test key; never commit a private key or trust it for actual assets.
        key=self.root/"key.pem";pub=self.root/"pub.pem";sig=self.root/"approval.sig"
        approval=self.root/"approval.json"
        def openssl(*args):
            subprocess.run(["/usr/bin/openssl",*map(str,args)],check=True,capture_output=True,timeout=10)
        openssl("genpkey","-algorithm","ED25519","-out",key)
        openssl("pkey","-in",key,"-pubout","-out",pub)
        statement=release.make_statement(self.db,self.id,self.ver,"synthetic fixture rights","synthetic fixture review")
        approval.write_bytes(r.canonical(statement))
        openssl("pkeyutl","-sign","-inkey",key,"-rawin","-in",approval,"-out",sig)
        fingerprint=r.sha(pub.read_bytes())
        out=self.root/"package"
        with self.assertRaisesRegex(ValueError,"fingerprint"):
            release.package(self.db,self.id,self.ver,approval,sig,pub,"b"*64,out)
        approval.write_bytes(r.canonical(dict(statement,owner="other")))
        with self.assertRaisesRegex(ValueError,"signature"):
            release.package(self.db,self.id,self.ver,approval,sig,pub,fingerprint,out)
        approval.write_bytes(r.canonical(statement))
        manifest=release.package(self.db,self.id,self.ver,approval,sig,pub,fingerprint,out)
        self.assertEqual(manifest["publication"],"BLOCKED")
        self.assertEqual(r.sha((out/"asset.glb").read_bytes()),statement["sha256"])
        self.assertEqual(r.history(self.db,self.id,self.ver)[-1]["kind"],"PACKAGED")
        with self.assertRaises(ValueError):release.package(self.db,self.id,self.ver,approval,sig,pub,fingerprint,out)
        r.revoke(self.db,self.id,self.ver,"test")
        with self.assertRaisesRegex(ValueError,"revoked"):
            release.package(self.db,self.id,self.ver,approval,sig,pub,fingerprint,self.root/"other")

    def test_bridge_correlation_not_authorization(self):
        plan=bridge.handoff(self.work/"request.json",self.rev,"test-job")
        self.assertEqual(plan["execution_authority"],"NONE")
        receipt={k:plan[k] for k in ("job_id","repository","revision","request_sha256")}
        receipt.update(schema=1,status="PASS",evidence_sha256="c"*64,
                       evidence_url="https://github.com/Jugadru/apex-asset-factory/actions/runs/123")
        result=bridge.validate_receipt(plan,receipt)
        self.assertEqual(result["status"],"CORRELATED")
        self.assertFalse(result["authenticated"])
        with self.assertRaisesRegex(ValueError,"mismatch"):
            bridge.validate_receipt(plan,dict(receipt,revision="b"*40))
        with self.assertRaises(ValueError):
            bridge.validate_receipt(plan,dict(receipt,evidence_url="https://evil.example/123"))

    def test_process_limits_and_timeout(self):
        import os
        from unittest.mock import patch
        with patch.dict(os.environ,{"GITHUB_TOKEN":"fake-secret"},clear=False):
            output=secure_run.run([sys.executable,"-c","import os;print(os.getenv('GITHUB_TOKEN'));print(os.environ['HOME'])"],
                                  self.work,self.work/"env.log",5)
        self.assertIn("None",output)
        self.assertIn("runtime-home",output)
        with self.assertRaises(subprocess.TimeoutExpired):
            secure_run.run([sys.executable,"-c","import time;time.sleep(10)"],self.work,self.work/"timeout.log",0.1)
        with self.assertRaises(ValueError):
            secure_run.run([sys.executable,"-c","pass"],self.work,self.work/"env.log",5)
        with self.assertRaises(ValueError):
            secure_run.run([sys.executable,"-c","pass"],self.work,self.root/"outside.log",5)

    def test_native_harness_failure_receipt(self):
        from unittest.mock import patch
        out=self.root/"native"
        with patch.object(r,"verified_revision",return_value=self.rev):
            result=native_acceptance.acceptance("/missing/blender","/missing/godot",out)
        self.assertEqual(result["status"],"FAIL")
        self.assertTrue((out/"acceptance.json").exists())
        self.assertEqual(result["promotion"],"BLOCKED")


if __name__=="__main__":
    unittest.main()
