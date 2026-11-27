import itertools
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from asset_factory.build import read_request, HERE
from asset_factory.detail_layout import design,validate_layout,shaped_mesh,tub_mesh,tube_mesh
from asset_factory.detail_qa import ray_height
from asset_factory.era_layout import ERAS
from asset_factory.modular_layout import PROFILES

class DetailTest(unittest.TestCase):
    def setUp(self):
        self.r=read_request(HERE/"demo_detail.json")

    def test_legacy_schema_compatibility(self):
        for i,name in enumerate(("demo.json","demo_modular.json","demo_era.json","demo_detail.json"),1):
            self.assertEqual(read_request(HERE/name)["schema"],i)

    def test_detail_envelope_all_combinations(self):
        for era,body,tire,w,l,h in itertools.product(ERAS,PROFILES,("standard","wide"),(1,2.5),(3,6),(.7,2)):
            r=dict(self.r,era=era,components={"body":body,"tires":tire},dimensions_m={"width":w,"length":l,"height":h})
            layout=design(r)
            result=validate_layout(layout,r)
            self.assertEqual(result["status"],"PASS")
            self.assertEqual(result["halo"],era=="2020-inspired")
            self.assertEqual(result["suspension_links"],20)
            self.assertEqual(result["components"],53 if result["halo"] else 51)

    def test_cavity_has_no_top_cover(self):
        part=next(p for p in design(self.r) if p["name"]=="Chassis")
        vertices,faces=tub_mesh(part["rings"])
        self.assertNotIn({20,21,28,29},[set(f) for f in faces])
        self.assertIn({48,49,50,51},[set(f) for f in faces])
        ids=[i for f in faces for j in range(1,len(f)-1) for i in (f[0],f[j],f[j+1])]
        doc={"meshes":[{"primitives":[{"attributes":{"POSITION":0},"indices":1}]}]}
        data=[[(x,z,-y) for x,y,z in vertices],[(i,) for i in ids]]
        a,b=part["rings"][2:4]
        y=(a[0]+b[0])/2
        floor=(a[2]+.24*(a[3]-a[2])+b[2]+.24*(b[3]-b[2]))/2
        self.assertAlmostEqual(ray_height(doc,data,{"mesh":0},0,-y),floor)
        # An accidental cover at the former rim must be detectable.
        data[1].extend([(i,) for i in (20,21,29,20,29,28)])
        self.assertGreater(ray_height(doc,data,{"mesh":0},0,-y),floor+.01)

    def test_tube_invalid(self):
        with self.assertRaises(ValueError):
            tube_mesh([(0,0,0),(0,0,0)],.01)
