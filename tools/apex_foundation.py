#!/usr/bin/env python3
"""APEX foundation: offline catalog validation and non-mutating asset planning."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "references"
KINDS = {"car", "track", "garage", "environment", "texture", "audio"}
LICENSES = {"CC0-1.0", "ORIGINAL", "CC-BY-4.0", "OTHER_REVIEWED"}

def load(path):
    with Path(path).open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict) or data.get("schema") != 1:
        raise ValueError("unsupported schema")
    return data

def catalog(data, prefix, minimum):
    rows = data["entries"]
    ids = [row["id"] for row in rows]
    if len(rows) < minimum or len(set(ids)) != len(ids):
        raise ValueError("missing or duplicate catalog records")
    if any(not re.fullmatch(prefix + r"-[0-9]{3,}", i) for i in ids):
        raise ValueError("invalid catalog id")
    if not {f"{prefix}-{i:03}" for i in range(1, minimum+1)} <= set(ids):
        raise ValueError("historical ids missing")
    if any(not row.get("name", "").strip() for row in rows):
        raise ValueError("empty name")
    return rows, set(ids)

def validate():
    refs, ref_ids = catalog(load(DOCS / "references.json"), "REF", 198)
    ideas, _ = catalog(load(DOCS / "possibilities.json"), "IDEA", 120)
    domains = load(DOCS / "domains.json")["domains"]
    if len(domains) != 8 or len(set(domains)) != 8:
        raise ValueError("domain registry")
    for row in ideas:
        if not row["references"] or not set(row["references"]) <= ref_ids:
            raise ValueError("invalid reference " + row["id"])
    return {"status": "PASS", "scope": "catalog structure only",
            "references": len(refs), "possibilities": len(ideas), "domains": len(domains)}

def plan(manifest):
    rows = load(manifest)["jobs"]
    seen, outputs, result = set(), set(), []
    for job in rows:
        ident = job["id"]
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", ident) or ident in seen:
            raise ValueError("invalid or duplicate job id")
        seen.add(ident)
        raw = job["output"]
        p = PurePosixPath(raw)
        if (p.is_absolute() or ".." in p.parts or "\\" in raw or
                str(p) != raw or len(p.parts) < 2 or p.parts[0] != "staging" or
                p.suffix != ".glb" or raw in outputs):
            raise ValueError("output must be unique staging/*.glb")
        outputs.add(raw)
        if job["kind"] not in KINDS or not 0 < job["triangle_budget"] <= 10000000:
            raise ValueError("invalid asset type/budget")
        if job["texture_max_px"] not in (256, 512, 1024, 2048, 4096, 8192):
            raise ValueError("invalid texture budget")
        # A license label alone never authorizes third-party use. External source
        # ingestion is deliberately blocked until a reviewed importer exists.
        ready = (job.get("approved") is True and job["kind"] == "car"
                 and job.get("source") is None and job.get("license") == "ORIGINAL")
        key = hashlib.sha256(json.dumps(job, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        result.append({"id": ident, "job_hash": key, "output": raw,
                       "status": "PLANNED" if ready else "BLOCKED",
                       "reason": "original demo only; execution separate" if ready else "approval or supported original source required"})
    return {"schema": 1, "executed": False, "jobs": result}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    subs.add_parser("validate")
    subs.add_parser("plan").add_argument("manifest", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate() if args.command == "validate" else plan(args.manifest), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
