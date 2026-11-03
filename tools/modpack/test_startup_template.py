"""Clean terrain/cache portability, integrity and existing-save preservation."""
import gzip
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from modpack import startup_template as template
from modpack.config import write_json,sha256

def text(value):
    raw=value.encode('utf-8');return struct.pack('>H',len(raw))+raw

def field(kind,name,payload):return bytes([kind])+text(name)+payload

def level(player=False,seed=20261014):
    data=field(3,'DataVersion',struct.pack('>i',3955))+field(8,'LevelName',text(template.WORLD))
    data+=field(10,'WorldGenSettings',field(4,'seed',struct.pack('>q',seed))+b'\0')
    if player:data+=field(10,'Player',b'\0')
    return gzip.compress(b'\x0a\0\0'+field(10,'Data',data+b'\0')+b'\0')

class TemplateTests(unittest.TestCase):
    def setUp(self):
        base=Path(__file__).resolve().parents[2]/'data/tmp'
        base.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=base);self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'中文 空格 包';self.root.mkdir()
        self.profile=self.root/'guest-passthrough-client'
        (self.profile/'mods').mkdir(parents=True)
        (self.profile/'mods/fixture.jar').write_bytes(b'own inert mod')
        (self.root/'modpack.json').write_text('{}')
        self.settings=dict(worldName=template.WORLD,worldSeed=20261014)
        self.make()

    def make(self,player=False,seed=20261014,name='cache/.fabric/processedMods/fixture.jar'):
        archive=self.root/template.PAYLOAD;archive.parent.mkdir(parents=True,exist_ok=True)
        values={'world/level.dat':level(player,seed),name:b'inert cache'}
        rows=[dict(path=n,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()) for n,b in values.items()]
        with zipfile.ZipFile(archive,'w') as z:
            for n,b in values.items():z.writestr(n,b)
        self.meta=dict(schemaVersion=1,worldName=template.WORLD,worldSeed=20261014,dataVersion=3955,
                       playerDataRemoved=True,files=rows,mods={'fixture.jar':sha256(self.profile/'mods/fixture.jar')})
        write_json(self.root/template.METADATA,self.meta)
        write_json(self.root/'manifest.json',dict(schemaVersion=1,files=[dict(path=n,bytes=(self.root/n).stat().st_size,sha256=sha256(self.root/n)) for n in (template.METADATA,template.PAYLOAD)]))

    def test_clean_world_and_cache_install_in_unicode_root(self):
        result=template.install(self.root,self.profile,self.settings)
        self.assertTrue(result['installed']);self.assertEqual(result['cachesPrepared'],1)
        self.assertTrue((self.profile/'saves/Overwatch World/level.dat').is_file())

    def test_existing_personal_world_is_preserved(self):
        world=self.profile/'saves/Overwatch World';world.mkdir(parents=True)
        (world/'level.dat').write_bytes(b'personal world must stay byte-identical')
        self.assertFalse(template.install(self.root,self.profile,self.settings)['installed'])
        self.assertEqual((world/'level.dat').read_bytes(),b'personal world must stay byte-identical')

    def test_same_size_corruption_is_rejected(self):
        archive=self.root/template.PAYLOAD;data=bytearray(archive.read_bytes());data[-1]^=1;archive.write_bytes(data)
        with self.assertRaisesRegex(ValueError,'pinned'):template.install(self.root,self.profile,self.settings)

    def test_player_nbt_is_rejected_despite_a_claimed_privacy_flag(self):
        self.make(player=True)
        with self.assertRaisesRegex(ValueError,'privacy'):template.checked(self.meta,self.root/template.PAYLOAD)

    def test_wrong_actual_seed_is_rejected(self):
        self.make(seed=1)
        with self.assertRaisesRegex(ValueError,'seed'):template.checked(self.meta,self.root/template.PAYLOAD)

    def test_archive_traversal_is_rejected(self):
        self.make(name='cache/../../outside.jar')
        with self.assertRaisesRegex(ValueError,'path'):template.checked(self.meta,self.root/template.PAYLOAD)

    def test_changed_mods_fall_back_without_opening_the_template_world(self):
        (self.profile/'mods/fixture.jar').write_bytes(b'changed own mod')
        result=template.install(self.root,self.profile,self.settings)
        self.assertFalse(result['installed']);self.assertFalse((self.profile/'saves').exists())

    def test_explicit_other_world_is_preserved(self):
        result=template.install(self.root,self.profile,{**self.settings,'worldName':'Other'})
        self.assertFalse(result['installed']);self.assertFalse((self.profile/'saves').exists())

    def test_ui_layout_preflight_cannot_bypass_coordinator_sha_gate(self):
        from modpack import first_run
        from modpack.config import PackPaths
        import project_launcher
        paths=PackPaths(self.root)
        for path in (paths.get('python'),paths.get('java'),paths.get('owExecutable'),
                     self.root/'guest/build/libs/owmc-guest-0.1.0.jar'):
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'inert unverified fixture')
        write_json(self.root/'passthrough-settings.json',dict(schemaVersion=1))
        with patch.object(first_run,'environment',return_value={'checks':[]}):
            self.assertTrue(first_run.startup_check(self.root,layout_only=True)['ready'])
        backend=project_launcher.SessionBackend(self.root)
        with patch.object(backend,'supervisors',return_value=[]),patch.object(backend,'spawn') as spawn:
            with self.assertRaisesRegex(ValueError,'SHA256'):
                backend.start(self.root/'never-spawn.log')
            spawn.assert_not_called()

if __name__=='__main__':unittest.main()
