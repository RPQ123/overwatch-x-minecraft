import hashlib,json,tempfile,unittest,zipfile
from pathlib import Path
from boss_mods import verify
class BossModsCheck(unittest.TestCase):
    def test_absent_optional_manifest_keeps_existing_profile(self):
        with tempfile.TemporaryDirectory() as d:self.assertEqual(verify(Path(d)),[])
    def test_exact_manifest_and_missing_changed_package(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'mods').mkdir();jar=p/'mods/aether.jar'
            with zipfile.ZipFile(jar,'w') as z:z.writestr('fabric.mod.json',json.dumps(dict(id='aether',version='1')))
            row=dict(file=jar.name,id='aether',version='1',sha256=hashlib.sha256(jar.read_bytes()).hexdigest());manifest=p/'owmc-boss-mods.json';manifest.write_text(json.dumps([row]))
            self.assertEqual(verify(p),[row]);jar.write_bytes(b'changed')
            with self.assertRaises(ValueError):verify(p)
            jar.unlink()
            with self.assertRaises(ValueError):verify(p)
    def test_parent_path_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'owmc-boss-mods.json').write_text(json.dumps([dict(file='../aether.jar')]))
            with self.assertRaises(ValueError):verify(p)
if __name__=='__main__':unittest.main()
