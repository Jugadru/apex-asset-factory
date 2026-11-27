import itertools
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from asset_factory.build import HERE, read_request, validate
from asset_factory import advanced_body_layout as body
from asset_factory.closed_wheel_layout import design as legacy_design


class AdvancedBodyTest(unittest.TestCase):
    def setUp(self):
        self.r=read_request(HERE/"demo_curved_gt.json")

    def test_schema_compatibility(self):
        for i,name in enumerate(("demo.json","demo_modular.json","demo_era.json","demo_detail.json","demo_gt.json","demo_curved_gt.json"),1):
            self.assertEqual(read_request(HERE/name)["schema"],i)
        schema=json.loads((HERE/"request_v6.schema.json").read_text())
        for change in ({"schema":5},{"style":"original-closed-wheel"},{"category":"unknown"}):
            with self.assertRaises(ValueError):validate(dict(self.r,**change),schema)

    def test_hermite_bounds(self):
        p=[(0,1),(.25,3),(.75,2),(1,4)]
        for a,b in zip(p,p[1:]):
            self.assertAlmostEqual(body.smooth_profile(p,a[0])[0],a[1])
            for i in range(21):
                x=a[0]+(b[0]-a[0])*i/20
                value=body.smooth_profile(p,x)[0]
                self.assertLessEqual(value,max(a[1],b[1])+1e-9)
                self.assertGreaterEqual(value,min(a[1],b[1])-1e-9)
        with self.assertRaises(ValueError):body.smooth_profile(p,2)

    def test_all_extreme_dimension_and_lod_combinations(self):
        for cat,w,l,h,tire in itertools.product(("gt","endurance"),(1.7,2.3),(4,5.5),(1,1.5),("standard","wide")):
            r=dict(self.r,category=cat,dimensions_m=dict(width=w,length=l,height=h),components={"tires":tire})
            results=[]
            for level in (0,1,2):
                parts=body.design(r,level)
                result=body.validate_layout(parts,r)
                self.assertEqual(result["status"],"PASS")
                self.assertGreater(result["sampled_arch_clearance_m"],.005)
                results.append(result["surface_vertices"])
            self.assertGreater(results[0],results[1])
            self.assertGreater(results[1],results[2])

    def test_wheels_and_category_identity_unchanged(self):
        original={p["name"]:p for p in legacy_design(self.r)}
        curved={p["name"]:p for p in body.design(self.r)}
        self.assertEqual(set(original),set(curved))
        self.assertNotEqual(original["BodyShell"]["vertices"],curved["BodyShell"]["vertices"])
        for name in original:
            if name.startswith(("Wheel_","Hub_")):
                self.assertEqual(original[name],curved[name])
        self.assertEqual(body.design(self.r),body.design(self.r))
        self.assertNotEqual(body.design(self.r),body.design(dict(self.r,seed=987)))
        with self.assertRaises(ValueError):body.design(self.r,True)

if __name__=="__main__":
    unittest.main()
