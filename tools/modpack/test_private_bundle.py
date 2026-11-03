"""Personal-only bundle selection and audit fixtures; no real private inputs."""
from __future__ import annotations

import json
import struct
import subprocess
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

TOOLS=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(TOOLS))
from modpack import build, config, private_assets, game_client


class PrivateFixtures(unittest.TestCase):
    def setUp(self):
        temporary=TOOLS.parent/'data/tmp';temporary.mkdir(parents=True,exist_ok=True)
        directory=tempfile.TemporaryDirectory(dir=temporary)
        self.addCleanup(directory.cleanup);self.root=Path(directory.name)

    def file(self,relative,data=b'fixture'):
        p=self.root/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);return p

    def builder(self,name='OWMC-fixture-private'):
        builder=build.Builder(self.root,self.root/name,'fixture')
        builder.destination.mkdir()
        builder.component('owmc',build.INTERNAL,'fixture')
        builder.component('private',private_assets.LICENSE,'fixture')
        config.write_json(builder.destination/'modpack.json',dict(includesPrivate=True))
        builder.record('modpack.json','owmc')
        return builder

    def manifest(self,builder,**extra):
        value=dict(schemaVersion=1,distribution='fan-content-preview',includesPrivate=True,
                   components=builder.components,files=list(builder.rows.values()))
        value.update(extra);config.write_json(builder.destination/'manifest.json',value)

    def test_assets_require_explicit_marker_and_notice_without_a_directory_suffix(self):
        builder=self.builder()
        builder.copy(self.file('source.ogg',b'OggSfixture'),'private-assets/voice.ogg','private')
        self.manifest(builder)
        self.assertEqual(build.verify_manifest(builder.destination)['privateFiles'],1)
        public=self.root/'OWMC-public';shutil.copytree(builder.destination,public)
        self.assertEqual(build.verify_manifest(public)['privateFiles'],1)
        self.manifest(builder,includesPrivate=False)
        with self.assertRaises(ValueError):build.verify_manifest(builder.destination)

    def test_private_rows_cannot_hide_as_project_files_or_include_game_executables(self):
        builder=self.builder()
        builder.copy(self.file('source.json',b'{}'),'private-assets/source.json','owmc')
        self.manifest(builder)
        with self.assertRaisesRegex(ValueError,'private 组件'):build.verify_manifest(builder.destination)
        builder.rows.clear();(builder.destination/'private-assets/source.json').unlink()
        builder.record('modpack.json','owmc')
        builder.copy(self.file('game.exe'),'private-assets/game.exe','private')
        self.manifest(builder)
        with self.assertRaisesRegex(ValueError,'非运行资源'):build.verify_manifest(builder.destination)

    def test_model_selection_uses_runtime_literals_concat_and_bounded_turret_levels(self):
        self.file('guest/src/client/java/Fixture.java',b'''class Fixture {
 Object x=OriginalMeshPack.get("used"); String a="arrow-";String b="glow";
 Object turret=OriginalMeshPack.get("torb-turret-"+tv.level());
 // OriginalMeshPack.get("retired");
}''')
        selected=private_assets.model_references(self.root,{'used','arrow-glow','unused','retired','torb-turret-2'})
        self.assertEqual(selected,{'used','arrow-glow','torb-turret-1','torb-turret-2','torb-turret-3'})

    def test_catalog_requires_exactly_785_unique_rows(self):
        path=self.file('guest/src/main/java/lab/owmcguest/HeroVoiceDefaultCatalog.java',
                       '\n'.join(f'hero|kill|{i:032x}' for i in range(785)).encode())
        self.assertEqual(len(private_assets.voice_catalog(self.root)),785)
        path.write_text('hero|kill|'+'0'*32)
        with self.assertRaisesRegex(ValueError,'785'):private_assets.voice_catalog(self.root)

    def test_voice_copy_filters_the_catalog_and_validates_cached_receipts(self):
        builder=self.builder()
        paths=config.PackPaths(self.root,configuration=dict(schemaVersion=1,paths={'heroVoiceAssets':'voices','profile':'profile'}))
        cached='profile/resourcepacks/owmc-private-full-voice/assets/owmcguest/sounds/private/full/'
        identity='0'*32;excluded='f'*32;pin='1'*64
        config.write_json(self.root/'voices/manifest.json',{'entries':{
            identity:dict(hero='hero',event='kill',sha256=pin),
            excluded:dict(hero='hero',event='excluded',sha256=pin)}})
        ogg=self.file(cached+identity+'.ogg',b'OggSsynthetic')
        self.file(cached+excluded+'.ogg',b'OggSunselected')
        config.write_json(self.root/(cached+identity+'.json'),dict(sourceSha256=pin,oggSha256=config.sha256(ogg)))
        bundle=private_assets.PrivateBundle(builder,paths)
        bundle.voices([('hero','kill',identity)])
        self.assertEqual(bundle.summary['voiceClipsCopied'],1)
        self.assertFalse(any(excluded in p for p in builder.rows))
        entry=config.read_json(builder.destination/(private_assets.VOICE_DIRECTORY+'/manifest.json'))['entries'][identity]
        self.assertEqual(entry['format'],'ogg');self.assertEqual(entry['originalMp3Sha256'],pin)
        self.assertFalse(any(p.endswith('.mp3') or 'ffmpeg' in p for p in builder.rows))

    def test_missing_voice_keeps_an_unavailable_manifest_entry_for_runtime_degradation(self):
        builder=self.builder();paths=config.PackPaths(self.root,configuration=dict(schemaVersion=1,paths={'heroVoiceAssets':'voices'}))
        identity='0'*32
        config.write_json(self.root/'voices/manifest.json',{identity:dict(hero='hero',event='kill',sha256='1'*64)})
        bundle=private_assets.PrivateBundle(builder,paths);bundle.voices([('hero','kill',identity)])
        self.assertEqual(bundle.summary['voiceClipsCopied'],0)
        row=config.read_json(builder.destination/(private_assets.VOICE_DIRECTORY+'/manifest.json'))['entries'][identity]
        self.assertTrue(row['unavailable'])

    def test_model_copy_only_uses_verified_provenance_files_and_skips_bad_group(self):
        builder=self.builder();paths=config.PackPaths(self.root)
        pack=self.file('model/pack.json',b'{}');texture=self.file('model/texture.png',b'synthetic')
        self.file('model/unreferenced.raw')
        config.write_json(self.root/'model/provenance.json',dict(files={'pack.json':config.sha256(pack),'texture.png':config.sha256(texture)}))
        bundle=private_assets.PrivateBundle(builder,paths)
        bundle.model('used',self.root/'model','private-assets/owmc-mesh/used',mesh=True)
        self.assertEqual(bundle.summary['modelPacksCopied'],1)
        self.assertFalse(any(p.endswith('.raw') for p in builder.rows))
        texture.write_bytes(b'changed')
        bundle.model('bad',self.root/'model','private-assets/owmc-mesh/bad',mesh=True)
        self.assertEqual(len(bundle.summary['missingModels']),1)
        self.assertFalse(any('/bad/' in p for p in builder.rows))

    def test_ffmpeg_is_included_with_its_own_upstream_license(self):
        builder=self.builder()
        self.file('ffmpeg/bin/ffmpeg.exe')
        self.file('ffmpeg/LICENSE.txt',b'GNU GENERAL PUBLIC LICENSE\nVersion 3')
        paths=config.PackPaths(self.root,configuration=dict(schemaVersion=1,paths={'ffmpeg':'ffmpeg/bin/ffmpeg.exe'}))
        bundle=private_assets.PrivateBundle(builder,paths);bundle.ffmpeg()
        self.assertTrue(bundle.summary['ffmpegIncluded'])
        self.assertEqual(builder.rows['tools/ffmpeg/ffmpeg.exe']['license'],'GPL-3.0-or-later')
        self.assertNotEqual(builder.rows['tools/ffmpeg/ffmpeg.exe']['license'],private_assets.LICENSE)

    def test_no_files_from_the_ow_installation_may_be_packaged(self):
        builder=self.builder()
        source=builder.ow_directory/'example.json';source.parent.mkdir(parents=True)
        source.write_text('{}')
        with self.assertRaisesRegex(ValueError,'OW 客户端安装目录'):
            builder.copy(source,'private-assets/example.json','private',builder.ow_directory)

    def test_client_local_copy_is_hash_guarded_and_cannot_pass_as_public(self):
        builder=self.builder('OWMC-fixture')
        executable=self.file('offline-client/GameClientApp.patched.exe',b'inert fixture, never executable')
        self.file('offline-client/data/fixture.data',b'fixture game data')
        self.file('offline-client/cache/fixture.cache')
        self.file('offline-client/credentials.json',b'fixture-do-not-copy')
        configured=config.PackPaths(self.root,configuration={'schemaVersion':1,'paths':{'owExecutable':str(executable)}})
        with self.assertRaisesRegex(ValueError,'SHA256'):game_client.stage(builder,configured)
        self.assertFalse(any(p.startswith('game/') for p in builder.rows))
        expected=config.sha256(executable)
        with patch.object(game_client,'OW_SHA256',expected),patch.object(build,'OW_SHA256',expected):
            result=game_client.stage(builder,configured)
            self.assertEqual(result['files'],2)
            self.assertFalse(any('credentials' in p or 'cache/' in p for p in builder.rows))
            config.write_json(builder.destination/'modpack.json',dict(includesPrivate=True,includesClient=True))
            builder.record('modpack.json','owmc')
            self.manifest(builder,includesClient=True,clientSummary=result)
            self.assertEqual(build.verify_manifest(builder.destination)['clientFiles'],2)
            self.assertEqual(config.sha256(executable),expected)
            self.manifest(builder,includesClient=True,includesPrivate=False,clientSummary=result)
            with self.assertRaisesRegex(ValueError,'客户端仅允许'):build.verify_manifest(builder.destination)
            self.manifest(builder,includesClient=True,clientSummary=dict(result,executable='game/missing.exe'))
            with self.assertRaisesRegex(ValueError,'SHA256'):build.verify_manifest(builder.destination)

    def test_public_audit_rejects_ffmpeg_even_with_its_correct_license(self):
        builder=self.builder()
        builder.component('ffmpeg','GPL-3.0-or-later','fixture')
        builder.copy(self.file('fixture.exe'),'tools/ffmpeg/ffmpeg.exe','ffmpeg')
        self.manifest(builder,includesPrivate=False)
        with self.assertRaisesRegex(ValueError,'ffmpeg'):build.verify_manifest(builder.destination)

    def test_java_loads_preconverted_ogg_without_ffmpeg_and_preserves_source_receipt(self):
        repository=TOOLS.parent
        configured=config.PackPaths(repository)
        java=configured.get('java');javac=java.with_name('javac.exe')
        gson=list((configured.get('minecraft')/'libraries/com/google/code/gson/gson').glob('*/gson-*.jar'))
        if not javac.is_file() or not gson:self.skipTest('Java 21/Gson unavailable for standalone loader fixture')
        hero,event,identity=private_assets.voice_catalog(repository)[0]
        data=bytearray(27);data[:4]=b'OggS';struct.pack_into('<q',data,6,2400)
        source=self.file(f'voices/{hero}/{identity}.ogg',bytes(data))
        config.write_json(self.root/'voices/manifest.json',{'entries':{identity:dict(hero=hero,event=event,
            format='ogg',file=f'{hero}/{identity}.ogg',sha256=config.sha256(source),originalMp3Sha256='1'*64)}})
        stub=self.file('stubs/net/minecraft/util/Identifier.java',b'''package net.minecraft.util;
public record Identifier(String value){ public static Identifier of(String a,String b){return new Identifier(a+":"+b);} }''')
        fixture=self.file('LoaderCheck.java',b'''package lab.owmcguest;
import java.nio.file.*;
public class LoaderCheck {
 public static void main(String[] args)throws Exception {
  System.setProperty("owmc.heroVoiceDirectory",args[0]);
  System.setProperty("owmc.heroVoiceFfmpeg",args[0]+"/absent-ffmpeg.exe");
  try(var assets=new HeroVoiceAssets()){
   var load=HeroVoiceAssets.class.getDeclaredMethod("load",Path.class,long.class);load.setAccessible(true);
   var result=(HeroVoiceAssets.Loaded)load.invoke(assets,Path.of(args[1]),1L);
   if(result.clips().size()!=1)throw new AssertionError(result.error());
  }
 }
}''')
        classes=self.root/'classes'
        sourcepath=';'.join(str(repository/p) for p in ('guest/src/main/java','guest/src/client/java'))+';'+str(self.root/'stubs')
        compile=subprocess.run([str(javac),'-encoding','UTF-8','-cp',str(gson[-1]),'-sourcepath',sourcepath,
            '-d',str(classes),str(repository/'guest/src/client/java/lab/owmcguest/HeroVoiceAssets.java'),str(stub),str(fixture)],
            capture_output=True,text=True,encoding='utf-8',timeout=30)
        self.assertEqual(compile.returncode,0,compile.stderr[-1500:])
        run=subprocess.run([str(java),'-cp',str(classes)+';'+str(gson[-1]),'lab.owmcguest.LoaderCheck',
            str(self.root/'voices'),str(self.root/'profile')],capture_output=True,text=True,encoding='utf-8',timeout=20)
        self.assertEqual(run.returncode,0,run.stderr[-1500:])
        cache=self.root/'profile/resourcepacks/owmc-private-full-voice/assets/owmcguest/sounds/private/full'
        self.assertEqual((cache/(identity+'.ogg')).read_bytes(),bytes(data))
        self.assertEqual(config.read_json(cache/(identity+'.json'))['sourceSha256'],'1'*64)


if __name__=='__main__':unittest.main()
