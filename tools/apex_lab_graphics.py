#!/usr/bin/env python3
"""Collect fresh captures from existing software-rendered UI contracts."""
import hashlib
import json
from pathlib import Path
import shutil
import struct

CAPTURES = {
    "pitwall_0649_ui_test.gd": (
        ("qa/stabilization_0667/pitwall_1600.png", 1600, 900),
        ("qa/stabilization_0667/pitwall_1920.png", 1920, 1080),
    ),
    "race_engineer_0922_ui_test.gd": (
        ("qa/engineer_0922/radio_1280.png", 1280, 720),
        ("qa/engineer_0922/radio_1600.png", 1600, 900),
        ("qa/engineer_0922/radio_1920.png", 1920, 1080),
    ),
}
MAX_BYTES = 32 * 1024 * 1024
SIGNATURE = b"\x89PNG\r\n\x1a\n"


def prepare(root):
    """Delete only known output paths inside the disposable hosted checkout."""
    for items in CAPTURES.values():
        for path, _, _ in items:
            p = root / path
            if p.resolve() != p:
                raise ValueError("Nonregular capture path")
            if p.exists():
                if not p.is_file():
                    raise ValueError("Nonregular capture path")
                p.unlink()


def inspect(path, width, height):
    if path.resolve() != path or not path.is_file():
        raise ValueError("Missing/nonregular fresh capture: " + path.name)
    if not 33 <= path.stat().st_size <= MAX_BYTES:
        raise ValueError("Capture size outside bound: " + path.name)
    raw = path.read_bytes()
    if raw[:8] != SIGNATURE or raw[8:16] != b"\x00\x00\x00\rIHDR":
        raise ValueError("Not a PNG: " + path.name)
    actual = struct.unpack(">II", raw[16:24])
    if actual != (width, height):
        raise ValueError("Unexpected dimensions: " + path.name)
    if raw[-12:] != b"\x00\x00\x00\x00IEND\xaeB\x60\x82":
        raise ValueError("Missing PNG end: " + path.name)
    return {"file": path.name, "width": width, "height": height,
            "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def collect(root, out):
    root = root.resolve()
    target = out / "captures"
    target.mkdir(exist_ok=False)
    rows = []
    for script, items in CAPTURES.items():
        for path, width, height in items:
            source = root / path
            row = inspect(source, width, height)
            shutil.copyfile(source, target / row["file"])
            rows.append({"fixture": script, **row})
    result = {"schema": 1, "status": "PASS", "renderer": "xvfb_gl_compatibility",
              "captures": rows, "visual_review": "NOT_RUN",
              "limitations": ["PNG header, size, end marker and fixture assertions only.",
                              "Software rendering; no physical GPU, FPS or visual quality verdict."]}
    (out / "graphics.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("APEX_LAB_GRAPHICS " + json.dumps(result))
    return result
