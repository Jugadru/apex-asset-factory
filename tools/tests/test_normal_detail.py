import math
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from asset_factory.normal_detail import PROFILES,height,normal_pixels
from asset_factory import material_factory as mf
from asset_factory.uv_repair import repair
from test_uv_repair import fixture
from test_material_factory import unpack,pixels


class NormalDetailTest(unittest.TestCase):
    def test_periodic_height_and_normal_encoding(self):
        for name in PROFILES:
            self.assertAlmostEqual(height(name,.137,.281),height(name,1.137,-.719),places=12)
            raw=normal_pixels(name,256)
            self.assertEqual(len(raw),256*256*3)
            self.assertEqual(raw,normal_pixels(name,256))
            for i in range(0,len(raw),3*113):
                n=[2*v/255-1 for v in raw[i:i+3]]
                self.assertGreater(n[2],0)
                self.assertAlmostEqual(math.hypot(*n),1,delta=.007)
        self.assertEqual(set(zip(*[iter(normal_pixels('glass',256))]*3)),{(128,128,255)})
        self.assertNotEqual(normal_pixels('carbon',256),normal_pixels('rubber',256))
        for size in (True,256.0,128,1024):
            with self.assertRaises(ValueError):normal_pixels('carbon',size)

    def test_direction_and_resolution(self):
        size=256;step=1/256;name='carbon';x,y=3,5
        def expected(x,y):
            u,v=x/size,y/size
            # Negative central height differences in the tangent +U,+V directions.
            dx=(height(name,u-step,v)-height(name,u+step,v))/2
            dy=(height(name,u,v+step)-height(name,u,v-step))/2
            length=math.hypot(dx,dy,1)
            return tuple(round(127.5*(a/length+1)) for a in (dx,dy,1))
        raw=normal_pixels(name,size)
        self.assertEqual(tuple(raw[(y*size+x)*3:(y*size+x)*3+3]),expected(x,y))
        hi=normal_pixels(name,512)
        self.assertEqual(tuple(hi[(2*y*512+2*x)*3:(2*y*512+2*x)*3+3]),expected(x,y))

    def test_uv_gate_and_exact_enrichment(self):
        with tempfile.TemporaryDirectory() as tmp:
            w=Path(tmp);a=w/'source.glb';a.write_bytes(fixture())
            with self.assertRaisesRegex(ValueError,'nondegenerate'):mf.enrich(a,100,256,True)
            b=w/'repaired.glb';repair(a,b,mf.sha(a.read_bytes()),100)
            old,old_r=mf.enrich(b,100,256);new,r=mf.enrich(b,100,256,True)
            self.assertEqual(r['normal_maps'],'PASS');self.assertEqual(len(r['maps']),3)
            self.assertEqual(r['maps'][:2],old_r['maps']);self.assertEqual(r['geometry_buffer_sha256'],old_r['geometry_buffer_sha256'])
            od,ob=unpack(old);nd,nb=unpack(new)
            for k in ('accessors','meshes','nodes','scenes','scene'):self.assertEqual(od[k],nd[k])
            self.assertEqual(nd['materials'][0]['normalTexture'],{'index':2,'scale':1})
            v=nd['bufferViews'][nd['images'][2]['bufferView']]
            self.assertEqual(pixels(nb[v['byteOffset']:v['byteOffset']+v['byteLength']],256),normal_pixels('carbon',256))
            target=w/'normal.glb';target.write_bytes(new);self.assertEqual(mf.verify(b,target,100,256,True),r)
            target.write_bytes(new[:-8]+b'12345678')
            with self.assertRaises(ValueError):mf.verify(b,target,100,256,True)

    def test_default_preserves_previous_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=Path(tmp)/'a.glb';a.write_bytes(fixture())
            raw,r=mf.enrich(a,100,256)
            self.assertEqual(r['normal_maps'],'NOT_RUN');self.assertEqual(len(r['maps']),2)
            self.assertNotIn('normalTexture',unpack(raw)[0]['materials'][0])
            with self.assertRaises(ValueError):mf.enrich(a,100,256,1)

if __name__=='__main__':unittest.main()
