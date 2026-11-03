"""离线打包回归：明确选择、灰色混组、缺图拒绝、索引和来源哈希。"""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

import build_mesh_pack as packer


class PackTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.cache = self.root/'cache'
        self.entity = '0400000000000001'
        self.model = '0d00000000000001'
        self.material = '0e00000000000001'
        self.texture = '0c00000000000001'
        self.src = self.cache/self.entity
        self.src.mkdir(parents=True)
        self.mesh = dict(positions=[[0,0,0],[1,0,0],[0,1,0]],normals=[[0,0,1]]*3,
                         uv=[[0,0],[1,0],[0,1]],indices=[0,1,2,2,1,0],
                         triangleTextureIds=[self.texture,None],height=1)
        self.filename = self.model+'.lod0.mesh.json'
        self.chain = dict(build='0.8.0.24919',entity=self.entity,
                          resources={self.entity:dict(refs=[dict(guid=self.model)]),
                                     self.texture:dict(texture=dict(status='decoded'))},
                          meshExports=[dict(model=self.model,material=None,file=self.filename)])
        Image.new('RGB',(4,4),'red').save(self.src/(self.texture+'.png'))
        self.write()
        self.patch = patch.object(packer,'CACHE',self.cache)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def write(self):
        (self.src/'chain.json').write_text(json.dumps(self.chain),encoding='utf-8')
        (self.src/self.filename).write_text(json.dumps(self.mesh),encoding='utf-8')

    def build(self,**kwargs):
        return packer.build('mercy-pistol',self.entity,out_root=self.root/'staged',**kwargs)

    def test_pack_groups_arrays_and_hashes_roundtrip(self):
        result = self.build()
        out = Path(result['output'])
        pack = json.loads((out/'pack.json').read_text())
        self.assertEqual(pack['positions'],[c for row in self.mesh['positions'] for c in row])
        self.assertEqual(result['groups'],{self.texture:1,'grey':1})
        self.assertEqual([g['indices'] for g in pack['groups']],[[0,1,2],[2,1,0]])
        provenance = json.loads((out/'provenance.json').read_text())
        self.assertEqual(provenance['sourceSha256'],packer.sha(self.src/self.filename))
        for filename,digest in provenance['files'].items():
            self.assertEqual(packer.sha(out/filename),digest)

    def test_missing_color_refuses_and_preserves_previous_output(self):
        self.build()
        old = (self.root/'staged/mercy-pistol/pack.json').read_bytes()
        (self.src/(self.texture+'.png')).unlink()
        with self.assertRaisesRegex(ValueError,'PNG is missing'):
            self.build()
        self.assertEqual((self.root/'staged/mercy-pistol/pack.json').read_bytes(),old)

    def test_effect_mask_is_copied_without_becoming_a_diffuse_texture(self):
        self.mesh['triangleTextureIds'] = [None,None]
        self.mesh['materialBindingComplete'] = False
        self.mesh['submeshes'] = [dict(binding=dict(material=self.material,status='unresolved',textureSlots=[
            dict(guid=self.texture,slot='a726d0a7',refType=3),
            dict(guid='0c000000dec3b596',slot='65bcf745',refType=2)]))]
        self.chain['resources'][self.texture]['texture'].update(file=self.texture+'.png',format=80)
        self.write()
        result = self.build()
        out = Path(result['output'])
        pack = json.loads((out/'pack.json').read_text())
        self.assertEqual(result['groups'],{'grey':2})
        self.assertFalse(pack['materialBindingComplete'])
        self.assertEqual(len(pack['materialTextures']),1)
        self.assertEqual(pack['materialTextures'][0]['format'],80)
        self.assertTrue((out/(self.texture+'.png')).exists())

    def test_stale_mesh_file_is_not_an_authoritative_export(self):
        self.chain['meshExports'] = []
        self.write()
        with self.assertRaisesRegex(ValueError,'没有 LOD0'):
            self.build()

    def test_multiple_effect_materials_require_explicit_selection(self):
        self.chain['resources'][self.entity]['refs'] = []
        variant = self.model+'.'+self.material+'.lod0.mesh.json'
        self.chain['meshExports'].append(dict(model=self.model,material=self.material,file=variant))
        self.write()
        (self.src/variant).write_text(json.dumps(self.mesh),encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'不唯一'):
            self.build(model=self.model)
        self.build(model=self.model,material=self.material)

    def test_invalid_indices_count_or_nonfinite_arrays_refuse(self):
        for field,value in [('indices',[0,1,3]),('triangleTextureIds',[]),('positions',[[float('nan'),0,0]]*3)]:
            mesh = copy.deepcopy(self.mesh);mesh[field] = value
            with self.assertRaises(ValueError):
                packer.validate_mesh(mesh)

    def test_source_overlap_and_name_traversal_refuse(self):
        with self.assertRaisesRegex(ValueError,'Invalid pack name'):
            packer.build('../escape',self.entity,out_root=self.root)
        with self.assertRaisesRegex(ValueError,'overlaps source'):
            packer.build(self.entity,self.entity,out_root=self.cache)


if __name__=='__main__':
    unittest.main()
