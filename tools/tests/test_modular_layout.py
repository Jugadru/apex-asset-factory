import copy
import itertools
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from asset_factory.build import read_request, validate, HERE
from asset_factory.modular_layout import design, validate_layout, PROFILES

class ModularLayoutTest(unittest.TestCase):
    def setUp(self):
        self.request=read_request(HERE/"demo_modular.json")
        self.schema=json.loads((HERE/"request_v2.schema.json").read_text())

    def test_legacy_and_new_schema(self):
        self.assertEqual(read_request(HERE/"demo.json")["schema"],1)
        self.assertEqual(self.request["schema"],2)
        for changes in ({"schema":True},{"components":{"body":"unknown","tires":"wide"}},
                        {"components":{"body":"balanced","tires":"wide","extra":1}},
                        {"style":"original-low-poly"},{"references":["external"]}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):
                validate(dict(self.request,**changes),self.schema)

    def test_all_profiles_and_dimension_extrema(self):
        for body,tire,w,l,h in itertools.product(PROFILES,("standard","wide"),(1,2.5),(3,6),(.7,2)):
            r=dict(self.request,components={"body":body,"tires":tire},dimensions_m={"width":w,"length":l,"height":h})
            parts=design(r)
            result=validate_layout(parts,r)
            self.assertEqual(result["status"],"PASS")
            self.assertGreater(result["components"],28)
            for wheel in (p for p in parts if p["name"].startswith("Wheel_")):
                self.assertEqual(wheel["center"][2],wheel["radius"])

    def test_reproducibility_and_geometry_variation(self):
        a=design(self.request)
        self.assertEqual(a,design(self.request))
        b=design(dict(self.request,seed=2027))
        self.assertNotEqual(a,b)
        a_by={x["name"]:x for x in a}
        b_by={x["name"]:x for x in b}
        self.assertNotEqual(a_by["Chassis"]["rings"],b_by["Chassis"]["rings"])
        self.assertEqual(a_by["Wheel_L_F"],b_by["Wheel_L_F"])
        c=design(dict(self.request,components={"body":"low-drag","tires":"wide"}))
        c_by={x["name"]:x for x in c}
        self.assertNotEqual(a_by["Sidepod_L"]["size"],c_by["Sidepod_L"]["size"])
        self.assertGreater(c_by["Wheel_L_R"]["width"],a_by["Wheel_L_R"]["width"])

    def test_hub_alignment_and_bad_envelope(self):
        for name,field,value in (("Hub_L_F","center",[0,0,0]),("Wheel_L_F","radius",.01),
                                 ("FrontWing","size",[10,10,10])):
            parts=copy.deepcopy(design(self.request))
            next(p for p in parts if p["name"]==name)[field]=value
            with self.subTest(name=name),self.assertRaises(ValueError):
                validate_layout(parts,self.request)

if __name__=="__main__":
    unittest.main()
