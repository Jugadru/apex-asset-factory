import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from asset_factory.native_uv_audit import compare

def fixture():
    pad=2/2048
    return [[(0.,0.,x+pad,pad),(1.,0.,x+.5-pad,pad),(0.,1.,x+pad,.5-pad)] for x in (0.,.5)]

class NativeUVAuditTest(unittest.TestCase):
    def test_flip_reorder_and_precision(self):
        e=fixture()
        a=[[(u,1-v,x,1-y) for u,v,x,y in reversed(t)] for t in reversed(e)]
        r=compare(e,a,2048,True)
        self.assertEqual(r["uv2_overlap"],"PASS")
        self.assertEqual(r["triangles"],2)
        self.assertAlmostEqual(r["uv0_max_abs_delta"],0)
    def test_reject_duplicate_missing_and_uv0_drift(self):
        e=fixture()
        with self.assertRaises(ValueError):compare(e,[e[0],e[0]],2048)
        with self.assertRaises(ValueError):compare(e,e[:1],2048)
        a=[list(t) for t in e]
        u,v,x,y=a[0][0];a[0][0]=(u+.01,v,x,y)
        with self.assertRaisesRegex(ValueError,"corner drift"):compare(e,a,2048)
    def test_reject_uv2_cell_escape(self):
        e=fixture();a=[list(t) for t in e]
        u,v,x,y=a[0][0];a[0][0]=(u,v,0.,y)
        with self.assertRaisesRegex(ValueError,"padding"):compare(e,a,2048)

if __name__=="__main__":unittest.main()
