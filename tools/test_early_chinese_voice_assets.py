import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import early_chinese_voice_assets as v

class ChinesePackTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.profile=self.root/'profile';self.profile.mkdir()
        self.options=self.profile/'options.txt';self.options.write_text('resourcePacks:["vanilla","fabric","file/custom"]\nsoundCategory_voice:0.7\nparticles:0\n')
        self.source=self.root/'source';(self.source/'selected').mkdir(parents=True)
        self.blob=b'OggSowned-test-fixture';(self.source/'selected/fixture.ogg').write_bytes(self.blob)
        (self.source/'manifest.json').write_text(json.dumps({'fixture':{'sourcePage':'https://example.invalid/reference','earliestRecordingDateVerified':True}}))
        self.patch=patch.object(v,'CLIPS',{'genji.dragonblade':('fixture',hashlib.sha256(self.blob).hexdigest())});self.patch.start();self.addCleanup(self.patch.stop)
    def test_priority_replace_idempotence_and_preservation(self):
        self.assertTrue(v.prepare(self.profile,self.source));before=self.options.read_bytes()
        self.assertTrue(v.prepare(self.profile,self.source));self.assertEqual(self.options.read_bytes(),before)
        self.assertIn(b'soundCategory_voice:0.7',before);self.assertIn(b'file/custom',before)
        packs=json.loads(self.options.read_text().splitlines()[0].split(':',1)[1]);self.assertEqual(packs[-1],'file/'+v.PACK)
        p=self.profile/'resourcepacks'/v.PACK
        self.assertTrue(json.loads((p/'assets/owmcguest/sounds.json').read_text())['genji.dragonblade']['replace'])
        self.assertFalse(json.loads((p/'provenance.json').read_text())['genji.dragonblade']['earliestRecordingDateVerified'])
    def test_bad_source_does_not_touch_profile(self):
        original=self.options.read_bytes();(self.source/'selected/fixture.ogg').write_bytes(b'OggSchanged')
        with self.assertRaises(ValueError):v.prepare(self.profile,self.source)
        self.assertEqual(self.options.read_bytes(),original);self.assertFalse((self.profile/'resourcepacks').exists())
    def test_modified_destination_is_preserved(self):
        v.prepare(self.profile,self.source);p=self.profile/'resourcepacks'/v.PACK/'assets/owmcguest/sounds/private/early_chinese/fixture.ogg';p.write_bytes(b'user recording')
        with self.assertRaises(ValueError):v.prepare(self.profile,self.source)
        self.assertEqual(p.read_bytes(),b'user recording')
    def test_missing_optional_assets_keeps_options(self):
        before=self.options.read_bytes();(self.source/'selected/fixture.ogg').unlink()
        self.assertFalse(v.prepare(self.profile,self.source));self.assertEqual(before,self.options.read_bytes())
    def test_verified_japanese_variant_is_randomized_without_duplicate_merge(self):
        import genji_voice_assets
        japanese=self.profile/'resourcepacks/owmc-private-voice/assets/owmcguest/sounds/private/genji_dragonblade.ogg'
        japanese.parent.mkdir(parents=True);japanese.write_bytes(self.blob)
        with patch.object(genji_voice_assets,'SHA256',hashlib.sha256(self.blob).hexdigest()):
            v.prepare(self.profile,self.source)
        event=json.loads((self.profile/'resourcepacks'/v.PACK/'assets/owmcguest/sounds.json').read_text())['genji.dragonblade']
        self.assertTrue(event['replace']);self.assertEqual(len(event['sounds']),2)
        self.assertEqual(event['sounds'][1]['name'],'owmcguest:private/genji_dragonblade')
        self.assertEqual(japanese.read_bytes(),self.blob)
        before=self.options.read_bytes();japanese.write_bytes(b'changed private recording')
        with self.assertRaises(ValueError):v.prepare(self.profile,self.source)
        self.assertEqual(before,self.options.read_bytes())

if __name__=='__main__':unittest.main()
