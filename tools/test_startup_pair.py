"""Cold-start ordering and failure fixtures, without a JVM or native process."""
import threading
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import launch_passthrough_session as session
import benchmark_startup


class StartupPairTests(unittest.TestCase):
    def setUp(self):
        self.settings=dict(worldName='selected',showMinecraft=False)
        self.guest=dict(worldName='selected',sourcePid=7)

    def test_default_is_serial_until_live_acceptance(self):
        order=[]
        def guest(*args,**kwargs):
            order.append('guest');return self.guest
        def native(*args,**kwargs):
            order.append('native');return 8,{}
        with patch.object(session,'launch_guest',side_effect=guest),patch.object(session,'launch_native',side_effect=native):
            self.assertEqual(session.launch_pair(self.settings,1),(self.guest,8,{}))
        self.assertEqual(order,['guest','native'])

    def test_parallel_native_loading_does_not_wait_for_world_loading(self):
        entered=threading.Event();native_started=threading.Event()
        def guest(*args,**kwargs):
            entered.set()
            if not native_started.wait(2):raise AssertionError('Native load was serialized')
            return self.guest
        def native(*args):
            if not entered.wait(2):raise AssertionError('Guest worker did not start')
            native_started.set();return 8,{}
        with patch.object(session,'launch_guest',side_effect=guest),patch.object(session,'launch_native',side_effect=native):
            self.assertEqual(session.launch_pair({**self.settings,'startupParallel':True},1),(self.guest,8,{}))

    def test_wrong_live_world_cannot_start_or_attach_native(self):
        with patch.object(session,'launch_guest') as guest,patch.object(session,'launch_native') as native:
            with self.assertRaisesRegex(RuntimeError,'different world'):
                session.launch_pair(self.settings,1,dict(worldName='other',sourcePid=7))
        guest.assert_not_called();native.assert_not_called()

    def test_existing_guest_is_adopted_without_starting_another_worker(self):
        with patch.object(session,'launch_guest') as guest,patch.object(session,'launch_native',return_value=(8,{})):
            self.assertEqual(session.launch_pair({**self.settings,'startupParallel':True},1,self.guest),(self.guest,8,{}))
        guest.assert_not_called()

    def test_serial_failed_or_wrong_guest_never_starts_native(self):
        for result in (RuntimeError('guest failed'),dict(worldName='other')):
            call=Mock(side_effect=result) if isinstance(result,Exception) else Mock(return_value=result)
            with patch.object(session,'launch_guest',call),patch.object(session,'launch_native') as native:
                with self.assertRaises(RuntimeError):session.launch_pair({**self.settings,'startupParallel':False},1)
            native.assert_not_called()

    def test_parallel_guest_failure_propagates_before_shared_adapters(self):
        with patch.object(session,'launch_guest',side_effect=RuntimeError('guest failed')), \
             patch.object(session,'launch_native',return_value=(8,{})),patch.object(session,'connect_stages') as attach:
            with self.assertRaisesRegex(RuntimeError,'guest failed'):
                session.launch_pair({**self.settings,'startupParallel':True},1)
        attach.assert_not_called()

    def test_native_failure_joins_guest_worker_without_kill_or_orphan_thread(self):
        entered=threading.Event();release=threading.Event();finished=threading.Event()
        def guest(*args,**kwargs):
            entered.set()
            if not release.wait(2):raise AssertionError('Worker was not released')
            finished.set();return self.guest
        def native(*args):
            if not entered.wait(2):raise AssertionError('No worker')
            release.set();raise RuntimeError('native failed')
        with patch.object(session,'launch_guest',side_effect=guest),patch.object(session,'launch_native',side_effect=native):
            with self.assertRaisesRegex(RuntimeError,'native failed'):
                session.launch_pair({**self.settings,'startupParallel':True},1)
        self.assertTrue(finished.is_set())
        self.assertFalse(any(t.name.startswith('owmc-startup') for t in threading.enumerate()))


class BenchmarkSettingsTests(unittest.TestCase):
    def test_failed_experiment_restores_original_bytes_after_normal_stop(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);path=root/'passthrough-settings.json'
            original=b'{"worldName": "fixture", "shaders": "off"}\n'
            path.write_bytes(original)
            with patch.object(benchmark_startup,'ROOT',root), \
                 patch.object(benchmark_startup,'project_processes',return_value=[]), \
                 patch.object(benchmark_startup,'SessionBackend') as backend:
                backend.return_value.supervisors.return_value=[]
                with self.assertRaisesRegex(RuntimeError,'fixture'):
                    with benchmark_startup.benchmark_settings(root/'result','parallel'):
                        self.assertTrue(json.loads(path.read_text())['startupParallel'])
                        raise RuntimeError('fixture failed')
            self.assertEqual(path.read_bytes(),original)
            self.assertTrue(json.loads((root/'result-settings-restoration.json').read_text())['restored'])

    def test_concurrent_settings_edit_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);path=root/'passthrough-settings.json'
            path.write_text('{}',encoding='utf-8')
            with patch.object(benchmark_startup,'ROOT',root), \
                 patch.object(benchmark_startup,'project_processes',return_value=[]), \
                 patch.object(benchmark_startup,'SessionBackend') as backend:
                backend.return_value.supervisors.return_value=[]
                with benchmark_startup.benchmark_settings(root/'result','serial'):
                    path.write_text('{"concurrent": true}',encoding='utf-8')
            self.assertEqual(json.loads(path.read_text()),{'concurrent':True})


if __name__=='__main__':
    unittest.main()
