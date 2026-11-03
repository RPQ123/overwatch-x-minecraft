"""Integrity and static-parser fixtures only; never execute bundled programs."""
from pathlib import Path
import json
import struct
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from modpack.archive import (compatibility_audit, create_archive, digest, pe_metadata,
                             safe_name, verify_archive)


class ArchiveCheck(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.source = self.directory / '中文 空格' / 'OWMC-1.0.0'
        self.source.mkdir(parents=True)
        (self.source / '说明.txt').write_bytes('完整离线包\n'.encode('utf-8'))

    def test_real_zip_roundtrip_root_unicode_and_checksum(self):
        result = create_archive(self.source)
        archive = self.source.parent / 'OWMC-1.0.0.zip'
        self.assertEqual(result['output'], str(archive))
        self.assertTrue(result['checksumVerified'])
        self.assertEqual(result['sha256'], digest(archive))
        self.assertEqual(verify_archive(archive)['files'], 1)
        with zipfile.ZipFile(archive) as stream:
            self.assertEqual(set(stream.namelist()), {'OWMC-1.0.0/', 'OWMC-1.0.0/说明.txt'})
            self.assertEqual(stream.read('OWMC-1.0.0/说明.txt'), '完整离线包\n'.encode())
            item = stream.getinfo('OWMC-1.0.0/说明.txt')
            self.assertTrue(item.flag_bits & 0x800)
            # Streaming entries reserve ZIP64 fields even for this small fixture.
            with archive.open('rb') as raw:
                raw.seek(item.header_offset + 28)
                self.assertGreaterEqual(struct.unpack('<H', raw.read(2))[0], 20)

    def test_existing_output_and_checksum_are_preserved(self):
        output = self.directory / 'existing.zip'
        output.write_bytes(b'owned')
        with self.assertRaises(FileExistsError):
            create_archive(self.source, output)
        self.assertEqual(output.read_bytes(), b'owned')
        checksum = self.directory / 'other.zip.sha256'
        checksum.write_text('owned', encoding='utf-8')
        with self.assertRaises(FileExistsError):
            create_archive(self.source, self.directory / 'other.zip')
        self.assertEqual(checksum.read_text(), 'owned')

    def test_changed_source_keeps_partial_and_no_finished_archive(self):
        def modify(root, expected):
            (root / 'new-file.txt').write_text('parallel build', encoding='utf-8')
            from modpack.archive import snapshot
            if snapshot(root) != expected:
                raise ValueError('changed')
        with mock.patch('modpack.archive.assert_snapshot', side_effect=modify):
            with self.assertRaisesRegex(ValueError, 'changed'):
                create_archive(self.source)
        self.assertFalse((self.source.parent / 'OWMC-1.0.0.zip').exists())
        self.assertEqual(len(list(self.source.parent.glob('*.partial-*'))), 1)

    def test_wrong_file_hash_and_extra_member_are_rejected(self):
        archive = self.directory / 'wrong.zip'
        inventory = dict(schemaVersion=1, rootDirectory='OWMC-1.0.0',
                         files=[dict(path='x.txt', bytes=1, sha256='0' * 64)])
        with zipfile.ZipFile(archive, 'w') as stream:
            stream.writestr('OWMC-1.0.0/x.txt', 'x')
        archive.with_name(archive.name + '.manifest.json').write_text(json.dumps(inventory), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, '内容校验失败'):
            verify_archive(archive)
        good = create_archive(self.source, self.directory / 'extra.zip')
        with zipfile.ZipFile(good['output'], 'a') as stream:
            stream.writestr('OWMC-1.0.0/unlisted.txt', 'extra')
        with self.assertRaisesRegex(ValueError, '实际 ZIP'):
            verify_archive(Path(good['output']))

    def test_zip_checksum_tampering_is_rejected(self):
        result = create_archive(self.source)
        Path(result['checksum']).write_text('0' * 64 + '  OWMC-1.0.0.zip\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, '整体 SHA256'):
            verify_archive(Path(result['output']))

    def test_unsafe_zip_paths_output_inside_source_and_inventory_collision(self):
        for value in ('../x', '/x', 'a/../x', 'C:/x', 'a\\x', 'a//x', 'x/CON.txt', 'x/hi.', 'x/?', 'x/\x01'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                safe_name(value)
        with self.assertRaises(ValueError):
            create_archive(self.source, self.source / 'bad.zip')
        (self.source.parent / 'OWMC-1.0.0.zip.manifest.json').write_text('owned', encoding='utf-8')
        with self.assertRaises(FileExistsError):
            create_archive(self.source)

    def test_multiple_roots_duplicates_and_symlinks_are_rejected(self):
        archive = self.directory / 'unsafe.zip'
        with zipfile.ZipFile(archive, 'w') as stream:
            stream.writestr('one/a.txt', 'a')
            stream.writestr('two/b.txt', 'b')
        with self.assertRaisesRegex(ValueError, '根目录'):
            verify_archive(archive)
        collision = self.directory / 'collision.zip'
        with zipfile.ZipFile(collision, 'w') as stream:
            stream.writestr('one/A.txt', 'a')
            stream.writestr('one/a.txt', 'b')
        with self.assertRaisesRegex(ValueError, '大小写冲突'):
            verify_archive(collision)
        linkzip = self.directory / 'link.zip'
        with zipfile.ZipFile(linkzip, 'w') as stream:
            link = zipfile.ZipInfo('one/link')
            link.create_system = 3
            link.external_attr = 0o120777 << 16
            stream.writestr(link, '../outside')
        with self.assertRaisesRegex(ValueError, '符号链接'):
            verify_archive(linkzip)

    def test_normal_and_delay_pe_imports_are_both_audited(self):
        # Independent tiny PE32+ section with two different import mechanisms.
        data = bytearray(2048)
        data[:2] = b'MZ'
        struct.pack_into('<I', data, 0x3c, 0x80)
        data[0x80:0x84] = b'PE\0\0'
        struct.pack_into('<HH', data, 0x84, 0x8664, 1)
        struct.pack_into('<H', data, 0x94, 240)
        struct.pack_into('<H', data, 0x98, 0x20b)
        struct.pack_into('<Q', data, 0xb0, 0x140000000)
        struct.pack_into('<I', data, 0xd4, 512)
        struct.pack_into('<I', data, 0x104, 16)
        struct.pack_into('<II', data, 0x110, 0x1000, 40)
        struct.pack_into('<II', data, 0x170, 0x1040, 64)
        struct.pack_into('<IIII', data, 0x190, 1024, 0x1000, 1024, 512)
        struct.pack_into('<IIIII', data, 512, 1, 0, 0, 0x1080, 1)
        struct.pack_into('<IIIIIIII', data, 576, 1, 0x10a0, 0, 0, 0, 0, 0, 0)
        data[640:653] = b'KERNEL32.dll\0'
        data[672:689] = b'D3DCOMPILER_47\0\0\0'
        result = pe_metadata(bytes(data))
        self.assertEqual(result['imports'], ['kernel32.dll'])
        self.assertEqual(result['delayImports'], ['d3dcompiler_47'])
        self.assertEqual(result['bits'], 64)

    def test_audit_detects_utf16_windows_config_paths(self):
        (self.source / 'options.ini').write_text('path=Q:\\Fixture\\project\\资源\n', encoding='utf-16')
        report = compatibility_audit(self.source)
        self.assertEqual(report['counts']['absolutePathFiles'], 1)
        self.assertEqual(report['absolutePaths'][0]['path'], 'options.ini')
        self.assertEqual(report['absolutePaths'][0]['values'], ['Q:\\Fixture\\project\\资源'])


if __name__ == '__main__':
    unittest.main()
