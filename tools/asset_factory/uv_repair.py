"""Repair collapsed UV triangles of validated static vehicles, without moving geometry."""
import math
import struct
from pathlib import Path
from asset_factory.validate_glb import inspect, require, MAX_BYTES
from asset_factory.material_factory import glb

EPS=1e-12
ATTRS=("POSITION","NORMAL","TEXCOORD_0")


def area2(a,b,c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


def projected(points):
    """Local planar chart, same aspect ratio as 3D triangle; no atlas claim."""
    a,b,c=points
    u=tuple(y-x for x,y in zip(a,b));v=tuple(y-x for x,y in zip(a,c))
    length=math.hypot(*u);require(length>0,"zero edge")
    along=sum(x*y for x,y in zip(u,v))/length
    cross=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
    height=math.hypot(*cross)/length
    xy=[(0.,0.),(length,0.),(along,height)]
    lo=[min(p[k] for p in xy) for k in (0,1)]
    span=max(max(p[k] for p in xy)-lo[k] for k in (0,1))
    uv=[struct.unpack("<2f",struct.pack("<2f",*(.125+.75*(p[k]-lo[k])/span for k in (0,1)))) for p in xy]
    require(abs(area2(*uv))>EPS,"triangle too thin for UV repair")
    return uv


def repair(source,output,source_sha,budget):
    """Repack accessors; split only corners of collapsed triangles, validate result."""
    p=Path(output).absolute()
    require(not p.exists() and not p.is_symlink() and p.suffix==".glb" and p.parent.resolve()==p.parent,"new regular GLB required")
    qa,doc,decoded=inspect(source,budget)
    require(qa["sha256"]==source_sha,"source hash mismatch")
    before_doc=doc.copy()
    # Keep source mesh topology/metadata for comparison; rebuild buffers with only used accessors.
    from copy import deepcopy
    before_doc=deepcopy(before_doc)
    doc["accessors"]=[];doc["bufferViews"]=[];data=bytearray()
    def put(rows,ctype,kind,target):
        data.extend(b"\0"*((-len(data))%4));start=len(data)
        fmt=struct.Struct("<"+({5126:"f",5125:"I",5123:"H"}[ctype])*len(rows[0]))
        for row in rows:data.extend(fmt.pack(*row))
        view=len(doc["bufferViews"]);doc["bufferViews"].append(dict(buffer=0,byteOffset=start,byteLength=len(data)-start,target=target))
        idx=len(doc["accessors"]);acc=dict(bufferView=view,componentType=ctype,count=len(rows),type=kind)
        if target==34962 and kind=="VEC3":
            acc.update(min=[min(r[k] for r in rows) for k in range(3)],max=[max(r[k] for r in rows) for k in range(3)])
        doc["accessors"].append(acc);return idx
    repaired=0;added=0;rows=[]
    for mesh in doc["meshes"]:
        for prim in mesh["primitives"]:
            pos,norm,uv=[list(decoded[prim["attributes"][k]]) for k in ATTRS]
            ids=[r[0] for r in decoded[prim["indices"]]]
            count=0
            for j in range(0,len(ids),3):
                corners=ids[j:j+3]
                if abs(area2(*(uv[i] for i in corners)))>EPS:continue
                chart=projected([pos[i] for i in corners])
                for k,i in enumerate(corners):
                    ids[j+k]=len(pos);pos.append(pos[i]);norm.append(norm[i]);uv.append(chart[k])
                count+=1
            repaired+=count;added+=3*count
            if count:rows.append({"mesh":mesh.get("name",""),"material":prim["material"],"repaired_triangles":count})
            # Compact unreferenced originals while preserving corner order exactly.
            used=sorted(set(ids));remap={old:new for new,old in enumerate(used)}
            prim["attributes"]={k:put([array[i] for i in used],5126,kind,34962) for k,array,kind in zip(ATTRS,(pos,norm,uv),("VEC3","VEC3","VEC2"))}
            prim["indices"]=put([(remap[i],) for i in ids],5123 if len(used)<=65536 else 5125,"SCALAR",34963)
    doc["buffers"][0]["byteLength"]=len(data)
    raw=glb(doc,data);require(len(raw)<=MAX_BYTES,"repaired GLB size")
    with p.open("xb") as f:f.write(raw)
    after,ad,ax=inspect(p,budget)
    require(after["triangles"]==qa["triangles"],"triangle count drift")
    for key in ("nodes","scenes","scene","materials","asset"):
        require(ad[key]==before_doc[key],"metadata drift: "+key)
    checked=0;zero=0;changed=0
    for m,n in zip(before_doc["meshes"],ad["meshes"]):
        require(m.get("name")==n.get("name") and len(m["primitives"])==len(n["primitives"]),"mesh drift")
        for a,b in zip(m["primitives"],n["primitives"]):
            require(a["material"]==b["material"] and a.get("mode",4)==b.get("mode",4),"primitive drift")
            ia=[r[0] for r in decoded[a["indices"]]];ib=[r[0] for r in ax[b["indices"]]]
            require(len(ia)==len(ib),"corner count drift")
            au=decoded[a["attributes"]["TEXCOORD_0"]];bu=ax[b["attributes"]["TEXCOORD_0"]]
            for k in ("POSITION","NORMAL"):
                x=decoded[a["attributes"][k]];y=ax[b["attributes"][k]]
                require(all(x[i]==y[j] for i,j in zip(ia,ib)),"corner geometry drift")
            for j in range(0,len(ia),3):
                old=[au[i] for i in ia[j:j+3]];new=[bu[i] for i in ib[j:j+3]]
                zero+=abs(area2(*new))<=EPS
                if abs(area2(*old))>EPS:
                    require(old==new,"valid UV modified")
                else:changed+=1
                checked+=1
    require(checked==qa["triangles"] and changed==repaired and zero==0,"UV acceptance failed")
    require(inspect(source,budget)[0]["sha256"]==source_sha,"source changed")
    return {"status":"PASS","source_sha256":source_sha,"sha256":after["sha256"],"bytes":after["bytes"],"triangles":checked,"uv_degenerate_before":repaired,"uv_degenerate_after":zero,"split_corners":added,"affected_primitives":rows,"corner_geometry":"EXACT","valid_uvs":"EXACT","uv_overlap":"NOT_RUN","texel_density":"NOT_RUN","promotion":"BLOCKED"}
