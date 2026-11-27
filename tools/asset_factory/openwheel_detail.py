"""Original era-inspired open-wheel assemblies; no sporting or historical certification."""
import math
try:
    from .detail_layout import design as base_design, validate_layout as base_validate, shaped_mesh
    from .wheel_detail import lathe, ring, sector, TOL
except ImportError:
    from detail_layout import design as base_design, validate_layout as base_validate, shaped_mesh
    from wheel_detail import lathe, ring, sector, TOL

# Artistic profiles, not measured historical tire or rim specifications.
PROFILES={"1990-inspired":(.56,5,.18),"2012-inspired":(.60,6,.23),"2020-inspired":(.64,8,.27)}


def assembly(wheel,era,level):
    rim,count,shoulder=PROFILES[era]
    r,w=wheel["radius"],wheel["width"]
    tag=wheel["name"][6:];out=-1 if tag.startswith("L") else 1
    n=(48,24,12)[level];steps=(3,2,1)[level]
    profile=[((rim-.02)*r,-.50*w),(.82*r,-.50*w),(.94*r,-.45*w),(.985*r,-.36*w),
             (r,-shoulder*w),(r,shoulder*w),(.985*r,.36*w),(.94*r,.45*w),(.82*r,.50*w),((rim-.02)*r,.50*w)]
    vs=[];fs=[]
    for i in range(count):
        angle=2*math.pi*i/count
        v,f=sector(.20*r,(rim-.01)*r,out*.28*w-.045*w,out*.28*w+.045*w,angle-.09,angle+.09,steps)
        offset=len(vs);vs.extend(v);fs.extend(tuple(j+offset for j in face) for face in f)
    # Inboard hub sleeve reaches the existing suspension end points.
    geometry=[("Wheel",lathe(profile,n),"rubber",True),
              ("Hub",ring(.055*r,.29*r,min(-out*.50*w,out*.34*w),max(-out*.50*w,out*.34*w),n),"metal",True),
              ("Rim",ring((rim-.065)*r,rim*r,-.47*w,.47*w,n),"alloy",True),
              ("Spokes",(vs,fs),"alloy",False),
              ("BrakeDisc",ring(.22*r,(rim-.10)*r,-out*.16*w-.045*w,-out*.16*w+.045*w,n),"rotor",True),
              ("Caliper",sector((rim-.15)*r,(rim-.035)*r,min(-out*.24*w,out*.18*w),max(-out*.24*w,out*.18*w),.95,1.72,steps+2),"caliper",False),
              ("CenterNut",ring(.025*r,.15*r,out*.42*w-.055*w,out*.42*w+.055*w,6),"metal",False)]
    return [dict(name=f"{name}_{tag}",kind="wheel_mesh",center=wheel["center"][:],radius=r,width=w,
                 material=mat,vertices=v,faces=f,smooth=smooth,level=level)
            for name,(v,f),mat,smooth in geometry]


def design(request,level=0):
    if type(level) is not int or level not in (0,1,2):raise ValueError("invalid wheel level")
    base=base_design(request)
    parts=[p for p in base if not p["name"].startswith(("Wheel_","Hub_"))]
    for wheel in base:
        if wheel["name"].startswith("Wheel_"):parts.extend(assembly(wheel,request["era"],level))
    return parts


def validate_layout(parts,request):
    detailed=[p for p in parts if p["kind"]=="wheel_mesh"]
    if len(detailed)!=28:raise ValueError("incomplete openwheel assemblies")
    level=detailed[0]["level"]
    report=base_validate(base_design(request),request)
    if parts!=design(request,level):raise ValueError("openwheel layout differs from deterministic design")
    for p in detailed:
        vs,fs=p["vertices"],p["faces"]
        edges={}
        for f in fs:
            if len(set(f))!=len(f):raise ValueError("degenerate wheel face")
            for a,b in zip(f,f[1:]+f[:1]):
                k=tuple(sorted((a,b)));edges[k]=edges.get(k,0)+1
        if len(set(vs))!=len(vs) or any(n!=2 for n in edges.values()):raise ValueError("non-manifold wheel part")
        if any(math.hypot(x,y)>p["radius"]+TOL or abs(z)>p["width"]/2+TOL for x,y,z in vs):
            raise ValueError("wheel part outside tire envelope")
    report.update(components=len(parts),wheel_parts=28,level=level,era=request["era"],spokes_per_wheel=PROFILES[request["era"]][1],scope="static visual openwheel assemblies and base cockpit")
    return report
