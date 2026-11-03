"""Small synthetic format fixtures; no game files/processes needed."""
from pathlib import Path
import struct
import tempfile
import unittest

import numpy as np

from ow_model_submeshes import bind_materials,parse_look_materials,parse_model_submeshes


def model_fixture():
    raw=bytearray(932)
    struct.pack_into('<I',raw,72,len(raw))
    struct.pack_into('<2H',raw,324,2,2)
    struct.pack_into('<4B',raw,336,1,1,3,2)
    struct.pack_into('<4Q',raw,352,400,416,560,672)
    struct.pack_into('<2Q',raw,400,88,99)
    for off,base,start,mask in [(416,1,0,1),(488,0,3,2)]:
        struct.pack_into('<I4HH3B',raw,off+52,base,start,3,3,0,46,0,1,mask)
    struct.pack_into('<I',raw,560,6)
    struct.pack_into('<4B',raw,568,20,16,7,6)
    struct.pack_into('<3Q',raw,592,616,704,824)
    expected=[(0,0,2,0,0),(4,0,6,0,0xc0000),(5,0,8,0,0x100000),
              (1,0,9,1,0),(3,0,9,1,0x40000),(9,0,4,1,0x80000),(16,0,12,1,0xc0000)]
    for i,row in enumerate(expected):struct.pack_into('<4BI',raw,616+i*8,*row)
    struct.pack_into('<2I',raw,672,6,0)
    struct.pack_into('<Q',raw,688,920)
    for i in range(6):
        struct.pack_into('<3f',raw,704+20*i,i/10,i%2/10,0)
        raw[704+20*i+16]=255
        raw[824+16*i]=127
        struct.pack_into('<2e',raw,824+16*i+8,i/8,0)
    struct.pack_into('<6H',raw,920,0,2,4,0,1,2)
    return raw


def look_fixture(slot=99,material=0x0e00000000000001):
    raw=bytearray(152)
    raw[:4]=b'DUTS'
    struct.pack_into('<2Q',raw,112,1,128)
    struct.pack_into('<3Q',raw,128,0xffffffffffffffff,material,slot)
    return raw


class SubmeshTests(unittest.TestCase):
    def test_hero_body_colour_skin_and_two_uv_streams(self):
        old=model_fixture();raw=bytearray(1060);raw[:696]=old[:696]
        struct.pack_into('<I',raw,72,len(raw));struct.pack_into('<4B',raw,568,20,24,9,2)
        struct.pack_into('<3Q',raw,592,696,768,888);struct.pack_into('<Q',raw,688,1048)
        expected=[(0,0,2,0,0),(4,0,6,0,0xc0000),(5,0,8,0,0x100000),
                  (1,0,9,1,0),(3,0,9,1,0x40000),(8,0,8,1,0x80000),
                  (9,0,4,1,0xc0000),(9,1,4,1,0x100000),(16,0,12,1,0x140000)]
        for i,row in enumerate(expected):struct.pack_into('<4BI',raw,696+i*8,*row)
        raw[768:888]=old[704:824]
        for i in range(6):
            raw[888+i*24]=127;raw[896+i*24:900+i*24]=bytes([80,90,100,255])
            struct.pack_into('<2e',raw,900+i*24,i/8,0);struct.pack_into('<2e',raw,904+i*24,i/16,0)
        raw[1048:1060]=old[920:932];mesh=parse_model_submeshes(raw)
        np.testing.assert_allclose(mesh['uv'][:,0],[1/8,3/8,5/8]);np.testing.assert_allclose(mesh['uv1'][:,0],[1/16,3/16,5/16])
        np.testing.assert_array_equal(mesh['vertexColorsUnorm8'],[[80,90,100,255]]*3)
        # A contradictory count in an unused LOD never weakens default checks.
        struct.pack_into('<H',raw,488+60,2)
        with self.assertRaisesRegex(ValueError,'vertex range'):parse_model_submeshes(raw)
        self.assertEqual(len(parse_model_submeshes(raw,selected_lods_only=True)['positions']),3)

    def test_lod_mask_and_sparse_relative_indices(self):
        mesh=parse_model_submeshes(model_fixture())
        self.assertEqual(len(mesh['submeshes']),1)
        self.assertEqual(mesh['submeshes'][0]['sourceVertexIndices'],[1,3,5])
        self.assertEqual(mesh['submeshes'][0]['vertexBase'],1)
        self.assertEqual(mesh['indices'].tolist(),[0,1,2])
        self.assertEqual(len(mesh['positions']),3)
        np.testing.assert_allclose(mesh['uv'][:,0],[1/8,3/8,5/8])
        self.assertEqual(mesh['sourceSubmeshes'][1]['lods'],[1])

    def test_invalid_descriptor_refuses_instead_of_guessing(self):
        raw=model_fixture()
        struct.pack_into('<I',raw,416+52,4)
        with self.assertRaisesRegex(ValueError,'vertex range'):parse_model_submeshes(raw)
        raw=model_fixture()
        struct.pack_into('<H',raw,416+58,4)
        with self.assertRaisesRegex(ValueError,'descriptor'):parse_model_submeshes(raw)

    def test_shared_all_lods_mask(self):
        raw=model_fixture()
        raw[416+68]=255
        mesh=parse_model_submeshes(raw)
        self.assertEqual(mesh['submeshes'][0]['lods'],list(range(8)))

    def test_blended_skin_exports_stored_bind_pose_without_changing_rigid(self):
        raw=model_fixture()
        rigid=parse_model_submeshes(raw)
        raw[560+11]=2
        for i in range(6):
            raw[704+20*i+12:704+20*i+16]=bytes([1,2,0,0])
            raw[704+20*i+16:704+20*i+20]=bytes([128,127,0,0])
        skin=parse_model_submeshes(raw)
        for key in ('positions','normals','uv','indices'):
            np.testing.assert_array_equal(skin[key],rigid[key])
        self.assertEqual(skin['skin']['boneIndices'],[[1,2,0,0]]*3)
        self.assertEqual(skin['skin']['weightsUnorm8'],[[128,127,0,0]]*3)
        self.assertFalse(skin['skin']['animationEvaluated'])
        raw[704+20+16]=127
        with self.assertRaisesRegex(ValueError,'sum to 255'):
            parse_model_submeshes(raw)

    def test_twenty_byte_secondary_stream_keeps_uv0_and_uv1_separate(self):
        old=model_fixture()
        reference=parse_model_submeshes(old)
        raw=bytearray(1020)
        raw[:696]=old[:696]
        struct.pack_into('<I',raw,72,len(raw))
        struct.pack_into('<4B',raw,568,20,20,8,2)
        struct.pack_into('<3Q',raw,592,696,768,888)
        struct.pack_into('<Q',raw,688,1008)
        expected=[(0,0,2,0,0),(4,0,6,0,0xc0000),(5,0,8,0,0x100000),
                  (1,0,9,1,0),(3,0,9,1,0x40000),(9,0,4,1,0x80000),
                  (9,1,4,1,0xc0000),(16,0,12,1,0x100000)]
        for i,row in enumerate(expected):struct.pack_into('<4BI',raw,696+i*8,*row)
        raw[768:888]=old[704:824]
        for i in range(6):
            raw[888+i*20:900+i*20]=old[824+i*16:836+i*16]
            struct.pack_into('<2e',raw,900+i*20,i/16,0)
            raw[904+i*20:908+i*20]=old[836+i*16:840+i*16]
        raw[1008:1020]=old[920:932]
        mesh=parse_model_submeshes(raw)
        for key in ('positions','normals','uv','indices'):
            np.testing.assert_array_equal(mesh[key],reference[key])
        np.testing.assert_allclose(mesh['uv1'][:,0],[1/16,3/16,5/16])
        struct.pack_into('<4BI',raw,696+5*8,8,0,8,1,0x80000)
        struct.pack_into('<4BI',raw,696+6*8,9,0,4,1,0xc0000)
        for i in range(6):raw[896+i*20:900+i*20]=bytes([80,90,100,255])
        mesh=parse_model_submeshes(raw)
        np.testing.assert_allclose(mesh['uv'][:,0],[1/16,3/16,5/16])
        self.assertNotIn('uv1',mesh)
        np.testing.assert_array_equal(mesh['vertexColorsUnorm8'],[[80,90,100,255]]*3)

    def test_unskinned_twelve_byte_position_stream(self):
        old=model_fixture();raw=old.copy();reference=parse_model_submeshes(old)
        struct.pack_into('<4B',raw,568,12,16,5,0)
        expected=[(0,0,2,0,0),(1,0,9,1,0),(3,0,9,1,0x40000),
                  (9,0,4,1,0x80000),(16,0,12,1,0xc0000)]
        for i,row in enumerate(expected):struct.pack_into('<4BI',raw,616+i*8,*row)
        for i in range(6):raw[704+12*i:716+12*i]=old[704+20*i:716+20*i]
        mesh=parse_model_submeshes(raw)
        for key in ('positions','normals','uv','indices'):
            np.testing.assert_array_equal(mesh[key],reference[key])
        self.assertNotIn('skin',mesh)

    def test_static_color_and_two_uv_channels_validate_semantics(self):
        old=model_fixture();raw=bytearray(980);raw[:932]=old
        struct.pack_into('<I',raw,72,len(raw))
        struct.pack_into('<4B',raw,568,12,24,7,0)
        struct.pack_into('<Q',raw,688,968)
        expected=[(0,0,2,0,0),(1,0,9,1,0),(3,0,9,1,0x40000),
                  (8,0,8,1,0x80000),(9,0,4,1,0xc0000),
                  (9,1,4,1,0x100000),(16,0,12,1,0x140000)]
        for i,row in enumerate(expected):struct.pack_into('<4BI',raw,616+i*8,*row)
        for i in range(6):
            raw[704+12*i:716+12*i]=old[704+20*i:716+20*i]
            raw[824+24*i:832+24*i]=old[824+16*i:832+16*i]
            raw[832+24*i:836+24*i]=bytes([40,50,60,255])
            struct.pack_into('<4e',raw,836+24*i,i/8,0,i/16,0)
        raw[968:980]=old[920:932]
        mesh=parse_model_submeshes(raw)
        np.testing.assert_allclose(mesh['uv'][:,0],[1/8,3/8,5/8])
        np.testing.assert_allclose(mesh['uv1'][:,0],[1/16,3/16,5/16])
        np.testing.assert_array_equal(mesh['vertexColorsUnorm8'],[[40,50,60,255]]*3)
        raw[616+3*8+2]=9
        with self.assertRaisesRegex(ValueError,'semantics'):
            parse_model_submeshes(raw)

    def test_independent_vertex_and_index_buffer_selectors(self):
        old=model_fixture();raw=bytearray(1288);raw[:560]=old[:560]
        struct.pack_into('<I',raw,72,len(raw))
        struct.pack_into('<4B',raw,336,2,2,1,2)
        struct.pack_into('<2Q',raw,368,560,784)
        raw[488+65]=1;raw[488+66]=1;raw[488+68]=1
        for i,(desc,s1,s2) in enumerate(((672,832,1072),(728,952,1168))):
            raw[560+56*i:616+56*i]=old[560:616]
            struct.pack_into('<3Q',raw,592+56*i,desc,s1,s2)
            raw[desc:desc+56]=old[616:672]
            raw[s1:s1+120]=old[704:824]
            raw[s2:s2+96]=old[824:920]
            for v in range(6):
                struct.pack_into('<f',raw,s1+20*v,v/10+2*i)
                struct.pack_into('<2e',raw,s2+16*v+8,v/(8+8*i),0)
            struct.pack_into('<2I',raw,784+24*i,6,0)
            struct.pack_into('<Q',raw,800+24*i,1264+12*i)
        raw[1264:1276]=old[920:932]
        struct.pack_into('<6H',raw,1276,0,1,2,1,3,5)
        mesh=parse_model_submeshes(raw)
        self.assertEqual(mesh['sourceBufferCounts'],[2,2])
        self.assertEqual(mesh['indices'].tolist(),[0,1,2,3,4,5])
        self.assertEqual([(s['vertexBuffer'],s['indexBuffer']) for s in mesh['submeshes']],[(0,0),(1,1)])
        np.testing.assert_allclose(mesh['uv'][:,0],[1/8,3/8,5/8,1/16,3/16,5/16])

    def test_zero_vertex_count_low_lod_placeholder_does_not_block_lod0(self):
        raw=model_fixture()
        struct.pack_into('<H',raw,488+60,0)
        mesh=parse_model_submeshes(raw)
        self.assertEqual(len(mesh['positions']),3)

    def test_look_slot_binding_and_no_global_texture_fallback(self):
        entity,model,look,material='0400000000000001','0d00000000000001','0980000000000001','0e00000000000001'
        color,unrelated='0c00000000000001','0c00000000000002'
        chain={'resources':{entity:{'refs':[{'guid':model},{'guid':look}]},look:{'status':'read'},
                            material:{'refs':[{'guid':color}]},
                            color:{'texture':{'status':'decoded','file':color+'.png','format':78}},
                            unrelated:{'texture':{'status':'decoded','file':unrelated+'.png','format':72}}}}
        with tempfile.TemporaryDirectory() as directory:
            cache=Path(directory)
            (cache/(look+'.raw')).write_bytes(look_fixture())
            header=bytearray(32);header[3]=78
            (cache/(color+'.raw')).write_bytes(header)
            mesh=bind_materials(parse_model_submeshes(model_fixture()),model,chain,cache)
            self.assertTrue(mesh['materialBindingComplete'])
            self.assertEqual(mesh['triangleTextureIds'],[color])
            header[3]=71
            (cache/(color+'.raw')).write_bytes(header)
            mesh=bind_materials(parse_model_submeshes(model_fixture()),model,chain,cache)
            self.assertFalse(mesh['materialBindingComplete'])
            self.assertEqual(mesh['triangleTextureIds'],[None])
            self.assertIn(color,mesh['submeshes'][0]['binding']['rejectedNonSrgb'])
            (cache/(color+'.raw')).unlink()
            chain['resources'][color]={'status':'unresolved'}
            mesh=bind_materials(parse_model_submeshes(model_fixture()),model,chain,cache)
            self.assertIn(color,mesh['submeshes'][0]['binding']['missingTextureResources'])
            self.assertIn('absent from searched package index',mesh['submeshes'][0]['binding']['reason'])

    def test_look_bounds_and_material_type_guard(self):
        self.assertEqual(parse_look_materials(look_fixture())['0000000000000063']['material'],'0e00000000000001')
        with self.assertRaisesRegex(ValueError,'bounds'):parse_look_materials(look_fixture()[:-1])
        with self.assertRaisesRegex(ValueError,'row'):parse_look_materials(look_fixture(material=0x0400000000000001))


if __name__=='__main__':unittest.main()
