#!/usr/bin/env python3
"""Opt-in original demo asset runner. No network, no promotion."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

from apex_foundation import load, plan

MAX_BYTES = 32 * 1024 * 1024

def inspect_glb(path, budget):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or not 20 <= path.stat().st_size <= MAX_BYTES:
        raise ValueError("invalid GLB file")
    raw = path.read_bytes()
    magic, version, length = struct.unpack_from("<4sII", raw)
    if magic != b"glTF" or version != 2 or length != len(raw):
        raise ValueError("invalid GLB header")
    size, kind = struct.unpack_from("<I4s", raw, 12)
    if kind != b"JSON" or size % 4 or size > len(raw)-20:
        raise ValueError("invalid JSON chunk")
    data = json.loads(raw[20:20+size].decode("utf-8"))
    if data.get("asset", {}).get("version") != "2.0":
        raise ValueError("unsupported glTF version")
    # This demo permits no external URI, including textures.
    if any("uri" in obj for group in ("buffers", "images") for obj in data.get(group, [])):
        raise ValueError("non-embedded resource")
    if data.get("extensionsRequired"):
        raise ValueError("unsupported required extension")
    accessors = data.get("accessors", [])
    triangles = 0
    for mesh in data.get("meshes", []):
        for primitive in mesh.get("primitives", []):
            if primitive.get("mode", 4) != 4:
                raise ValueError("non-triangular primitive")
            index = primitive.get("indices", primitive.get("attributes", {}).get("POSITION"))
            if not isinstance(index, int) or not 0 <= index < len(accessors):
                raise ValueError("bad accessor index")
            count = accessors[index]["count"]
            if not isinstance(count, int) or count <= 0 or count % 3:
                raise ValueError("bad triangle count")
            triangles += count // 3
    if not 0 < triangles <= budget:
        raise ValueError("triangle budget exceeded or empty mesh")
    return {"sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw), "mesh_triangles": triangles,
            "structural_qa": "PASS", "godot_import": "NOT_RUN",
            "visual_review": "NOT_RUN", "promotion": "BLOCKED"}

def build(manifest, blender, workspace):
    manifest = Path(manifest).resolve(strict=True)
    executable = Path(blender).resolve(strict=True)
    requested = Path(workspace).absolute()
    if requested.is_symlink() or requested.exists():
        raise ValueError("workspace must not exist")
    work = requested.resolve()
    # Reject output inside the repository; isolate generated artifacts.
    root = Path(__file__).resolve().parents[1]
    if work == root or root in work.parents:
        raise ValueError("workspace must be outside repository")
    planned = plan(manifest)
    jobs = {row["id"]: row for row in load(manifest)["jobs"]}
    work.mkdir(parents=False, exist_ok=False)
    result = []
    for row in planned["jobs"]:
        if row["status"] != "PLANNED":
            result.append(row)
            continue
        out = work / row["output"]
        out.parent.mkdir(parents=True, exist_ok=True)
        log = work / (row["id"] + ".log")
        try:
            with log.open("x", encoding="utf-8") as handle:
                subprocess.run([str(executable), "--background", "--factory-startup",
                                "--python-exit-code", "1", "--python",
                                str(Path(__file__).with_name("apex_blender_scaffold.py").resolve()),
                                "--", "--output", str(out)], cwd=work, stdout=handle,
                               stderr=subprocess.STDOUT, timeout=180, check=True)
            evidence = inspect_glb(out, jobs[row["id"]]["triangle_budget"])
            result.append({**row, **evidence, "status": "EXPORTED"})
        except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
            result.append({**row, "status": "FAIL", "error": str(exc)})
    report = {"schema": 1, "jobs": result, "promotion": "BLOCKED"}
    (work / "report.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    return report

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("manifest")
    p.add_argument("--blender", required=True)
    p.add_argument("--workspace", required=True)
    a = p.parse_args()
    report = build(a.manifest, a.blender, a.workspace)
    print(json.dumps(report, indent=2))
    return 0 if report["jobs"] and all(j["status"] == "EXPORTED" for j in report["jobs"]) else 1

if __name__ == "__main__":
    sys.exit(main())
