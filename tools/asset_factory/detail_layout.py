"""Original open cockpit, era-appropriate halo and visual suspension geometry."""
import math
try:
    from .era_layout import design as era_design, shaped_mesh as era_mesh, closed_sections
except ImportError:
    from era_layout import design as era_design, shaped_mesh as era_mesh, closed_sections


def sub(a,b):
    return tuple(x-y for x,y in zip(a,b))


def unit(a):
    length=math.sqrt(sum(x*x for x in a))
    if length<=1e-12:
        raise ValueError("zero-length tube tangent")
    return tuple(x/length for x in a)


def cross(a,b):
    return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])


def tube_mesh(path,radius,sides=10):
    vertices=[]
    for i,p in enumerate(path):
        tangent=unit(sub(path[min(i+1,len(path)-1)],path[max(i-1,0)]))
        reference=(0,0,1) if abs(tangent[2])<.92 else (1,0,0)
        u=unit(cross(tangent,reference))
        v=cross(tangent,u)
        for j in range(sides):
            angle=2*math.pi*j/sides
            vertices.append(tuple(p[k]+radius*(math.cos(angle)*u[k]+math.sin(angle)*v[k]) for k in range(3)))
    return closed_sections(vertices,sides)


def tub_mesh(rings):
    section=[(-.62,0),(.62,0),(1,.22),(1,.72),(.65,1),(-.65,1),(-1,.72),(-1,.22)]
    vertices=[(x*w,y,lo+t*(hi-lo)) for y,w,lo,hi in rings for x,t in section]
    faces=[tuple(reversed(range(8)))]
    for i in range(len(rings)-1):
        for j in range(8):
            if i==2 and j==4:
                continue
            k=(j+1)%8
            faces.append((8*i+j,8*i+k,8*(i+1)+k,8*(i+1)+j))
    n=len(vertices)
    faces.append(tuple(range(n-8,n)))
    # Replace the removed top quad with a recessed floor and four interior walls.
    rim=[20,21,29,28]
    inner=[]
    for idx in rim:
        x,y,z=vertices[idx]
        ring=rings[2 if idx<24 else 3]
        inner.append(len(vertices))
        vertices.append((x*.76,y,ring[2]+.24*(ring[3]-ring[2])))
    for i in range(4):
        j=(i+1)%4
        faces.append((rim[i],rim[j],inner[j],inner[i]))
    faces.append(tuple(inner))
    return vertices,faces


def design(request):
    w,l,h=(request["dimensions_m"][k] for k in ("width","length","height"))
    parts=[p for p in era_design(request) if p["name"]!="Cockpit" and not p["name"].startswith("Suspension_")]
    def box(name,center,size,material):
        parts.append(dict(name=name,kind="box",center=list(center),size=list(size),material=material,bevel=.004))
    def tube(name,path,radius,material):
        parts.append(dict(name=name,kind="tube",shape="tube",path=path,radius=radius,material=material))
    chassis=next(p for p in parts if p["name"]=="Chassis")
    chassis["shape"]="open_tub"
    # Seat is entirely inside the cavity; a dark interior is not a fake top cover.
    ring_a,ring_b=chassis["rings"][2:4]
    def inner_z(y):
        t=(y-ring_a[0])/(ring_b[0]-ring_a[0])
        return (1-t)*(ring_a[2]+.24*(ring_a[3]-ring_a[2]))+t*(ring_b[2]+.24*(ring_b[3]-ring_b[2]))
    seat_y=.014*l
    box("Cockpit_Seat",(0,seat_y,inner_z(seat_y)+.04*h),(.11*w,.057*l,.04*h),"carbon")
    back_y=-.018*l
    box("Cockpit_Backrest",(0,back_y,inner_z(back_y)+.12*h),(.12*w,.014*l,.20*h),"carbon")
    wheel_y=.087*l
    wheel_z=inner_z(wheel_y)+.15*h
    wheel_r=min(.062*w,.10*h)
    tube("Steering_Rim",[(wheel_r*math.cos(i*2*math.pi/12),wheel_y,wheel_z+wheel_r*math.sin(i*2*math.pi/12)) for i in range(12)],wheel_r*.13,"carbon")
    box("Steering_Display",(0,wheel_y,wheel_z),(.7*wheel_r,.10*wheel_r,.5*wheel_r),"accent")
    if request["era"]=="2020-inspired":
        r=min(.014*w,.024*h)
        path=[(-.14*w,-.043*l,.63*h),(-.14*w,-.018*l,.77*h),(-.12*w,.063*l,.77*h),
              (0,.125*l,.72*h),(.12*w,.063*l,.77*h),(.14*w,-.018*l,.77*h),(.14*w,-.043*l,.63*h)]
        tube("Halo_Ring",path,r,"carbon")
        tube("Halo_Front_Post",[(0,.145*l,.41*h),(0,.125*l,.72*h)],r,"carbon")
    for s,side in ((-1,"L"),(1,"R")):
        for axle in ("F","R"):
            tag=side+"_"+axle
            wheel=next(p for p in parts if p["name"]=="Wheel_"+tag)
            x,y,z=wheel["center"]
            outer=x-s*wheel["width"]*.48
            radius=min(w*.0075,h*.011)
            for level,mult in (("Upper",1.19),("Lower",.79)):
                for arm,dy in (("Front",.042*l),("Rear",-.042*l)):
                    tube("Suspension_"+level+"_"+arm+"_"+tag,
                         [(s*w*.13,y+dy,z*mult),(outer,y,z*mult)],radius,"metal")
            tube("Suspension_Pushrod_"+tag,[(s*w*.16,y-.018*l,z*1.48),(outer,y,z*.82)],radius,"carbon")
    return parts


def shaped_mesh(part):
    if part["shape"]=="open_tub":
        return tub_mesh(part["rings"])
    if part["shape"]=="tube":
        return tube_mesh(part["path"],part["radius"])
    return era_mesh(part)


def validate_layout(parts,request):
    names={p["name"] for p in parts}
    if len(names)!=len(parts) or "Cockpit" in names:
        raise ValueError("duplicate or covered cockpit")
    expected_halo=request["era"]=="2020-inspired"
    if ("Halo_Ring" in names)!=expected_halo or ("Halo_Front_Post" in names)!=expected_halo:
        raise ValueError("era halo mismatch")
    if sum(n.startswith("Suspension_") for n in names)!=20:
        raise ValueError("suspension coverage")
    vertices=[]
    for part in parts:
        if "shape" in part:
            vs,faces=shaped_mesh(part)
            edges={}
            for face in faces:
                if len(set(face))!=len(face):
                    raise ValueError("degenerate face")
                for a,b in zip(face,face[1:]+face[:1]):
                    k=tuple(sorted((a,b)))
                    edges[k]=edges.get(k,0)+1
            if len(set(vs))!=len(vs) or any(n!=2 for n in edges.values()):
                raise ValueError("non-manifold shaped component")
            vertices.extend(vs)
        else:
            dims=part["size"] if part["kind"]=="box" else [part["width"],2*part["radius"],2*part["radius"]]
            vertices.extend(tuple(c+s*d/2 for c,d,s in zip(part["center"],dims,signs)) for signs in ((-1,-1,-1),(1,1,1)))
    lo=[min(v[i] for v in vertices) for i in range(3)]
    hi=[max(v[i] for v in vertices) for i in range(3)]
    w,l,h=(request["dimensions_m"][k] for k in ("width","length","height"))
    if any(abs(a-b)>1e-8 for a,b in zip(lo,[-w/2,-l/2,0])) or any(abs(a-b)>1e-8 for a,b in zip(hi,[w/2,l/2,h])):
        raise ValueError("detail envelope")
    return {"status":"PASS","components":len(parts),"bounds":[lo,hi],"halo":expected_halo,
            "cockpit":"recessed mesh","suspension_links":20,"scope":"visual geometry only"}
