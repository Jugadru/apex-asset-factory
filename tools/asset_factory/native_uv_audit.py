"""Check UV0/UV2 corner correspondence in native imported triangle arrays.

Use UV2 exclusive cell as an order-independent key. Blender has V inverted
relative to glTF; Godot has the glTF convention. No fitted per-chart transform.
"""
from itertools import permutations
import json
import math
from pathlib import Path
from asset_factory.validate_glb import inspect, require, MAX_BYTES
from asset_factory.uv_atlas import grid_size
from asset_factory.uv_repair import area2

TOLERANCE=3e-5

def source_triangles(doc,decoded):
    for mesh in doc["meshes"]:
        for p in mesh["primitives"]:
            uv0=decoded[p["attributes"]["TEXCOORD_0"]]
            uv2=decoded[p["attributes"]["TEXCOORD_1"]]
            ids=[row[0] for row in decoded[p["indices"]]]
            for j in range(0,len(ids),3):
                yield [tuple(uv0[i])+tuple(uv2[i]) for i in ids[j:j+3]]

def compare(expected,actual,resolution,flip_v=False,tolerance=TOLERANCE):
    require(type(flip_v) is bool and 0<tolerance<=TOLERANCE,"invalid precision policy")
    expected=list(expected);grid=grid_size(len(expected),resolution)
    require(type(actual) is list and len(actual)==len(expected),"native triangle count")
    seen=set();max0=max2=0.;margin=math.inf;minimum_altitude=math.inf;subpixel=0
    for tri in actual:
        require(type(tri) is list and len(tri)==3 and all(type(r) in (tuple,list) and len(r)==4 and all(type(v) in (int,float) and math.isfinite(v) for v in r) for r in tri),"native UV data")
        rows=[(r[0],1-r[1] if flip_v else r[1],r[2],1-r[3] if flip_v else r[3]) for r in tri]
        uv=[r[2:] for r in rows]
        require(all(0<=v<=1 for r in uv for v in r),"native UV2 bounds")
        col,row=(int(sum(r[k] for r in uv)/3*grid) for k in range(2))
        idx=row*grid+col
        require(0<=col<grid and 0<=row<grid and 0<=idx<len(expected) and idx not in seen,"native UV2 missing or duplicate cell")
        seen.add(idx)
        for u,v in uv:
            margin=min(margin,(u-col/grid)*resolution,((col+1)/grid-u)*resolution,(v-row/grid)*resolution,((row+1)/grid-v)*resolution)
        require(margin>=2-(tolerance*resolution+.001),"native UV2 padding")
        area=abs(area2(*uv))
        require(area>1e-12,"native UV2 degeneracy")
        height=area*resolution/max(math.dist(uv[k],uv[(k+1)%3]) for k in range(3))
        minimum_altitude=min(minimum_altitude,height);subpixel+=height<1
        # Pair both UV layers under the same permutation, including flipped winding.
        def error(order):
            return tuple(max(abs(rows[k][j]-expected[idx][order[k]][j]) for k in range(3) for j in dims) for dims in ((0,1),(2,3)))
        e0,e2=min((error(order) for order in permutations(range(3))),key=lambda x:(max(x),x))
        require(max(e0,e2)<=tolerance,f"native UV corner drift cell {idx}: {e0:.9g}/{e2:.9g}")
        max0=max(max0,e0);max2=max(max2,e2)
    require(len(seen)==len(expected),"native UV2 coverage")
    return {"status":"PASS","triangles":len(seen),"uv0_max_abs_delta":max0,
            "uv2_max_abs_delta":max2,"tolerance":tolerance,"min_cell_margin_px":margin,
            "min_altitude_px":minimum_altitude,"subpixel_altitude_triangles":subpixel,
            "uv2_overlap":"PASS","v_flipped":flip_v}

def verify_import(source,receipt,budget,resolution,flip_v=False):
    p=Path(receipt)
    require(p.is_file() and not p.is_symlink() and p.stat().st_size<=MAX_BYTES,"native UV receipt missing or oversized")
    qa,doc,decoded=inspect(source,budget,allow_uv2=True)
    require(len({n["mesh"] for n in doc["nodes"] if "mesh" in n})==sum("mesh" in n for n in doc["nodes"]),"shared mesh instances unsupported for native global atlas")
    result=compare(source_triangles(doc,decoded),json.loads(p.read_text()),resolution,flip_v)
    require(result["triangles"]==qa["triangles"],"native triangle mismatch")
    return result
