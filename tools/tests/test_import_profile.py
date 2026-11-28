import sys
from pathlib import Path
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from asset_factory.import_profile import precise_project, verify_precise_import

class ImportProfileTest(unittest.TestCase):
    def test_opt_in_idempotent_and_conflict(self):
        base='[application]\nconfig/name="fixture"\n'
        precise=precise_project(base)
        self.assertTrue(precise.startswith(base))
        self.assertEqual(precise_project(precise),precise)
        self.assertIn('"meshes/force_disable_compression": true',precise)
        with self.assertRaises(ValueError):precise_project(base+'[importer_defaults]\nscene={}\n')

    def test_receipt_gate(self):
        with tempfile.TemporaryDirectory() as t:
            w=Path(t);p=w/'asset.glb.import'
            with self.assertRaises(ValueError):verify_precise_import(w)
            p.write_text('meshes/force_disable_compression=true\nmeshes/generate_lods=true\n')
            self.assertEqual(verify_precise_import(w),{'mesh_compression_disabled':True,'generate_lods':True})
            for value in ('meshes/force_disable_compression=false\nmeshes/generate_lods=true\n','meshes/force_disable_compression=true\nmeshes/generate_lods=false\n','meshes/force_disable_compression=true\nmeshes/force_disable_compression=false\nmeshes/generate_lods=true\n'):
                p.write_text(value)
                with self.assertRaises(ValueError):verify_precise_import(w)

    def test_symlink_receipt_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            w=Path(t); real=w/'other';real.write_text('meshes/force_disable_compression=true\nmeshes/generate_lods=true\n')
            (w/'asset.glb.import').symlink_to(real)
            with self.assertRaises(ValueError):verify_precise_import(w)
