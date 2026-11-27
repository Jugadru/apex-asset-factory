import copy
import itertools
import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from asset_factory.build import HERE,read_request
from asset_factory import wheel_detail as wd
from asset_factory.advanced_body_layout import design as original


class WheelDetailTest(unittest.TestCase):
    def setUp(self):
        self.r=read_request(HERE/"demo_wheel_gt.json")

    def test_schema_compatibility(self):
        for i,name in enumerate(("demo.json","demo_modular.json","demo_era.json","demo_detail.json","demo_gt.json","demo_curved_gt.json","demo_wheel_gt.json"),1):
            self.assertEqual(read_request(HERE/name)["schema"],i)

    def test_all_dimensional_lod_cases(self):
        for category,w,l,h,tire,level in itertools.product(("gt","endurance"),(1.7,2.3),(4,5.5),(1,1.5),("standard","wide"),(0,1,2)):
            r=dict(self.r,category=category,dimensions_m=dict(width=w,length=l,height=h),components={"tires":tire})
            parts=wd.design(r,level)
            qa=wd.validate_layout(parts,r)
            self.assertEqual(qa["status"],"PASS")
            self.assertEqual(qa["wheel_parts"],28)

    def test_preserve_pivots_envelope_and_lod_reduction(self):
        base={p["name"]:p for p in original(self.r)}
        counts=[];names=None
        for level in (0,1,2):
            parts=wd.design(self.r,level)
            detailed=[p for p in parts if p["kind"]=="wheel_mesh"]
            current={p["name"] for p in detailed}
            self.assertEqual(len(current),28)
            if names is not None:self.assertEqual(current,names)
            names=current
            counts.append(sum(len(f)-2 for p in detailed for f in p["faces"]))
            for p in detailed:
                old=base["Wheel_"+p["name"].split("_",1)[1]]
                self.assertEqual(p["center"],old["center"])
                if p["name"].startswith("Wheel_"):
                    self.assertAlmostEqual(max(math.hypot(x,y) for x,y,z in p["vertices"]),old["radius"])
                    self.assertAlmostEqual(max(z for x,y,z in p["vertices"])-min(z for x,y,z in p["vertices"]),old["width"])
        self.assertGreater(counts[0],counts[1]);self.assertGreater(counts[1],counts[2])
        self.assertEqual(wd.design(self.r),wd.design(self.r))
        with self.assertRaises(ValueError):wd.design(self.r,True)

    def test_exported_vertex_pivot_material_guard(self):
        parts=wd.design(self.r,2)
        doc={"nodes":[],"meshes":[],"materials":[],"scenes":[{"nodes":list(range(len(parts)))}],"scene":0}
        decoded=[]
        for i,p in enumerate(parts):
            node={"name":p["name"],"mesh":i}
            if p["kind"]=="wheel_mesh":
                x,y,z=p["center"];node.update(translation=[x,z,-y],rotation=[0,0,-math.sqrt(.5),math.sqrt(.5)])
                pts=[(a,c,-b) for a,b,c in p["vertices"]]
            else:pts=[]
            doc["nodes"].append(node);doc["materials"].append({"name":p["material"]})
            doc["meshes"].append({"primitives":[{"material":i,"attributes":{"POSITION":i}}]});decoded.append(pts)
        self.assertEqual(len(wd.verify_wheel_details(doc,decoded,parts)["parts"]),28)
        idx=next(i for i,p in enumerate(parts) if p["name"]=="Wheel_R_F")
        for mutation in ("pivot","rotation","material","missing_vertex","radial"):
            d=copy.deepcopy(doc);v=copy.deepcopy(decoded)
            if mutation=="pivot":d["nodes"][idx]["translation"][0]+=.001
            elif mutation=="rotation":d["nodes"][idx]["rotation"]=[0,0,0,1]
            elif mutation=="material":d["materials"][idx]["name"]="paint"
            elif mutation=="missing_vertex":v[idx].pop()
            elif mutation=="radial":v[idx][0]=(9,9,9)
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):wd.verify_wheel_details(d,v,parts)

if __name__=="__main__":unittest.main()
