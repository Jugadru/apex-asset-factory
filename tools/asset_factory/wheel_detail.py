"""Original slick tire, rim, five spokes and brake assembly; static visual geometry."""
import math
from itertools import product
try:
    from .advanced_body_layout import design as base_design, validate_layout as base_validate
except ImportError:
    from advanced_body_layout import design as base_design, validate_layout as base_validate

PREFIXES=("Wheel","Hub","Rim","Spokes","BrakeDisc","Caliper","CenterNut")
TOL=1e-6


def lathe(profile,sides):
    verts=[(r*math.cos(2*math.pi*i/sides),r*math.sin(2*math.pi*i/sides),z)
           for r,z in profile for i in range(sides)]
    faces=[]
    for j in range(len(profile)):
        k=(j+1)%len(profile)
        for i in range(sides):
            n=(i+1)%sides
            faces.append((j*sides+i,j*sides+n,k*sides+n,k*sides+i))
    return verts,faces


def ring(inner,outer,lo,hi,sides):
    return lathe([(inner,lo),(outer,lo),(outer,hi),(inner,hi)],sides)


def sector(inner,outer,lo,hi,start,end,steps):
    verts=[(r*math.cos(start+(end-start)*i/steps),r*math.sin(start+(end-start)*i/steps),z)
           for i in range(steps+1) for r,z in ((inner,lo),(outer,lo),(outer,hi),(inner,hi))]
    faces=[(3,2,1,0)]
    for i in range(steps):
        for j in range(4):
            k=(j+1)%4
            faces.append((4*i+j,4*i+k,4*(i+1)+k,4*(i+1)+j))
    faces.append(tuple(range(4*steps,4*steps+4)))
    return verts,faces


def spokes(r,w,out,steps):
    verts=[];faces=[]
    for i in range(5):
        angle=2*math.pi*i/5
        vs,fs=sector(.19*r,.65*r,out*.27*w-.045*w,out*.27*w+.045*w,angle-.10,angle+.10,steps)
        offset=len(verts);verts.extend(vs);faces.extend(tuple(j+offset for j in f) for f in fs)
    return verts,faces


def assembly(wheel,level):
    r,w=wheel["radius"],wheel["width"]
    tag=wheel["name"][6:];out=-1 if tag.startswith("L") else 1
    n=(48,24,12)[level];steps=(4,2,1)[level]
    profile=[(.65*r,-.50*w),(.81*r,-.50*w),(.93*r,-.45*w),(.985*r,-.35*w),
             (r,-.23*w),(r,.23*w),(.985*r,.35*w),(.93*r,.45*w),(.81*r,.50*w),(.65*r,.50*w)]
    geometry=[("Wheel",lathe(profile,n),"rubber",True),
              ("Hub",ring(.075*r,.23*r,-.34*w,.34*w,n),"metal",True),
              ("Rim",ring(.60*r,.67*r,-.47*w,.47*w,n),"alloy",True),
              ("Spokes",spokes(r,w,out,steps),"alloy",False),
              ("BrakeDisc",ring(.20*r,.53*r,-out*.15*w-.045*w,-out*.15*w+.045*w,n),"rotor",True),
              ("Caliper",sector(.46*r,.59*r,min(-out*.24*w,out*.18*w),max(-out*.24*w,out*.18*w),.95,1.72,steps+2),"caliper",False),
              ("CenterNut",ring(.025*r,.14*r,out*.42*w-.055*w,out*.42*w+.055*w,6),"metal",False)]
    return [dict(name=f"{name}_{tag}",kind="wheel_mesh",center=wheel["center"][:],radius=r,width=w,
                 material=mat,vertices=vs,faces=fs,smooth=smooth,level=level)
            for name,(vs,fs),mat,smooth in geometry]


def design(request,level=0):
    if type(level) is not int or level not in (0,1,2):raise ValueError("invalid wheel level")
    base=base_design(request,level)
    parts=[p for p in base if not p["name"].startswith(("Wheel_","Hub_"))]
    for wheel in base:
        if wheel["name"].startswith("Wheel_"):parts.extend(assembly(wheel,level))
    return parts


def validate_layout(parts,request):
    detailed=[p for p in parts if p["kind"]=="wheel_mesh"]
    if len(detailed)!=28:raise ValueError("incomplete wheel assemblies")
    level=detailed[0]["level"]
    base=base_design(request,level)
    report=base_validate(base,request)
    if parts!=design(request,level):raise ValueError("wheel layout differs from deterministic design")
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
    report.update(components=len(parts),wheel_parts=28,level=level,scope="static visual wheel assemblies and base shell clearance")
    return report


def verify_wheel_details(doc,decoded,layout):
    def check(ok,msg):
        if not ok:raise ValueError("detailed wheel QA: "+msg)
    nodes={n.get("name"):n for n in doc["nodes"]}
    roots={doc["nodes"][i]["name"] for i in doc["scenes"][doc["scene"]]["nodes"]}
    check(len(nodes)==len(doc["nodes"]) and set(nodes)=={p["name"] for p in layout},"component coverage")
    rows=[]
    for p in layout:
        if p["kind"]!="wheel_mesh":continue
        name=p["name"];node=nodes[name];x,y,z=p["center"]
        center=node.get("translation",[]);q=node.get("rotation",[])
        check(name in roots and node.get("scale",[1,1,1])==[1,1,1] and "matrix" not in node,name+" root/scale")
        check(len(center)==3 and max(abs(a-b) for a,b in zip(center,[x,z,-y]))<=TOL,name+" pivot")
        check(len(q)==4 and abs(sum(v*v for v in q)-1)<=TOL,name+" rotation")
        qx,qy,qz,qw=q;axis=[2*(qx*qy-qz*qw),1-2*(qx*qx+qz*qz),2*(qy*qz+qx*qw)]
        check(max(abs(a-b) for a,b in zip(axis,[1,0,0]))<=TOL,name+" axle")
        check(abs(abs((qw-qz)/math.sqrt(2))-1)<=TOL,name+" rotation around axle")
        prims=doc["meshes"][node["mesh"]]["primitives"]
        actual={tuple(v) for prim in prims for v in decoded[prim["attributes"]["POSITION"]]}
        check({doc["materials"][prim["material"]]["name"] for prim in prims}=={p["material"]},name+" material")
        expected=[(a,c,-b) for a,b,c in p["vertices"]]
        def key(v):return tuple(math.floor(x/TOL) for x in v)
        bins={}
        for i,v in enumerate(expected):bins.setdefault(key(v),[]).append(i)
        seen=set();max_error=0.0
        for v in actual:
            k=key(v);matches=[]
            for delta in product((-1,0,1),repeat=3):
                for i in bins.get(tuple(a+b for a,b in zip(k,delta)),[]):
                    error=max(abs(a-b) for a,b in zip(v,expected[i]))
                    if error<=TOL:matches.append((error,i))
            check(bool(matches),name+" unexpected vertex")
            error,i=min(matches);seen.add(i);max_error=max(max_error,error)
        check(len(seen)==len(expected),name+" missing profile vertices")
        rows.append({"component":name,"vertices":len(expected),"max_error_m":max_error})
    check(len(rows)==28,"wheel part count")
    return {"status":"PASS","tolerance_m":TOL,"parts":rows,"scope":"local mesh vertices, pivots and materials; not articulation or full collision"}
