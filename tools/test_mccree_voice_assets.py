"""Protect private voice migration and the user's existing resource packs."""
import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import mccree_voice_assets as voice

class VoiceMigration(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.source=self.root/'source';self.source.mkdir();self.profile=self.root/'profile';self.profile.mkdir()
        self.old=b'known previous English recording';self.new=b'new pinned Chinese recording';self.flash=b'preserved flashbang'
        self.hash=lambda b:hashlib.sha256(b).hexdigest()
        for name,data in [('deadeye-zhcn-2016.ogg',self.new),('flashbang.ogg',self.flash)]:
            (self.source/name).write_bytes(data);(self.source/(name[:-4]+'-source.json')).write_text(json.dumps({'file':name}),encoding='utf-8')
        self.options=self.profile/'options.txt';self.options.write_text('masterVolume:0.7\nresourcePacks:["vanilla","file/custom"]\n',encoding='utf-8')
        self.destination=self.profile/'resourcepacks/owmc-private-mccree/assets/owmcguest/sounds/private/mccree/deadeye.ogg'
        self.destination.parent.mkdir(parents=True)
        for name,value in [('ROOT',self.source),('FILES',{'deadeye.ogg':self.hash(self.new),'flashbang.ogg':self.hash(self.flash)}),('PREVIOUS_DEADEYE',self.hash(self.old))]:
            p=patch.object(voice,name,value);p.start();self.addCleanup(p.stop)

    def test_known_english_migrates_once_and_preserves_options(self):
        self.destination.write_bytes(self.old);self.assertTrue(voice.prepare(self.profile));self.assertTrue(voice.prepare(self.profile))
        self.assertEqual(self.destination.read_bytes(),self.new)
        self.assertEqual((self.profile/'resourcepacks/owmc-private-mccree/migration-backup/deadeye-english-classic.ogg').read_bytes(),self.old)
        self.assertIn('masterVolume:0.7',self.options.read_text());packs=json.loads(next(v for v in self.options.read_text().splitlines() if v.startswith('resourcePacks:')).split(':',1)[1])
        self.assertEqual(packs,['vanilla','file/custom','file/owmc-private-mccree'])

    def test_unknown_existing_recording_is_not_overwritten(self):
        self.destination.write_bytes(b'user recording')
        with self.assertRaises(ValueError):voice.prepare(self.profile)
        self.assertEqual(self.destination.read_bytes(),b'user recording')

    def test_bad_source_hash_is_rejected_before_destination_write(self):
        self.destination.write_bytes(self.old);(self.source/'deadeye-zhcn-2016.ogg').write_bytes(b'corrupt')
        with self.assertRaises(ValueError):voice.prepare(self.profile)
        self.assertEqual(self.destination.read_bytes(),self.old)

    def test_missing_chinese_does_not_silently_install_english(self):
        self.destination.write_bytes(self.old);(self.source/'deadeye-zhcn-2016.ogg').unlink()
        self.assertFalse(voice.prepare(self.profile));self.assertEqual(self.destination.read_bytes(),self.old)
    def test_later_bad_shot_cannot_partly_migrate_voice(self):
        self.destination.write_bytes(self.old);shot=b'private original beta shot';(self.source/'deadeye-shot-beta-recorded.ogg').write_bytes(b'corrupted later input')
        files=dict(voice.FILES,**{'shot.ogg':self.hash(shot)})
        with patch.object(voice,'FILES',files):
            with self.assertRaises(ValueError):voice.prepare(self.profile)
        self.assertEqual(self.destination.read_bytes(),self.old)
        self.assertFalse((self.profile/'resourcepacks/owmc-private-mccree/migration-backup').exists())

    def test_unknown_migration_backup_is_preserved(self):
        self.destination.write_bytes(self.old);p=self.profile/'resourcepacks/owmc-private-mccree/migration-backup';p.mkdir();(p/'deadeye-english-classic.ogg').write_bytes(b'user backup')
        with self.assertRaises(ValueError):voice.prepare(self.profile)
        self.assertEqual(self.destination.read_bytes(),self.old)

if __name__=='__main__':unittest.main()
