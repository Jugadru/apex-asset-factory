import itertools
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from asset_factory.build import read_request, validate, HERE
from asset_factory.closed_wheel_layout import design,validate_layout
from asset_factory.closed_wheel_qa import verify_closed_wheel

class ClosedWheelTest(unittest.TestCase):
    def setUp(self):
        self.r=read_request(HERE/"demo_gt.json")

    def test_request_compatibility(self):
        for i,name in enumerate(("demo.json","demo_modular.json","demo_era.json","demo_detail.json","demo_gt.json"),1):
            self.assertEqual(read_request(HERE/name)["schema"],i)
        schema=json.loads((HERE/"request_v5.schema.json").read_text())
        for changes in ({"category":"f1"},{"era":"2012-inspired"},{"references":["external"]},
                        {"dimensions_m":{"width":1,"length":5,"height":1.1}},{"components":{"tires":"unknown"}}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):
                validate(dict(self.r,**changes),schema)

    def test_dimensions_and_clearance(self):
        for category,w,l,h,tire in itertools.product(("gt","endurance"),(1.7,2.3),(4,5.5),(1,1.5),("standard","wide")):
            r=dict(self.r,category=category,dimensions_m=dict(width=w,length=l,height=h),components={"tires":tire})
            parts=design(r)
            result=validate_layout(parts,r)
            self.assertEqual(result["status"],"PASS")
            self.assertGreater(result["sampled_arch_clearance_m"],.005)

    def test_category_seed_and_tires(self):
        a={p["name"]:p for p in design(self.r)}
        b={p["name"]:p for p in design(dict(self.r,category="endurance"))}
        self.assertNotEqual(a["BodyShell"]["vertices"],b["BodyShell"]["vertices"])
        self.assertNotEqual(a["Canopy"]["vertices"],b["Canopy"]["vertices"])
        self.assertNotIn("DorsalFin",a)
        self.assertIn("DorsalFin",b)
        self.assertEqual(design(self.r),design(self.r))
        self.assertNotEqual(design(self.r),design(dict(self.r,seed=999)))
        c={p["name"]:p for p in design(dict(self.r,components={"tires":"standard"}))}
        self.assertGreater(a["Wheel_L_R"]["width"],c["Wheel_L_R"]["width"])

    def test_exported_shell_collision_regression(self):
        layout=design(self.r)
        body=next(p for p in layout if p["name"]=="BodyShell")
        nodes=[{"name":p["name"],"mesh":0} for p in layout]
        ids=[i for f in body["faces"] for j in range(1,len(f)-1) for i in (f[0],f[j],f[j+1])]
        pts=[(x,z,-y) for x,y,z in body["vertices"]]
        doc={"nodes":nodes,"meshes":[{"primitives":[{"attributes":{"POSITION":0},"indices":1}]}]}
        data=[pts,[(i,) for i in ids]]
        result=verify_closed_wheel(doc,data,layout)
        self.assertEqual(result["status"],"PASS")
        self.assertEqual(result["samples_with_shell"],84)
        data[0]=[(x,y-.08,z) for x,y,z in pts]
        with self.assertRaisesRegex(ValueError,"intersects"):
            verify_closed_wheel(doc,data,layout)

if __name__=="__main__":
    unittest.main()
