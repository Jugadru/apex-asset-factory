"""Check the actual exported chassis opening and named detail meshes."""
import math

def ray_height(doc,decoded,node,x,z):
    heights=[]
    for prim in doc["meshes"][node["mesh"]]["primitives"]:
        pts=decoded[prim["attributes"]["POSITION"]]
        ids=[r[0] for r in decoded[prim["indices"]]]
        for i in range(0,len(ids),3):
            a,b,c=(pts[j] for j in ids[i:i+3])
            den=(b[2]-c[2])*(a[0]-c[0])+(c[0]-b[0])*(a[2]-c[2])
            if abs(den)<1e-14:
                continue
            u=((b[2]-c[2])*(x-c[0])+(c[0]-b[0])*(z-c[2]))/den
            v=((c[2]-a[2])*(x-c[0])+(a[0]-c[0])*(z-c[2]))/den
            w=1-u-v
            if min(u,v,w)>=-1e-7:
                heights.append(u*a[1]+v*b[1]+w*c[1])
    return max(heights) if heights else None


def verify_details(doc,decoded,layout):
    def check(ok,msg):
        if not ok:
            raise ValueError("detail QA: "+msg)
    nodes={n.get("name"):n for n in doc["nodes"]}
    expected={p["name"] for p in layout}
    check(set(nodes)==expected,"component coverage")
    check(all("mesh" in n for n in nodes.values()),"meshless component")
    chassis=nodes["Chassis"]
    check(chassis.get("translation",[0,0,0])==[0,0,0] and chassis.get("rotation",[0,0,0,1])==[0,0,0,1] and chassis.get("scale",[1,1,1])==[1,1,1],"unexpected chassis transform")
    a,b=next(p["rings"][2:4] for p in layout if p["name"]=="Chassis")
    samples=[]
    for t in (.25,.5,.75):
        y=(1-t)*a[0]+t*b[0]
        floor=(1-t)*(a[2]+.24*(a[3]-a[2]))+t*(b[2]+.24*(b[3]-b[2]))
        rim=(1-t)*a[3]+t*b[3]
        actual=ray_height(doc,decoded,chassis,0,-y)
        check(actual is not None and abs(actual-floor)<=1e-5 and rim-actual>1e-3,"cockpit blocked or incorrect depth")
        samples.append({"longitudinal_m":y,"floor_m":actual,"opening_depth_m":rim-actual})
    return {"status":"PASS","cavity_samples":samples,"components":len(expected),
            "halo":"Halo_Ring" in expected,"suspension_links":sum(n.startswith("Suspension_") for n in expected),
            "scope":"exported chassis opening and mesh coverage, not mechanical articulation"}
