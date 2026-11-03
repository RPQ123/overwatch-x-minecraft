"""Offline regressions for GUID discovery, package fallback and BC5 deplaning."""
import struct
import hashlib
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np

from ow_asset_chain import (Archive, collect, guid_arg, package_candidates, scan_refs,
                            manifest_packages, parse_effect, parse_material_slots, color_binding,
                            parse_asset_model, decode_asset_texture)
from ow_beta_texture import decode


class ChainTests(unittest.TestCase):
    def test_effect_three_uv_channels_preserve_their_independent_values(self):
        raw = bytearray(722)
        struct.pack_into('<I',raw,72,len(raw))
        struct.pack_into('<2H',raw,324,1,1)
        struct.pack_into('<4B',raw,336,1,1,1,1)
        struct.pack_into('<4Q',raw,352,392,400,472,528)
        struct.pack_into('<Q',raw,392,123)
        struct.pack_into('<I4HH3B',raw,452,0,0,3,3,0,46,0,0,1)
        struct.pack_into('<I',raw,472,3)
        struct.pack_into('<4B',raw,480,12,24,7,0)
        struct.pack_into('<3Q',raw,504,552,608,644)
        struct.pack_into('<2I',raw,528,3,0)
        struct.pack_into('<Q',raw,544,716)
        descriptors = [(0,0,2,0,0),(1,0,9,1,0),(3,0,9,1,0x40000),
                       (9,0,4,1,0x80000),(9,1,4,1,0xc0000),
                       (9,2,4,1,0x100000),(16,0,12,1,0x140000)]
        for i,row in enumerate(descriptors):
            struct.pack_into('<4BI',raw,552+i*8,*row)
        for i in range(3):
            struct.pack_into('<3f',raw,608+i*12,i/4,0,0)
            raw[644+i*24]=127
            struct.pack_into('<6e',raw,652+i*24,.25,.75,.125,.375,.5,.875)
        struct.pack_into('<3H',raw,716,0,1,2)
        original = bytes(raw)
        mesh = parse_asset_model(raw)
        self.assertEqual(bytes(raw),original)
        np.testing.assert_array_equal(mesh['uv'],[[.25,.75]]*3)
        np.testing.assert_array_equal(mesh['uv1'],[[.125,.375]]*3)
        np.testing.assert_array_equal(mesh['uv2'],[[.5,.875]]*3)
        self.assertNotIn('vertexColorsUnorm8',mesh)

    def test_single_payload_ramp_uses_zero_suffix_and_zero_lower_mips(self):
        header = bytearray(32)
        header[3],header[6] = 72,1
        struct.pack_into('<2H',header,8,4,4)
        # Solid red BC1 block: endpoints f800 and 0000, index bits all zero.
        payload = struct.pack('<4I',0,1,8,16)+struct.pack('<HHI',0xf800,0,0)
        refs = scan_refs(header,'0c0000000000241c',{})
        self.assertEqual(refs[-1]['guid'],'032000000000241c')
        image = decode_asset_texture(header,payload)
        self.assertEqual(image.getpixel((0,0)),(255,0,0,255))
        with self.assertRaises(ValueError):
            decode_asset_texture(header,payload[:-1])

    def test_empty_visual_tables_are_explicit_and_unaligned_entity_effect_aliases_are_ignored(self):
        self.assertEqual(parse_effect(bytes(432))['renderers'],[])
        raw = b'x'+struct.pack('<Q',0x0300000000000001)
        self.assertEqual(scan_refs(raw,'0400000000000001',{}),[])

    def test_main_manifest_preserves_duplicate_primary_versions(self):
        raw = bytearray(24+2*72)
        struct.pack_into('<2I',raw,12,2,0)
        for i in range(2):
            off = 24+i*72
            struct.pack_into('<2Q',raw,off+8,0x040000000000001c,0x0a50000000000001+i)
            struct.pack_into('<I',raw,off+44,80)
            raw[off+56:off+72] = bytes([i+1])*16
        rows = manifest_packages(raw)
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[0]['guid'],rows[1]['guid'])
        self.assertNotEqual(rows[0]['ckey'],rows[1]['ckey'])
        self.assertEqual([r['bytes'] for r in rows],[80,80])

    def test_package_loader_reads_every_content_version(self):
        archive = Archive.__new__(Archive)
        archive.attempted = set()
        archive.manifest_rows = {'040000000000001c':[{'ckey':'first'},{'ckey':'second'}]}
        calls = []
        archive.load_package_version = lambda row:calls.append(row['ckey'])
        archive.load_package('040000000000001c')
        archive.load_package('040000000000001c')
        self.assertEqual(calls,['first','second'])

    def test_versioned_package_rejects_wrong_manifest_content_key(self):
        archive = Archive.__new__(Archive)
        archive.packages = {}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'fixture.apm'
            path.write_bytes(bytes(80))
            archive.cached_packages = {'a'*32:path}
            with self.assertRaisesRegex(ValueError,'content-key/size mismatch'):
                archive.load_package_version(dict(guid='040000000000001c',ckey='a'*32,bytes=80))

    def test_flat_effect_binds_each_renderer_material_and_ignores_float_aliases(self):
        raw = bytearray(432+240+336+192+320)
        struct.pack_into('<Q',raw,24,432)
        struct.pack_into('<Q',raw,32,672)
        struct.pack_into('<Q',raw,48,1008)
        struct.pack_into('<Q',raw,80,1200)
        struct.pack_into('<Q',raw,672+184,0x0d00000000000801)
        struct.pack_into('<Q',raw,672+248,0x0e00000011111111)
        struct.pack_into('<Q',raw,1200+184,0x0d000000000007f5)
        struct.pack_into('<Q',raw,1200+216,0x0e00000022222222)
        alias = '0400000000000032'
        struct.pack_into('<Q',raw,337,int(alias,16))
        effect = parse_effect(raw)
        self.assertEqual(effect['emitterCount'],1)
        self.assertEqual([r['kind'] for r in effect['renderers']],['particle-renderer','trail-renderer'])
        refs = scan_refs(raw,'0300000000000001',{alias:{}})
        self.assertNotIn(alias,[r['guid'] for r in refs])
        self.assertEqual(len(refs),4)
        struct.pack_into('<Q',raw,48,1009)
        with self.assertRaisesRegex(ValueError,'table bounds'):
            parse_effect(raw)

    def test_emitter_only_effect_keeps_trail_bindings(self):
        raw = bytearray(500+5*240+192+320)
        struct.pack_into('<Q',raw,24,500)
        struct.pack_into('<Q',raw,48,1700)
        struct.pack_into('<Q',raw,80,1892)
        struct.pack_into('<Q',raw,1892+184,0x0d0000000000075d)
        struct.pack_into('<Q',raw,1892+216,0x0e0000008e2eb8c3)
        effect = parse_effect(raw)
        self.assertEqual(effect['emitterCount'],5)
        self.assertEqual(len(effect['renderers']),1)
        self.assertEqual(effect['renderers'][0]['kind'],'trail-renderer')
        self.assertEqual(len(scan_refs(raw,'0300000000000497',{})),2)
        struct.pack_into('<Q',raw,48,1701)
        with self.assertRaisesRegex(ValueError,'bounds'):
            parse_effect(raw)

    def test_terminal_mips_and_flat_model_never_scan_as_guids(self):
        guid = '0400000000000001'
        raw = int(guid,16).to_bytes(8,'little')
        self.assertEqual(scan_refs(raw,'0320000100000001',{guid:{}}),[])
        self.assertEqual(scan_refs(raw,'0d00000000000001',{guid:{}}),[])

    def test_material_variable_is_not_a_texture(self):
        raw = bytearray(144)
        struct.pack_into('<Q',raw,0,0x0e10000000000030)
        struct.pack_into('<2Q',raw,32,112,144)
        raw[96] = 2
        struct.pack_into('<QII',raw,112,0x0c000000000011c4,0xd74c2428,3)
        struct.pack_into('<QII',raw,128,0x0c0000007cb030ef,0x12bbc7d3,2)
        self.assertEqual([r['refType'] for r in parse_material_slots(raw)],[3,2])
        refs = scan_refs(raw,'0e00000011111111',{},material_textures=True)
        self.assertEqual([r['guid'] for r in refs],['0c000000000011c4'])

    def test_diffuse_slot_outranks_another_srgb_and_rejects_bc5(self):
        material = '0e00000000000001'
        textures = ['0c00000000000001','0c00000000000002','0c00000000000003']
        raw = bytearray(160)
        struct.pack_into('<Q',raw,0,0x0e10000000000021)
        struct.pack_into('<2Q',raw,32,112,160)
        raw[96] = 3
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            resources = {material:dict(status='read',file=material+'.raw')}
            for i,(guid,fmt) in enumerate(zip(textures,[78,72,83])):
                struct.pack_into('<QII',raw,112+i*16,int(guid,16),0xad10f602 if i==0 else i,3)
                header = bytearray(32);header[3] = fmt
                (out/(guid+'.raw')).write_bytes(header)
                resources[guid] = dict(status='read',file=guid+'.raw',texture=dict(status='decoded',file=guid+'.png',format=fmt))
            (out/(material+'.raw')).write_bytes(raw)
            result = color_binding(material,resources,out)
            self.assertEqual(result['colorTexture'],textures[0])
            self.assertEqual(result['rejectedNonSrgb'],[textures[2]])
            # A declared diffuse BC5 is explicitly rejected, not replaced by
            # a visually plausible but unrelated sRGB texture from another slot.
            raw[112:120] = int(textures[2],16).to_bytes(8,'little')
            (out/(material+'.raw')).write_bytes(raw)
            self.assertEqual(color_binding(material,resources,out)['status'],'unresolved')

    def test_unregistered_unaligned_entity_model_and_look(self):
        guids = ['0d000000000006f2', '0980000000000605', '0900000000000606']
        raw = b'x' + b''.join(int(g, 16).to_bytes(8, 'little') for g in guids)
        refs = scan_refs(raw, '04000000000000af', {})
        self.assertEqual([(r['offset'], r['guid']) for r in refs], list(zip((1, 9, 17), guids)))
        self.assertTrue(all(r['via'] == 'entity-offset-scan' for r in refs))

    def test_variable_guid_is_not_a_model(self):
        raw = int('0d8000000000094b', 16).to_bytes(8, 'little')
        self.assertEqual(scan_refs(raw, '04000000000000af', {}), [])

    def test_registered_cycle_and_texture_payload(self):
        guid = '0c00000000001427'
        raw = bytes(32)
        self.assertEqual(scan_refs(raw, guid, {})[0]['guid'], '0320000100001427')
        self.assertEqual(scan_refs(int(guid, 16).to_bytes(8, 'little'), guid, {guid: {}}), [])

    def test_main_manifest_candidates_and_sequential_fallback(self):
        # A GUID at a byte offset is only a candidate; resolve still checks APMs.
        raw = b'x' + int('040000000000001c', 16).to_bytes(8, 'little')
        self.assertEqual(package_candidates(raw), ['040000000000001c'])
        archive = Archive.__new__(Archive)
        archive.records = {}
        archive.candidates = ['0400000000000001', '040000000000001c']
        calls = []

        def load(guid):
            calls.append(guid)
            if guid.endswith('001c'):
                archive.records['04000000000000af'] = {'bytes': 656}

        archive.load_package = load
        self.assertEqual(archive.resolve('04000000000000af'), {'bytes': 656})
        self.assertEqual(calls, ['04000000000000af', *archive.candidates])

    def test_main_manifest_includes_non_hero_package_types(self):
        raw=bytearray(24+12+72)
        struct.pack_into('<2I',raw,12,1,1)
        struct.pack_into('<Q',raw,24+12+8,int('0350000000000001',16))
        self.assertIn('0350000000000001',package_candidates(raw))

    def test_package_flags_can_differ_but_content_cannot(self):
        archive = Archive.__new__(Archive)
        archive.records, archive.owners, archive.packages, archive.attempted = {}, {}, {}, set()
        archive.fetch = lambda *args, **kwargs: b'fixture'
        guid = '04000000000000af'
        row = {'bytes': 656, 'ckey': 'a' * 32, 'flags': 1, 'unknown': 0}
        with patch('ow_asset_chain.package_records', side_effect=[{guid: row}, {guid: {**row, 'flags': 2}}]):
            archive.load_package('0400000000000001')
            archive.load_package('040000000000001c')
        self.assertEqual(len(archive.owners[guid]), 2)
        with patch('ow_asset_chain.package_records', return_value={guid: {**row, 'ckey': 'b' * 32}}):
            with self.assertRaisesRegex(ValueError, 'Conflicting package'):
                archive.load_package('02e000000000000a')

    def test_zero_record_apm_is_explicitly_empty(self):
        archive=Archive.__new__(Archive)
        archive.records,archive.owners,archive.packages,archive.attempted={},{},{},set()
        raw=bytearray(80)
        struct.pack_into('<Q',raw,0,80)
        archive.fetch=lambda *args,**kwargs:bytes(raw)
        archive.load_package('0350000000000001')
        self.assertEqual(archive.packages['0350000000000001']['status'],'empty')
        self.assertEqual(archive.records,{})

    def test_later_package_reveals_earlier_entity_reference(self):
        root, child, model = '04000000000000af', '0400000000000161', '0d000000000006f2'
        blobs = {root: struct.pack('<QQ', int(child, 16), int(model, 16)), child: bytes(8), model: bytes(80)}
        rows = {g: {'bytes': len(b), 'ckey': hashlib.md5(b).hexdigest()} for g, b in blobs.items()}
        with tempfile.TemporaryDirectory() as directory:
            class FakeArchive:
                out = Path(directory)
                records = {root: rows[root]}
                owners, packages = {}, {}
                from ow_asset_chain import GAME
                build = (GAME / '.build.info').read_bytes()

                def resolve(self, guid):
                    if guid == model:
                        self.records.update(rows)
                    return rows.get(guid)

                def fetch(self, key, name):
                    raw = blobs[Path(name).stem]
                    (self.out / name).write_bytes(raw)
                    return raw

            with patch('ow_asset_chain.Archive', return_value=FakeArchive()), patch('ow_asset_chain.contact_sheet', return_value=[1, 1]):
                result = collect(root)
            self.assertEqual(set(result['resources']), {root, child, model})
            self.assertTrue(result['complete'])

    def test_missing_archive_resource_is_reported_but_corruption_still_fails(self):
        root='0400000000000001'
        with tempfile.TemporaryDirectory() as directory:
            archive=Archive.__new__(Archive)
            archive.out=Path(directory)
            archive.records={};archive.owners={};archive.packages={}
            from ow_asset_chain import GAME
            archive.build=(GAME/'.build.info').read_bytes()
            archive.resolve=lambda guid:{'bytes':3,'ckey':hashlib.md5(b'old').hexdigest()}
            def absent(*args):raise ValueError('Local archive read failed: fixture, exit 3')
            archive.fetch=absent
            with patch('ow_asset_chain.contact_sheet',return_value=[1,1]):
                result=collect(root,archive=archive)
            self.assertFalse(result['complete'])
            self.assertEqual(result['resources'][root]['status'],'unavailable')
            archive.fetch=lambda *args:b'bad'
            with self.assertRaisesRegex(ValueError,'size/content-key mismatch'):
                collect(root,archive=archive)

    def test_bc5_four_dword_planes_preserve_both_channels(self):
        blocks = np.array([[255, 255, *([0] * 6), 64, 64, *([0] * 6)],
                           [32, 32, *([0] * 6), 128, 128, *([0] * 6)]], dtype='u1')
        planes = b''.join(blocks[:, i:i + 4].tobytes() for i in range(0, 16, 4))
        header = bytearray(32)
        header[3] = 83
        struct.pack_into('<HH', header, 8, 8, 4)
        payload = struct.pack('<4I', 1, 1, len(planes), 16) + planes
        image = np.asarray(decode(bytes(header), payload))
        self.assertTrue(np.all(image[:, :4] == [255, 64, 0]))
        self.assertTrue(np.all(image[:, 4:] == [32, 128, 0]))
        with self.assertRaisesRegex(ValueError, 'layout mismatch'):
            decode(bytes(header), payload[:-1])

    def test_guid_validation_does_not_accept_paths(self):
        self.assertEqual(guid_arg('0x04000000000000AF'), '04000000000000af')
        import argparse
        with self.assertRaises(argparse.ArgumentTypeError):
            guid_arg('../outside')


if __name__ == '__main__':
    unittest.main()
