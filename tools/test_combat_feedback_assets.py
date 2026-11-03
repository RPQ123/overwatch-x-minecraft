import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import combat_feedback_assets as assets

class CombatFeedbackAssetsTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);self.source=self.base/'source';self.source.mkdir();self.profile=self.base/'profile';self.profile.mkdir()
        self.pins={}
        for name in ['hit.ogg','kill.ogg']:
            data=(name+'-fixture').encode();(self.source/name).write_bytes(data);self.pins[name]=hashlib.sha256(data).hexdigest()
        (self.source/'source.json').write_text('{}',encoding='utf-8')
        (self.profile/'options.txt').write_text('particles:0\nresourcePacks:["vanilla","file/user-custom"]\n',encoding='utf-8')
        self.addCleanup(patch.stopall);patch.object(assets,'ROOT',self.source).start();patch.object(assets,'FILES',self.pins).start()
    def test_idempotent_preserves_existing_pack_order(self):
        self.assertTrue(assets.prepare(self.profile));before=(self.profile/'options.txt').read_bytes()
        assets.prepare(self.profile);self.assertEqual(before,(self.profile/'options.txt').read_bytes())
        self.assertIn('"vanilla","file/user-custom","file/owmc-private-combat-feedback"',before.decode())
    def test_corrupt_later_input_does_not_write_earlier(self):
        (self.source/'kill.ogg').write_bytes(b'changed');before=(self.profile/'options.txt').read_bytes()
        with self.assertRaisesRegex(ValueError,'hash changed'):assets.prepare(self.profile)
        self.assertFalse((self.profile/'resourcepacks').exists());self.assertEqual(before,(self.profile/'options.txt').read_bytes())
    def test_preserves_user_modified_destination(self):
        assets.prepare(self.profile)
        dst=self.profile/'resourcepacks/owmc-private-combat-feedback/assets/owmcguest/sounds/private/combat/hit.ogg';dst.write_bytes(b'user-change')
        with self.assertRaisesRegex(ValueError,'Preserve modified'):assets.prepare(self.profile)
        self.assertEqual(dst.read_bytes(),b'user-change')

if __name__=='__main__':unittest.main()
