"""Strict GLB 2.0 subset for original static untextured indexed vehicles.

Reject unsupported features instead of treating them as validated. No external IO.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

MAX_BYTES = 32 * 1024 * 1024
MAX_JSON = 4 * 1024 * 1024
MAX_ROWS = 300000
MAX_RECORDS = 10000
FORMATS = {5121: "B", 5123: "H", 5125: "I", 5126: "f"}
WIDTHS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3}
WHEELS = {"Wheel_" + s + "_" + a for s in ("L", "R") for a in ("F", "R")}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def integer(value, low, high, name):
    require(type(value) is int and low <= value <= high, name)
    return value


def record(value, name):
    require(type(value) is dict, name)
    return value


def array(value, name, limit=MAX_RECORDS):
    require(type(value) is list and len(value) <= limit, name)
    return value


def finite(value):
    return type(value) in (float, int) and abs(value) <= 1e12 and math.isfinite(value)


def vector(value, n, name):
    require(type(value) is list and len(value) == n and all(finite(x) for x in value), name)
    return value


def unique(pairs):
    out = {}
    for k, v in pairs:
        require(k not in out, "duplicate JSON key: " + k)
        out[k] = v
    return out


def reject_constant(value):
    raise ValueError("non-finite JSON constant: " + value)


def index(items, i, name):
    return items[integer(i, 0, len(items) - 1, name)]


def allowed(obj, fields, name):
    record(obj, name)
    require(set(obj) <= set(fields.split()), "unsupported " + name + " fields")


def read_document(path):
    p = Path(path)
    require(not p.is_symlink() and p.is_file() and 28 <= p.stat().st_size <= MAX_BYTES, "invalid GLB file")
    with p.open("rb") as f:
        raw = f.read(MAX_BYTES + 1)
    require(28 <= len(raw) <= MAX_BYTES, "GLB size")
    magic, version, total = struct.unpack_from("<4sII", raw)
    require(magic == b"glTF" and version == 2 and total == len(raw), "invalid GLB header")
    n, kind = struct.unpack_from("<I4s", raw, 12)
    require(kind == b"JSON" and 0 < n <= MAX_JSON and n % 4 == 0 and 28 + n <= len(raw), "invalid JSON chunk")
    try:
        doc = json.loads(raw[20:20+n].decode("utf-8"), object_pairs_hook=unique, parse_constant=reject_constant)
    except (UnicodeError, RecursionError, OverflowError) as exc:
        raise ValueError("invalid GLB JSON") from exc
    size, kind = struct.unpack_from("<I4s", raw, 20+n)
    require(kind == b"BIN\0" and size % 4 == 0 and 28+n+size == len(raw), "invalid BIN chunk or trailing data")
    allowed(doc, "asset scene scenes nodes meshes materials buffers bufferViews accessors", "document")
    asset = record(doc.get("asset"), "asset")
    require(asset.get("version") == "2.0", "glTF version")
    buffers = array(doc.get("buffers"), "buffers")
    require(len(buffers) == 1, "one embedded buffer required")
    allowed(buffers[0], "byteLength name", "buffer")
    length = integer(buffers[0].get("byteLength"), 1, size, "buffer byteLength")
    require(size-length <= 3 and not any(raw[28+n+length:]), "BIN padding")
    return doc, memoryview(raw)[28+n:28+n+length], hashlib.sha256(raw).hexdigest(), len(raw)


def inspect(path, budget=100000, *, allow_uv2=False):
    require(type(allow_uv2) is bool, "invalid UV2 option")
    integer(budget, 1, 10000000, "triangle budget")
    doc, data, digest, size = read_document(path)
    views = array(doc.get("bufferViews"), "bufferViews")
    accessors = array(doc.get("accessors"), "accessors")
    meshes = array(doc.get("meshes"), "meshes")
    nodes = array(doc.get("nodes"), "nodes")
    scenes = array(doc.get("scenes"), "scenes")
    materials = array(doc.get("materials"), "materials")
    require(all((views, accessors, meshes, nodes, scenes, materials)), "empty required collection")
    for v in views:
        allowed(v, "buffer byteOffset byteLength byteStride target name", "bufferView")
        integer(v.get("buffer"), 0, 0, "buffer index")
        off = integer(v.get("byteOffset", 0), 0, len(data), "view offset")
        length = integer(v.get("byteLength"), 1, len(data), "view length")
        require(off + length <= len(data), "view outside buffer")
        if "byteStride" in v:
            stride = integer(v["byteStride"], 4, 252, "stride")
            require(stride % 4 == 0, "stride alignment")
        if "target" in v:
            require(type(v["target"]) is int and v["target"] in (34962, 34963), "view target")

    decoded = []
    total_rows = 0
    for a in accessors:
        allowed(a, "bufferView byteOffset componentType count type min max normalized name", "accessor")
        v = index(views, a.get("bufferView"), "accessor view")
        c = a.get("componentType")
        typ = a.get("type")
        require(type(c) is int and c in FORMATS and type(typ) is str and typ in WIDTHS, "unsupported accessor format")
        require(a.get("normalized", False) is False, "normalized accessor unsupported")
        fmt = struct.Struct("<" + FORMATS[c] * WIDTHS[typ])
        unit = struct.calcsize("<" + FORMATS[c])
        count = integer(a.get("count"), 1, MAX_ROWS, "accessor count")
        total_rows += count
        require(total_rows <= MAX_ROWS, "decoded row limit")
        off = integer(a.get("byteOffset", 0), 0, v["byteLength"], "accessor offset")
        start = v.get("byteOffset", 0) + off
        stride = v.get("byteStride", fmt.size)
        require(off % unit == 0 and start % unit == 0 and stride >= fmt.size and stride % unit == 0, "accessor alignment")
        require(off + (count-1)*stride + fmt.size <= v["byteLength"], "accessor outside view")
        rows = [fmt.unpack_from(data, start+i*stride) for i in range(count)]
        require(all(finite(x) for row in rows for x in row), "nonfinite or excessive accessor value")
        for key, fn in (("min", min), ("max", max)):
            if key in a:
                declared = vector(a[key], WIDTHS[typ], "accessor " + key)
                actual = [fn(row[k] for row in rows) for k in range(WIDTHS[typ])]
                require(all(abs(x-y) <= 1e-6 for x,y in zip(declared,actual)), "incorrect accessor " + key)
        decoded.append(rows)

    for m in materials:
        allowed(m, "name pbrMetallicRoughness doubleSided alphaMode alphaCutoff emissiveFactor", "material")
        pbr = m.get("pbrMetallicRoughness", {})
        allowed(pbr, "baseColorFactor metallicFactor roughnessFactor", "PBR")
        for key in ("metallicFactor", "roughnessFactor"):
            if key in pbr:
                require(finite(pbr[key]) and 0 <= pbr[key] <= 1, "PBR range")
        if "baseColorFactor" in pbr:
            require(all(0 <= x <= 1 for x in vector(pbr["baseColorFactor"],4,"base color")), "color range")
        if "emissiveFactor" in m:
            require(all(0 <= x <= 1 for x in vector(m["emissiveFactor"],3,"emissive")), "emissive range")
        require(type(m.get("doubleSided",False)) is bool, "doubleSided")
        require(m.get("alphaMode","OPAQUE") in ("OPAQUE","MASK","BLEND"), "alpha mode")
        if "alphaCutoff" in m:
            require(finite(m["alphaCutoff"]) and m["alphaCutoff"] >= 0, "alpha cutoff")

    triangles = 0
    used = set()
    for mesh in meshes:
        allowed(mesh, "name primitives", "mesh")
        primitives = array(mesh.get("primitives"), "primitives")
        require(primitives, "empty mesh")
        for p in primitives:
            allowed(p, "attributes indices material mode", "primitive")
            require(type(p.get("mode",4)) is int and p.get("mode",4) == 4, "triangles only")
            index(materials, p.get("material"), "material index")
            attrs = record(p.get("attributes"), "attributes")
            require(set(attrs) == {"POSITION","NORMAL","TEXCOORD_0"} | ({"TEXCOORD_1"} if allow_uv2 else set()), "required attributes")
            pos, normal, uv = [index(accessors, attrs[k], k) for k in ("POSITION","NORMAL","TEXCOORD_0")]
            require([(a["componentType"], a["type"]) for a in (pos,normal,uv)] == [(5126,"VEC3"),(5126,"VEC3"),(5126,"VEC2")], "attribute formats")
            require(pos["count"] == normal["count"] == uv["count"] and "min" in pos and "max" in pos, "attribute count or position bounds")
            extra = []
            if allow_uv2:
                uv2 = index(accessors, attrs["TEXCOORD_1"], "TEXCOORD_1")
                require((uv2["componentType"],uv2["type"],uv2["count"]) == (5126,"VEC2",pos["count"]), "UV2 format/count")
                require(all(0 <= x <= 1 for row in decoded[attrs["TEXCOORD_1"]] for x in row), "UV2 range")
                extra.append(uv2)
            for a in (pos,normal,uv,*extra):
                v = views[a["bufferView"]]
                require(v.get("target",34962) == 34962 and (v.get("byteOffset",0)+a.get("byteOffset",0)) % 4 == 0, "vertex view")
            ia = index(accessors,p.get("indices"),"indices")
            iv = views[ia["bufferView"]]
            require(ia["type"] == "SCALAR" and ia["componentType"] in (5121,5123,5125) and ia["count"] % 3 == 0 and "byteStride" not in iv and iv.get("target",34963) == 34963, "index format")
            used.update([*attrs.values(),p["indices"]])
            positions = decoded[attrs["POSITION"]]
            normals = decoded[attrs["NORMAL"]]
            require(all(abs(sum(x*x for x in row)-1) <= 0.002 for row in normals), "invalid unit normal")
            ids = [r[0] for r in decoded[p["indices"]]]
            require(all(i < len(positions) for i in ids), "index outside positions")
            triangles += len(ids)//3
            require(triangles <= budget, "triangle budget")
            for j in range(0,len(ids),3):
                a,b,c = (positions[i] for i in ids[j:j+3])
                u = [b[k]-a[k] for k in range(3)]
                v = [c[k]-a[k] for k in range(3)]
                cross = (u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
                require(any(x != 0 for x in cross), "degenerate triangle")
    require(triangles > 0 and used == set(range(len(accessors))), "empty or unused accessor")

    parents = {}
    names = set()
    wheel_meshes = set()
    used_meshes = set()
    for i,n in enumerate(nodes):
        allowed(n, "name mesh children translation rotation scale matrix", "node")
        name = n.get("name")
        require(name is None or type(name) is str, "node name")
        if name in WHEELS:
            require(name not in names and "mesh" in n, "duplicate or meshless wheel")
            wheel_meshes.add(name)
        names.add(name)
        if "mesh" in n:
            index(meshes,n["mesh"],"node mesh")
            used_meshes.add(n["mesh"])
        require("matrix" not in n, "matrix nodes unsupported")
        for k,dim in (("translation",3),("rotation",4),("scale",3)):
            if k in n:
                vector(n[k],dim,k)
        if "rotation" in n:
            require(abs(sum(x*x for x in n["rotation"])-1) <= 0.002, "rotation quaternion")
        if "scale" in n:
            require(all(x > 0 for x in n["scale"]), "nonpositive scale")
        for child in array(n.get("children",[]),"children"):
            index(nodes,child,"child index")
            require(child not in parents and child != i, "multiple parents or self cycle")
            parents[child] = i
    require(wheel_meshes == WHEELS and used_meshes == set(range(len(meshes))), "wheel or mesh coverage")
    require(len(scenes) == 1, "one scene required")
    scene = index(scenes,doc.get("scene"),"default scene")
    allowed(scene,"name nodes","scene")
    roots = array(scene.get("nodes"),"scene roots")
    seen = set()
    stack = list(roots)
    for root in roots:
        index(nodes,root,"scene root")
        require(root not in parents, "scene root has parent")
    while stack:
        i = stack.pop()
        require(i not in seen, "cycle or duplicate scene node")
        seen.add(i)
        stack.extend(nodes[i].get("children",[]))
    require(len(seen) == len(nodes), "unreachable or cyclic nodes")
    return {"status":"PASS","scope":"static untextured indexed vehicle subset",
            "sha256":digest,"bytes":size,"triangles":triangles,"accessors":len(accessors),
            "decoded_rows":total_rows,"nodes":len(nodes),"wheel_nodes":sorted(wheel_meshes),
            "uv_overlap":"NOT_RUN","pivot_quality":"NOT_RUN","visual_review":"NOT_RUN",
            "promotion":"BLOCKED"}, doc, decoded


def compare(first, second, budget=100000, tolerance=1e-6):
    require(finite(tolerance) and 0 <= tolerance <= 1e-4, "tolerance range")
    a, da, xa = inspect(first,budget)
    b, db, xb = inspect(second,budget)
    # Strict document topology, metadata and integer/index equality; floats may differ.
    def same(x,y):
        if type(x) is not type(y):
            return False
        if type(x) is dict:
            return x.keys() == y.keys() and all(same(x[k],y[k]) for k in x)
        if type(x) is list:
            return len(x) == len(y) and all(same(i,j) for i,j in zip(x,y))
        return abs(x-y) <= tolerance if type(x) is float else x == y
    topology = same(da,db)
    max_diff = 0.0
    equivalent = topology
    if topology:
        for aa, bb in zip(xa,xb):
            for row1,row2 in zip(aa,bb):
                for x,y in zip(row1,row2):
                    if type(x) is int:
                        equivalent &= x == y
                    else:
                        diff = abs(x-y)
                        max_diff = max(max_diff,diff)
                        equivalent &= diff <= tolerance
    return {"status":"PASS" if equivalent else "FAIL", "binary_equal":a["sha256"]==b["sha256"],
            "numeric_equivalent":bool(equivalent),"document_equivalent":topology,
            "max_accessor_delta":max_diff if topology else None,"tolerance":tolerance,
            "sha256":[a["sha256"],b["sha256"]],"scope":"same layout/order and finite numeric tolerance; not arbitrary mesh equivalence",
            "promotion":"BLOCKED"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("asset")
    p.add_argument("--compare")
    p.add_argument("--budget",type=int,default=100000)
    p.add_argument("--tolerance",type=float,default=1e-6)
    a=p.parse_args()
    try:
        result=compare(a.asset,a.compare,a.budget,a.tolerance) if a.compare else inspect(a.asset,a.budget)[0]
    except (ValueError,OSError,TypeError,KeyError,OverflowError,RecursionError) as exc:
        result={"status":"FAIL","error":str(exc),"promotion":"BLOCKED"}
    print(json.dumps(result,indent=2,allow_nan=False))
    return 0 if result["status"]=="PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
