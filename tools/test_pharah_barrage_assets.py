import unittest,tempfile,json
from pathlib import Path
from pack_pharah_barrage import prepare,digest

class BarrageAssets(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.profile=self.root/'profile';self.profile.mkdir();self.source=self.root/'source';self.source.mkdir()
  (self.profile/'options.txt').write_text('resourcePacks:[]\nparticles:0\n',encoding='utf-8');self.blob=b'OggSfixture';(self.source/'fire-loop.ogg').write_bytes(self.blob);(self.source/'provenance.json').write_text(json.dumps({'files':{'fire-loop.ogg':digest(self.blob)}}),encoding='utf-8')
 def test_install_and_repeat(self):
  self.assertTrue(prepare(self.profile,self.source));self.assertTrue(prepare(self.profile,self.source));s=(self.profile/'options.txt').read_text();self.assertEqual(s.count('file/owmc-private-pharah-barrage'),1);self.assertIn('particles:0',s)
 def test_corrupt_source_is_not_installed(self):
  (self.source/'fire-loop.ogg').write_bytes(b'bad');before=(self.profile/'options.txt').read_bytes()
  with self.assertRaises(ValueError):prepare(self.profile,self.source)
  self.assertEqual(before,(self.profile/'options.txt').read_bytes());self.assertFalse((self.profile/'resourcepacks').exists())
 def test_modified_destination_is_preserved(self):
  prepare(self.profile,self.source);p=self.profile/'resourcepacks/owmc-private-pharah-barrage/assets/owmcguest/sounds/private/pharah/fire-loop.ogg';p.write_bytes(b'user clip');before=(self.profile/'options.txt').read_bytes()
  with self.assertRaises(ValueError):prepare(self.profile,self.source)
  self.assertEqual(p.read_bytes(),b'user clip');self.assertEqual(before,(self.profile/'options.txt').read_bytes())

if __name__=='__main__':unittest.main()
