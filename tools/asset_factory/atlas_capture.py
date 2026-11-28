"""Additional A/B capture at explicit source LOD; leave normal staging untouched."""
import hashlib
from pathlib import Path
import shutil
from asset_factory.secure_run import run
from apex_lab_graphics import inspect as inspect_png

HERE = Path(__file__).resolve().parent
MAX_BYTES = 32 * 1024 * 1024


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def capture_full_detail(staging, workspace, godot, expected_sha):
    src = Path(staging).absolute()
    w = Path(workspace).absolute()
    if src.resolve() != src or not src.is_dir():
        raise ValueError("regular staging directory required")
    if w.exists() or w.is_symlink() or w.resolve() != w or src in w.parents:
        raise ValueError("new independent capture workspace required")
    for name in ("asset.glb", "project.godot", "staging.gd"):
        p = src / name
        if p.resolve() != p or not p.is_file() or not 0 < p.stat().st_size <= MAX_BYTES:
            raise ValueError("invalid capture source: " + name)
    if digest(src / "asset.glb") != expected_sha:
        raise ValueError("capture source hash mismatch")
    w.mkdir()
    for name in ("asset.glb", "project.godot", "staging.gd"):
        shutil.copyfile(src / name, w / name)
    shutil.copyfile(HERE / "atlas_capture.gd", w / "atlas_capture.gd")
    if digest(w / "asset.glb") != expected_sha:
        raise ValueError("capture copy hash mismatch")
    g = str(Path(godot).resolve(strict=True))
    log = run([g, "--headless", "--path", str(w), "--editor", "--import"], w, w / "import.log", 120)
    if any(s in log for s in ("ERROR:", "SCRIPT ERROR", "Parse Error:")):
        raise ValueError("full-detail import errors")
    cmd = (["xvfb-run", "-a"] if shutil.which("xvfb-run") else []) + [
        g, "--path", str(w), "--rendering-method", "gl_compatibility", "--audio-driver", "Dummy",
        "--script", "res://atlas_capture.gd", "--", "--capture"]
    log = run(cmd, w, w / "capture.log", 60)
    if "ERROR:" in log or "APEX_IMPORT " not in log:
        raise ValueError("full-detail capture error")
    receipt = inspect_png(w / "capture.png", 960, 540)
    if any(digest(p) != expected_sha for p in (src / "asset.glb", w / "asset.glb")):
        raise ValueError("capture asset changed")
    return dict(receipt, source_sha256=expected_sha, mesh_lod_threshold=0.0, visual_review="NOT_RUN")
