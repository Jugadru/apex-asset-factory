import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from asset_factory.atlas_capture import capture_full_detail


class AtlasCaptureTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.src = self.root / "staging"
        self.src.mkdir()
        for name in ("asset.glb", "project.godot", "staging.gd", "capture.png"):
            (self.src / name).write_bytes(name.encode())
        self.sha = hashlib.sha256(b"asset.glb").hexdigest()
        self.godot = self.root / "godot"
        self.godot.touch()

    def test_new_workspace_and_hash_gate(self):
        dest = self.root / "full"
        with self.assertRaisesRegex(ValueError, "source hash mismatch"):
            capture_full_detail(self.src, dest, self.godot, "0" * 64)
        self.assertFalse(dest.exists())
        with self.assertRaisesRegex(ValueError, "independent capture workspace"):
            capture_full_detail(self.src, self.src / "nested", self.godot, self.sha)
        self.assertEqual((self.src / "capture.png").read_bytes(), b"capture.png")

    @patch("asset_factory.atlas_capture.inspect_png", return_value={"sha256": "fixture"})
    @patch("asset_factory.atlas_capture.run", side_effect=["import ok", "APEX_IMPORT fixture"])
    def test_isolated_capture_keeps_default(self, run, inspect_png):
        dest = self.root / "full"
        result = capture_full_detail(self.src, dest, self.godot, self.sha)
        self.assertEqual(result["mesh_lod_threshold"], 0.0)
        self.assertEqual(result["visual_review"], "NOT_RUN")
        self.assertEqual(result["source_sha256"], self.sha)
        self.assertEqual((dest / "asset.glb").read_bytes(), b"asset.glb")
        self.assertEqual((self.src / "capture.png").read_bytes(), b"capture.png")
        self.assertFalse((self.src / "atlas_capture.gd").exists())
        self.assertIn("res://atlas_capture.gd", run.call_args.args[0])
        inspect_png.assert_called_once_with(dest / "capture.png", 960, 540)


if __name__ == "__main__":
    unittest.main()
