"""Explicitly authorized read-only Factory adapter; original demo, isolated staging."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time
import uuid

from .orchestrator import checked_targets, digest, git, require, SHA, unique_object
from .registry import Registry, encode, now, ident

FACTORY_SHA = "640b037b30fbe729885867bf51ea6d40d0b66466"
REQUIRED = ("tools/asset_factory/build.py", "tools/asset_factory/demo.json",
            "tools/asset_factory/request.schema.json", "tools/asset_factory/vehicle.py",
            "tools/asset_factory/staging.gd", "tools/apex_asset_build.py",
            "tools/apex_foundation.py", "tools/apex_lab_graphics.py")
MAX_JSON = 65536
MAX_ASSET = 32 * 1024 * 1024
MAX_LOG = 2 * 1024 * 1024
HEX = re.compile(r"[0-9a-f]{64}\Z")
STAGES = ("plan", "export", "structural_validation", "godot_import", "capture",
          "manual_review", "promotion")
# Fixed wrapper imports existing domain validator, never a command from request JSON.
PLAN_CODE = r"""
import sys, json, importlib.util
from pathlib import Path
root = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("factory", root / "tools/asset_factory/build.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
request = module.read_request(Path(sys.argv[2]))
legacy = {"schema":1,"jobs":[{"id":request["id"],"kind":"car","era":request["era"],
          "source":None,"approved":True,"license":"ORIGINAL","output":"staging/asset.glb",
          "triangle_budget":request["triangle_budget"],"texture_max_px":request["texture_max_px"]}]}
p = Path(sys.argv[3])
with p.open("x", encoding="utf-8") as f:
    json.dump(legacy, f, allow_nan=False)
print(json.dumps({"request":request,"plan":module.plan(p)},allow_nan=False))
"""


def read(path, limit=MAX_JSON):
    path = Path(path)
    require(path.is_file() and path.resolve() == path, "Missing or unsafe evidence file")
    with path.open("rb") as f:
        raw = f.read(limit + 1)
    require(len(raw) <= limit, "Evidence exceeds byte limit")
    return json.loads(raw, object_pairs_hook=unique_object,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite JSON")))


def dump(path, value):
    with path.open("x", encoding="utf-8") as f:
        json.dump(value, f, indent=2, sort_keys=True, allow_nan=False)
        f.write("\n")


def number(value, minimum, maximum):
    return type(value) is int and minimum <= value <= maximum


def file_evidence(root, relative, limit):
    p = root / relative
    require(p.is_file() and p.resolve() == p and 0 < p.stat().st_size <= limit, "Missing/oversized artifact: " + relative)
    return {"path": relative, "bytes": p.stat().st_size, "sha256": digest(p)}


def check_factory(checkout, revision):
    require(revision == FACTORY_SHA, "Factory revision not reviewed by Hub 1.5")
    root, head = checked_targets([("assets", checkout, revision)])["assets"]
    for rel in REQUIRED:
        p = root / rel
        require(p.is_file() and p.resolve() == p and git(root, "ls-files", "--error-unmatch", "--", rel) == rel,
                "Required tracked Factory file missing")
    return root, head, {rel: digest(root / rel) for rel in REQUIRED}


def executable(path, expected, roots):
    require(isinstance(expected, str) and HEX.fullmatch(expected), "Exact executable SHA256 required")
    p = Path(path).resolve(strict=True)
    require(p.is_file() and os.access(p, os.X_OK) and
            not any(p.is_relative_to(root) for root in roots), "Executable must be outside checkout and evidence")
    require(digest(p) == expected, "Executable digest mismatch")
    return p


def execute(argv, cwd, log, timeout, home, capture=False):
    env = {"PATH": os.defpath, "LANG": "C.UTF-8", "HOME": str(home),
           "XDG_CONFIG_HOME": str(home / "config"), "XDG_CACHE_HOME": str(home / "cache"),
           "PYTHONDONTWRITEBYTECODE": "1", "OMP_NUM_THREADS": "2"}
    if capture:
        # Always use software rendering; Factory itself chooses xvfb-run.
        env["LIBGL_ALWAYS_SOFTWARE"] = "1"
    with log.open("xb") as stream:
        p = subprocess.Popen(argv, cwd=cwd, env=env, stdout=stream, stderr=subprocess.STDOUT,
                             start_new_session=True)
        end = time.monotonic() + timeout
        reason = None
        try:
            while p.poll() is None:
                if time.monotonic() >= end:
                    reason = "deadline exceeded"
                    break
                if log.stat().st_size > MAX_LOG:
                    reason = "log budget exceeded"
                    break
                time.sleep(.05)
        finally:
            # Kill surviving group members as well; trusted tools must not detach.
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            p.wait(timeout=10)
    if reason:
        raise ValueError(reason)
    require(log.stat().st_size <= MAX_LOG, "Log budget exceeded")
    return p.returncode


def accept_plan(data, request):
    require(isinstance(data, dict) and set(data) == {"request", "plan"} and data["request"] == request,
            "Factory request mismatch")
    plan = data["plan"]
    require(isinstance(plan, dict) and plan.get("executed") is False and plan.get("schema") == 1
            and isinstance(plan.get("jobs"), list) and len(plan["jobs"]) == 1, "Invalid Factory plan")
    job = plan["jobs"][0]
    require(job.get("id") == request["id"] and job.get("status") == "PLANNED"
            and job.get("output") == "staging/asset.glb", "Factory did not plan original staging")
    return plan


def accept_build(work, request, capture):
    report = read(work / "report.json")
    registry = read(work / "registry.json")
    require(report.get("factory_version") == "0.1.0" and report.get("status") == "BUILT"
            and report.get("approval") == "PENDING" and report.get("promotion") == "BLOCKED", "Factory build not accepted")
    stages = report.get("stages")
    expected = {k: "PASS" for k in STAGES[:4]}
    expected.update(capture="PASS" if capture else "NOT_RUN", manual_review="NOT_RUN", promotion="BLOCKED")
    require(stages == expected, "Factory stage acceptance mismatch")
    require(read(work / "request.json") == request, "Built request mismatch")
    asset = report.get("asset", {})
    actual = file_evidence(work, "staging/asset.glb", MAX_ASSET)
    require(asset.get("sha256") == actual["sha256"] and asset.get("bytes") == actual["bytes"]
            and number(asset.get("mesh_triangles"), 1, request["triangle_budget"])
            and asset.get("textures") == 0 and type(asset.get("textures")) is int
            and asset.get("structural_qa") == "PASS" and asset.get("attribute_presence") == "PASS"
            and asset.get("godot_import") == "PASS" and asset.get("promotion") == "BLOCKED",
            "Asset evidence/budget mismatch")
    require(registry.get("id") == request["id"] and registry.get("version") == request["version"]
            and registry.get("author") == request["author"] and registry.get("license") == "ORIGINAL"
            and registry.get("origin") == "original procedural" and registry.get("dependencies") == []
            and registry.get("approval") == "PENDING" and registry.get("promotion") == "BLOCKED"
            and registry.get("asset") == asset and registry.get("status") == "BUILT"
            and registry.get("request_sha256") == digest(work / "request.json"), "Registry provenance mismatch")
    fixture = report.get("godot_fixture", {})
    sizes = fixture.get("size")
    require(number(fixture.get("meshes"), 4, 100000) and isinstance(sizes, list) and len(sizes) == 3,
            "Invalid Godot fixture")
    expected_sizes = [request["dimensions_m"][k] for k in ("width", "height", "length")]
    require(all(type(x) in (int, float) and math.isfinite(x) and abs(x-y) <= .02*y
                for x,y in zip(sizes, expected_sizes)), "Godot size mismatch")
    require(str(report.get("blender", "")).startswith("Blender 5.3.")
            and str(report.get("godot", "")).startswith("4.7.2."), "Unexpected native runtime")
    evidence = [actual, file_evidence(work, "request.json", MAX_JSON),
                file_evidence(work, "report.json", MAX_JSON), file_evidence(work, "registry.json", MAX_JSON)]
    for rel in ("plan.json", "blender-version.log", "godot-version.log", "blender.log",
                "godot-import.log", "godot-test.log"):
        evidence.append(file_evidence(work, rel, MAX_LOG))
    if capture:
        image = file_evidence(work, "staging/capture.png", MAX_ASSET)
        info = report.get("capture", {})
        require(info.get("sha256") == image["sha256"] and info.get("bytes") == image["bytes"]
                and info.get("width") == 960 and info.get("height") == 540, "Capture evidence mismatch")
        evidence += [image, file_evidence(work, "godot-capture.log", MAX_LOG)]
    return report, evidence


class Graphics:
    def __init__(self, registry):
        self.store = Registry(registry)
        with self.store.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS graphics_runs (id TEXT PRIMARY KEY, created TEXT NOT NULL, state TEXT NOT NULL, snapshot TEXT NOT NULL)")

    def get(self, sid):
        with self.store.connect() as db:
            row = db.execute("SELECT snapshot FROM graphics_runs WHERE id=?", (ident(sid),)).fetchone()
            require(row is not None, "Unknown graphics run")
            return json.loads(row[0])

    def list(self):
        with self.store.connect() as db:
            return [json.loads(x[0]) for x in db.execute("SELECT snapshot FROM graphics_runs ORDER BY created DESC LIMIT 100")]

    def recover(self, sid):
        with self.store.lock(sid):
            row = self.get(sid)
            require(row["state"] == "RUNNING", "Only abandoned graphics run may be recovered")
            row.update(state="INTERRUPTED", reason="No replay; inspect orphan processes and evidence")
            self.save(row)
            return row

    def save(self, row, start=False):
        with self.store.connect() as db:
            if start:
                db.execute("INSERT INTO graphics_runs VALUES (?,?,?,?)", (row["id"], now(), row["state"], encode(row)))
            else:
                db.execute("UPDATE graphics_runs SET state=?,snapshot=? WHERE id=?", (row["state"], encode(row), row["id"]))

    def run(self, checkout, revision, request_path, *, build=False, blender=None, godot=None,
            blender_sha=None, godot_sha=None, capture=False):
        root, head, source = check_factory(checkout, revision)
        require(not self.store.root.is_relative_to(root) and not root.is_relative_to(self.store.root),
                "Registry must be outside Factory checkout")
        request_path = Path(request_path).resolve(strict=True)
        request = read(request_path)
        require(isinstance(request, dict), "Request must be object")
        require(not capture or build, "Capture requires build")
        sid = uuid.uuid4().hex
        row = {"schema": 1, "id": sid, "factory_sha": head, "source_sha256": source,
               "mode": "build" if build else "plan", "state": "RUNNING",
               "promotion": "BLOCKED", "approval": "PENDING", "manual_review": "NOT_RUN",
               "physical_gpu": "NOT_RUN", "request": request, "evidence": []}
        with self.store.lock(sid):
            # Fresh private workspace, no overwrite or asset promotion.
            work = self.store.root / ("graphics-" + sid)
            work.mkdir(mode=0o700, exist_ok=False)
            self.save(row, start=True)
            try:
                home = work / "home"
                home.mkdir(mode=0o700)
                req = work / "request.json"
                dump(req, request)
                row["request_sha256"] = digest(req)
                log = work / "plan.log"
                code = execute([sys.executable, "-I", "-B", "-c", PLAN_CODE, str(root),
                                str(req), str(work / "foundation-job.json")], work, log, 30, home)
                require(code == 0, "Factory request validator rejected request")
                row["plan"] = accept_plan(read(log), request)
                row["evidence"] = [file_evidence(work, "request.json", MAX_JSON),
                                   file_evidence(work, "plan.log", MAX_JSON),
                                   file_evidence(work, "foundation-job.json", MAX_JSON)]
                row["native"] = "NOT_RUN"
                if build:
                    b = executable(blender, blender_sha, (root, self.store.root))
                    g = executable(godot, godot_sha, (root, self.store.root))
                    row["runtimes"] = {"blender_sha256": blender_sha, "godot_sha256": godot_sha}
                    if capture:
                        import shutil
                        require(shutil.which("xvfb-run", path=os.defpath), "Xvfb required for capture")
                    native = work / "native"
                    args = [sys.executable, "-I", "-B", str(root / REQUIRED[0]), str(req),
                            "--blender", str(b), "--godot", str(g), "--workspace", str(native)]
                    if capture:
                        args.append("--capture")
                    row["native"] = "BLOCKED"
                    self.save(row)
                    code = execute(args, work, work / "build.log", 480, home, capture)
                    row["evidence"].append(file_evidence(work, "build.log", MAX_LOG))
                    require(code == 0, "Native Factory build failed; inspect build.log")
                    report, evidence = accept_build(native, request, capture)
                    require(digest(b) == blender_sha and digest(g) == godot_sha, "Runtime changed during build")
                    require(read(native / "registry.json").get("generator_sha256") == source["tools/asset_factory/vehicle.py"],
                            "Generator digest mismatch")
                    row["report"] = report
                    row["evidence"] += [{**e, "path": "native/" + e["path"]} for e in evidence]
                    row["native"] = "PASS"
                require(git(root, "rev-parse", "HEAD") == head and not git(root, "status", "--porcelain", "--untracked-files=all")
                        and all(digest(root / rel) == h for rel,h in source.items()), "Factory checkout changed")
                row["state"] = "PASS"
            except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
                row.update(state="BLOCKED", reason=type(exc).__name__ + ": " + str(exc)[:180])
                if "native" not in row:
                    row["native"] = "NOT_RUN"
                if row.get("native") == "PASS":
                    row["native"] = "INCONCLUSIVE"
                # Preserve bounded failure logs where available.
                known = {x["path"] for x in row["evidence"]}
                for rel in ("plan.log", "build.log", "native/report.json", "native/registry.json"):
                    try:
                        if rel not in known:
                            row["evidence"].append(file_evidence(work, rel, MAX_LOG))
                    except (ValueError, OSError):
                        pass
            self.save(row)
            return row


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--registry", type=Path, required=True)
    sub = p.add_subparsers(dest="mode", required=True)
    sub.add_parser("list")
    for name in ("show", "recover"):
        sub.add_parser(name).add_argument("id")
    for name in ("plan", "build"):
        q = sub.add_parser(name)
        q.add_argument("--checkout", required=True)
        q.add_argument("--sha", required=True)
        q.add_argument("--request", required=True)
        q.add_argument("--trusted-checkout", action="store_true", required=True)
        if name == "build":
            for flag in ("blender", "godot", "blender-sha", "godot-sha"):
                q.add_argument("--" + flag, required=True)
            q.add_argument("--capture", action="store_true")
    a = p.parse_args()
    try:
        g = Graphics(a.registry)
        if a.mode in ("plan", "build"):
            kw = {k: getattr(a,k) for k in ("blender","godot","blender_sha","godot_sha","capture")} if a.mode == "build" else {}
            out = g.run(a.checkout, a.sha, a.request, build=a.mode == "build", **kw)
        elif a.mode == "list":
            out = g.list()
        else:
            out = getattr(g, "get" if a.mode == "show" else a.mode)(a.id)
        print(json.dumps(out, indent=2, ensure_ascii=True))
        return 1 if a.mode in ("plan", "build") and out["state"] != "PASS" else 0
    except (ValueError, OSError, sqlite3.Error, subprocess.SubprocessError, KeyError, TypeError) as exc:
        print("APEX_GRAPHICS_BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
