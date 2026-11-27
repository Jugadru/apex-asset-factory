import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

path = Path(__file__).resolve().parents[1] / "apex_foundation.py"
spec = importlib.util.spec_from_file_location("apex_foundation", path)
foundation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(foundation)

class FoundationTest(unittest.TestCase):
    def test_catalog(self):
        result = foundation.validate()
        self.assertGreaterEqual(result["references"], 198)
        self.assertGreaterEqual(result["possibilities"], 120)
    def test_example_blocked(self):
        report = foundation.plan(foundation.DOCS / "asset_jobs.example.json")
        self.assertFalse(report["executed"])
        self.assertEqual(report["jobs"][0]["status"], "BLOCKED")
    def test_original_and_unsafe_paths(self):
        job = {"id":"demo","kind":"car","source":None,"license":"ORIGINAL","approved":True,
               "output":"staging/demo.glb","triangle_budget":1000,"texture_max_px":512}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "jobs.json"
            def run(jobs):
                path.write_text(json.dumps({"schema":1,"jobs":jobs}), encoding="utf-8")
                return foundation.plan(path)
            self.assertEqual(run([job])["jobs"][0]["status"], "PLANNED")
            self.assertEqual(run([dict(job,source="external.obj")])["jobs"][0]["status"], "BLOCKED")
            with self.assertRaises(ValueError):
                run([dict(job,output="staging/../assets/demo.glb")])
            with self.assertRaises(ValueError):
                run([job,dict(job,id="other")])

if __name__ == "__main__":
    unittest.main()
