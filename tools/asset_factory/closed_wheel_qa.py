"""Actual GLB body shell clearance samples, not collision certification."""
import math


def verify_closed_wheel(doc,decoded,layout):
    nodes={n.get("name"):n for n in doc["nodes"]}
    if set(nodes)!={p["name"] for p in layout}:
        raise ValueError("closed-wheel export component coverage")
    body=nodes["BodyShell"]
    if body.get("translation",[0,0,0])!=[0,0,0] or body.get("rotation",[0,0,0,1])!=[0,0,0,1] or body.get("scale",[1,1,1])!=[1,1,1]:
        raise ValueError("unexpected shell transform")
    triangles=[]
    for prim in doc["meshes"][body["mesh"]]["primitives"]:
        pts=decoded[prim["attributes"]["POSITION"]]
        ids=[r[0] for r in decoded[prim["indices"]]]
        triangles.extend(tuple(pts[j] for j in ids[i:i+3]) for i in range(0,len(ids),3))
    minimum=float("inf");hits=0
    for p in layout:
        if not p["name"].startswith("Wheel_"):continue
        cx,cy,cz=p["center"];r=p["radius"]
        for offset in (-.35,0,.35):
            x=cx+offset*p["width"]
            for f in (-.9,-.6,-.3,0,.3,.6,.9):
                y=cy+f*r;z=-y;heights=[]
                for a,b,c in triangles:
                    den=(b[2]-c[2])*(a[0]-c[0])+(c[0]-b[0])*(a[2]-c[2])
                    if abs(den)<1e-14:continue
                    u=((b[2]-c[2])*(x-c[0])+(c[0]-b[0])*(z-c[2]))/den
                    v=((c[2]-a[2])*(x-c[0])+(a[0]-c[0])*(z-c[2]))/den
                    w=1-u-v
                    if min(u,v,w)>=-1e-7:heights.append(u*a[1]+v*b[1]+w*c[1])
                if heights:
                    hits+=1
                    gap=min(heights)-cz-r*math.sqrt(1-f*f)
                    minimum=min(minimum,gap)
                    if gap<.005:raise ValueError("exported shell intersects wheel clearance")
                elif offset==0 and f==0:
                    raise ValueError("body missing above wheel center")
    if not hits:raise ValueError("no shell clearance samples")
    return {"status":"PASS","samples_with_shell":hits,"min_sampled_clearance_m":minimum,"scope":"sampled exported static shell only"}
