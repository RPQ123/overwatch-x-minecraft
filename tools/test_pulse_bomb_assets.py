"""Synthetic format/identity fixtures; no owned game bytes copied into tests."""
import gzip
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

import pulse_bomb_assets as assets


def planar(linear, words):
    return np.frombuffer(linear,dtype="u1").reshape(-1,words,4).transpose(1,0,2).copy().tobytes()


def texture(fmt):
    header=bytearray(32);header[3]=fmt
    struct.pack_into("<HH",header,8,512,512)
    block=struct.pack("<HHI",0xffff,0,0)
    if fmt==78:block=bytes([255,0])+bytes(6)+block
    linear=block*(512*512//16)
    payload=struct.pack("<4I",7,1,len(linear),16)+planar(linear,2 if fmt==72 else 4)
    return bytes(header),payload


def package(records):
    body=gzip.compress(b"".join(struct.pack("<QIII16s",*row) for row in records),mtime=0)
    header=bytearray(80);struct.pack_into("<Q",header,0,80)
    struct.pack_into("<II",header,24,len(records),len(body))
    return bytes(header)+body


def model():
    raw=bytearray(38480);struct.pack_into("<I",raw,72,len(raw))
    struct.pack_into("<QQ",raw,368,1080,1192)
    struct.pack_into("<I",raw,1080,731);struct.pack_into("<4B",raw,1088,20,16,7,6)
    struct.pack_into("<QQQ",raw,1112,1136,1728,16352)
    semantics=[(0,0,2,0,0),(4,0,6,0,0xc0000),(5,0,8,0,0x100000),
        (1,0,9,1,0),(3,0,9,1,0x40000),(9,0,4,1,0x80000),(16,0,12,1,0xc0000)]
    for i,row in enumerate(semantics):struct.pack_into("<4BI",raw,1136+8*i,*row)
    struct.pack_into("<II",raw,1192,2604,0);struct.pack_into("<Q",raw,1208,28048)
    for i in range(731):
        struct.pack_into("<3f",raw,1728+20*i,.1 if i%2 else -.1,.04 if i%3 else -.06,.08 if i%2 else -.12)
        raw[1728+20*i+16]=255
        struct.pack_into("<3b",raw,16352+16*i,0,127,0)
        struct.pack_into("<2e",raw,16352+16*i+8,.25,.75)
    struct.pack_into("<2604H",raw,28048,*[i%731 for i in range(2604)])
    return raw


class TextureFixtures(unittest.TestCase):
    def test_word_planes_roundtrip_bc1_and_bc3(self):
        for words in (2,4):
            linear=bytes(range(128))
            self.assertEqual(assets.deplane_words(planar(linear,words),words),linear)

    def test_word_planes_reject_invalid_alignment(self):
        for data,words in ((b"x",2),(bytes(16),3),(bytes(12),4)):
            with self.assertRaises(ValueError):assets.deplane_words(data,words)

    def test_bc1_and_bc3_top_mips_recover_white(self):
        for fmt in (72,78):
            image=assets.decode_top_texture(*texture(fmt))
            self.assertEqual(image.size,(512,512))
            self.assertEqual(image.getpixel((300,200)),(255,255,255,255))

    def test_wrong_dimensions_refused(self):
        header,payload=texture(72);header=bytearray(header)
        struct.pack_into("<H",header,8,1024)
        with self.assertRaises(ValueError):assets.decode_top_texture(header,payload)

    def test_wrong_format_refused(self):
        header,payload=texture(72);header=bytearray(header);header[3]=71
        with self.assertRaises(ValueError):assets.decode_top_texture(header,payload)

    def test_truncated_or_extra_payload_refused(self):
        header,payload=texture(72)
        for changed in (payload[:-1],payload+b"x",payload[:15]):
            with self.assertRaises(ValueError):assets.decode_top_texture(header,changed)


class PackageFixtures(unittest.TestCase):
    def test_exact_records_and_identical_duplicate(self):
        row=(0x0d00000000000b2c,38480,3,4,bytes.fromhex("11"*16))
        parsed=assets.package_records(package([row,row]))
        self.assertEqual(len(parsed),1)
        self.assertEqual(parsed["0d00000000000b2c"]["ckey"],"11"*16)

    def test_conflicting_duplicate_refused(self):
        a=(1,10,0,0,bytes(16));b=(1,11,0,0,bytes(16))
        with self.assertRaisesRegex(ValueError,"Conflicting"):assets.package_records(package([a,b]))

    def test_truncated_header_and_gzip_refused(self):
        valid=package([(1,10,0,0,bytes(16))])
        for raw in (valid[:79],valid[:-1],valid[:80]+bytes(len(valid)-80)):
            with self.assertRaises(ValueError):assets.package_records(raw)

    def test_count_mismatch_and_expansion_limit(self):
        raw=bytearray(package([(1,10,0,0,bytes(16))]))
        for count in (0,2,100001):
            changed=raw.copy();struct.pack_into("<I",changed,24,count)
            with self.assertRaises(ValueError):assets.package_records(changed)


class ModelFixtures(unittest.TestCase):
    def test_unscaled_centered_rigid_mesh(self):
        result=assets.parse_rigid_model(model())
        self.assertEqual(result["positions"].shape,(731,3))
        np.testing.assert_allclose(result["positions"].min(0),[-.1,-.05,-.1],atol=1e-7)
        np.testing.assert_allclose(result["positions"].max(0),[.1,.05,.1],atol=1e-7)
        np.testing.assert_allclose(result["normals"],np.tile([0,1,0],(731,1)))
        self.assertAlmostEqual(result["halfThickness"],.05,places=7)
        self.assertEqual(result["indices"].shape,(2604,))

    def test_descriptor_or_semantic_drift_refused(self):
        for offset,value,fmt in ((368,1081,"<Q"),(1136,1,"<B"),(1088,24,"<B"),(1208,28050,"<Q")):
            raw=model();struct.pack_into(fmt,raw,offset,value)
            with self.assertRaises(ValueError):assets.parse_rigid_model(raw)

    def test_nonrigid_bone_or_weight_refused(self):
        for offset in (1728+12,1728+16):
            raw=model();raw[offset]=1
            with self.assertRaisesRegex(ValueError,"rigid"):assets.parse_rigid_model(raw)

    def test_nan_or_overscale_position_refused(self):
        for value in (float("nan"),float("inf"),.21):
            raw=model();struct.pack_into("<f",raw,1728,value)
            with self.assertRaises(ValueError):assets.parse_rigid_model(raw)

    def test_bad_index_uv_or_normal_refused(self):
        for offset,fmt,value in ((28048,"<H",731),(16352+8,"<e",1.1),(16352+1,"<b",0)):
            raw=model();struct.pack_into(fmt,raw,offset,value)
            with self.assertRaises(ValueError):assets.parse_rigid_model(raw)

    def test_size_and_truncation_refused(self):
        valid=model()
        for raw in (valid[:80],valid[:-1]):
            with self.assertRaises(ValueError):assets.parse_rigid_model(raw)


class PrivatePackFixtures(unittest.TestCase):
    def setUp(self):
        # Keep all synthetic fixture writes on the workspace volume, never in
        # the developer's real private asset cache (which may be on C:).
        from modpack.config import PackPaths
        temporary=assets.ROOT/'data/tmp'
        temporary.mkdir(parents=True,exist_ok=True)
        directory=tempfile.TemporaryDirectory(prefix='pulse-tests-',dir=temporary)
        self.addCleanup(directory.cleanup)
        base=Path(directory.name)
        configured=PackPaths(assets.ROOT,configuration=dict(schemaVersion=1,paths={'privateAssets':str(base)}))
        for replacement in (patch.object(assets,'BASE',base),patch.object(assets,'paths',return_value=configured)):
            replacement.start();self.addCleanup(replacement.stop)

    def test_private_root_and_repo_paths_refused(self):
        for path in (assets.BASE,assets.ROOT/"research/fake-pulse"):
            with self.assertRaises(ValueError):assets.private_path(path)
        self.assertFalse(assets.prepare(output=assets.ROOT/"research/fake-pulse")["ready"])

    def test_absent_sources_return_explicit_error(self):
        assets.BASE.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="pulse-fixture-",dir=assets.BASE) as temp:
            root=Path(temp);result=assets.prepare(root/"missing",root/"out")
            self.assertFalse(result["ready"])
            self.assertFalse(result["originalModel"])
            self.assertFalse((root/"out").exists())

    def test_existing_bad_pack_never_overwritten(self):
        assets.BASE.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="pulse-fixture-",dir=assets.BASE) as temp:
            root=Path(temp);output=root/"out";output.mkdir()
            proof=output/"provenance.json";proof.write_text('{"clientBuild":"other"}',encoding="utf-8")
            before=proof.read_bytes();result=assets.prepare(root/"missing",output)
            self.assertFalse(result["ready"]);self.assertEqual(proof.read_bytes(),before)

    def test_pack_checksum_change_rejected(self):
        assets.BASE.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="pulse-fixture-",dir=assets.BASE) as temp:
            output=Path(temp)
            for name in ("pulse.json","body.png","emission.png"):(output/name).write_bytes(b"fixture")
            manifest={"clientBuild":"0.8.0.24919","originalModelSha256":assets.MODEL_SHA256,
                "model":"0d00000000000b2c","files":{n:assets.sha(b"fixture") for n in ("pulse.json","body.png","emission.png")}}
            (output/"provenance.json").write_text(json.dumps(manifest),encoding="utf-8")
            self.assertTrue(assets.validate_pack(output)["ready"])
            (output/"body.png").write_bytes(b"altered")
            with self.assertRaisesRegex(ValueError,"hash mismatch"):assets.validate_pack(output)

    def test_large_manifest_refused_before_parsing(self):
        assets.BASE.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="pulse-fixture-",dir=assets.BASE) as temp:
            output=Path(temp);(output/"provenance.json").write_bytes(b" "*65537)
            with self.assertRaisesRegex(ValueError,"bounds/path"):assets.validate_pack(output)


if __name__=="__main__":unittest.main()
