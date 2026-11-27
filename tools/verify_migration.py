"""Check byte-preserved upstream baseline. Update manifest only after reviewed upstream changes."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "docs/source-manifest.json").read_text())
evolved = json.loads((ROOT / "docs/evolved-sources.json").read_text())
assert set(evolved["paths"]) <= {x["path"] for x in manifest["files"]}
for entry in manifest["files"]:
    p = ROOT / entry["path"]
    if p.is_symlink() or ROOT not in p.resolve().parents:
        raise SystemExit("unsafe migration path: " + entry["path"])
    if entry["path"] in evolved["paths"]:
        raw = subprocess.check_output(["git", "show", evolved["baseline"] + ":" + entry["path"]], cwd=ROOT)
        print("Historical blob (intentionally evolved):", entry["path"])
    else:
        raw = p.read_bytes()
    sha = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if sha != entry["blob_sha"]:
        raise SystemExit("migration mismatch: " + entry["path"])
print("APEX_MIGRATION_BLOBS_PASS", len(manifest["files"]), "historical:", len(evolved["paths"]))
