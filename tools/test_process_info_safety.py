"""Portable psutil cache/metadata regressions; no real process operations."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch

import psutil
import launch_passthrough_session as session
import native_display_mode as display
import stop_passthrough_session as stop
import minecraft_shaders
import twilight_forest


def process(info,*,pid=7,name='unrelated.exe'):
    return SimpleNamespace(info=info,pid=pid,name=Mock(return_value=name),terminate=Mock(),wait=Mock())


class ProcessInfoTests(unittest.TestCase):
    def scan(self,*items):
        with patch.object(session.psutil,'process_iter',return_value=list(items)):
            return session.native_pids()

    def test_unrelated_missing_exe_and_empty_cache_do_not_raise_keyerror(self):
        self.assertEqual(self.scan(process({'name':'unrelated.exe'}),process({})),[])

    def test_native_without_executable_still_refuses_to_prove_absence(self):
        for info in ({'name':session.EXE.name},{'name':session.EXE.name,'exe':None},{}):
            with self.subTest(info=info),self.assertRaisesRegex(RuntimeError,'无法证明不存在'):
                self.scan(process(info,name=session.EXE.name))

    def test_unreadable_name_cannot_authorize_another_native_owner(self):
        item=process({});item.name.side_effect=psutil.AccessDenied(item.pid)
        with self.assertRaisesRegex(RuntimeError,'cannot prove absence'):self.scan(item)

    def test_exited_process_is_not_an_existing_owner(self):
        item=process({});item.name.side_effect=psutil.NoSuchProcess(item.pid)
        self.assertEqual(self.scan(item),[])

    def test_matching_image_without_cached_pid_uses_real_process_pid(self):
        self.assertEqual(self.scan(process({'exe':str(session.EXE)},pid=123)),[123])

    def test_foreign_image_cannot_match_by_filename(self):
        foreign=session.EXE.parent/'foreign'/session.EXE.name
        self.assertEqual(self.scan(process({'pid':7,'name':session.EXE.name,'exe':str(foreign)})),[])

    def test_parallel_cache_replacement_is_read_only_once(self):
        class Replaced:
            pid=71
            reads=0
            @property
            def info(self):
                self.reads+=1
                return {'exe':str(session.EXE),'pid':self.pid} if self.reads==1 else {'cmdline':[]}
        item=Replaced()
        self.assertEqual(self.scan(item),[71]);self.assertEqual(item.reads,1)

    def test_duplicate_native_clients_still_refuse(self):
        with self.assertRaisesRegex(RuntimeError,'Multiple original'):
            self.scan(process({'exe':str(session.EXE)},pid=1),process({'exe':str(session.EXE)},pid=2))

    def test_missing_supervisor_metadata_cannot_terminate_a_process(self):
        items=[process({}),process({'cmdline':[str(stop.ROOT/'tools/launch_passthrough_session.py')]}),
               process({'exe':'python.exe'})]
        with patch.object(stop.psutil,'process_iter',return_value=items):stop.stop_supervisor()
        for item in items:item.terminate.assert_not_called()

    def test_known_jvm_with_missing_identity_still_refuses_absence(self):
        for info in ({'name':'javaw.exe'},{'name':'java.exe','exe':'java.exe'},{'exe':'javaw.exe'}):
            with self.subTest(info=info),patch.object(stop.psutil,'process_iter',return_value=[process(info)]):
                with self.assertRaisesRegex(RuntimeError,'cannot prove absence'):stop._project_guest_processes()

    def test_partial_metadata_in_non_destructive_checks_is_safe(self):
        for info in ({},{'cmdline':None}):
            with self.subTest(info=info),patch.object(psutil,'process_iter',return_value=[process(info)]):
                self.assertFalse(display.any_native_running())
                minecraft_shaders.stopped();twilight_forest.stopped()

    def test_display_restore_cannot_assume_absence_from_a_missing_cached_name(self):
        item=process({},name=display.EXE.name)
        with patch.object(display.psutil,'process_iter',return_value=[item]):
            self.assertTrue(display.any_native_running())
        item.name.side_effect=psutil.AccessDenied(item.pid)
        with patch.object(display.psutil,'process_iter',return_value=[item]),self.assertRaisesRegex(RuntimeError,'无法证明不存在'):
            display.any_native_running()
        item.name.side_effect=psutil.NoSuchProcess(item.pid)
        with patch.object(display.psutil,'process_iter',return_value=[item]):
            self.assertFalse(display.any_native_running())

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
