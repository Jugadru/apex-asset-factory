"""Original curved closed-wheel body surfaces; no licensed replicas or sporting model."""
import math
try:
    from .closed_wheel_layout import design as base_design, validate_layout as base_validate, PROFILES
    from .era_layout import closed_sections
    from .closed_wheel_qa import verify_closed_wheel
except ImportError:
    from closed_wheel_layout import design as base_design, validate_layout as base_validate, PROFILES
    from era_layout import closed_sections
    from closed_wheel_qa import verify_closed_wheel


def smooth_profile(points, y):
    """Shape-preserving cubic Hermite, with zero slope at local extrema."""
    xs=[p[0] for p in points]
    if not xs[0]<=y<=xs[-1]:raise ValueError("station outside profile")
    i=next((j for j in range(len(xs)-1) if y<=xs[j+1]),len(xs)-2)
    dx=xs[i+1]-xs[i];t=(y-xs[i])/dx
    values=[]
    for k in range(1,len(points[0])):
        v=[p[k] for p in points]
        d=[(b-a)/(xs[j+1]-xs[j]) for j,(a,b) in enumerate(zip(v,v[1:]))]
        m=[d[0]]+[0 if a*b<=0 else 2*a*b/(a+b) for a,b in zip(d,d[1:])]+[d[-1]]
        z=(2*t**3-3*t*t+1)*v[i]+(t**3-2*t*t+t)*dx*m[i]+(-2*t**3+3*t*t)*v[i+1]+(t**3-t*t)*dx*m[i+1]
        values.append(max(min(v[i],v[i+1]),min(max(v[i],v[i+1]),z)))
    return tuple(values)


def stations(points,count,extra=()):
    lo,hi=points[0][0],points[-1][0]
    ys=sorted(set([p[0] for p in points]+[lo+(hi-lo)*i/count for i in range(count+1)]+list(extra)))
    result=[]
    for y in ys:
        if not result or y-result[-1]>1e-5:result.append(y)
    return result


def curved_shell(request,parts,level):
    w,l,h=(request["dimensions_m"][k] for k in ("width","length","height"))
    points=[(max(-.493,min(.497,y)),width,top) for y,width,top in PROFILES[request["category"]]]
    if request["category"]=="gt":
        points=[(y,width,max(top,{.10:.59,.26:.63,.40:.46}.get(y,top))) for y,width,top in points]
    arches=[];extra=[]
    for wheel in parts:
        if not wheel["name"].startswith("Wheel_L_"):continue
        _,y,z=wheel["center"];r=wheel["radius"];R=r+max(.025,.12*r)
        arches.append((y,z,R))
        n=(24,16,12)[level]
        extra.extend((y+R*math.cos(math.pi*i/n))/l for i in range(n+1))
        extra.extend(((y-R-.04*l)/l,(y+R+.04*l)/l))
    ys=stations(points,(48,24,16)[level],extra)
    rows=[]
    for yf in ys:
        y=yf*l;width,top=smooth_profile(points,yf);width*=w
        bottom=.13*h
        for cy,z,R in arches:
            gap=abs(y-cy)
            if gap<=R:
                bottom=max(bottom,z+math.sqrt(max(0,R*R-gap*gap)))
            elif gap<R+.04*l:
                t=(gap-R)/(.04*l);bottom=max(bottom,.13*h+(z-.13*h)*(1-3*t*t+2*t*t*t))
        shoulder=max(top*h*.91,bottom+.026*h)
        crown=max(top*h,shoulder+.027*h)
        inner=.19*w
        # Lower return, arch lip, rounded fender shoulder, and broad hood crown.
        right=[(inner,.075*h),(inner,bottom),(.88*width,bottom),(.96*width,bottom+.20*(shoulder-bottom)),(width,shoulder),(.96*width,shoulder+.60*(crown-shoulder)),(.81*width,crown),(.43*width,crown+.006*h)]
        section=right+[(-x,z) for x,z in reversed(right)]
        rows.append([(x,y,z) for x,z in section])
    return rows,closed_sections([v for row in rows for v in row],16)


def curved_cabin(request,parts,level):
    w,l,h=(request["dimensions_m"][k] for k in ("width","length","height"))
    # Roof crown and side glass have different sections; front is positive Y.
    gt=request["category"]=="gt"
    profile=[(-.30,.15,.52,.63),(-.19,.245,.53,.86),(-.095,.26,.54,1),(.035,.255,.54,1),(.105,.24,.54,.92),(.23,.19,.53,.58)] if gt else [(-.22,.10,.46,.56),(-.12,.175,.48,.83),(-.02,.185,.49,1),(.055,.17,.48,.97),(.13,.145,.47,.76),(.22,.09,.46,.54)]
    factor=max(abs(v[0]) for v in next(p for p in parts if p["name"]=="Canopy")["vertices"])/(w*(.25 if gt else .18))
    section=[(.68,0),(.94,.10),(1,.30),(.94,.53),(.78,.77),(.61,.94),(.48,1),(.20,1)]
    section=section+[(-x,z) for x,z in reversed(section)]
    verts=[]
    for y in stations(profile,(24,12,8)[level]):
        half,lo,hi=smooth_profile(profile,y)
        verts.extend((x*half*w*factor,y*l,(lo+t*(hi-lo))*h) for x,t in section)
    return closed_sections(verts,len(section))


def top_at(rows,x,y):
    for a,b in zip(rows,rows[1:]):
        if a[0][1]<=y<=b[0][1]:
            t=(y-a[0][1])/(b[0][1]-a[0][1]);row=[((1-t)*p[0]+t*q[0],(1-t)*p[2]+t*q[2]) for p,q in zip(a,b)]
            hits=[]
            for (xa,za),(xb,zb) in zip(row,row[1:]+row[:1]):
                if min(xa,xb)<=x<=max(xa,xb) and abs(xb-xa)>1e-10:
                    hits.append(za+(zb-za)*(x-xa)/(xb-xa))
            if hits:return max(hits)
    raise ValueError("lamp outside shell")


def design(request,level=0):
    if type(level) is not int or level not in (0,1,2):raise ValueError("invalid surface level")
    parts=base_design(request)
    rows,shell=curved_shell(request,parts,level)
    cabin=curved_cabin(request,parts,level)
    w,l,h=(request["dimensions_m"][k] for k in ("width","length","height"))
    for p in parts:
        name=p["name"]
        if name in ("BodyShell","Canopy"):
            p["vertices"],p["faces"]=shell if name=="BodyShell" else cabin
        elif name.startswith("Headlight_"):
            s=-1 if name.endswith("_L") else 1
            coords=[(s*.22*w,.442*l),(s*.34*w,.427*l),(s*.375*w,.354*l),(s*.30*w,.365*l)]
            verts=[(x,y,top_at(rows,x,y)+offset*h) for offset in (.008,.024) for x,y in coords]
            for k in ("center","size","bevel"):p.pop(k)
            p.update(kind="mesh",vertices=verts,faces=closed_sections(verts,4)[1],smooth=False)
    return parts


def validate_layout(parts,request):
    report=base_validate(parts,request)
    # Inspect the actual new body, not the old analytic profile used by base_validate.
    body=next(p for p in parts if p["name"]=="BodyShell")
    pts=[(x,z,-y) for x,y,z in body["vertices"]]
    ids=[(i,) for face in body["faces"] for j in range(1,len(face)-1) for i in (face[0],face[j],face[j+1])]
    doc={"nodes":[{"name":p["name"],"mesh":0} for p in parts],"meshes":[{"primitives":[{"attributes":{"POSITION":0},"indices":1}]}]}
    qa=verify_closed_wheel(doc,[pts,ids],parts)
    report.update(surface_vertices=len(body["vertices"]),sampled_arch_clearance_m=qa["min_sampled_clearance_m"],scope="curved surface layout and sampled shell clearance")
    return report
