import json
import math
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from asset_factory.validate_glb import inspect, compare, main
from asset_factory.build import inspect_attributes, read_request


def fixture():
    raw = struct.pack("<9f9f6f3H",0,0,0,1,0,0,0,1,0,
                      0,0,1,0,0,1,0,0,1,0,0,1,0,0,1,0,1,2)
    doc = {"asset":{"version":"2.0"},"scene":0,"scenes":[{"nodes":[0,1,2,3]}],
           "nodes":[{"name":f"Wheel_{s}_{a}","mesh":0} for s in "LR" for a in "FR"],
           "meshes":[{"primitives":[{"attributes":{"POSITION":0,"NORMAL":1,"TEXCOORD_0":2},"indices":3,"material":0}]}],
           "materials":[{"pbrMetallicRoughness":{"roughnessFactor":0.5}}],
           "buffers":[{"byteLength":len(raw)}],
           "bufferViews":[{"buffer":0,"byteOffset":o,"byteLength":n,"target":t}
                          for o,n,t in [(0,36,34962),(36,36,34962),(72,24,34962),(96,6,34963)]],
           "accessors":[{"bufferView":i,"componentType":c,"count":3,"type":k}
                        for i,c,k in [(0,5126,"VEC3"),(1,5126,"VEC3"),(2,5126,"VEC2"),(3,5123,"SCALAR")]]}
    doc["accessors"][0].update(min=[0,0,0],max=[1,1,0])
    return doc, bytearray(raw)


def encode(doc, data):
    j = json.dumps(doc,separators=(",",":")).encode()
    j += b" " * (-len(j)%4)
    b = bytes(data) + b"\0" * (-len(data)%4)
    return struct.pack("<4sII",b"glTF",2,28+len(j)+len(b))+struct.pack("<I4s",len(j),b"JSON")+j+struct.pack("<I4s",len(b),b"BIN\0")+b


class AdvancedValidatorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.a = Path(self.tmp.name)/"a.glb"
        self.b = Path(self.tmp.name)/"b.glb"
        self.doc,self.raw = fixture()

    def write(self,path=None):
        (path or self.a).write_bytes(encode(self.doc,self.raw))

    def reject(self,edit):
        self.doc,self.raw = fixture()
        edit(self.doc,self.raw)
        self.write()
        with self.assertRaises(ValueError):
            inspect(self.a,100)

    def test_valid_and_budget(self):
        self.write()
        report,_,_=inspect(self.a,1)
        self.assertEqual(report["triangles"],1)
        self.assertEqual(report["promotion"],"BLOCKED")
        self.assertEqual(report["pivot_quality"],"NOT_RUN")
        with self.assertRaises(ValueError):
            inspect(self.a,0)

    def test_pipeline_integration(self):
        self.write()
        self.assertEqual(inspect_attributes(self.a,100)["advanced_validation"]["status"],"PASS")
        struct.pack_into("<H",self.raw,100,3)
        self.write()
        with self.assertRaisesRegex(ValueError,"index outside positions"):
            inspect_attributes(self.a,100)
        request=Path(self.tmp.name)/"request.json"
        request.write_text('{"seed":NaN}')
        with self.assertRaisesRegex(ValueError,"nonfinite JSON constant"):
            read_request(request)

    def test_chunks_and_duplicate_json(self):
        self.write()
        raw=self.a.read_bytes()
        for data in (raw[:-1],raw+b"\0",raw[:8]+b"\0\0\0\0"+raw[12:],
                     raw[:16]+b"JUNK"+raw[20:]):
            self.a.write_bytes(data)
            with self.assertRaises(ValueError):
                inspect(self.a)
        j=b'{"asset":{},"asset":{}}'
        j+=b" "*(-len(j)%4)
        self.a.write_bytes(struct.pack("<4sII",b"glTF",2,28+len(j))+struct.pack("<I4s",len(j),b"JSON")+j+struct.pack("<I4s",0,b"BIN\0"))
        with self.assertRaisesRegex(ValueError,"duplicate"):
            inspect(self.a)

    def test_buffer_and_accessor_bounds(self):
        for edit in (
            lambda d,b:d["buffers"][0].update(uri="external.bin"),
            lambda d,b:d["buffers"][0].update(byteLength=99999),
            lambda d,b:d["bufferViews"][0].update(byteOffset=99999),
            lambda d,b:d["accessors"][0].update(count=True),
            lambda d,b:d["accessors"][0].update(count=4),
            lambda d,b:d["accessors"][0].update(byteOffset=1),
            lambda d,b:d["accessors"][0].update(bufferView=-1),
            lambda d,b:d["accessors"][0].update(componentType=5125),
            lambda d,b:d["accessors"][0].update(sparse={}),
            lambda d,b:d["accessors"][0].update(max=[2,1,0]),
            lambda d,b:d["bufferViews"][0].update(byteStride=8),
        ):
            with self.subTest(edit=edit):
                self.reject(edit)

    def test_geometry_and_nonfinite(self):
        for edit in (
            lambda d,b:struct.pack_into("<f",b,0,math.nan),
            lambda d,b:struct.pack_into("<f",b,72,math.inf),
            lambda d,b:struct.pack_into("<f",b,44,0),
            lambda d,b:struct.pack_into("<H",b,100,3),
            lambda d,b:struct.pack_into("<H",b,100,0),
            lambda d,b:d["meshes"][0]["primitives"][0]["attributes"].pop("NORMAL"),
            lambda d,b:d["meshes"][0]["primitives"][0].update(material=True),
            lambda d,b:d["materials"][0]["pbrMetallicRoughness"].update(roughnessFactor=-1),
            lambda d,b:d.update(extensionsRequired=["UNKNOWN"]),
            lambda d,b:d["nodes"][0].update(translation=[0,0,math.nan]),
        ):
            with self.subTest(edit=edit):
                self.reject(edit)

    def test_scene_constraints(self):
        for edit in (
            lambda d,b:d["nodes"][0].update(name="wrong"),
            lambda d,b:d["nodes"][1].update(name=d["nodes"][0]["name"]),
            lambda d,b:d["nodes"][0].update(mesh=999),
            lambda d,b:d["nodes"][0].update(children=[0]),
            lambda d,b:d["nodes"][0].update(children=[1]),
            lambda d,b:d["nodes"][0].update(scale=[1,0,1]),
            lambda d,b:d["nodes"][0].update(rotation=[0,0,0,0]),
            lambda d,b:d["scenes"][0].update(nodes=[0,1,2]),
            lambda d,b:d["scenes"][0].update(nodes=[0,1,2,3,3]),
        ):
            with self.subTest(edit=edit):
                self.reject(edit)

    def test_comparison(self):
        self.write()
        self.write(self.b)
        self.assertTrue(compare(self.a,self.b)["binary_equal"])
        struct.pack_into("<f",self.raw,72,5e-8)
        self.write(self.b)
        report=compare(self.a,self.b)
        self.assertTrue(report["numeric_equivalent"])
        self.assertFalse(report["binary_equal"])
        struct.pack_into("<f",self.raw,72,0.001)
        self.write(self.b)
        self.assertEqual(compare(self.a,self.b)["status"],"FAIL")
        self.doc,self.raw=fixture()
        self.doc["nodes"][0]["translation"]=[1,0,0]
        self.write(self.b)
        self.assertEqual(compare(self.a,self.b)["status"],"FAIL")
        with self.assertRaises(ValueError):
            compare(self.a,self.b,tolerance=1)

    def test_cli_failure(self):
        self.a.write_bytes(b"broken")
        with patch("sys.argv",["validator",str(self.a)]):
            self.assertEqual(main(),1)


if __name__=="__main__":
    unittest.main()
