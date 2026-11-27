import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from apex_asset_build import inspect_glb

class AssetBuildTest(unittest.TestCase):
    def test_structural_glb(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "demo.glb"
            data = {"asset":{"version":"2.0"}, "accessors":[{"count":6}],
                    "meshes":[{"primitives":[{"indices":0}]}]}
            def write(d):
                chunk = json.dumps(d).encode()
                chunk += b" " * ((-len(chunk)) % 4)
                p.write_bytes(struct.pack("<4sII", b"glTF", 2, 20+len(chunk)) +
                              struct.pack("<I4s", len(chunk), b"JSON") + chunk)
            write(data)
            self.assertEqual(inspect_glb(p, 2)["mesh_triangles"], 2)
            self.assertEqual(inspect_glb(p, 2)["promotion"], "BLOCKED")
            with self.assertRaises(ValueError):
                inspect_glb(p, 1)
            write(dict(data, buffers=[{"uri":"outside.bin"}]))
            with self.assertRaises(ValueError):
                inspect_glb(p, 2)
            p.write_bytes(b"broken")
            with self.assertRaises(ValueError):
                inspect_glb(p, 2)

if __name__ == "__main__":
    unittest.main()
