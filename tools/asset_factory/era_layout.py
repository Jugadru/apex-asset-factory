"""Original open-wheel era-inspired silhouettes; visual only, no sporting data."""
try:
    from .modular_layout import design as base_design, validate_layout as base_validate
except ImportError:
    from modular_layout import design as base_design, validate_layout as base_validate

ERAS={
    "1990-inspired": {"nose_height":0.78,"pod_width":1.12,"airbox_height":0.82,"wing_shape":0.82},
    "2012-inspired": {"nose_height":1.0,"pod_width":1.0,"airbox_height":1.0,"wing_shape":1.0},
    "2020-inspired": {"nose_height":0.88,"pod_width":0.85,"airbox_height":1.05,"wing_shape":1.16},
}


def design(request):
    parts=base_design(request)
    profile=ERAS[request["era"]]
    for p in parts:
        name=p["name"]
        if name=="Chassis":
            for i,r in enumerate(p["rings"]):
                if i>=3:
                    r[3]=r[2]+(r[3]-r[2])*profile["nose_height"]
            p["shape"]="rounded_loft"
        elif name.startswith("Sidepod_") and "inlet" not in name:
            p["size"][0]*=profile["pod_width"]
            p["shape"]="tapered"
        elif name=="Airbox":
            p["size"][2]*=profile["airbox_height"]
            p["center"][2]=min(p["center"][2],request["dimensions_m"]["height"]-p["size"][2]/2)
            p["shape"]="tapered"
        elif name in ("FrontWing","RearWing") or "_flap_" in name:
            p["shape"]="airfoil"
            p["camber"]=profile["wing_shape"]
        elif name=="Cockpit":
            p["shape"]="tapered"
    return parts


def rings_mesh(rings,offset=0):
    # Octagonal cross-section with rounded shoulders; exact bounding extents.
    section=[(-.62,0),(.62,0),(1,.22),(1,.72),(.65,1),(-.65,1),(-1,.72),(-1,.22)]
    verts=[(offset+x*w,y,lo+t*(hi-lo)) for y,w,lo,hi in rings for x,t in section]
    return closed_sections(verts,len(section))


def closed_sections(verts,n):
    count=len(verts)//n
    faces=[tuple(reversed(range(n)))]
    for i in range(count-1):
        for j in range(n):
            k=(j+1)%n
            faces.append((i*n+j,i*n+k,(i+1)*n+k,(i+1)*n+j))
    faces.append(tuple(range((count-1)*n,count*n)))
    return verts,faces


def shaped_mesh(part):
    shape=part.get("shape")
    if shape=="rounded_loft":
        return rings_mesh(part["rings"])
    x,y,z=part["center"]
    dx,dy,dz=part["size"]
    if shape=="tapered":
        rings=[]
        for t,w,low,high in ((-.5,.65,.14,.72),(-.32,1,0,.92),(.12,1,0,1),(.5,.55,.16,.65)):
            rings.append((y+t*dy,dx*.5*w,z+dz*(low-.5),z+dz*(high-.5)))
        return rings_mesh(rings,x)
    if shape=="airfoil":
        # Eight-point closed section, wing spans X. Not an aerodynamic model.
        c=part["camber"]
        section=[(0,.38),(.12,min(.97,.75*c)),(.35,1),(.72,min(.92,.65*c)),
                 (1,.34),(.78,.10),(.3,0),(.08,.08)]
        verts=[(x+s*dx/2,y+(t-.5)*dy,z+(v-.5)*dz) for s in (-1,1) for t,v in section]
        return closed_sections(verts,len(section))
    raise ValueError("unsupported shaped component")


def validate_layout(parts,request):
    result=base_validate(parts,request)
    shaped=0
    for p in parts:
        if "shape" not in p:
            continue
        vertices,faces=shaped_mesh(p)
        if len(set(vertices))!=len(vertices) or any(len(set(f))!=len(f) for f in faces):
            raise ValueError("degenerate shaped mesh")
        shaped+=1
    result.update(era=request["era"],shaped_components=shaped,scope="analytic original visual layout")
    return result
