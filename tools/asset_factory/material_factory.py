"""Original deterministic embedded PBR maps for validated staged vehicles."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import zlib
from asset_factory.validate_glb import inspect, read_document, require, MAX_BYTES

NAMES={"paint","carbon","rubber","metal","accent","alloy","rotor","caliper","glass","light","tail"}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def chunk(tag,data):
    return struct.pack(">I",len(data))+tag+data+struct.pack(">I",zlib.crc32(tag+data)&0xffffffff)


def png(size,rgb):
    require(type(size) is int and size in (256,512),"texture resolution")
    require(len(rgb)==size*size*3,"RGB payload")
    rows=b"".join(b"\0"+rgb[y*size*3:(y+1)*size*3] for y in range(size))
    return b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">IIBBBBB",size,size,8,2,0,0,0))+chunk(b"IDAT",zlib.compress(rows,9))+chunk(b"IEND",b"")


def maps(name,pbr,size):
    require(name in NAMES and type(size) is int and size in (256,512),"unsupported material or texture resolution")
    salt=int.from_bytes(hashlib.sha256(name.encode()).digest()[:4],"little")
    metal=round(255*pbr.get("metallicFactor",1));rough=round(255*pbr.get("roughnessFactor",1))
    color=bytearray();mr=bytearray()
    def clamp(v):return max(0,min(255,v))
    for y in range(size):
        for x in range(size):
            u=x*256//size;v=y*256//size
            n=((u*73856093)^(v*19349663)^salt)&0xffffffff
            n=((n^(n>>13))*1274126177)&0xffffffff
            grain=(n>>24)%17-8
            if name=="carbon":
                warp=((u//8+v//8)%4)<2;fiber=(u if warp else v)%8
                value=178+35*warp+min(fiber,7-fiber)*10+grain;delta=12 if warp else -12
            elif name=="rubber":
                value=225+grain*2;delta=grain*2
            elif name in ("metal","alloy","rotor"):
                value=238+((v*19)%13)-6+grain;delta=((v*19)%13)-6+grain
            elif name in ("paint","caliper","accent"):
                value=253+grain//4;delta=grain//4
            else:
                value=250+grain//2;delta=grain//2
            color.extend((clamp(value),)*3)
            # glTF roughness G, metallic B; R unused, not ambient occlusion.
            mr.extend((255,clamp(rough+delta),metal))
    return png(size,bytes(color)),png(size,bytes(mr))


def glb(doc,data):
    raw=json.dumps(doc,sort_keys=True,separators=(",",":"),allow_nan=False).encode();raw+=b" "*((-len(raw))%4)
    data=bytes(data)+b"\0"*((-len(data))%4)
    return struct.pack("<4sII",b"glTF",2,28+len(raw)+len(data))+struct.pack("<I4s",len(raw),b"JSON")+raw+struct.pack("<I4s",len(data),b"BIN\0")+data


def enrich(source,budget,size):
    qa,_,decoded=inspect(source,budget)
    doc,data,source_hash,_=read_document(source)
    require(qa["sha256"]==source_hash,"source changed during validation")
    original=bytes(data);payload=bytearray(original)
    names=[m.get("name") for m in doc["materials"]]
    require(len(set(names))==len(names) and set(names)<=NAMES,"material names")
    doc.update(images=[],textures=[],samplers=[{"magFilter":9729,"minFilter":9987,"wrapS":10497,"wrapT":10497}])
    records=[];uv_total=uv_zero=0
    for mesh in doc["meshes"]:
        for p in mesh["primitives"]:
            uv=decoded[p["attributes"]["TEXCOORD_0"]];ids=[r[0] for r in decoded[p["indices"]]]
            for i in range(0,len(ids),3):
                a,b,c=(uv[j] for j in ids[i:i+3]);uv_total+=1
                uv_zero+=abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))<=1e-12
    for material in doc["materials"]:
        name=material["name"];pbr=material.setdefault("pbrMetallicRoughness",{})
        for role,raw in zip(("baseColor","metallicRoughness"),maps(name,pbr,size)):
            payload.extend(b"\0"*((-len(payload))%4));offset=len(payload);payload.extend(raw)
            view=len(doc["bufferViews"]);doc["bufferViews"].append({"buffer":0,"byteOffset":offset,"byteLength":len(raw)})
            idx=len(doc["images"]);label=name+"_"+role
            doc["images"].append({"name":label,"bufferView":view,"mimeType":"image/png"})
            doc["textures"].append({"name":label,"source":idx,"sampler":0})
            pbr[role+"Texture"]={"index":idx}
            records.append({"material":name,"role":role,"name":label,"sha256":sha(raw),"bytes":len(raw),"size":size})
        pbr.update(metallicFactor=1,roughnessFactor=1)
    doc["buffers"][0]["byteLength"]=len(payload)
    output=glb(doc,payload);require(len(output)<=MAX_BYTES,"textured GLB budget")
    return output,{"source_sha256":source_hash,"sha256":sha(output),"bytes":len(output),"geometry_buffer_sha256":sha(original),"triangles":qa["triangles"],"materials":len(names),"maps":records,"uv_triangles":uv_total,"uv_degenerate_triangles":uv_zero,"uv_overlap":"NOT_RUN","normal_maps":"NOT_RUN","promotion":"BLOCKED"}


def verify(source,output,budget,size):
    expected,receipt=enrich(source,budget,size);p=Path(output)
    require(not p.is_symlink() and p.is_file() and p.stat().st_size==len(expected),"invalid textured output")
    require(p.read_bytes()==expected,"textured GLB differs from canonical enrichment")
    return receipt


def generate(source,source_sha,output,budget=20000,size=256):
    source=Path(source);p=Path(output).absolute()
    require(not p.exists() and not p.is_symlink() and p.suffix==".glb" and p.parent.resolve()==p.parent,"new GLB in regular directory required")
    raw,receipt=enrich(source,budget,size)
    require(receipt["source_sha256"]==source_sha,"source hash mismatch")
    with p.open("xb") as f:f.write(raw)
    return verify(source,p,budget,size)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("source");p.add_argument("output");p.add_argument("--source-sha256",required=True);p.add_argument("--budget",type=int,default=20000);p.add_argument("--size",type=int,choices=(256,512),default=256)
    a=p.parse_args()
    try:r=generate(a.source,a.source_sha256,a.output,a.budget,a.size);r["status"]="PASS"
    except (ValueError,OSError,KeyError,TypeError,OverflowError) as exc:r={"status":"FAIL","error":str(exc),"promotion":"BLOCKED"}
    print(json.dumps(r,indent=2));return 0 if r["status"]=="PASS" else 1

if __name__=="__main__":sys.exit(main())
