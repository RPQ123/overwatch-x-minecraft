"""Offline regression for flat tables, HDR offsets and ONE/ONE coverage."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import struct
import unittest
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

import numpy as np
from PIL import Image

from ow_material_params import parse, rgb_at, bake_additive
import build_mesh_pack as packer


class ColorChecks(unittest.TestCase):
    def material(self):
        raw=bytearray(208)
        struct.pack_into('<Q',raw,0,0x0e10000000000028)
        struct.pack_into('<4Q',raw,32,112,128,136,152)
        raw[96]=1;raw[97]=1;raw[100]=1
        struct.pack_into('<H',raw,94,1)
        struct.pack_into('<QII',raw,112,0x0c00000000000001,0x12345678,3)
        struct.pack_into('<2I',raw,128,0x22944c2a,0x12345678)
        struct.pack_into('<IIQ',raw,136,0x01234567,0,0x0e10000000000002)
        struct.pack_into('<QBBHI',raw,152,24,2,5,32,0x01020304)
        struct.pack_into('<8f',raw,176,1,2,3,4,5,6,7,8)
        return raw

    def test_register_five_is_not_float_width(self):
        d=parse(self.material());self.assertEqual(d['constantBuffers'][0]['register'],5)
        self.assertEqual(rgb_at(d,2,4),[2,3,4])
        self.assertEqual(d['blendHash'],'12345678')

    def test_truncated_overlapping_and_nonfinite_blocks_refuse(self):
        for change in ('truncate','overlap','nonfinite'):
            raw=self.material()
            if change=='truncate':raw=raw[:-1]
            elif change=='overlap':struct.pack_into('<Q',raw,152,0)
            else:struct.pack_into('<f',raw,176,float('nan'))
            with self.assertRaises(ValueError):parse(raw)

    def test_color_never_comes_from_header_or_other_stage(self):
        d=parse(self.material())
        for stage,offset in [(1,4),(2,-4),(2,24),(2,1)]:
            with self.assertRaises(ValueError):rgb_at(d,stage,offset)

    def test_alpha_and_black_edges_emit_zero_under_one_one(self):
        source=Image.fromarray(np.array([[[255,255,255,0],[0,0,0,255],[255,255,255,128]]],dtype='uint8'))
        a=np.asarray(bake_additive(source))
        self.assertEqual(a[0,0].tolist(),[0,0,0,0]);self.assertEqual(a[0,1].tolist(),[0,0,0,255])
        self.assertEqual(a[0,2].tolist(),[128,128,128,128])

    def test_intensity_ramp_uses_mask_coordinate_and_preserves_hue(self):
        source=Image.fromarray(np.array([[[0,0,0,255],[255,255,255,255]]],dtype='uint8'))
        ramp=Image.fromarray(np.array([[[255,0,0],[0,0,255]]],dtype='uint8'))
        a=np.asarray(bake_additive(source,(2,2,2),intensity=True,ramp=ramp))
        self.assertEqual(a[0,0].tolist(),[0,0,0,0]);self.assertEqual(a[0,1].tolist(),[0,0,255,255])

    def test_materials_sharing_one_texture_do_not_merge(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);entity='0400000000000001';model='0d00000000000001';tex='0c00000000000001'
            cache=root/'cache';src=cache/entity;src.mkdir(parents=True)
            materials=['0e00000000000001','0e00000000000002']
            mesh=dict(positions=[[0,0,0],[1,0,0],[0,1,0]],normals=[[0,0,1]]*3,uv=[[0,0],[1,0],[0,1]],
                      indices=[0,1,2,2,1,0],triangleTextureIds=[tex,tex],
                      submeshes=[dict(triangleStart=i,triangleCount=1,binding=dict(material=m)) for i,m in enumerate(materials)])
            file=model+'.lod0.mesh.json';(src/file).write_text(json.dumps(mesh))
            (src/'chain.json').write_text(json.dumps(dict(entity=entity,build='0.8.0.24919',
                resources={tex:dict(texture=dict(status='decoded'))},meshExports=[dict(model=model,material=None,file=file)])))
            Image.new('RGB',(2,2),'blue').save(src/(tex+'.png'))
            with patch.object(packer,'CACHE',cache):result=packer.build('check',entity,out_root=root/'packs')
            data=json.loads((Path(result['output'])/'pack.json').read_text())
            self.assertEqual([g['material'] for g in data['groups']],materials)
            self.assertEqual([g['indices'] for g in data['groups']],[[0,1,2],[2,1,0]])


if __name__=='__main__':unittest.main()
