"""Bounded client discovery and picker fallback; never executes fixture EXEs."""
from __future__ import annotations
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock,patch

TOOLS=Path(__file__).resolve().parents[1];sys.path.insert(0,str(TOOLS))
from modpack import client,config


class ClientDiscovery(unittest.TestCase):
    def setUp(self):
        temporary=TOOLS.parent/'data/tmp';temporary.mkdir(parents=True,exist_ok=True)
        directory=tempfile.TemporaryDirectory(dir=temporary)
        self.addCleanup(directory.cleanup);self.base=Path(directory.name);self.root=self.base/'OWMC-1.0.0'
        self.root.mkdir();self.data=b'inert fixture, not a game';self.pin=hashlib.sha256(self.data).hexdigest()

    def executable(self,folder,data=None):
        p=folder/'GameClientApp.patched.exe';p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(self.data if data is None else data);return p

    def test_game_folder_takes_priority_over_sibling_and_common_locations(self):
        expected=self.executable(self.root/'game'/client.FOLDER)
        self.executable(self.root.parent/client.FOLDER)
        self.executable(self.base/'drive/Games'/client.FOLDER)
        self.assertEqual(client.discover(self.root,drives=[self.base/'drive'],expected_sha256=self.pin),expected)

    def test_game_contents_directly_under_game_are_also_accepted(self):
        expected=self.executable(self.root/'game')
        self.assertEqual(client.discover(self.root,drives=[],expected_sha256=self.pin),expected)

    def test_wrong_hash_is_ignored_and_verified_sibling_is_found(self):
        self.executable(self.root/'game'/client.FOLDER,b'wrong')
        expected=self.executable(self.root.parent/client.FOLDER)
        self.assertEqual(client.discover(self.root,drives=[],expected_sha256=self.pin),expected)

    def test_common_drive_position_is_found_without_recursing_unrelated_trees(self):
        expected=self.executable(self.base/'drive/Games'/client.FOLDER)
        self.executable(self.base/'drive/unrelated/deep'/client.FOLDER)
        self.assertEqual(client.discover(self.root,drives=[self.base/'drive'],expected_sha256=self.pin),expected)

    def test_picker_is_only_called_after_discovery_fails_and_result_is_hash_checked(self):
        chosen=self.executable(self.base/'chosen'/client.FOLDER)
        picker=Mock(return_value=str(chosen))
        self.assertEqual(client.choose(self.root,picker=picker,allow_picker=True,drives=[],expected_sha256=self.pin),chosen)
        picker.assert_called_once()
        self.executable(self.root/'game'/client.FOLDER)
        picker.reset_mock()
        client.choose(self.root,picker=picker,allow_picker=True,drives=[],expected_sha256=self.pin)
        picker.assert_not_called()

    def test_bad_picker_result_is_refused_and_readonly_checks_never_pick(self):
        wrong=self.executable(self.base/'wrong',b'wrong')
        with self.assertRaisesRegex(ValueError,'SHA256'):
            client.choose(self.root,picker=lambda:str(wrong),allow_picker=True,drives=[],expected_sha256=self.pin)
        picker=Mock()
        self.assertIsNone(client.choose(self.root,picker=picker,drives=[],expected_sha256=self.pin))
        picker.assert_not_called()

    def test_pack_path_resolves_a_verified_local_client_without_manual_configuration(self):
        config.write_json(self.root/config.MARKER,dict(schemaVersion=1))
        expected=self.executable(self.root/'game'/client.FOLDER)
        with patch.object(client,'OW_SHA256',self.pin),patch.object(client,'local_drives',return_value=[]):
            paths=config.PackPaths(self.root)
            self.assertEqual(paths.get('owExecutable'),expected)
            self.assertIn(expected,paths.native_allowed_paths())

    def test_explicit_wrong_hash_selection_is_not_silently_overridden(self):
        config.write_json(self.root/config.MARKER,dict(schemaVersion=1))
        wrong=self.executable(self.base/'explicit',b'wrong')
        self.executable(self.root/'game'/client.FOLDER)
        paths=config.PackPaths(self.root,configuration=dict(schemaVersion=1,paths={'owExecutable':str(wrong)}))
        with patch.object(client,'OW_SHA256',self.pin):
            self.assertEqual(paths.get('owExecutable'),wrong)
            self.assertFalse(client.valid(wrong,self.pin))

    def test_existing_first_run_prepare_uses_picker_only_for_a_missing_client(self):
        from modpack import first_run
        import tkinter as tk
        chosen=self.executable(self.root/'game'/client.FOLDER)
        with patch.object(first_run,'OW_SHA256',self.pin),patch.object(tk,'_default_root',Mock()), \
             patch.object(client,'choose',return_value=chosen) as choose:
            receipt=first_run.prepare(self.root,self.root/'missing.exe','Fixture World')
        self.assertFalse(receipt['gameLaunched'])
        self.assertTrue(choose.call_args.kwargs['allow_picker'])
        self.assertEqual(config.PackPaths(self.root).overrides['owExecutable'],chosen.relative_to(self.root).as_posix())


if __name__=='__main__':unittest.main()
