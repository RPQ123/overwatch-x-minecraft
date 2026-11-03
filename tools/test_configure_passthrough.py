"""Configuration conflict fixtures; only temporary directories are written."""
import contextlib
import io
import json
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import configure_passthrough as configure


class ConfigurationTests(unittest.TestCase):
    def test_f6_is_preserved_and_reserved_keys_are_rejected(self):
        self.assertEqual(configure.validate_flight_key('F6'), 'F6')
        self.assertEqual(configure.validate_flight_key('f6'), 'F6')
        for key in ('F7', 'F8', 'F9', 'F10', 'F11'):
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, '不能兼作飞行键'):
                configure.validate_flight_key(key)

    def run_fixture(self, settings, args):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        path = root / 'settings.json'
        path.write_text(json.dumps(settings), encoding='utf-8')
        saves = root / 'saves'
        saves.mkdir()
        self.addCleanup(patch.stopall)
        patch.object(configure, 'SETTINGS', path).start()
        patch.object(configure, 'SAVES', saves).start()
        patch('sys.argv', ['configure_passthrough.py', *args]).start()
        return path, saves

    def test_legacy_conflict_does_not_silently_migrate_on_graphics_edit(self):
        path, _ = self.run_fixture({'schemaVersion': 1, 'flightKey': 'F9', 'worldName': 'fixture'}, ['--resolution', '1080p'])
        before = path.read_bytes()
        with self.assertRaisesRegex(ValueError, '原设置不会自动迁移'):
            configure.main()
        self.assertEqual(path.read_bytes(), before)

    def test_explicit_f6_can_migrate_without_losing_unrelated_settings(self):
        path, _ = self.run_fixture({'schemaVersion': 1, 'flightKey': 'F9', 'worldName': 'fixture',
                                    'worldSeed': -490526775015596785, 'dayNightCycle': True}, ['--flight-key', 'F6'])
        with contextlib.redirect_stdout(io.StringIO()):
            configure.main()
        value = json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(value['flightKey'], 'F6')
        self.assertEqual(value['worldSeed'], -490526775015596785)
        self.assertTrue(value['dayNightCycle'])

    def test_cli_reserved_key_is_refused_before_write(self):
        path, _ = self.run_fixture({'schemaVersion': 1, 'flightKey': 'F6'}, ['--flight-key', 'F7'])
        before = path.read_bytes()
        stderr=io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as error:
            configure.main()
        self.assertEqual(error.exception.code, 2)
        self.assertIn('不能兼作飞行键',stderr.getvalue())
        self.assertEqual(path.read_bytes(), before)

    def test_new_world_preserves_seed_and_does_not_touch_live_world(self):
        path, saves = self.run_fixture({'schemaVersion': 1, 'flightKey': 'F6', 'worldSeed': -490526775015596785,
                                        'worldName': 'Current'}, ['--new-world', 'Fixture New World'])
        with contextlib.redirect_stdout(io.StringIO()):
            configure.main()
        value = json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(value['worldName'], 'Fixture New World')
        self.assertTrue(value['createWorld'])
        self.assertEqual(value['worldSeed'], -490526775015596785)
        self.assertEqual(list(saves.iterdir()), [])

    def test_stale_settings_editor_cannot_overwrite_a_new_configuration(self):
        path, _ = self.run_fixture({'schemaVersion': 1, 'flightKey': 'F6', 'renderDistance': 15},
                                   ['--resolution', '1080p', '--expected-settings-sha256', '0' * 64])
        before = path.read_bytes()
        with self.assertRaisesRegex(ValueError, '没有覆盖新设置'):
            configure.main()
        self.assertEqual(path.read_bytes(), before)

    def test_matching_editor_revision_can_save_without_losing_other_fields(self):
        path, _ = self.run_fixture({'schemaVersion': 1, 'flightKey': 'F6', 'worldName': 'fixture', 'worldSeed': 42}, [])
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        with patch('sys.argv', ['configure_passthrough.py', '--resolution', '1080p', '--expected-settings-sha256', digest]), \
             contextlib.redirect_stdout(io.StringIO()):
            configure.main()
        value = json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual((value['width'], value['height']), (1920, 1080))
        self.assertEqual(value['worldSeed'], 42)

    def test_gui_entry_uses_shared_action_owner_instead_of_opening_directly(self):
        self.run_fixture({'schemaVersion': 1, 'flightKey': 'F6'}, ['--gui'])
        import project_launcher
        with patch.object(project_launcher, 'run_action', return_value=0) as action, patch.object(configure, 'gui') as gui:
            self.assertEqual(configure.main(), 0)
        gui.assert_not_called()
        self.assertEqual(action.call_args.args[1], 'settings')

    def test_coordinated_gui_child_does_not_recurse_into_another_owner(self):
        self.run_fixture({'schemaVersion': 1, 'flightKey': 'F6'}, ['--gui', '--settings-owned'])
        import project_launcher
        with patch.object(project_launcher, 'run_action') as action, patch.object(configure, 'gui', return_value=None) as gui:
            configure.main()
        gui.assert_called_once()
        action.assert_not_called()


if __name__ == '__main__':
    unittest.main()
