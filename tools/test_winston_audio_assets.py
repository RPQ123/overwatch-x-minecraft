"""Offline file boundaries and preservation; never starts a game or plays audio."""
import hashlib,json,tempfile,unittest
from pathlib import Path
import prepare_winston_audio as prepare
import voice_download as download

class WinstonAudioAssetsTest(unittest.TestCase):
    def setUp(self):
        parent=prepare.ROOT/'research/winston/W3/tmp';parent.mkdir(parents=True,exist_ok=True)
        self.root=Path(tempfile.mkdtemp(prefix='audio-test-',dir=parent)).resolve()
        self.assertTrue(self.root.is_relative_to(parent.resolve()))
        self.old_dest=download.DEST;download.DEST=self.root
    def tearDown(self):download.DEST=self.old_dest
    def fixture(self):
        h='1'*32;raw=b'OggS'+b'fixture-with-no-audio-playback'*4;p=self.root/'clip.ogg';p.write_bytes(raw)
        row={'hash':h,'hero':'winston','event':'sfx:winston_takeoff','localOnly':True}
        metadata={h:{'hero':'winston','event':row['event'],'format':'ogg','file':'clip.ogg','sha256':hashlib.sha256(raw).hexdigest()}}
        return row,metadata,p
    def test_local_ogg_and_missing(self):
        r,m,p=self.fixture();self.assertTrue(download.local_only_ready(r,m));p.rename(self.root/'saved.ogg');self.assertFalse(download.local_only_ready(r,m))
    def test_modified_audio_preserved_and_rejected(self):
        r,m,p=self.fixture();p.write_bytes(b'OggSchanged');self.assertFalse(download.local_only_ready(r,m));self.assertEqual(p.read_bytes(),b'OggSchanged')
    def test_owner_and_path_escape(self):
        r,m,p=self.fixture();m[r['hash']]['hero']='mei';self.assertFalse(download.local_only_ready(r,m));m[r['hash']]['hero']='winston'
        m[r['hash']]['file']='../outside.ogg';self.assertFalse(download.local_only_ready(r,m))
        with self.assertRaises(ValueError):prepare.member(self.root,'../outside.ogg')
    def test_copy_refuses_changed_target(self):
        source=self.root/'source';target=self.root/'target';source.write_bytes(b'original');target.write_bytes(b'user change')
        with self.assertRaises(ValueError):prepare.copy_guard(source,target,prepare.sha(source))
        self.assertEqual(target.read_bytes(),b'user change')
    def test_only_voice_path_configured(self):
        old=prepare.ROOT;prepare.ROOT=self.root
        try:
            folder=self.root/'config';folder.mkdir();file=folder/'launcher.json';file.write_text('{"paths":{"meshAssets":"keep"},"save":"keep-world"}',encoding='utf-8')
            target=self.root/'private-assets/voices';prepare.configure(target);result=json.loads(file.read_text(encoding='utf-8'))
            self.assertEqual(result,{'paths':{'meshAssets':'keep','heroVoiceAssets':'private-assets/voices'},'save':'keep-world'})
            before=file.read_bytes();prepare.configure(target);self.assertEqual(file.read_bytes(),before)
        finally:prepare.ROOT=old
    def test_exact_recipe_and_date_disclosure(self):
        recipe=json.loads(prepare.RECIPE.read_text(encoding='utf-8'));self.assertFalse(recipe['mandarinOriginal24919DateVerified']);self.assertEqual(len(recipe['voices']),3);self.assertEqual(len(recipe['sfx']),4)
        for row in recipe['sfx']:
            self.assertEqual(row['sourceBuild'],24919);self.assertTrue(row['media'].startswith('07c'));self.assertEqual(len(row['oggSha256']),64)

if __name__=='__main__':unittest.main()
