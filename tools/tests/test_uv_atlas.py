import sys
from pathlib import Path
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from asset_factory.uv_atlas import generate_atlas, audit, grid_size
from asset_factory.validate_glb import inspect
from asset_factory.material_factory import sha, enrich
from test_uv_repair import fixture

class AtlasTest(unittest.TestCase):
    def test_atlas_is_opt_in_exact_and_deterministic(self):
        with tempfile.TemporaryDirectory() as t:
            w=Path(t);a=w/"a.glb";a.write_bytes(fixture(False))
            b=w/"b.glb";c=w/"c.glb";h=sha(a.read_bytes())
            r=generate_atlas(a,b,h,100);generate_atlas(a,c,h,100)
            self.assertEqual(b.read_bytes(),c.read_bytes())
            self.assertEqual(r["triangles"],2)
            self.assertEqual(r["uv0"],"EXACT")
            self.assertEqual(r["shared_mesh_instances"],3)
            self.assertGreaterEqual(r["min_cell_margin_px"],1.999)
            self.assertGreater(r["occupied_uv_fraction"],0)
            self.assertEqual(r["baking_readiness"],"NOT_RUN")
            with self.assertRaises(ValueError):inspect(b,100)
            _,doc,dec=inspect(b,100,allow_uv2=True)
            _,old,old_dec=inspect(a,100)
            oldp=old["meshes"][0]["primitives"][0];newp=doc["meshes"][0]["primitives"][0]
            for k in ("POSITION","NORMAL","TEXCOORD_0"):
                self.assertEqual([old_dec[oldp["attributes"][k]][i[0]] for i in old_dec[oldp["indices"]]],
                                 [dec[newp["attributes"][k]][i[0]] for i in dec[newp["indices"]]])
            raw,pbr=enrich(b,100,256,True,uv_atlas=True)
            self.assertEqual(pbr["triangles"],2)
            self.assertEqual(pbr["maps"],enrich(a,100,256,True)[1]["maps"])
            self.assertEqual(a.read_bytes(),fixture(False))
            uv=dec[newp["attributes"]["TEXCOORD_1"]]
            uv[3:6]=uv[:3]
            with self.assertRaises(ValueError):audit(doc,dec,2,2048)

    def test_capacity_and_hash(self):
        self.assertEqual(grid_size(11804,2048),109)
        for count,res in ((0,2048),(True,2048),(65536,1024),(2,256)):
            with self.assertRaises(ValueError):grid_size(count,res)
        with tempfile.TemporaryDirectory() as t:
            w=Path(t);a=w/"a.glb";a.write_bytes(fixture(False))
            with self.assertRaises(ValueError):generate_atlas(a,w/"b.glb","0"*64,100)
            self.assertFalse((w/"b.glb").exists())

    def test_reference_resolution_sweep(self):
        with tempfile.TemporaryDirectory() as t:
            w=Path(t);a=w/"a.glb";a.write_bytes(fixture(False))
            for size in (1024,2048,4096):
                r=generate_atlas(a,w/f"{size}.glb",sha(a.read_bytes()),100,size)
                self.assertGreaterEqual(r["min_cell_margin_px"],1.999)
                self.assertEqual(r["subpixel_area_triangles"],0)

if __name__=="__main__":unittest.main()
