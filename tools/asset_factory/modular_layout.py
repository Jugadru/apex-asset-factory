"""Pure, deterministic geometry layout in metres; Blender axes X/right, Y/front, Z/up."""
import random

PROFILES={
    "balanced":{"nose":0.115,"pod":0.205,"front_wing":0.22,"rear_wing":0.23},
    "low-drag":{"nose":0.095,"pod":0.175,"front_wing":0.17,"rear_wing":0.18},
    "high-downforce":{"nose":0.125,"pod":0.225,"front_wing":0.28,"rear_wing":0.29},
}
# Profile names describe appearance only, not physical or sporting effects.
def design(request):
    w,l,h=(request["dimensions_m"][k] for k in ("width","length","height"))
    profile=PROFILES[request["components"]["body"]]
    tire=request["components"]["tires"]
    radius=min(h*.285,w*.19,l*.074)
    front_width=w*(.132 if tire=="wide" else .105)
    rear_width=w*(.158 if tire=="wide" else .127)
    rng=random.Random(request["seed"])
    # Geometry variation is deterministic and symmetric.
    variation=1+(rng.random()-.5)*.08
    parts=[]
    def box(name,x,y,z,dx,dy,dz,material,bevel=0.008):
        parts.append(dict(name=name,kind="box",center=[x,y,z],size=[dx,dy,dz],material=material,bevel=bevel))
    def cyl(name,x,y,z,r,width,material,sides=40):
        parts.append(dict(name=name,kind="cylinder",center=[x,y,z],radius=r,width=width,material=material,sides=sides))
    def loft(name,rings,material):
        parts.append(dict(name=name,kind="loft",rings=rings,material=material))
    loft("Chassis",[[l*y,w*half*variation,h*lo,h*hi] for y,half,lo,hi in [
        (-.36,.15,.16,.47),(-.25,.23,.16,.68),(-.04,.21,.15,.64),
        (.12,.15,.16,.46),(.29,profile["nose"],.18,.34),(.40,.045,.19,.27)]],"paint")
    box("Floor",0,-l*.08,h*.12,w*.70,l*.53,h*.07,"carbon")
    box("Cockpit",0,l*.035,h*.61,w*.18,l*.12,h*.10,"carbon")
    box("Airbox",0,-l*.13,h*.79,w*.17,l*.075,h*.34,"paint")
    # Exact envelope is established by rectangular wing extremities,
    # not by anisotropic rescaling of tires.
    box("FrontWing",0,l*.455,h*.19,w*.98,l*.09,h*.07,"paint",0)
    box("RearWing",0,-l*.455,h*.955,w*.75,l*.09,h*.09,"paint",0)
    box("RearWing_support",0,-l*.42,h*.57,w*.08,l*.04,h*.70,"carbon")
    box("Livery_stripe",0,l*.22,h*.40,w*.046,l*.16,h*.018,"accent")
    for sign,side in ((-1,"L"),(1,"R")):
        box("Sidepod_"+side,sign*w*.265,-l*.10,h*.37,w*profile["pod"],l*.26,h*.36,"paint")
        box("Sidepod_inlet_"+side,sign*w*.265,l*.035,h*.40,w*profile["pod"]*.72,l*.018,h*.16,"carbon")
        box("Front_endplate_"+side,sign*w*.476,l*.455,h*.25,w*.048,l*.09,h*.19,"carbon",0)
        box("Rear_endplate_"+side,sign*w*.36,-l*.455,h*.84,w*.045,l*.09,h*.30,"carbon",0)
        box("Front_flap_"+side,sign*w*.27,l*.43,h*.25,w*.42,l*profile["front_wing"]*.12,h*.05,"paint")
        box("Rear_flap_"+side,sign*w*.18,-l*.42,h*.87,w*.34,l*profile["rear_wing"]*.12,h*.04,"paint")
        for axle,y,width in (("F",l*.265,front_width),("R",-l*.27,rear_width)):
            # Wheel and hub share an axle and center. No radial distortion.
            x=sign*(w*.48-width/2)
            tag=side+"_"+axle
            cyl("Wheel_"+tag,x,y,radius,radius,width,"rubber")
            cyl("Hub_"+tag,x,y,radius,radius*.61,width*.72,"metal",32)
            for upper,z in (("Upper",radius*1.17),("Lower",radius*.76)):
                box("Suspension_"+upper+"_"+tag,sign*w*.24,y,z,w*.36,l*.017,h*.028,"metal",.003)
    return parts

def validate_layout(parts,request):
    names={p["name"] for p in parts}
    if len(names)!=len(parts):raise ValueError("duplicate component")
    indexed={p["name"]:p for p in parts}
    w,l,h=(request["dimensions_m"][k] for k in ("width","length","height"))
    for axle in ("F","R"):
        a,b=(indexed["Wheel_"+s+"_"+axle] for s in "LR")
        if a["radius"]!=b["radius"] or a["width"]!=b["width"] or a["center"][0]!=-b["center"][0] or a["center"][1:]!=b["center"][1:]:
            raise ValueError("asymmetric wheels")
        for s in "LR":
            wheel=indexed["Wheel_"+s+"_"+axle]
            hub=indexed["Hub_"+s+"_"+axle]
            if hub["center"]!=wheel["center"] or hub["radius"]>=wheel["radius"] or wheel["center"][2]!=wheel["radius"]:
                raise ValueError("wheel/hub pivot")
    # Analytic bounding boxes, before Blender export.
    bounds=[]
    for p in parts:
        if p["kind"]=="loft":
            pts=[(x,y,z) for y,half,lo,hi in p["rings"] for x in (-half,half) for z in (lo,hi)]
        else:
            dims=p["size"] if p["kind"]=="box" else [p["width"],2*p["radius"],2*p["radius"]]
            pts=[tuple(c+s*d/2 for c,d,s in zip(p["center"],dims,signs)) for signs in ((-1,-1,-1),(1,1,1))]
        bounds.extend(pts)
    lo=[min(p[i] for p in bounds) for i in range(3)]
    hi=[max(p[i] for p in bounds) for i in range(3)]
    if any(abs(x-y)>1e-8 for x,y in zip(lo,[-w/2,-l/2,0])) or any(abs(x-y)>1e-8 for x,y in zip(hi,[w/2,l/2,h])):
        raise ValueError("layout envelope")
    return {"status":"PASS","components":len(parts),"bounds":[lo,hi],"wheel_profile":"round","wheel_pivots":"analytic only"}
