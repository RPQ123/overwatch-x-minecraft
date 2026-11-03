"""Offline pack/first-run fixtures; no games, network, private assets or C: writes."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import zipfile

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
from modpack import build, config, first_run, install
import project_launcher as launcher


class TemporaryRoot(unittest.TestCase):
    def setUp(self):
        temporary = TOOLS.parent / 'data/tmp'
        temporary.mkdir(parents=True, exist_ok=True)
        directory = tempfile.TemporaryDirectory(dir=temporary)
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    def file(self, relative, data=b'fixture'):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path


class ConfigurationFixtures(TemporaryRoot):
    def test_development_paths_preserve_existing_layout(self):
        paths = config.PackPaths(self.root)
        self.assertEqual(paths.get('python'), self.root / '.venv/Scripts/python.exe')
        self.assertEqual(paths.get('owExecutable'), self.root / config.OW_RELATIVE)
        self.assertEqual(paths.launch_blockers(), [])

    def test_pack_paths_relocate_without_using_build_machine(self):
        self.file(config.MARKER, b'{}')
        paths = config.PackPaths(self.root)
        self.assertEqual(paths.get('python'), self.root / 'runtime/python/python.exe')
        self.assertEqual(paths.get('java'), self.root / 'runtime/java/bin/java.exe')
        self.assertTrue(paths.launch_blockers())

    def test_external_ow_is_resolved_without_legacy_path_blocker(self):
        external = self.root.parent / 'external.exe'
        config.write_json(self.root / config.CONFIG, {'schemaVersion': 1, 'paths': {'owExecutable': str(external)}})
        paths = config.PackPaths(self.root)
        self.assertEqual(paths.get('owExecutable'), external)
        self.assertEqual(paths.launch_blockers(), [])

    def test_write_paths_reject_absolute_and_parent_escape(self):
        for value in ('../escape.json', str(self.root / 'absolute.json'), ''):
            with self.subTest(value=value), self.assertRaises(ValueError):
                config.local_path(self.root, value)

    def test_config_rejects_bad_schema_and_path_types(self):
        for value in ({'schemaVersion': 9}, {'schemaVersion': 1, 'paths': []}):
            config.write_json(self.root / config.CONFIG, value)
            with self.assertRaises(ValueError):
                config.PackPaths(self.root)
        config.write_json(self.root / config.CONFIG, {'schemaVersion': 1, 'paths': {'python': 1}})
        with self.assertRaises(ValueError):
            config.PackPaths(self.root).get('python')

    def test_pack_ready_flag_cannot_bypass_backend_gate(self):
        self.file(config.MARKER, b'{"ready":true,"backendIntegration":"ready"}')
        config.write_json(self.root/config.CONFIG,dict(schemaVersion=1,account={'mode':'external'}))
        self.assertTrue(config.PackPaths(self.root).launch_blockers())


class FirstRunFixtures(TemporaryRoot):
    def test_wrong_ow_hash_does_not_write_any_configuration(self):
        exe = self.file('unverified.exe')
        with self.assertRaisesRegex(ValueError, 'SHA256'):
            first_run.prepare(self.root, exe, 'New World')
        self.assertFalse((self.root / 'config').exists())
        self.assertFalse((self.root / 'passthrough-settings.json').exists())

    def test_configure_creates_only_settings_not_a_world(self):
        exe = self.file('owned.exe')
        with patch.object(first_run, 'OW_SHA256', config.sha256(exe)):
            result = first_run.prepare(self.root, exe, 'New World', expected_config='')
        settings = config.read_json(self.root / 'passthrough-settings.json')
        self.assertEqual(settings['worldName'], 'New World')
        self.assertTrue(settings['createWorld'])
        self.assertFalse(result['worldCreated'])
        self.assertFalse(result['gameLaunched'])
        self.assertFalse((self.root / 'guest-passthrough-client/saves').exists())
        self.assertEqual(config.PackPaths(self.root).overrides['owExecutable'], 'owned.exe')

    def test_existing_settings_are_byte_preserved(self):
        raw = b'{"schemaVersion":1, "worldName":"Existing", "createWorld":false}\n'
        path = self.file('passthrough-settings.json', raw)
        with patch.object(first_run, 'verify_ow', return_value={'sha256': 'fixture'}):
            result = first_run.prepare(self.root, self.root / 'owned.exe', 'Another Name')
        self.assertEqual(path.read_bytes(), raw)
        self.assertEqual(result['worldName'], 'Existing')

    def test_changed_config_is_not_overwritten(self):
        config.write_json(self.root / config.CONFIG, {'schemaVersion': 1})
        old = (self.root / config.CONFIG).read_bytes()
        with patch.object(first_run, 'verify_ow', return_value={}), self.assertRaisesRegex(ValueError, '其他窗口'):
            first_run.prepare(self.root, self.root / 'owned.exe', 'World', expected_config='wrong')
        self.assertEqual((self.root / config.CONFIG).read_bytes(), old)

    def test_invalid_world_name_has_no_side_effects(self):
        with self.assertRaises(ValueError):
            first_run.prepare(self.root, self.root / 'owned.exe', '../bad')
        self.assertFalse((self.root / 'config').exists())

    def test_environment_is_offline_and_reports_low_resources(self):
        with patch.object(first_run.psutil, 'virtual_memory', return_value=SimpleNamespace(total=4 * 1024**3)), \
             patch.object(first_run.shutil, 'disk_usage', return_value=SimpleNamespace(free=2 * 1024**3)), \
             patch.object(first_run.platform, 'system', return_value='Windows'), \
             patch.object(first_run.platform, 'release', return_value='11'), \
             patch.object(first_run.platform, 'machine', return_value='AMD64'), \
             patch.object(first_run.subprocess, 'run') as run:
            result = first_run.environment(self.root, gpu=False)
        self.assertFalse(result['ok'])
        run.assert_not_called()

    def test_readonly_status_does_not_create_files_or_trust_lock_presence(self):
        self.file('config/installation-sha256.json', b'{}')
        before = set(self.root.rglob('*'))
        value = first_run.status(self.root)
        self.assertTrue(value['minecraftLockPresent'])
        self.assertFalse(value['installationVerified'])
        self.assertEqual(before, set(self.root.rglob('*')))


class InstallFixtures(TemporaryRoot):
    def test_install_requires_saved_verified_ow_before_network(self):
        with patch.object(first_run, 'environment', return_value={'ok': True}), \
             patch.object(install, 'fetch') as fetch, self.assertRaisesRegex(ValueError, '保存配置'):
            install.install(self.root)
        fetch.assert_not_called()

    def test_install_success_uses_official_metadata_and_never_launches(self):
        config.write_json(self.root / config.CONFIG, {'schemaVersion': 1})
        self.file('guest/build/libs/owmc-guest-0.1.0.jar')
        self.file('minecraft-1.21.1/mods/fabric-api-0.116.17+1.21.1.jar')
        base = {'id': install.MC}
        fabric = {'id': install.PROFILE, 'inheritsFrom': install.MC, 'libraries': []}
        base_bytes = json.dumps(base).encode()
        fabric_bytes = json.dumps(fabric).encode()
        catalog = {'versions': [{'id': install.MC, 'url': 'https://piston-meta.mojang.com/fixture',
                                 'sha1': hashlib.sha1(base_bytes).hexdigest()}]}
        responses = [(catalog, b'{}'), (base, base_bytes), (fabric, fabric_bytes)]
        with patch.object(first_run, 'environment', return_value={'ok': True}), \
             patch.object(first_run, 'verify_ow', return_value={}), \
             patch.object(install, 'official_json', side_effect=responses) as fetch, \
             patch('minecraft_launcher_lib.install.install_minecraft_version') as mc_install, \
             patch.object(install, 'verify_official_files', return_value=[]), \
             patch.object(launcher.subprocess, 'Popen') as spawn:
            result = install.install(self.root, report=lambda _: None)
        self.assertFalse(result['gameLaunched'])
        spawn.assert_not_called()
        self.assertEqual([c.args[0] for c in mc_install.call_args_list], [install.MC, install.PROFILE])
        self.assertEqual(fetch.call_args_list[1].args[1], catalog['versions'][0]['sha1'])
        self.assertTrue((self.root / 'config/installation-sha256.json').is_file())
        self.assertTrue((self.root / 'guest-passthrough-client/mods/owmc-guest-0.1.0.jar').is_file())

    def test_download_plan_performs_no_network(self):
        with patch.object(install, 'fetch') as fetch:
            result = install.download_plan()
        fetch.assert_not_called()
        self.assertFalse(result['downloadsPerformed'])
        self.assertIn('SHA1', result['upstreamIntegrity'])

    def test_unofficial_urls_and_credentials_are_refused(self):
        for url in ('http://meta.fabricmc.net/a', 'https://meta.fabricmc.net.evil.test/a',
                    ('https://user' + '@' + 'meta.fabricmc.net/a'), 'file:///private', 'https://meta.fabricmc.net:444/a'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                install.official_url(url)

    def test_metadata_sha1_mismatch_is_a_failure(self):
        with patch.object(install, 'fetch', return_value=b'{}'), self.assertRaisesRegex(ValueError, 'SHA1'):
            install.official_json(install.VERSION_MANIFEST, '0' * 40)

    def test_existing_install_is_not_overwritten_or_downloaded(self):
        self.file('minecraft-1.21.1/versions/existing.json')
        with patch.object(first_run, 'environment', return_value={'ok': True}), \
             patch.object(install, 'fetch') as fetch, self.assertRaisesRegex(ValueError, '已有'):
            install.install(self.root)
        fetch.assert_not_called()

    def test_local_sha256_lock_detects_modification_and_missing_file(self):
        path = self.file('minecraft-1.21.1/versions/fixture.jar', b'clean')
        row = dict(path='versions/fixture.jar', bytes=5, sha256=config.sha256(path))
        config.write_json(self.root / 'config/installation-sha256.json',
                          dict(schemaVersion=1, minecraft=install.MC, fabricLoader=install.LOADER, files=[row]))
        self.assertTrue(install.verify_installation(self.root)['installationVerified'])
        path.write_bytes(b'other')
        with self.assertRaisesRegex(ValueError, 'SHA256'):
            install.verify_installation(self.root)
        path.unlink()
        with self.assertRaises(ValueError):
            install.verify_installation(self.root)

    def test_lock_cannot_read_outside_installation(self):
        config.write_json(self.root / 'config/installation-sha256.json',
                          dict(schemaVersion=1, minecraft=install.MC, fabricLoader=install.LOADER,
                               files=[dict(path='../secret', bytes=0, sha256='0' * 64)]))
        with self.assertRaisesRegex(ValueError, '超出'):
            install.verify_installation(self.root)

    def test_required_client_assets_libraries_are_verified_before_sha256_pin(self):
        game = self.root / 'minecraft-1.21.1'
        def artifact(relative, data):
            path = self.file('minecraft-1.21.1/' + relative, data)
            return dict(path=relative.removeprefix('libraries/'), sha1=hashlib.sha1(data).hexdigest(),
                        size=len(data), url='https://libraries.minecraft.net/fixture')
        client = artifact('versions/1.21.1/1.21.1.jar', b'client')
        library = artifact('libraries/group/artifact.jar', b'lib')
        asset = b'asset'
        digest = hashlib.sha1(asset).hexdigest()
        artifact('assets/objects/' + digest[:2] + '/' + digest, asset)
        index = json.dumps({'objects': {'name': {'hash': digest, 'size': len(asset)}}}).encode()
        index_meta = artifact('assets/indexes/fixture.json', index)
        index_meta['id'] = 'fixture'
        base = dict(downloads={'client': client}, assetIndex=index_meta, libraries=[{'downloads': {'artifact': library}}])
        rows = install.verify_official_files(game, base, {'libraries': []})
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(r['officialSha1'] and len(r['sha256']) == 64 for r in rows))
        (game / 'libraries/group/artifact.jar').unlink()
        with self.assertRaisesRegex(ValueError, '缺少'):
            install.verify_official_files(game, base, {'libraries': []})


class BuildFixtures(TemporaryRoot):
    def test_secret_scanner_does_not_treat_getmask_documentation_as_api_key(self):
        self.assertIsNone(build.SECRET.search(b'getmask-rgba-' + b'font-reference-' * 5))
        self.assertIsNotNone(build.SECRET.search(b'token="' + b'sk-' + b'a' * 48 + b'"'))

    def builder(self):
        self.pack_index = getattr(self, 'pack_index', 0) + 1
        destination = self.root / f'dist/OWMC-fixture-{self.pack_index}'
        destination.mkdir(parents=True)
        builder = build.Builder(self.root, destination, 'fixture')
        builder.component('own', build.INTERNAL, 'fixture')
        return builder

    def manifest(self, builder):
        config.write_json(builder.destination / 'manifest.json',
                          dict(files=list(builder.rows.values()), components=builder.components))

    def test_clean_manifest_has_size_hash_license_and_checks_every_file(self):
        builder = self.builder()
        builder.copy(self.file('authored.py', b'print(1)'), 'tools/authored.py', 'own')
        self.manifest(builder)
        self.assertEqual(build.verify_manifest(builder.destination)['files'], 1)
        self.assertEqual(builder.rows['tools/authored.py']['license'], build.INTERNAL)
        (builder.destination / 'tools/authored.py').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, '完整性'):
            build.verify_manifest(builder.destination)

    def test_unlisted_private_file_causes_audit_failure(self):
        builder = self.builder()
        self.manifest(builder)
        (builder.destination / 'secret.txt').write_text('private')
        with self.assertRaisesRegex(ValueError, '清单不一致'):
            build.verify_manifest(builder.destination)

    def test_listed_game_files_and_resource_packs_are_rejected(self):
        for relative in ('overwatch-2015/client.exe', 'guest-passthrough-client/saves/World/level.dat',
                         'minecraft-1.21.1/versions/client.jar', 'guest-passthrough-client/resourcepacks/private.zip'):
            with self.subTest(relative=relative):
                builder = self.builder()
                builder.copy(self.file('source-' + str(len(relative))), relative, 'own')
                self.manifest(builder)
                with self.assertRaises(ValueError):
                    build.verify_manifest(builder.destination)

    def test_duplicate_copy_and_escape_are_rejected(self):
        builder = self.builder()
        source = self.file('authored.py')
        builder.copy(source, 'tools/a.py', 'own')
        with self.assertRaisesRegex(ValueError, '重复'):
            builder.copy(source, 'tools/a.py', 'own')
        with self.assertRaises(ValueError):
            builder.copy(source, '../escape.py', 'own')

    def test_concurrent_artifact_update_cannot_finish_with_a_clean_manifest(self):
        builder = self.builder()
        source = self.file('authored.py', b'old')
        original = build.shutil.copyfile
        def racing_copy(src, dst):
            result = original(src, dst)
            src.write_bytes(b'new-and-different-size')
            return result
        with patch.object(build.shutil, 'copyfile', side_effect=racing_copy), self.assertRaisesRegex(ValueError, '源文件被更新'):
            builder.copy(source, 'tools/authored.py', 'own')
        self.assertFalse((builder.destination / 'manifest.json').exists())

    def test_existing_output_is_preserved(self):
        builder = self.builder()
        sentinel = builder.destination / 'sentinel'
        sentinel.write_text('preserve')
        with self.assertRaises(FileExistsError):
            builder.stage(None, None, False)
        self.assertEqual(sentinel.read_text(), 'preserve')

    def test_partial_build_is_marked_and_cannot_masquerade_as_development(self):
        destination = self.root / 'dist/OWMC-incomplete'
        builder = build.Builder(self.root, destination, 'fixture')
        with patch.object(build, 'source_closure', side_effect=ValueError('fixture build failure')):
            with self.assertRaises(ValueError):
                builder.stage(None, None, False)
        self.assertTrue(config.PackPaths(destination).packaged)
        self.assertFalse((destination / 'manifest.json').exists())
        self.assertTrue(config.PackPaths(destination).launch_blockers())

    def test_java_accepts_original_title_case_gpl_and_keeps_exception_notice(self):
        self.file('java/bin/java.exe')
        self.file('java/lib/modules')
        self.file('java/release', b'JAVA_VERSION="21.0.7"')
        self.file('java/legal/java.base/LICENSE', b'The GNU General Public License (GPL)\nVersion 2')
        self.file('java/legal/java.base/ADDITIONAL_LICENSE_INFO', b'GNU Classpath Exception')
        builder = self.builder()
        builder.java(self.root / 'java')
        self.assertIn('runtime/java/legal/java.base/ADDITIONAL_LICENSE_INFO', builder.rows)
        self.assertIn('Classpath-exception', builder.components['openjdk']['license'])

    def test_java_rejects_missing_runtime_binary(self):
        with self.assertRaisesRegex(ValueError, '缺少 java.exe'):
            self.builder().java(self.root / 'java')

    def test_guest_archive_rejects_extracted_media(self):
        path = self.root / 'guest.jar'
        for media in (False, True):
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr('fabric.mod.json', '{"id":"owmcguest"}')
                archive.writestr('assets/extracted.ogg' if media else 'lab/Own.class', b'fixture')
            if media:
                with self.assertRaisesRegex(ValueError, '媒体'):
                    build.validate_guest(path)
            else:
                build.validate_guest(path)

    def test_build_imports_do_not_execute_source(self):
        for name in build.SEEDS:
            self.file('tools/' + name + '.py', b'raise RuntimeError("do not import")')
        closure = build.source_closure(self.root)
        self.assertEqual(len(closure), len(build.SEEDS))


class LauncherIntegrationFixtures(TemporaryRoot):
    @unittest.skipUnless(sys.platform == 'win32', 'Real Windows Tk layout smoke fixture')
    def test_real_tk_first_run_layout_has_no_overlap_or_game_actions(self):
        import tkinter as tk
        import shutil
        self.file(config.MARKER, b'{}')
        backend = launcher.SessionBackend(self.root)
        backend.snapshot = Mock(return_value={'settings': {}, 'status': {}, 'supervisorPids': []})
        backend.spawn = Mock(side_effect=AssertionError('UI smoke must not spawn any action'))
        # This sandbox's Tcl cannot resolve the C: installation even though
        # Python can read it. Copy only Tcl/Tk scripts into this fixture's D:
        # directory, just as the real portable build does; never alter C:.
        scripts = self.root / 'tk-scripts'
        for folder in ('tcl8.6', 'tk8.6'):
            shutil.copytree(Path(sys.base_prefix) / 'tcl' / folder, scripts / folder)
        environment = patch.dict(os.environ, {'TCL_LIBRARY': str(scripts / 'tcl8.6'),
                                              'TK_LIBRARY': str(scripts / 'tk8.6')})
        environment.start()
        self.addCleanup(environment.stop)
        window = None
        ui = None
        try:
            window = tk.Tk()
            self.assertNotEqual(launcher.NamedMutex(self.root, 'ui').name,
                                launcher.NamedMutex(launcher.ROOT, 'ui').name)
            ui = launcher.LauncherUI(window, backend)
            self.assertEqual(ui.page, 'setup')
            receipt = {'requestId': 'fixture', 'phase': 'succeeded', 'action': 'setup-check',
                       'result': {'ok': True, 'checks': [dict(name=name, detail='准备检查 ' * 20)
                                                        for name in ('系统', '内存', '磁盘', 'Python', '显卡')]}}
            ui.first_run.completed(0, 'fixture', receipt)
            window.update_idletasks()
            checks = ui.canvas.bbox(ui.first_run.checks)
            self.assertLess(checks[3], 246, checks)
            self.assertLessEqual(ui.canvas.bbox(ui.first_run.note)[3], 508)
            self.assertEqual(ui.first_run.ow_entry.winfo_width(), 622)
            for button in ui.first_run.buttons:
                left, top, right, bottom = ui.canvas.bbox(button.shape)
                self.assertGreaterEqual(left, 0)
                self.assertLessEqual(right, ui.WIDTH)
                self.assertLessEqual(bottom, ui.HEIGHT)
            ui.show_page('main')
            self.assertFalse(ui.first_run.ow_entry.winfo_ismapped())
            ui.show_page('settings')
            ui.show_page('setup')
            backend.spawn.assert_not_called()
        finally:
            if ui is not None:
                ui.closed = True
            if window is not None:
                try:
                    window.destroy()
                except tk.TclError:
                    pass

    def test_pack_blocks_start_before_any_process_spawn(self):
        self.file(config.MARKER, b'{}')
        config.write_json(self.root/config.CONFIG,dict(schemaVersion=1,account={'mode':'external'}))
        config.write_json(self.root / 'passthrough-settings.json', first_run.DEFAULT_SETTINGS)
        backend = launcher.SessionBackend(self.root)
        with patch.object(backend, 'supervisors', return_value=[]), patch.object(backend, 'spawn') as spawn:
            with self.assertRaisesRegex(ValueError, 'MC 账号'):
                backend.start(self.root / 'start.log')
        spawn.assert_not_called()

    def test_install_refuses_live_project_before_network(self):
        backend = launcher.SessionBackend(self.root)
        with patch.object(backend, 'supervisors', return_value=[Mock()]), patch.object(install, 'install') as download:
            with self.assertRaisesRegex(ValueError, '关闭游戏'):
                launcher.execute_action(backend, 'setup-install', self.root / 'install.log')
        download.assert_not_called()

    def test_pack_stop_still_delegates_to_the_existing_strict_shutdown(self):
        self.file(config.MARKER, b'{}')
        backend = launcher.SessionBackend(self.root)
        with patch.object(backend, 'checked_command', return_value={'exitCode': 0}) as checked:
            backend.stop(self.root / 'stop.log')
        self.assertEqual(Path(checked.call_args.args[0][-1]), self.root / 'tools/stop_passthrough_session.py')


if __name__ == '__main__':
    unittest.main()
