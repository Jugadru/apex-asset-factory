import math
from pathlib import Path
import struct
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from asset_factory import uv_repair as uv
from asset_factory.material_factory import glb,sha,enrich
from asset_factory.validate_glb import inspect


def fixture(collapsed=True):
    positions=[(0,0,0),(1,0,0),(0,1,0),(1,1,0)]
    coords=[(0,0),(1,0),(0,1),(.5,.5) if collapsed else (1,1)]
    arrays=[positions,[(0,0,1)]*4,coords,[(i,) for i in (0,1,2,1,3,2)]]
    data=bytearray();views=[];accessors=[]
    for i,(rows,ctype,kind) in enumerate(zip(arrays,(5126,5126,5126,5123),("VEC3","VEC3","VEC2","SCALAR"))):
        start=len(data)
        for row in rows:data.extend(struct.pack("<"+("H" if i==3 else "f")*len(row),*row))
        views.append(dict(buffer=0,byteOffset=start,byteLength=len(data)-start,target=34963 if i==3 else 34962))
        accessors.append(dict(bufferView=i,componentType=ctype,count=len(rows),type=kind))
    accessors[0].update(min=[0,0,0],max=[1,1,0])
    doc={"asset":{"version":"2.0"},"scene":0,"scenes":[{"nodes":[0,1,2,3]}],"nodes":[{"name":f"Wheel_{s}_{a}","mesh":0} for s in "LR" for a in "FR"],"meshes":[{"primitives":[{"attributes":dict(zip(uv.ATTRS,range(3))),"indices":3,"material":0}]}],"materials":[{"name":"carbon"}],"buffers":[{"byteLength":len(data)}],"bufferViews":views,"accessors":accessors}
    return glb(doc,data)


class UVRepairTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.w=Path(self.tmp.name);self.a=self.w/"a.glb";self.a.write_bytes(fixture())

    def test_shared_vertex_repair_preserves_valid_corner_data(self):
        b=self.w/"b.glb";r=uv.repair(self.a,b,sha(self.a.read_bytes()),100)
        self.assertEqual((r["uv_degenerate_before"],r["uv_degenerate_after"],r["split_corners"]),(1,0,3))
        for p in (self.a,b):
            qa,doc,dec=inspect(p,100);self.assertEqual(qa["triangles"],2)
            prim=doc["meshes"][0]["primitives"][0];ids=[i[0] for i in dec[prim["indices"]]]
            xyz=[dec[prim["attributes"]["POSITION"]][i] for i in ids];coords=[dec[prim["attributes"]["TEXCOORD_0"]][i] for i in ids]
            self.assertEqual(xyz,[(0,0,0),(1,0,0),(0,1,0),(1,0,0),(1,1,0),(0,1,0)])
            self.assertEqual(coords[:3],[(0,0),(1,0),(0,1)])
        self.assertGreater(abs(uv.area2(*coords[3:])),uv.EPS)
        self.assertEqual(enrich(b,100,256)[1]["uv_degenerate_triangles"],0)
        self.assertEqual(self.a.read_bytes(),fixture())

    def test_deterministic_and_clean_input(self):
        for name in ("b.glb","c.glb"):uv.repair(self.a,self.w/name,sha(self.a.read_bytes()),100)
        self.assertEqual((self.w/"b.glb").read_bytes(),(self.w/"c.glb").read_bytes())
        self.a.write_bytes(fixture(False));r=uv.repair(self.a,self.w/"clean.glb",sha(self.a.read_bytes()),100)
        self.assertEqual(r["uv_degenerate_before"],0);self.assertEqual(r["split_corners"],0)
        self.assertEqual(r["valid_uvs"],"EXACT")

    def test_reject_wrong_hash_existing_output_and_thin_triangle(self):
        b=self.w/"b.glb"
        with self.assertRaises(ValueError):uv.repair(self.a,b,"0"*64,100)
        self.assertFalse(b.exists());uv.repair(self.a,b,sha(self.a.read_bytes()),100)
        with self.assertRaises(ValueError):uv.repair(self.a,b,sha(self.a.read_bytes()),100)
        with self.assertRaises(ValueError):uv.projected([(0,0,0),(1,0,0),(1,1e-15,0)])

    def test_projection_aspect(self):
        a,b,c=uv.projected([(0,0,0),(2,0,0),(0,1,0)])
        self.assertAlmostEqual(math.dist(a,b)/math.dist(a,c),2)
        self.assertTrue(all(0<=x<=1 for row in (a,b,c) for x in row))

if __name__=="__main__":unittest.main()
