"""Original closed-wheel GT and endurance silhouettes, dimensions in metres."""
import math
import random
try:
    from .era_layout import closed_sections
except ImportError:
    from era_layout import closed_sections

PROFILES = {
    "gt": [(-.5,.40,.43),(-.40,.47,.55),(-.26,.50,.61),(-.10,.45,.59),(.10,.45,.56),(.26,.50,.56),(.40,.46,.44),(.5,.38,.34)],
    "endurance": [(-.5,.43,.42),(-.40,.48,.48),(-.26,.50,.55),(-.10,.42,.47),(.10,.41,.46),(.26,.50,.54),(.40,.47,.39),(.5,.39,.30)],
}


def interpolate(points,y):
    for a,b in zip(points,points[1:]):
        if a[0]<=y<=b[0]:
            t=(y-a[0])/(b[0]-a[0])
            return tuple((1-t)*x+t*z for x,z in zip(a[1:],b[1:]))
    raise ValueError("station outside profile")


def hull(request, wheels):
    w,l,h=(request["dimensions_m"][k] for k in ("width","length","height"))
    points=PROFILES[request["category"]]
    # Add stations at each wheel's inflated arch, plus outside transition stations.
    stations={max(-.493,min(.497,y))*l for y,_,_ in points}
    arches=[]
    for wheel in wheels:
        if not wheel["name"].startswith("Wheel_L_"):
            continue
        _,y,z=wheel["center"]
        r=wheel["radius"]
        R=r+max(.025,.12*r)
        arches.append((y,z,r,R))
        stations.update(y+R*math.cos(math.pi*i/20) for i in range(21))
        stations.update((y-R-.012*l,y+R+.012*l))
    ys=[]
    for y in sorted(stations):
        if not ys or y-ys[-1]>1e-6:
            ys.append(y)
    verts=[]
    rows=[]
    for y in ys:
        width,top=interpolate(points,y/l)
        width*=w
        # Pin max envelope to axle stations; cap shoulder at 0.86 h.
        if any(abs(y-a[0])<1e-6 for a in arches):width=w/2
        bottom=.13*h
        for center,z,r,R in arches:
            if abs(y-center)<=R+1e-8:
                bottom=max(bottom,z+math.sqrt(max(0,R*R-(y-center)**2)))
        shoulder=max(top*h*.90,bottom+.035*h)
        crown=max(top*h,shoulder+.035*h)
        inner=.19*w
        section=[(-inner,.075*h),(inner,.075*h),(inner,bottom),(.94*width,bottom),
                 (width,shoulder),(.82*width,crown),(-.82*width,crown),(-width,shoulder),
                 (-.94*width,bottom),(-inner,bottom)]
        verts.extend((x,y,z) for x,z in section)
        rows.append((y,bottom))
    mesh=closed_sections(verts,10)
    return mesh,rows,arches


def capsule(rings):
    # Rounded 12-sided section, reduced width at the roof and low belt line.
    section=[(-.70,0),(.70,0),(.94,.12),(1,.34),(.88,.68),(.58,.91),(.30,1),(-.30,1),(-.58,.91),(-.88,.68),(-1,.34),(-.94,.12)]
    verts=[(x*half,y,lo+t*(hi-lo)) for y,half,lo,hi in rings for x,t in section]
    return closed_sections(verts,len(section))


def design(request):
    w,l,h=(request["dimensions_m"][k] for k in ("width","length","height"))
    gt=request["category"]=="gt"
    rng=random.Random(request["seed"])
    cabin_factor=1+(rng.random()-.5)*.04
    parts=[]
    def box(name,center,size,material,bevel=.008):
        parts.append(dict(name=name,kind="box",center=list(center),size=list(size),material=material,bevel=bevel))
    def mesh(name,geometry,material,smooth=True):
        vertices,faces=geometry
        parts.append(dict(name=name,kind="mesh",vertices=vertices,faces=faces,material=material,smooth=smooth))
    r=min(.275*h,.178*w,.071*l)
    for sign,side in ((-1,"L"),(1,"R")):
        for axle,y in (("F",.26*l),("R",-.26*l)):
            width=w*((.125 if axle=="F" else .15) if request["components"]["tires"]=="wide" else (.105 if axle=="F" else .13))
            x=sign*(.475*w-width/2)
            for prefix,rad,dep,mat,sides in (("Wheel",r,width,"rubber",48),("Hub",r*.67,width*1.08,"metal",40)):
                parts.append(dict(name=f"{prefix}_{side}_{axle}",kind="cylinder",center=[x,y,r],radius=rad,width=dep,material=mat,sides=sides))
    geometry,_,_=hull(request,parts)
    mesh("BodyShell",geometry,"paint")
    cabin=[(-.27,.14,.53,.64),(-.16,.24,.54,.92),(-.04,.25,.55,1),(.08,.24,.55,.97),(.21,.19,.54,.69)] if gt else [(-.18,.11,.48,.65),(-.10,.17,.48,.91),(0,.18,.49,1),(.09,.16,.48,.91),(.19,.10,.47,.62)]
    mesh("Canopy",capsule([(y*l,half*w*cabin_factor,lo*h,hi*h) for y,half,lo,hi in cabin]),"glass")
    box("FrontSplitter",(0,.465*l,.10*h),(.82*w,.07*l,.045*h),"carbon")
    box("RearDiffuser",(0,-.46*l,.10*h),(.79*w,.08*l,.06*h),"carbon")
    wing_section=[(0,.42),(.15,.88),(.38,1),(.74,.65),(1,.32),(.73,.12),(.34,0),(.08,.08)]
    mesh("RearWing",closed_sections([(x,-.44*l+(t-.5)*.09*l,.80*h+(z-.5)*.055*h) for x in (-.44*w,.44*w) for t,z in wing_section],8),"carbon")
    box("FrontGrille",(0,.498*l,.255*h),(.43*w,.004*l,.13*h),"carbon",0)
    for sign,side in ((-1,"L"),(1,"R")):
        box("FrontIntake_"+side,(sign*.29*w,.495*l,.25*h),(.10*w,.006*l,.09*h),"carbon",0)
    for sign,side in ((-1,"L"),(1,"R")):
        box("WingSupport_"+side,(sign*.24*w,-.43*l,.64*h),(.025*w,.035*l,.30*h),"carbon")
        box("Headlight_"+side,(sign*.28*w,.468*l,.37*h),(.20*w,.025*l,.043*h),"light")
        box("Taillight_"+side,(sign*.27*w,-.496*l,.43*h),(.23*w,.008*l,.035*h),"tail")
        box("SideSkirt_"+side,(sign*.425*w,0,.145*h),(.06*w,.32*l,.045*h),"carbon")
        box("Mirror_"+side,(sign*.31*w,.095*l,.68*h),(.075*w,.037*l,.06*h),"paint")
    if not gt:
        mesh("DorsalFin",capsule([(-.40*l,.012*w,.49*h,.58*h),(-.24*l,.012*w,.48*h,.79*h),(-.12*l,.010*w,.48*h,.85*h)]),"paint")
    return parts


def validate_layout(parts,request):
    names={p["name"] for p in parts}
    if len(names)!=len(parts) or not {"BodyShell","Canopy","RearWing"}<=names:
        raise ValueError("closed-wheel component coverage")
    _,rows,arches=hull(request,parts)
    clearance=float("inf")
    for cy,cz,r,R in arches:
        for (ya,za),(yb,zb) in zip(rows,rows[1:]):
            for i in range(21):
                t=i/20;y=ya+(yb-ya)*t
                if abs(y-cy)<=r:
                    z=za+(zb-za)*t
                    gap=z-cz-math.sqrt(max(0,r*r-(y-cy)**2))
                    clearance=min(clearance,gap)
    if clearance<.005:
        raise ValueError("wheel arch clearance")
    vertices=[]
    for p in parts:
        if p["kind"]=="mesh":
            edges={}
            for f in p["faces"]:
                if len(set(f))!=len(f):raise ValueError("degenerate face")
                for a,b in zip(f,f[1:]+f[:1]):
                    k=tuple(sorted((a,b)));edges[k]=edges.get(k,0)+1
            if len(set(p["vertices"]))!=len(p["vertices"]) or any(n!=2 for n in edges.values()):raise ValueError("non-manifold surface")
            vertices.extend(p["vertices"])
        else:
            dims=p["size"] if p["kind"]=="box" else [p["width"],2*p["radius"],2*p["radius"]]
            vertices.extend(tuple(c+s*d/2 for c,d,s in zip(p["center"],dims,signs)) for signs in ((-1,-1,-1),(1,1,1)))
    lo=[min(v[i] for v in vertices) for i in range(3)];hi=[max(v[i] for v in vertices) for i in range(3)]
    w,l,h=(request["dimensions_m"][k] for k in ("width","length","height"))
    if any(abs(a-b)>1e-7 for a,b in zip(lo,[-w/2,-l/2,0])) or any(abs(a-b)>1e-7 for a,b in zip(hi,[w/2,l/2,h])):raise ValueError("closed-wheel envelope")
    return {"status":"PASS","category":request["category"],"components":len(parts),"bounds":[lo,hi],"sampled_arch_clearance_m":clearance,"scope":"analytic visual layout, not collision or mechanics"}
