import copy
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from asset_factory.build import HERE,read_request,build
from asset_factory.lod_policy import apply_policy,bevel_segments,level_for_distance
from asset_factory.lod import compare_levels,build_set,DISTANCES,compare_documents,verify_level_receipt
from asset_factory import modular_layout,era_layout,detail_layout,closed_wheel_layout

class LODTest(unittest.TestCase):
    def test_all_modular_schemas_preserve_geometry_contract(self):
        for module,name in ((modular_layout,"demo_modular.json"),(era_layout,"demo_era.json"),
                            (detail_layout,"demo_detail.json"),(closed_wheel_layout,"demo_gt.json"),
                            (closed_wheel_layout,"demo_endurance.json")):
            parts=module.design(read_request(HERE/name))
            before=copy.deepcopy(parts)
            for level in (0,1,2):
                derived=apply_policy(parts,level)
                self.assertEqual([p["name"] for p in parts],[p["name"] for p in derived])
                for old,new in zip(parts,derived):
                    expected=copy.deepcopy(old)
                    if level and old["kind"]=="cylinder":
                        expected["sides"]=min(old["sides"],24 if level==1 else 12)
                    if level==2 and old["kind"]=="box":expected["bevel"]=0
                    self.assertEqual(new,expected)
                self.assertEqual(module.validate_layout(derived,read_request(HERE/name))["status"],"PASS")
            self.assertEqual(parts,before)
        self.assertEqual([bevel_segments(i) for i in (0,1,2)],[2,1,1])

    def test_switch_hysteresis_and_teleport(self):
        current=0;levels=[]
        for distance in DISTANCES:
            current=level_for_distance(distance,current)
            levels.append(current)
        self.assertEqual(levels,[0,0,1,1,2,2,1,1,0,2,0])
        self.assertEqual(level_for_distance(28,0),1)
        self.assertEqual(level_for_distance(22,1),0)
        self.assertEqual(level_for_distance(73,1),2)
        self.assertEqual(level_for_distance(67,2),1)
        for d in (24,25,26):
            self.assertEqual(level_for_distance(d,0),0)
            self.assertEqual(level_for_distance(d,1),1)

    def test_reject_invalid_inputs(self):
        for invalid in (-1,3,True,"1"):
            with self.assertRaises(ValueError):apply_policy([],invalid)
            with self.assertRaises(ValueError):bevel_segments(invalid)
            with self.assertRaises(ValueError):level_for_distance(10,invalid)
        for invalid in (-1,float("nan"),float("inf")):
            with self.assertRaises(ValueError):level_for_distance(invalid,0)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"new"
            with self.assertRaises(ValueError):build_set(HERE/"demo.json","/missing","/missing",path)
            with self.assertRaises(ValueError):build(HERE/"demo.json","/missing","/missing",path,derived_lod=1)
            self.assertFalse(path.exists())

    def test_budget_and_envelope_gates(self):
        reports=[{"status":"BUILT","derived_lod":i,"promotion":"BLOCKED",
                  "stages":dict.fromkeys(("plan","export","structural_validation","godot_import"),"PASS"),"asset":{"mesh_triangles":n,"materials":7},
                  "godot_fixture":{"meshes":26,"size":[2,1.2,5]}} for i,n in enumerate((4000,2500,1700))]
        self.assertEqual(compare_levels(reports),[4000,2500,1700])
        for field,value in (("mesh_triangles",3900),("materials",6)):
            changed=copy.deepcopy(reports);changed[1]["asset"][field]=value
            with self.assertRaises(ValueError):compare_levels(changed)
        for field,value in (("meshes",25),("size",[2,1.1,5])):
            changed=copy.deepcopy(reports);changed[2]["godot_fixture"][field]=value
            with self.assertRaises(ValueError):compare_levels(changed)
        with self.assertRaises(ValueError):compare_levels(reports[:2])
        changed=copy.deepcopy(reports);changed[1]["derived_lod"]=0
        with self.assertRaises(ValueError):compare_levels(changed)

    def test_malformed_receipts_rejected(self):
        reports=[{"status":"BUILT","derived_lod":i,"promotion":"BLOCKED",
                  "stages":dict.fromkeys(("plan","export","structural_validation","godot_import"),"PASS"),
                  "asset":{"mesh_triangles":n,"materials":7},
                  "godot_fixture":{"meshes":26,"size":[2,1.2,5]}} for i,n in enumerate((4000,2500,1700))]
        for value in ([],[2],[2,1.2,float("nan")],[2,1.2,float("inf")],[2,True,5],[2,0,5]):
            bad=copy.deepcopy(reports);bad[2]["godot_fixture"]["size"]=value
            with self.subTest(value=value),self.assertRaises(ValueError):compare_levels(bad)
        bad=copy.deepcopy(reports);bad[1]["derived_lod"]=True
        with self.assertRaises(ValueError):compare_levels(bad)
        bad=copy.deepcopy(reports);bad[1]["stages"]["godot_import"]="FAIL"
        with self.assertRaises(ValueError):compare_levels(bad)
        bad=copy.deepcopy(reports);bad[1]["asset"]["mesh_triangles"]=2500.0
        with self.assertRaises(ValueError):compare_levels(bad)

    def test_document_identity_rejects_drift(self):
        doc={"nodes":[{"name":"Wheel","mesh":0,"translation":[1,2,3]},
                      {"name":"Body","mesh":1}],
             "materials":[{"name":"Rubber","pbrMetallicRoughness":{"roughnessFactor":.8}},
                          {"name":"Paint","pbrMetallicRoughness":{"roughnessFactor":.2}}],
             "meshes":[{"primitives":[{"material":0}]},{"primitives":[{"material":1}]}],
             "scenes":[{"nodes":[0,1]}],"scene":0}
        docs=[copy.deepcopy(doc) for _ in range(3)]
        compare_documents(docs)
        # Reordered material table with corrected references is semantically identical.
        docs[2]["materials"].reverse()
        for m in docs[2]["meshes"]:m["primitives"][0]["material"]=1-m["primitives"][0]["material"]
        compare_documents(docs)
        for mutation in ("pivot","material","properties","duplicate","hierarchy"):
            bad=copy.deepcopy(doc)
            if mutation=="pivot":bad["nodes"][0]["translation"][0]+=.01
            elif mutation=="material":bad["meshes"][0]["primitives"][0]["material"]=1
            elif mutation=="properties":bad["materials"][0]["pbrMetallicRoughness"]["roughnessFactor"]=.3
            elif mutation=="duplicate":bad["nodes"][1]["name"]="Wheel"
            elif mutation=="hierarchy":bad["scenes"][0]["nodes"]=[0]
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):compare_documents([doc,doc,bad])

    def test_receipt_hash_and_count_integrity(self):
        result={"sha256":"a"*64,"triangles":123}
        report={"asset":{"sha256":"a"*64,"mesh_triangles":123}}
        verify_level_receipt(result,report,"b"*64,"b"*64)
        with self.assertRaises(ValueError):verify_level_receipt(result,report,"b"*64,"c"*64)
        with self.assertRaises(ValueError):verify_level_receipt(dict(result,triangles=124),report,"b"*64,"b"*64)
        with self.assertRaises(ValueError):verify_level_receipt(dict(result,sha256="c"*64),report,"b"*64,"b"*64)

    def test_failed_build_writes_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"new"
            result=build_set(HERE/"demo_gt.json","/missing","/missing",path)
            self.assertEqual(result["status"],"FAIL")
            self.assertTrue((path/"lod-manifest.json").is_file())
            self.assertEqual(result["promotion"],"BLOCKED")
            with self.assertRaises(ValueError):build_set(HERE/"demo_gt.json","/missing","/missing",path)

if __name__=="__main__":unittest.main()
