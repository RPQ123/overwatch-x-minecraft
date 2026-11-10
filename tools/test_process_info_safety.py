"""Process image selection fixtures. No test opens a foreign process handle."""
import ast
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import psutil
import launch_passthrough_session as session
import native_display_mode as display
import stop_passthrough_session as stop
import minecraft_shaders
import process_images as images
import twilight_forest


def owner(executable, *, pid=7, arguments=()):
    return Mock(pid=pid, exe=Mock(return_value=str(executable)), cmdline=Mock(return_value=list(arguments)),
                is_running=Mock(return_value=True))


class ProcessInfoTests(unittest.TestCase):
    def scan(self, snapshot, *candidates):
        with patch.object(images, 'process_images', return_value=snapshot), \
             patch.object(psutil, 'Process', side_effect=candidates) as inspect:
            return session.native_pids(), inspect.call_args_list

    def test_protected_unrelated_images_are_never_opened(self):
        listing = [(4,'system'),(9,'securityguard.exe'),(10,''),(11,'anticheat.exe')]
        self.assertEqual(self.scan(listing), ([],[]))
        with patch.object(images,'process_images',return_value=listing), \
             patch.object(psutil,'Process',side_effect=AssertionError('unrelated process opened')):
            self.assertFalse(display.any_native_running())
            minecraft_shaders.stopped()
            twilight_forest.stopped()
            self.assertEqual(stop._project_guest_processes(), [])

    def test_unreadable_native_family_still_blocks(self):
        for name in ('gameclientapp.exe','gameclientapp.patched.exe','gameclientapp.offline.exe'):
            with self.subTest(name=name), self.assertRaisesRegex(RuntimeError,'原版 OW.*正常退出'):
                self.scan([(71,name)], psutil.AccessDenied(71))

    def test_exited_snapshot_pid_does_not_authorize_operations(self):
        self.assertEqual(self.scan([(7,session.EXE.name.casefold())],psutil.NoSuchProcess(7))[0], [])

    def test_matching_image_still_needs_exact_full_path(self):
        listing = [(7,session.EXE.name.casefold())]
        self.assertEqual(self.scan(listing,owner(session.EXE))[0],[7])
        foreign = session.EXE.parent/'另一套 文件'/session.EXE.name
        self.assertEqual(self.scan(listing,owner(foreign))[0],[])
        self.assertEqual(self.scan(listing,owner('C:/Windows/Security.exe'))[0],[])

    def test_duplicate_native_clients_still_refuse(self):
        with self.assertRaisesRegex(RuntimeError,'多个原版 OW'):
            self.scan([(7,session.EXE.name.casefold()),(8,session.EXE.name.casefold())],
                      owner(session.EXE),owner(session.EXE,pid=8))

    def test_missing_supervisor_metadata_cannot_terminate_a_process(self):
        items = [SimpleNamespace(info=info, terminate=Mock()) for info in
                 ({},{'cmdline':[str(stop.ROOT/'tools/launch_passthrough_session.py')]},{'exe':'python.exe'})]
        with patch.object(stop.psutil,'process_iter',return_value=items):
            stop.stop_supervisor()
        for item in items:
            item.terminate.assert_not_called()

    def test_unreadable_generic_java_skipped_and_known_runtime_guarded(self):
        owned = stop.paths().get('java')
        ours = owner(owned)
        ours.cmdline.side_effect = psutil.AccessDenied(ours.pid)
        foreign = owner(owned.parent.parent/'other'/'javaw.exe')
        foreign.cmdline.side_effect = psutil.AccessDenied(foreign.pid)
        with patch.object(images,'process_images',return_value=[(7,'java.exe')]):
            for item in (foreign, psutil.AccessDenied(7)):
                with patch.object(psutil,'Process',side_effect=[item]):
                    self.assertEqual(stop._project_guest_processes(), [])
            with patch.object(psutil,'Process',return_value=ours), self.assertRaisesRegex(RuntimeError,'本包的 Java'):
                stop._project_guest_processes()

    def test_display_mode_change_blocked_by_native_image_without_opening_it(self):
        with patch.object(images,'process_images',return_value=[(7,'gameclientapp.patched.exe')]), \
             patch.object(psutil,'Process',side_effect=AssertionError('opened an image')):
            self.assertTrue(display.any_native_running())

    @unittest.skipUnless(os.name == 'nt','Windows snapshot')
    def test_real_process_snapshot_includes_current_python(self):
        self.assertIn((os.getpid(),'python.exe'),images.process_images())

    def test_tools_have_no_direct_process_info_subscript_reads(self):
        root=Path(__file__).resolve().parent;unsafe=[]
        for path in root.rglob('*.py'):
            tree=ast.parse(path.read_text(encoding='utf-8-sig'))
            for node in ast.walk(tree):
                if (isinstance(node,ast.Subscript) and isinstance(node.ctx,ast.Load)
                        and isinstance(node.value,ast.Attribute) and node.value.attr=='info'):
                    unsafe.append(f'{path.relative_to(root)}:{node.lineno}')
        self.assertEqual(unsafe,[])


if __name__=='__main__':unittest.main()
