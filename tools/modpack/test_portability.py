"""Default parity, root relocation, missing resources and account boundaries."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

TOOLS = Path(__file__).resolve().parents[1]
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))
from modpack import account, config, first_run, resources, prepare_lab
from modpack.build import source_closure


class WorkspaceFixture(unittest.TestCase):
    def setUp(self):
        temporary = ROOT/'data/tmp'
        temporary.mkdir(parents=True, exist_ok=True)
        directory = tempfile.TemporaryDirectory(dir=temporary)
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    def file(self, relative, data=b'fixture'):
        path = self.root/relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path


class DefaultParity(unittest.TestCase):
    def test_every_development_default_equals_the_previous_machine_layout(self):
        home = Path.home()
        legacy = {
            'python': ROOT/'.venv/Scripts/python.exe',
            'java': ROOT/'minecraft-1.21.1/runtime/java-runtime-delta/windows-x64/java-runtime-delta/bin/java.exe',
            'owExecutable': ROOT/config.OW_RELATIVE,
            'owFallbackExecutable': ROOT/'overwatch-2015/offline-lab/GameClientApp.patched.exe',
            'minecraft': ROOT/'minecraft-1.21.1', 'profile': ROOT/'guest-passthrough-client',
            'poseProfile': ROOT/'guest-pose-test-client', 'aoaProfile': ROOT/'aoa3-connector-client',
            'neoProfile': ROOT/'aoa3-neoforge-client',
            'neoInstallSource': home/'.universal-modder/mod-cache/boss-mods-20261024/neoforge-install-source.json',
            'privateAssets': home/'.universal-modder/assets',
            'meshAssets': home/'.universal-modder/assets/owmc-mesh',
            'heroVoiceAssets': home/'.universal-modder/assets/ow1-zhcn-2016/thnu-full',
            'owTypes': home/'.universal-modder/toolchains/OWLib-source/TankLib/STU/Types',
            'ffmpeg': home/'AppData/Local/universal-modder/ffmpeg/bin/ffmpeg.exe',
            'displayLease': home/'.universal-modder/runtime/native-display-lease.json',
            'backups': home/'.universal-modder/backups',
        }
        current = config.PackPaths(ROOT, configuration={})
        for name, expected in legacy.items():
            with self.subTest(name=name):
                self.assertEqual(current.get(name), expected.resolve())
        self.assertEqual(current.native_allowed_paths(), {legacy[k].resolve() for k in ('owExecutable', 'owFallbackExecutable')})
        self.assertTrue(current.renderer_required())
        self.assertEqual(current.account_mode(), 'development-offline')
        if legacy['java'].is_file():
            from minecraft_launcher_lib.runtime import get_executable_path
            self.assertEqual(current.get('java'), Path(get_executable_path('java-runtime-delta', legacy['minecraft'])).resolve())


class ConfiguredPaths(WorkspaceFixture):
    def test_readonly_cli_preserves_unicode_paths_as_ascii_json_for_powershell(self):
        config.write_json(self.root/config.CONFIG, dict(schemaVersion=1,paths={'java':'含空格 Java/bin/java.exe'}))
        result = subprocess.run([sys.executable,'-B',str(TOOLS/'modpack/config.py'),'--get','java','--root',str(self.root),'--json'],
                                capture_output=True,text=True,encoding='ascii',timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(Path(json.loads(result.stdout)), self.root/'含空格 Java/bin/java.exe')
    def test_all_relative_values_follow_a_new_root_including_derived_private_paths(self):
        value = dict(schemaVersion=1, paths=dict(owExecutable='OW/target.exe', minecraft='MC', java='JRE/bin/java.exe',
                                                profile='profiles/main', privateAssets='local-only'))
        one = config.PackPaths(self.root/'one', configuration=value)
        two = config.PackPaths(self.root/'二号 root', configuration=value)
        for key in ('owExecutable','minecraft','java','profile','privateAssets','meshAssets','heroVoiceAssets'):
            self.assertEqual(one.get(key).relative_to(one.root), two.get(key).relative_to(two.root))
        self.assertEqual(two.get('meshAssets'), two.root/'local-only/owmc-mesh')
        self.assertEqual(two.native_allowed_paths(), {two.root/'OW/target.exe'})

    def test_pack_defaults_never_probe_another_users_private_home(self):
        self.file(config.MARKER, b'{}')
        paths = config.PackPaths(self.root)
        for name in ('python','java','privateAssets','meshAssets','heroVoiceAssets','owTypes','ffmpeg','displayLease','backups'):
            self.assertTrue(paths.get(name).is_relative_to(self.root), name)
        self.assertEqual(paths.account_mode(), 'development-offline')

    def test_unknown_credential_fields_are_refused_and_not_used(self):
        paths = config.PackPaths(self.root, configuration=dict(schemaVersion=1, account={'mode':'external','token':'not-a-real-token'}))
        with self.assertRaisesRegex(ValueError, '凭据'):
            paths.account_mode()


class AccountBoundary(WorkspaceFixture):
    def test_existing_offline_identity_is_preserved_with_empty_token(self):
        paths = config.PackPaths(self.root)
        path = self.file('minecraft-1.21.1/development-identity.json', b'{"username":"Lab","uuid":"fixture"}\n')
        before = path.read_bytes()
        options, offline = account.launch_options(paths)
        self.assertTrue(offline)
        self.assertEqual(options['token'], '')
        self.assertEqual(path.read_bytes(), before)

    def test_pack_requires_provider_and_does_not_create_an_offline_identity(self):
        self.file(config.MARKER, b'{}')
        paths = config.PackPaths(self.root,configuration=dict(schemaVersion=1,account={'mode':'external'}))
        with self.assertRaisesRegex(ValueError, '账号提供方'):
            account.launch_options(paths)
        self.assertFalse((self.root/'minecraft-1.21.1/development-identity.json').exists())

    def test_external_interface_uses_only_memory_and_hides_token_in_repr(self):
        self.file(config.MARKER, b'{}')
        session = account.AuthenticatedSession('Fixture', 'fixture-uuid', 'fixture-memory-only', time.time()+60, True)
        provider = Mock(session=Mock(return_value=session))
        before = set(self.root.rglob('*'))
        paths=config.PackPaths(self.root,configuration=dict(schemaVersion=1,account={'mode':'external'}))
        options, offline = account.launch_options(paths, provider)
        self.assertFalse(offline)
        self.assertEqual(options['userType'], 'msa')
        self.assertEqual(options['token'], 'fixture-memory-only')
        self.assertNotIn('fixture-memory-only', repr(session))
        self.assertEqual(set(self.root.rglob('*')), before)

    def test_expired_or_unverified_session_is_rejected(self):
        for expiry, ownership in ((0, True), (time.time()+60, False)):
            with self.subTest(expiry=expiry, ownership=ownership), self.assertRaises(ValueError):
                account.AuthenticatedSession('Fixture','uuid','fixture',expiry,ownership).options()


class OptionalAssets(WorkspaceFixture):
    def test_optional_sodium_does_not_allow_an_unverified_existing_binary(self):
        import render_optimization as renderer
        paths=config.PackPaths(self.root,configuration=dict(schemaVersion=1,rendererPolicy='optional-sodium'))
        self.file('profile/mods/'+renderer.NAME,b'unverified')
        with patch.object(renderer,'PROFILE',self.root/'profile'),patch.object(renderer,'paths',return_value=paths):
            with self.assertRaisesRegex(ValueError,'differs'):
                renderer.verify()

    def test_optional_sodium_still_rejects_conflicting_renderer(self):
        import render_optimization as renderer
        import zipfile
        paths=config.PackPaths(self.root,configuration=dict(schemaVersion=1,rendererPolicy='optional-sodium'))
        target=self.root/'profile/mods/fixture.jar';target.parent.mkdir(parents=True)
        with zipfile.ZipFile(target,'w') as archive:
            archive.writestr('fabric.mod.json','{"id":"embeddium"}')
        with patch.object(renderer,'PROFILE',self.root/'profile'),patch.object(renderer,'paths',return_value=paths):
            with self.assertRaisesRegex(ValueError,'Conflicting'):
                renderer.verify()
    def test_private_model_output_only_accepts_the_explicitly_configured_local_root(self):
        import pulse_bomb_assets as pulse
        paths = config.PackPaths(self.root,configuration=dict(schemaVersion=1,paths={'privateAssets':'private-assets'}))
        base = paths.get('privateAssets')
        with patch.object(pulse,'paths',return_value=paths):
            self.assertEqual(pulse.private_path(base/'model',base),base/'model')
            with self.assertRaises(ValueError):
                pulse.private_path(self.root/'outside',base)
    def test_absence_and_invalid_assets_warn_without_aborting_other_components(self):
        paths = config.PackPaths(self.root, configuration=dict(schemaVersion=1, paths={'privateAssets':'absent'}))
        callables = ('genji','mccree','feedback','chinese','skills','barrage','pulse')
        patches = [patch.object(resources, name, return_value=False) for name in callables]
        mocks = [p.start() for p in patches]
        self.addCleanup(lambda: [p.stop() for p in reversed(patches)])
        mocks[1].side_effect = FileNotFoundError('missing source')
        mocks[2].side_effect = ValueError('invalid SHA256; do not use')
        with patch.object(resources, 'paths', return_value=paths), patch('builtins.print'):
            report = resources.prepare_optional(self.root/'profile')
        self.assertEqual(len(report['warnings']), 9)
        self.assertTrue(all(not row['ready'] for row in report['components']))
        for mock in mocks:
            mock.assert_called_once()
        self.assertTrue((self.root/resources.REPORT).is_file())


class ShutdownInterpreters(WorkspaceFixture):
    def test_portable_python_supervisor_is_not_skipped_as_a_venv_redirector(self):
        import stop_passthrough_session as stop
        paths = config.PackPaths(self.root, configuration=dict(schemaVersion=1, paths={'python':'runtime/python/python.exe'}))
        process = Mock(info={'exe':str(paths.get('python')), 'cmdline':[str(paths.get('python')),str(self.root/'tools/launch_passthrough_session.py')]})
        with patch.object(stop,'ROOT',self.root), patch.object(stop,'paths',return_value=paths), \
             patch.object(stop.psutil,'process_iter',return_value=[process]):
            stop.stop_supervisor()
        process.terminate.assert_called_once()
        process.wait.assert_called_once_with(5)

    def test_original_venv_redirector_is_preserved_for_its_real_child_to_exit(self):
        import stop_passthrough_session as stop
        self.file('.venv/pyvenv.cfg', b'fixture')
        paths = config.PackPaths(self.root)
        process = Mock(info={'exe':str(paths.get('python')), 'cmdline':[str(paths.get('python')),str(self.root/'tools/launch_passthrough_session.py')]})
        with patch.object(stop,'ROOT',self.root), patch.object(stop,'paths',return_value=paths), \
             patch.object(stop.psutil,'process_iter',return_value=[process]):
            stop.stop_supervisor()
        process.terminate.assert_not_called()


class OutsideSandboxLab(WorkspaceFixture):
    def factory(self):
        package=self.root/'package'
        package.mkdir()
        config.write_json(package/config.MARKER,{'schemaVersion':1})
        path=package/config.MARKER
        config.write_json(package/'manifest.json',dict(components={'own':{'license':'fixture'}},files=[dict(
            path=config.MARKER,bytes=path.stat().st_size,sha256=config.sha256(path),component='own',license='fixture')]))
        return package

    def test_preparation_preserves_reference_and_factory_and_omits_private_packs(self):
        from render_optimization import NAME as sodium_name
        package=self.factory()
        raw=b'resourcePacks:["file/private"]\nrenderDistance:12\n'
        options=self.file('guest-passthrough-client/options.txt',raw)
        self.file('guest-passthrough-client/saves/Fixture/level.dat')
        self.file('guest-passthrough-client/resourcepacks/private/fixture.txt')
        self.file('guest-passthrough-client/launcher_accounts.json',b'fixture-do-not-read')
        sodium=self.file('guest-passthrough-client/mods/'+sodium_name)
        config.write_json(self.root/'passthrough-settings.json',first_run.DEFAULT_SETTINGS)
        backend=Mock(supervisors=Mock(return_value=[]),project_processes=Mock(return_value=[]))
        output=self.root/'data/relocated lab'
        with patch.object(prepare_lab,'verify_ow',return_value={}):
            result=prepare_lab.prepare(package,self.root,output,development_offline=True,without_sodium=True,backend=backend)
        self.assertFalse(result['gameStarted'])
        self.assertEqual(options.read_bytes(),raw)
        self.assertFalse((output/'data/profile/resourcepacks').exists())
        self.assertFalse((output/'data/profile/launcher_accounts.json').exists())
        self.assertFalse((output/'data/profile/mods'/sodium_name).exists())
        self.assertTrue(sodium.is_file())
        self.assertIn('resourcePacks:[]',(output/'data/profile/options.txt').read_text())
        self.assertTrue((Path(result['backup'])/'profile.zip').is_file())
        self.assertFalse(Path(result['backup']).is_relative_to(output))
        self.assertEqual(config.PackPaths(output).account_mode(),'development-offline')
        self.assertEqual(prepare_lab.verify_manifest(package)['privateFiles'],0)

    def test_preparation_requires_explicit_scope_and_never_overwrites_output(self):
        package=self.factory()
        output=self.root/'data/user files'
        sentinel=self.file('data/user files/sentinel',b'preserve')
        for flag in (False,True):
            with self.assertRaises(ValueError):
                prepare_lab.prepare(package,self.root,output,development_offline=flag)
        self.assertEqual(sentinel.read_bytes(),b'preserve')

    def test_live_reference_refuses_preparation_without_touching_profiles(self):
        package=self.factory()
        backend=Mock(supervisors=Mock(return_value=[Mock()]))
        with patch.object(prepare_lab,'verify_ow',return_value={}), self.assertRaisesRegex(ValueError,'仍在运行'):
            prepare_lab.prepare(package,self.root,self.root/'data/new lab',development_offline=True,backend=backend)
        self.assertFalse((self.root/'research').exists())

    def test_relocated_lab_uses_the_bundled_client_and_assets(self):
        package=self.factory()
        relative='game/Overwatch Beta 0.8.0.24919/GameClientApp.patched.exe'
        self.file('package/'+relative,b'inert client fixture')
        config.write_json(package/'manifest.json',dict(clientSummary={'executable':relative}))
        self.file('guest-passthrough-client/options.txt',b'resourcePacks:[]\n')
        config.write_json(self.root/'passthrough-settings.json',first_run.DEFAULT_SETTINGS)
        backend=Mock(supervisors=Mock(return_value=[]),project_processes=Mock(return_value=[]))
        output=self.root/'data/bundled lab'
        with patch.object(prepare_lab,'verify_manifest',return_value={'privateFiles':1,'clientFiles':1}), \
             patch.object(prepare_lab,'verify_ow',return_value={}) as guard:
            result=prepare_lab.prepare(package,self.root,output,development_offline=True,bundled_private=True,backend=backend)
        self.assertTrue(result['bundledClientUsed'])
        self.assertTrue(result['bundledPrivateAssetsUsed'])
        self.assertFalse(result['gameStarted'])
        configured=config.PackPaths(output)
        self.assertEqual(configured.get('owExecutable'),output/relative)
        self.assertEqual(configured.get('meshAssets'),output/'private-assets/owmc-mesh')
        guard.assert_called_with(output/relative)


class RelocatedLaunchChain(WorkspaceFixture):
    def test_relocated_source_builds_command_with_no_games_no_private_assets_and_no_old_root(self):
        # Copy project-authored source only. Every exe/jar below is inert fixture
        # content, never a game file, credential, save, model or audio recording.
        first = self.root/'initial root'
        final = self.root/'迁移后的 root'
        first.mkdir()
        for source in source_closure(ROOT):
            target = first/source.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        config.write_json(first/config.MARKER, dict(schemaVersion=1))
        config.write_json(first/config.CONFIG, dict(schemaVersion=1,
            account={'mode':'development-offline'}, paths=dict(python='portable/python.exe', java='jre/bin/java.exe',
                owExecutable='OW/GameClientApp.patched.exe', minecraft='MC', profile='profiles/main',
                privateAssets='no-assets')))
        config.write_json(first/'passthrough-settings.json', first_run.DEFAULT_SETTINGS)
        first.rename(final)
        code = r'''
from pathlib import Path
import sys,json,zipfile
from unittest.mock import patch
root=Path(sys.argv[1]);sys.path.insert(0,str(root/'tools'))
from modpack.config import paths
cfg=paths();game=cfg.get('minecraft');version='fabric-loader-0.19.5-1.21.1'
def file(path,data=b'fixture'):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
file(cfg.get('java'));file(cfg.get('python'));file(cfg.get('owExecutable'))
file(game/'versions'/version/(version+'.json'),b'{}')
file(game/'development-identity.json',b'{"username":"Fixture","uuid":"fixture"}')
library=game/'libraries/fixture.jar';file(library)
for path,id in [(root/'guest/build/libs/owmc-guest-0.1.0.jar','owmcguest'),(game/'mods/fabric-api-fixture.jar','fabric-api')]:
 path.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(path,'w') as z:z.writestr('fabric.mod.json',json.dumps({'id':id}))
import launch_minecraft as mc
def command(version,game,options):
 assert options['token']=='' and options['executablePath']==str(cfg.get('java'))
 return [options['executablePath'],'-cp',str(library),'Fixture','--gameDir',str(game),'--clientId','${clientid}','--xuid','${xuid}']
mc.get_minecraft_command=command
import launch_passthrough_guest as guest
import launch_passthrough_session as session
import stop_passthrough_session as stop
import native_normal_close, native_display_mode, observe_overwatch, configure_passthrough, minecraft_shaders, render_optimization
with patch('subprocess.Popen',side_effect=AssertionError('no process allowed')):
 result=guest.prepare()
assert session.EXE==native_normal_close.EXE==native_display_mode.EXE==cfg.get('owExecutable')
assert observe_overwatch.ALLOWED_PATHS=={cfg.get('owExecutable')}
assert session.PROFILE==stop.PROFILE==guest.PROFILE==minecraft_shaders.PROFILE==render_optimization.PROFILE==cfg.get('profile')
assert configure_passthrough.SAVES==cfg.get('profile')/'saves'
assert result[0]==str(cfg.get('java')) and result[result.index('--gameDir')+1]==str(cfg.get('profile'))
for prop,key in [('privateAssetsDirectory','privateAssets'),('meshDirectory','meshAssets'),('heroVoiceDirectory','heroVoiceAssets')]:
 assert '-Dowmc.'+prop+'='+str(cfg.get(key)) in result
assert '${clientid}' not in result and '${xuid}' not in result
assert all(sys.argv[2] not in item for item in result)
report=json.loads((root/'research/launcher/resource-status.json').read_text(encoding='utf-8'))
assert len(report['warnings'])==9
print(json.dumps(dict(configured=True,warnings=len(report['warnings']),gameStarted=False,java=result[0],profile=result[result.index('--gameDir')+1])))
'''
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8',
                           TEMP=str(ROOT/'data/tmp'), TMP=str(ROOT/'data/tmp'))
        result = subprocess.run([sys.executable,'-B','-c',code,str(final),str(first)],
                                capture_output=True,text=True,encoding='utf-8',env=environment,timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr[-2200:])
        report = json.loads(result.stdout.splitlines()[-1])
        self.assertFalse(report['gameStarted'])
        self.assertEqual(report['warnings'], 9)

    def test_java_receives_configured_paths_and_missing_assets_are_ordinary_paths(self):
        java = config.PackPaths(ROOT).get('java')
        javac = java.with_name('javac.exe')
        if not javac.is_file():
            self.skipTest('Java 21 compiler unavailable for standalone path fixture')
        source = self.file('PrivateAssetPathsCheck.java', b'''package lab.owmcguest;
import java.nio.file.*;
public class PrivateAssetPathsCheck {
 public static void main(String[] a) {
  System.setProperty("owmc.privateAssetsDirectory",a[0]);
  if(!PrivateAssetPaths.assets().equals(Path.of(a[0]).toAbsolutePath()))throw new AssertionError("assets");
  if(!PrivateAssetPaths.meshes().equals(Path.of(a[0],"owmc-mesh").toAbsolutePath()))throw new AssertionError("meshes");
  if(Files.exists(PrivateAssetPaths.voices()))throw new AssertionError("fixture must be absent");
  System.setProperty("owmc.meshDirectory",a[1]);
  if(!PrivateAssetPaths.meshes().equals(Path.of(a[1]).toAbsolutePath()))throw new AssertionError("override");
 }
}''')
        classes = self.root/'classes'
        compile = subprocess.run([str(javac),'-encoding','UTF-8','-d',str(classes),
                                  str(ROOT/'guest/src/client/java/lab/owmcguest/PrivateAssetPaths.java'),str(source)],
                                 capture_output=True,text=True,encoding='utf-8',timeout=20)
        self.assertEqual(compile.returncode, 0, compile.stderr)
        run = subprocess.run([str(java),'-cp',str(classes),'lab.owmcguest.PrivateAssetPathsCheck',
                              str(self.root/'absent assets'),str(self.root/'other meshes')],
                             capture_output=True,text=True,encoding='utf-8',timeout=20)
        self.assertEqual(run.returncode,0,run.stderr)


if __name__ == '__main__':
    unittest.main()
