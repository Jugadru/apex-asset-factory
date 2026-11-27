import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from asset_factory.modular_qa import verify_wheels
from asset_factory.modular_layout import design
from asset_factory.build import read_request, HERE

def fixture():
    layout=design(read_request(HERE/"demo_modular.json"))
    parts=[p for p in layout if p["name"].startswith(("Wheel_","Hub_"))]
    nodes=[];meshes=[];decoded=[]
    for p in parts:
        x,y,z=p["center"]
        i=len(nodes)
        nodes.append({"name":p["name"],"mesh":i,"translation":[x,z,-y],
                      "rotation":[0,0,-math.sqrt(.5),math.sqrt(.5)]})
        meshes.append({"primitives":[{"attributes":{"POSITION":i}}]})
        decoded.append([(p["radius"]*math.cos(angle),width,p["radius"]*math.sin(angle))
                        for angle in (0,math.pi/2,math.pi,3*math.pi/2)
                        for width in (-p["width"]/2,p["width"]/2)])
    return {"nodes":nodes,"meshes":meshes,"scene":0,"scenes":[{"nodes":list(range(8))}]},decoded,layout

class ModularWheelTest(unittest.TestCase):
    def test_valid(self):
        doc,data,layout=fixture()
        report=verify_wheels(doc,data,layout)
        self.assertEqual(report["status"],"PASS")
        self.assertEqual(len(report["components"]),8)
    def test_reject_export_defects(self):
        for mutation in ("center","scale","rotation","radius","width","nested"):
            doc,data,layout=fixture()
            i=next(i for i,n in enumerate(doc["nodes"]) if n["name"]=="Wheel_L_F")
            n=doc["nodes"][i]
            if mutation=="center":n["translation"][0]+=.01
            elif mutation=="scale":n["scale"]=[1,2,1]
            elif mutation=="rotation":n["rotation"]=[0,0,0,1]
            elif mutation=="radius":
                x,y,z=data[i][0];data[i][0]=(x*.9,y,z)
            elif mutation=="width":data[i]=[(x,y*.8,z) for x,y,z in data[i]]
            elif mutation=="nested":doc["scenes"][0]["nodes"].remove(i)
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):
                verify_wheels(doc,data,layout)
