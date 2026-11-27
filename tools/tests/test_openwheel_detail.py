import itertools
import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from asset_factory.build import HERE,read_request
from asset_factory import openwheel_detail as wd
from asset_factory.detail_layout import design as base_design
from asset_factory.wheel_detail import verify_wheel_details


class OpenwheelDetailTest(unittest.TestCase):
    def setUp(self):
        self.r=read_request(HERE/"demo_wheel_2012.json")

    def test_schema_compatibility(self):
        for i,name in enumerate(("demo.json","demo_modular.json","demo_era.json","demo_detail.json","demo_gt.json","demo_curved_gt.json","demo_wheel_gt.json","demo_wheel_2012.json"),1):
            self.assertEqual(read_request(HERE/name)["schema"],i)

    def test_all_dimensional_lod_cases(self):
        for era,body,tire,w,l,h,level in itertools.product(wd.PROFILES,("balanced","low-drag","high-downforce"),("standard","wide"),(1,2.5),(3,6),(.7,2),(0,1,2)):
            r=dict(self.r,era=era,dimensions_m=dict(width=w,length=l,height=h),components=dict(body=body,tires=tire))
            parts=wd.design(r,level)
            qa=wd.validate_layout(parts,r)
            self.assertEqual(qa["status"],"PASS")
            self.assertEqual(qa["wheel_parts"],28)
            self.assertEqual(qa["spokes_per_wheel"],wd.PROFILES[era][1])
            self.assertEqual(qa["components"],73 if era=="2020-inspired" else 71)

    def test_era_profiles_preserve_body_and_wheel_contract(self):
        profiles=[]
        for era in wd.PROFILES:
            r=dict(self.r,era=era)
            base={p["name"]:p for p in base_design(r)}
            counts=[]
            for level in (0,1,2):
                parts={p["name"]:p for p in wd.design(r,level)}
                self.assertEqual(set(parts)-set(base),{f"{prefix}_{side}_{axle}" for prefix in ("Rim","Spokes","BrakeDisc","Caliper","CenterNut") for side in "LR" for axle in "FR"})
                for name,p in parts.items():
                    if p["kind"]!="wheel_mesh":
                        self.assertEqual(p,base[name])
                        continue
                    old=base["Wheel_"+name.split("_",1)[1]]
                    self.assertEqual(p["center"],old["center"])
                    if name.startswith("Wheel_"):
                        self.assertAlmostEqual(max(math.hypot(x,y) for x,y,z in p["vertices"]),old["radius"])
                        self.assertAlmostEqual(max(z for x,y,z in p["vertices"])-min(z for x,y,z in p["vertices"]),old["width"])
                counts.append(sum(len(f)-2 for p in parts.values() if p["kind"]=="wheel_mesh" for f in p["faces"]))
                if level==0:profiles.append(parts["Rim_R_F"]["vertices"])
            self.assertGreater(counts[0],counts[1]);self.assertGreater(counts[1],counts[2])
            self.assertEqual(wd.design(r),wd.design(r))
        self.assertNotEqual(profiles[0],profiles[1]);self.assertNotEqual(profiles[1],profiles[2])
        with self.assertRaises(ValueError):wd.design(self.r,True)

    def test_exported_vertex_and_pivot_reuse(self):
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
        self.assertEqual(len(verify_wheel_details(doc,decoded,parts)["parts"]),28)
        idx=next(i for i,p in enumerate(parts) if p["name"]=="Hub_R_F")
        doc["nodes"][idx]["translation"][0]+=.001
        with self.assertRaises(ValueError):verify_wheel_details(doc,decoded,parts)

if __name__=="__main__":unittest.main()
