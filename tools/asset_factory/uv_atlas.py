"""Deterministic, conservative secondary UV atlas for static indexed GLBs.

Independent triangle charts are a structural baseline, not an artistic unwrap.
The atlas covers unique mesh primitives, not repeated scene instances.
"""
from collections import Counter
from pathlib import Path
import math
import struct
from asset_factory.validate_glb import inspect, require, MAX_BYTES
from asset_factory.material_factory import glb
from asset_factory.uv_repair import projected, area2, EPS

ATTRS=("POSITION","NORMAL","TEXCOORD_0")

def grid_size(count, resolution):
    require(type(count) is int and count>0,"positive triangle count")
    require(type(resolution) is int and resolution in (1024,2048,4096),"atlas resolution")
    grid=math.isqrt(count-1)+1
    require(resolution/grid>4,"atlas cells cannot accommodate two-pixel padding")
    return grid

def cell_chart(points, index, grid, resolution):
    # Uniform local scale preserves each triangle's shape (not global texel density).
    # The projection's own 1/8 margin is removed; the atlas margin is explicit.
    chart=projected(points)
    pad=2/resolution
    span=1/grid-2*pad
    x,y=index%grid,index//grid
    return [(x/grid+pad+(u-.125)/.75*span,
             y/grid+pad+(v-.125)/.75*span) for u,v in chart]

def audit(doc, decoded, count, resolution):
    grid=grid_size(count,resolution);seen=set();areas=[];density=[]
    margin=math.inf;min_edge=math.inf;min_height=math.inf;subpixel=0;small_area=0;ordinal=0
    for mesh in doc["meshes"]:
        for prim in mesh["primitives"]:
            attrs=prim["attributes"];uv=decoded[attrs["TEXCOORD_1"]]
            pos=decoded[attrs["POSITION"]]
            ids=[r[0] for r in decoded[prim["indices"]]]
            for j in range(0,len(ids),3):
                p=[uv[i] for i in ids[j:j+3]]
                require(all(math.isfinite(v) and 0<=v<=1 for row in p for v in row),"UV2 bounds")
                col,row=ordinal%grid,ordinal//grid
                require((col,row) not in seen,"atlas duplicate cell")
                seen.add((col,row))
                for u,v in p:
                    margin=min(margin,(u-col/grid)*resolution,((col+1)/grid-u)*resolution,
                               (v-row/grid)*resolution,((row+1)/grid-v)*resolution)
                require(margin>=2-.001,"UV2 cell padding violation")
                a=abs(area2(*p))/2
                require(a>EPS,"degenerate UV2 triangle")
                edges=[math.dist(p[k],p[(k+1)%3])*resolution for k in range(3)]
                height=2*a*resolution**2/max(edges)
                min_edge=min(min_edge,*edges);min_height=min(min_height,height)
                subpixel+=height<1;small_area+=a*resolution**2<1
                xyz=[pos[i] for i in ids[j:j+3]]
                u=[xyz[1][k]-xyz[0][k] for k in range(3)]
                v=[xyz[2][k]-xyz[0][k] for k in range(3)]
                physical=math.hypot(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])/2
                require(physical>0,"degenerate source triangle")
                density.append(math.sqrt(a/physical)*resolution);areas.append(a);ordinal+=1
    require(ordinal==count and len(seen)==count,"atlas coverage mismatch")
    instances=Counter(n["mesh"] for n in doc["nodes"] if "mesh" in n)
    return {"triangles":count,"grid":grid,"reference_resolution":resolution,
            "min_cell_margin_px":margin,"min_intercell_gap_bound_px":2*margin,
            "occupied_uv_fraction":math.fsum(areas),"min_edge_px":min_edge,
            "min_altitude_px":min_height,"subpixel_altitude_triangles":subpixel,
            "subpixel_area_triangles":small_area,
            "local_texels_per_unit_min":min(density),"local_texels_per_unit_max":max(density),
            "shared_mesh_instances":sum(n-1 for n in instances.values()),
            "uv_overlap":"PASS","overlap_scope":"unique mesh primitives; exclusive padded cells",
            "baking_readiness":"NOT_RUN","promotion":"BLOCKED"}

def generate_atlas(source,output,source_sha,budget,resolution=2048):
    p=Path(output).absolute()
    require(not p.exists() and not p.is_symlink() and p.suffix==".glb" and p.parent.resolve()==p.parent,"new regular GLB required")
    before,doc,decoded=inspect(source,budget)
    require(before["sha256"]==source_sha,"source hash mismatch")
    grid=grid_size(before["triangles"],resolution)
    from copy import deepcopy
    original=deepcopy(doc)
    doc["accessors"]=[];doc["bufferViews"]=[];data=bytearray()
    def put(rows,ctype,kind,target):
        data.extend(b"\0"*((-len(data))%4));start=len(data)
        fmt=struct.Struct("<"+{5126:"f",5123:"H",5125:"I"}[ctype]*len(rows[0]))
        for row in rows:data.extend(fmt.pack(*row))
        view=len(doc["bufferViews"]);doc["bufferViews"].append(dict(buffer=0,byteOffset=start,byteLength=len(data)-start,target=target))
        acc=dict(bufferView=view,componentType=ctype,count=len(rows),type=kind)
        if kind=="VEC3" and target==34962:
            acc.update(min=[min(r[k] for r in rows) for k in range(3)],max=[max(r[k] for r in rows) for k in range(3)])
        idx=len(doc["accessors"]);doc["accessors"].append(acc);return idx
    ordinal=0
    for mesh in doc["meshes"]:
        for prim in mesh["primitives"]:
            ids=[r[0] for r in decoded[prim["indices"]]]
            rows=[[decoded[prim["attributes"][k]][i] for i in ids] for k in ATTRS]
            atlas=[]
            for j in range(0,len(ids),3):
                atlas.extend(cell_chart(rows[0][j:j+3],ordinal,grid,resolution));ordinal+=1
            prim["attributes"]={k:put(r,5126,kind,34962) for k,r,kind in zip((*ATTRS,"TEXCOORD_1"),(*rows,atlas),("VEC3","VEC3","VEC2","VEC2"))}
            prim["indices"]=put([(i,) for i in range(len(ids))],5123 if len(ids)<=65536 else 5125,"SCALAR",34963)
    doc["buffers"][0]["byteLength"]=len(data)
    raw=glb(doc,data);require(len(raw)<=MAX_BYTES,"atlas GLB size")
    try:
        with p.open("xb") as f:f.write(raw)
        after,ad,ax=inspect(p,budget,allow_uv2=True)
        for k in ("nodes","scenes","scene","materials","asset"):
            require(ad[k]==original[k],"metadata drift: "+k)
        for a,b in zip(original["meshes"],ad["meshes"]):
            require(a.get("name")==b.get("name") and len(a["primitives"])==len(b["primitives"]),"mesh drift")
            for x,y in zip(a["primitives"],b["primitives"]):
                require(x["material"]==y["material"] and x.get("mode",4)==y.get("mode",4),"primitive drift")
                ia=[r[0] for r in decoded[x["indices"]]];ib=[r[0] for r in ax[y["indices"]]]
                require(len(ia)==len(ib),"corner count drift")
                for k in ATTRS:
                    u=decoded[x["attributes"][k]];v=ax[y["attributes"][k]]
                    require(all(u[i]==v[j] for i,j in zip(ia,ib)),"corner drift: "+k)
        receipt=audit(ad,ax,before["triangles"],resolution)
        require(inspect(source,budget)[0]["sha256"]==source_sha,"source changed")
    except Exception:
        # Keep a failed artifact in the isolated workspace for diagnosis; never promote it.
        raise
    return dict(receipt,status="PASS",sha256=after["sha256"],source_sha256=source_sha,
                bytes=after["bytes"],corner_geometry="EXACT",uv0="EXACT",
                vertex_rows_after=3*before["triangles"])
