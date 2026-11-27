import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from asset_factory import material_factory as mf
from asset_factory.build import HERE,digest
from asset_factory.stage_pbr import source_contract,stage
from asset_factory.validate_glb import inspect


def fixture():
    data=struct.pack("<9f9f6f3H",0,0,0,1,0,0,0,1,0,0,0,1,0,0,1,0,0,1,0,0,1,0,0,1,0,1,2)
    doc={"asset":{"version":"2.0"},"scene":0,"scenes":[{"nodes":[0,1,2,3]}],"nodes":[{"name":f"Wheel_{s}_{a}","mesh":0} for s in "LR" for a in "FR"],"meshes":[{"primitives":[{"attributes":{"POSITION":0,"NORMAL":1,"TEXCOORD_0":2},"indices":3,"material":0}]}],"materials":[{"name":"carbon","pbrMetallicRoughness":{"metallicFactor":.2,"roughnessFactor":.4}}],"buffers":[{"byteLength":len(data)}],"bufferViews":[{"buffer":0,"byteOffset":o,"byteLength":n,"target":t} for o,n,t in [(0,36,34962),(36,36,34962),(72,24,34962),(96,6,34963)]],"accessors":[{"bufferView":i,"componentType":c,"count":3,"type":k} for i,c,k in [(0,5126,"VEC3"),(1,5126,"VEC3"),(2,5126,"VEC2"),(3,5123,"SCALAR")]]}
    doc["accessors"][0].update(min=[0,0,0],max=[1,1,0])
    return doc,data


def unpack(raw):
    n=struct.unpack_from("<I",raw,12)[0]
    return json.loads(raw[20:20+n]),raw[28+n:]


def pixels(raw,size):
    assert raw[:8]==b"\x89PNG\r\n\x1a\n"
    p=8;data=b""
    while p<len(raw):
        n=struct.unpack_from(">I",raw,p)[0];tag=raw[p+4:p+8];body=raw[p+8:p+8+n]
        assert zlib.crc32(tag+body)&0xffffffff==struct.unpack_from(">I",raw,p+8+n)[0]
        if tag==b"IHDR":assert struct.unpack(">IIBBBBB",body)==(size,size,8,2,0,0,0)
        if tag==b"IDAT":data+=body
        p+=12+n
    rows=zlib.decompress(data);assert len(rows)==size*(size*3+1)
    return b"".join(rows[i+1:i+1+size*3] for i in range(0,len(rows),size*3+1))


class MaterialFactoryTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.w=Path(self.tmp.name);self.a=self.w/"source.glb"
        self.doc,self.raw=fixture();self.a.write_bytes(mf.glb(self.doc,self.raw))

    def test_maps_channel_and_determinism(self):
        p={"metallicFactor":.2,"roughnessFactor":.4}
        c,m=mf.maps("carbon",p,256);self.assertEqual((c,m),mf.maps("carbon",p,256))
        self.assertNotEqual(c,mf.maps("rubber",p,256)[0]);rgb=pixels(m,256)
        self.assertEqual(set(rgb[0::3]),{255});self.assertEqual(set(rgb[2::3]),{51});self.assertGreater(len(set(rgb[1::3])),1)
        self.assertEqual(len(pixels(mf.maps("paint",p,512)[0],512)),512*512*3)
        for size in (True,128,1024):
            with self.assertRaises(ValueError):mf.maps("carbon",p,size)

    def test_embedding_preserves_geometry(self):
        before=self.a.read_bytes();out,r=mf.enrich(self.a,100,256);doc,data=unpack(out)
        self.assertEqual(data[:len(self.raw)],self.raw);self.assertEqual(r["geometry_buffer_sha256"],mf.sha(self.raw));self.assertEqual(before,self.a.read_bytes())
        for k in ("accessors","meshes","nodes","scenes","scene"):self.assertEqual(doc[k],self.doc[k])
        self.assertEqual(doc["bufferViews"][:4],self.doc["bufferViews"]);self.assertEqual(len(doc["images"]),2);self.assertEqual(r["uv_degenerate_triangles"],0)
        for im,row in zip(doc["images"],r["maps"]):
            v=doc["bufferViews"][im["bufferView"]];raw=data[v["byteOffset"]:v["byteOffset"]+v["byteLength"]];self.assertEqual(mf.sha(raw),row["sha256"]);pixels(raw,256)
        self.assertEqual(out,mf.enrich(self.a,100,256)[0]);p=self.w/"pbr.glb";p.write_bytes(out)
        with self.assertRaises(ValueError):inspect(p,100) # legacy validator stays strict
        self.assertEqual(mf.verify(self.a,p,100,256),r)
        p.write_bytes(out[:-20]+bytes([out[-20]^1])+out[-19:])
        with self.assertRaises(ValueError):mf.verify(self.a,p,100,256)

    def test_reject_source_or_output_mutations(self):
        p=self.w/"pbr.glb"
        with self.assertRaises(ValueError):mf.generate(self.a,"0"*64,p,100,256)
        self.assertFalse(p.exists());mf.generate(self.a,digest(self.a),p,100,256)
        with self.assertRaises(ValueError):mf.generate(self.a,digest(self.a),p,100,256)
        self.doc["materials"][0]["name"]="unknown";self.a.write_bytes(mf.glb(self.doc,self.raw))
        with self.assertRaises(ValueError):mf.enrich(self.a,100,256)

    def test_source_receipt_and_failure_report(self):
        s=self.w/"source";s.mkdir();(s/"staging").mkdir();asset=s/"staging/asset.glb";asset.write_bytes(self.a.read_bytes())
        req=json.loads((HERE/"demo_wheel_2012.json").read_text());(s/"request.json").write_text(json.dumps(req))
        base={"status":"BUILT","promotion":"BLOCKED","derived_lod":0,"asset":{"sha256":digest(asset)},"stages":dict.fromkeys(("plan","export","structural_validation","godot_import"),"PASS")}
        reg=dict(base,id=req["id"],version=req["version"],license="ORIGINAL",request_sha256=digest(s/"request.json"))
        for name,content in (("report.json",base),("registry.json",reg)):(s/name).write_text(json.dumps(content))
        self.assertEqual(source_contract(s,digest(asset),256)[0],req)
        base["stages"]["godot_import"]="FAIL";(s/"report.json").write_text(json.dumps(base))
        with self.assertRaises(ValueError):source_contract(s,digest(asset),256)
        report=stage(s,digest(asset),"/missing","/missing",self.w/"failed",256)
        self.assertEqual(report["status"],"FAIL");self.assertEqual(report["stages"]["source"],"FAIL");self.assertTrue((self.w/"failed/pbr-report.json").is_file())

if __name__=="__main__":unittest.main()
