import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]/"asset_factory"
spec = importlib.util.spec_from_file_location("asset_factory_build", HERE/"build.py")
factory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(factory)

class FactoryTest(unittest.TestCase):
    def setUp(self):
        self.request = json.loads((HERE/"demo.json").read_text())
        self.schema = json.loads((HERE/"request.schema.json").read_text())

    def test_demo(self):
        self.assertEqual(factory.read_request(HERE/"demo.json"),self.request)

    def test_invalid(self):
        for changes in ({"id":"../escape"},{"license":"CC0-1.0"},{"approved":False},
                        {"references":["external"]},{"seed":True},{"triangle_budget":0},
                        {"dimensions_m":{"width":1.8,"length":float("nan"),"height":1.1}},
                        {"extra":"x"},{"destination":"assets"},{"kind":"track"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                factory.validate(dict(self.request,**changes),self.schema)

    def test_duplicate_keys(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"request.json"
            p.write_text('{"schema":1,"schema":1}')
            with self.assertRaises(ValueError):
                factory.read_request(p)

    def test_existing_workspace(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            with self.assertRaises(ValueError):
                factory.build(HERE/"demo.json","missing","missing",p)
            self.assertEqual(list(p.iterdir()),[])

    def test_failure_report(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"fresh"
            result=factory.build(HERE/"demo.json","/missing/blender","/missing/godot",p)
            self.assertEqual(result["status"],"FAIL")
            self.assertEqual(result["promotion"],"BLOCKED")
            self.assertEqual(json.loads((p/"registry.json").read_text())["approval"],"PENDING")

    def test_corrupt_glb(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"asset.glb"
            p.write_bytes(b"invalid")
            with self.assertRaises(ValueError):
                factory.inspect_attributes(p,100)

if __name__=="__main__":
    unittest.main()
