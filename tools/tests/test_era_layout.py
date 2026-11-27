import itertools
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from asset_factory.build import read_request, validate, HERE
from asset_factory.era_layout import design, validate_layout, shaped_mesh, ERAS
from asset_factory.modular_layout import PROFILES

class EraLayoutTest(unittest.TestCase):
    def setUp(self):
        self.request=read_request(HERE/"demo_era.json")
        self.schema=json.loads((HERE/"request_v3.schema.json").read_text())

    def test_schema_compatibility(self):
        self.assertEqual(read_request(HERE/"demo.json")["schema"],1)
        self.assertEqual(read_request(HERE/"demo_modular.json")["schema"],2)
        self.assertEqual(self.request["schema"],3)
        for changes in ({"era":"unknown"},{"style":"original-low-poly"},{"schema":2}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):
                validate(dict(self.request,**changes),self.schema)

    def test_all_era_profile_dimension_combinations(self):
        for era,body,tire,w,l,h in itertools.product(ERAS,PROFILES,("standard","wide"),(1,2.5),(3,6),(.7,2)):
            r=dict(self.request,era=era,components={"body":body,"tires":tire},dimensions_m={"width":w,"length":l,"height":h})
            parts=design(r)
            qa=validate_layout(parts,r)
            self.assertEqual(qa["status"],"PASS")
            self.assertEqual(qa["shaped_components"],11)
            for part in parts:
                if "shape" not in part:continue
                vertices,faces=shaped_mesh(part)
                self.assertTrue(all(all(0<=i<len(vertices) for i in f) for f in faces))
                self.assertTrue(all(len(set(f))==len(f) for f in faces))
                edges={}
                for face in faces:
                    for a,b in zip(face,face[1:]+face[:1]):
                        k=tuple(sorted((a,b)))
                        edges[k]=edges.get(k,0)+1
                self.assertTrue(all(n==2 for n in edges.values()))

    def test_era_and_seed_affect_geometry(self):
        a={p["name"]:p for p in design(dict(self.request,era="1990-inspired"))}
        b={p["name"]:p for p in design(dict(self.request,era="2020-inspired"))}
        self.assertNotEqual(a["Chassis"]["rings"],b["Chassis"]["rings"])
        self.assertNotEqual(a["Sidepod_L"]["size"],b["Sidepod_L"]["size"])
        self.assertNotEqual(shaped_mesh(a["FrontWing"]),shaped_mesh(b["FrontWing"]))
        self.assertEqual(a["Wheel_L_F"],b["Wheel_L_F"])
        self.assertEqual(design(self.request),design(self.request))
        self.assertNotEqual(design(self.request),design(dict(self.request,seed=2027)))

if __name__=="__main__":
    unittest.main()
