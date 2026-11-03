"""Display, relocation and hidden-start contracts; no real games/display writes."""
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch

import native_display_mode as display
import launch_passthrough_session as session
from test_native_display_mode import Display,mode


class AutomaticDisplayTests(unittest.TestCase):
    def test_native_desktops_do_not_switch_or_read_the_registry(self):
        for width,height,hz,source in ((1920,1080,60,[1920,1080]),(2560,1440,200,[2560,1440]),
                                      (3840,2160,144,[2560,1440]),(1366,768,59,[1366,768]),
                                      (2376,1080,144,[2376,1080]),(3440,1440,165,[2560,1070])):
            with self.subTest(size=(width,height)),tempfile.TemporaryDirectory() as folder:
                backend=Display();backend.current=mode(width,height,hz);backend.read=Mock(wraps=backend.read)
                settings=dict(width=1920,height=1080,nativeFullscreen=True)
                plan=display.configure_display(settings,backend)
                self.assertEqual([settings['width'],settings['height']],source)
                self.assertEqual(plan['target'],[width,height,hz,32]);self.assertFalse(plan['modeChangeRequired'])
                backend.read.reset_mock()
                lease=display.DisplayLease(Path(folder)/'receipt.json',backend)
                with patch.object(display,'verified_launch',return_value=dict(executable=display.stored_executable())):
                    result=lease.acquire(None,settings)
                self.assertFalse(result['changed']);self.assertEqual(backend.calls,[])
                backend.read.assert_called_once_with(display.CURRENT)
                self.assertFalse(lease.path.exists())

    def test_manual_refresh_uses_an_enumerated_rate(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(display,'verified_launch',return_value=dict(executable=display.stored_executable())):
            backend=Display();backend.current.hz=200
            settings=dict(width=1920,height=1080,nativeFullscreen=True,nativeDisplayAuto=False,nativeDisplayTemporary=True)
            display.configure_display(settings,backend)
            result=display.DisplayLease(Path(folder)/'receipt.json',backend).acquire(None,settings)
            self.assertEqual(result['mode'],[1920,1080,144,32])
            self.assertEqual([flags for _,flags in backend.calls],[display.TEST,0])

    def test_manual_source_quality_does_not_force_a_desktop_mode_switch(self):
        backend=Display();backend.current=mode(2560,1440,200)
        settings=dict(width=1920,height=1080,nativeFullscreen=True,sourceResolutionAuto=False)
        plan=display.configure_display(settings,backend)
        self.assertEqual(plan['target'],[2560,1440,200,32]);self.assertEqual(plan['sourceSize'],[1920,1080])
        self.assertFalse(plan['modeChangeRequired']);self.assertEqual(backend.calls,[])

    def test_unavailable_primary_falls_back_without_a_display_mutation(self):
        backend=Mock();backend.read.return_value=None
        settings=dict(width=1920,height=1080,nativeFullscreen=True)
        display.configure_display(settings,backend)
        self.assertFalse(settings['nativeFullscreen']);self.assertTrue(settings['displayWarnings'])
        backend.change.assert_not_called()

    def test_refused_test_falls_back_and_identity_failures_stay_fatal(self):
        with tempfile.TemporaryDirectory() as folder:
            backend=Display();backend.change=Mock(side_effect=display.DisplayModeRefused('TEST -1'))
            lease=display.DisplayLease(Path(folder)/'receipt.json',backend)
            settings=dict(width=1920,height=1080,nativeFullscreen=True)
            with patch.object(display,'DisplayLease',return_value=lease), \
                 patch.object(display,'verified_launch',return_value=dict(executable=display.stored_executable())):
                result=display.prepare_display(settings)
            self.assertEqual(result['fallback'],'desktop-native');self.assertFalse(lease.path.exists())
            self.assertEqual(settings['nativeDisplayWidth'],2376)
            self.assertEqual(backend.change.call_args.args[1],display.TEST)
            with patch.object(display,'DisplayLease',return_value=lease), \
                 patch.object(display,'verified_launch',side_effect=ValueError('SHA256 differs')):
                with self.assertRaisesRegex(ValueError,'SHA256'):
                    display.prepare_display(dict(width=1920,height=1080,nativeFullscreen=True))

    def test_success_return_with_original_desktop_readback_falls_back_without_repeating_apply(self):
        with tempfile.TemporaryDirectory() as folder, \
             patch.object(display,'verified_launch',return_value=dict(executable=display.stored_executable())), \
             patch.object(display,'any_native_running',return_value=False):
            backend=Display();backend.change=Mock()  # Driver reports success but keeps the original desktop.
            lease=display.DisplayLease(Path(folder)/'receipt.json',backend)
            with patch.object(display,'DisplayLease',return_value=lease):
                result=display.prepare_display(dict(width=1920,height=1080,nativeFullscreen=True,nativeDisplayTemporary=True))
            self.assertEqual(result['fallback'],'desktop-native')
            self.assertEqual(lease.load()['state'],'restored');self.assertEqual(backend.change.call_count,2)


class PortableReceiptTests(unittest.TestCase):
    def test_relative_and_legacy_receipts_restore_after_a_package_move(self):
        for legacy in (False,True):
            with self.subTest(legacy=legacy),tempfile.TemporaryDirectory() as folder,ExitStack() as stack:
                root=Path(folder)/'移动后的 中文包';exe=root/'game/client.exe'
                exe.parent.mkdir(parents=True);exe.write_bytes(b'guarded inert fixture')
                stack.enter_context(patch.object(display,'ROOT',root));stack.enter_context(patch.object(display,'EXE',exe))
                stack.enter_context(patch.object(display,'PATCHED_SHA256',hashlib.sha256(exe.read_bytes()).hexdigest()))
                identity=dict(kind='launch-reservation',pid=1,created=2,executable='game/client.exe')
                stack.enter_context(patch.object(display,'verified_launch',return_value=identity))
                stack.enter_context(patch.object(display,'any_native_running',return_value=False))
                backend=Display();lease=display.DisplayLease(root/'data/runtime/receipt.json',backend)
                lease.acquire(None,dict(width=1920,height=1080,nativeFullscreen=True,nativeDisplayTemporary=True))
                record=lease.load()
                self.assertEqual(record['identity']['executable'],'game/client.exe')
                self.assertTrue(all(not Path(item['path']).is_absolute() for item in record['backups'].values()))
                if legacy:
                    record['schema']=1;record['identity']['executable']='Z:/旧整合包/game/client.exe'
                    for item in record['backups'].values():item['path']='Z:/旧整合包/data/runtime/'+item['path']
                    lease.save(record)
                self.assertTrue(lease.restore()['restored'])
                self.assertEqual(display.signature(backend.current),[2376,1080,144,32])
                self.assertEqual(lease.load()['state'],'restored')

    def test_already_original_desktop_retires_stale_lease_without_rewriting_registry(self):
        with tempfile.TemporaryDirectory() as folder, \
             patch.object(display,'verified_launch',return_value=dict(executable=display.stored_executable())), \
             patch.object(display,'any_native_running',return_value=False):
            backend=Display();lease=display.DisplayLease(Path(folder)/'receipt.json',backend)
            lease.acquire(None,dict(width=1920,height=1080,nativeFullscreen=True))
            backend.current=mode(2376);backend.registered=mode(3840,2160)
            count=len(backend.calls)
            self.assertTrue(lease.restore()['alreadyOriginal'])
            self.assertEqual(len(backend.calls),count);self.assertEqual(lease.load()['state'],'restored')

    def test_relative_traversal_and_foreign_identity_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            lease=display.DisplayLease(Path(folder)/'receipt.json',Display())
            with self.assertRaisesRegex(ValueError,'outside'):lease.backup_path('../current.bin','current')
            self.assertFalse(display.receipt_executable_matches('../client.exe'))
            self.assertFalse(display.receipt_executable_matches('foreign/client.exe'))

    def test_original_desktop_size_preserves_external_refresh_instead_of_switching_it_back(self):
        with tempfile.TemporaryDirectory() as folder, \
             patch.object(display,'verified_launch',return_value=dict(executable=display.stored_executable())), \
             patch.object(display,'any_native_running',return_value=False):
            backend=Display();lease=display.DisplayLease(Path(folder)/'receipt.json',backend)
            lease.acquire(None,dict(width=1920,height=1080,nativeFullscreen=True))
            backend.current=mode(2376,hz=60);count=len(backend.calls)
            result=lease.restore()
            self.assertTrue(result['preservedRefresh']);self.assertEqual(result['current'],[2376,1080,60,32])
            self.assertEqual(len(backend.calls),count);self.assertEqual(lease.load()['state'],'restored')


class SessionPresentationTests(unittest.TestCase):
    def test_wait_checks_immediately_and_preserves_timeout_with_shorter_handoffs(self):
        now=[0.0];calls=[]
        def sleep(value):calls.append(value);now[0]+=value
        with patch.object(session.time,'monotonic',side_effect=lambda:now[0]),patch.object(session.time,'sleep',side_effect=sleep):
            self.assertTrue(session.wait('immediate',lambda:True));self.assertEqual(calls,[])
            self.assertTrue(session.wait('next frame',lambda:now[0]>=.12,seconds=1))
            self.assertAlmostEqual(now[0],.15)
            with self.assertRaises(TimeoutError):session.wait('bounded',lambda:False,seconds=.07)
            self.assertAlmostEqual(now[0],.22)

    def test_guest_starts_hidden_with_resolved_source_size_and_no_console(self):
        with tempfile.TemporaryDirectory() as folder,ExitStack() as stack:
            profile=Path(folder);stack.enter_context(patch.object(session,'PROFILE',profile))
            prepare=stack.enter_context(patch.object(session,'prepare',return_value=['java','-Dowmc.startHidden=false','-Dowmc.allowWindowShow=false','--width','1920','--height','1080']))
            spawn=stack.enter_context(patch.object(session.subprocess,'Popen',return_value=Mock(pid=7)))
            stack.enter_context(patch.object(session,'GuestStartupLog'))
            guest=dict(sourcePid=7,published=4)
            stack.enter_context(patch.object(session,'guest_ready',return_value=guest))
            self.assertEqual(session.launch_guest(True,display_settings=dict(width=2560,height=1440)),guest)
            prepare.assert_called_once_with(visible=False,timeline=None)
            command=spawn.call_args.args[0]
            self.assertEqual(command[command.index('--width')+1],'2560')
            self.assertIn('-Dowmc.startHidden=true',command)
            self.assertEqual([v for v in command if v.startswith('-Dowmc.startHidden=')],['-Dowmc.startHidden=true'])
            self.assertEqual([v for v in command if v.startswith('-Dowmc.allowWindowShow=')],['-Dowmc.allowWindowShow=true'])
            self.assertEqual(spawn.call_args.kwargs['creationflags'],session.subprocess.CREATE_NO_WINDOW)

    def test_show_minecraft_false_is_a_permanent_jvm_visibility_gate(self):
        with tempfile.TemporaryDirectory() as folder,ExitStack() as stack:
            stack.enter_context(patch.object(session,'PROFILE',Path(folder)))
            stack.enter_context(patch.object(session,'prepare',return_value=['java','-Dowmc.allowWindowShow=true','--width','1920','--height','1080']))
            spawn=stack.enter_context(patch.object(session.subprocess,'Popen',return_value=Mock(pid=7)))
            stack.enter_context(patch.object(session,'GuestStartupLog'))
            stack.enter_context(patch.object(session,'guest_ready',return_value={'sourcePid':7,'published':4}))
            session.launch_guest(False,display_settings=dict(width=1920,height=1080))
            command=spawn.call_args.args[0]
            self.assertEqual([v for v in command if v.startswith('-Dowmc.allowWindowShow=')],['-Dowmc.allowWindowShow=false'])
            self.assertIn('-Dowmc.startHidden=true',command)

    def test_native_console_is_suppressed_without_hiding_the_render_window(self):
        with ExitStack() as stack:
            for name,value in (('native_pids',[]),('restore_display',{}),('prepare_display',{}),('acquire_display',{}),
                               ('ensure_bootstrap',None),('read_loaded_map',{'state':8,'mapId':1}),('native_ready',True),('wait',True)):
                stack.enter_context(patch.object(session,name,return_value=value))
            stack.enter_context(patch.object(session,'ResearchProcess'))
            stack.enter_context(patch.object(session,'start_console_guard'))
            spawn=stack.enter_context(patch.object(session.subprocess,'Popen',return_value=Mock(pid=8)))
            session.launch_native(dict(nativeFullscreen=True),1)
            self.assertEqual(spawn.call_args.kwargs['creationflags'],session.subprocess.CREATE_NO_WINDOW)
            self.assertNotIn('startupinfo',spawn.call_args.kwargs)

    def test_guest_reveal_requires_fresh_composition_and_is_requested_only_once(self):
        guest=dict(sourcePid=7,generation=123)
        report=dict(blended=0,lastMcFrame=10,lastMcGeneration=123)
        with ExitStack() as stack:
            stack.enter_context(patch.object(session,'WINDOW_REVEALS',set()))
            arrange=stack.enter_context(patch.object(session,'arrange_windows',return_value={}))
            stack.enter_context(patch.object(session.psutil,'Process',return_value=Mock(create_time=Mock(return_value=100))))
            ready=stack.enter_context(patch.object(session,'stage_ready',return_value=True))
            stack.enter_context(patch.object(session,'read_report',side_effect=lambda path:report))
            show=stack.enter_context(patch.object(session,'api',return_value={'accepted':True}))
            settings=dict(showMinecraft=True,nativeFullscreen=True)
            session.arrange_visible_windows(8,guest,settings,reveal=False);ready.assert_not_called()
            session.arrange_visible_windows(8,guest,settings);show.assert_not_called()
            report['blended']=3;report['lastMcGeneration']=999
            session.arrange_visible_windows(8,guest,settings);show.assert_not_called()
            report['lastMcGeneration']=123
            session.arrange_visible_windows(8,guest,settings)
            session.arrange_visible_windows(8,guest,settings)
            show.assert_called_once_with('window/show',post=True,timeout=.25)
            self.assertTrue(all(call.kwargs['show_minecraft'] is False for call in arrange.call_args_list))

    def test_signed_java_generation_matches_unsigned_native_only_after_a_fresh_composed_frame(self):
        guest=dict(sourcePid=7,generation=-1)
        report=dict(blended=1,lastMcFrame=10,lastMcGeneration=(1<<64)-2)
        with ExitStack() as stack:
            stack.enter_context(patch.object(session,'WINDOW_REVEALS',set()))
            stack.enter_context(patch.object(session,'arrange_windows',return_value={}))
            stack.enter_context(patch.object(session.psutil,'Process',return_value=Mock(create_time=Mock(return_value=100))))
            stack.enter_context(patch.object(session,'stage_ready',return_value=True))
            stack.enter_context(patch.object(session,'read_report',side_effect=lambda path:report))
            show=stack.enter_context(patch.object(session,'api',return_value={'accepted':True}))
            session.arrange_visible_windows(8,guest,dict(showMinecraft=True));show.assert_not_called()
            report['lastMcGeneration']=(1<<64)-1
            session.arrange_visible_windows(8,guest,dict(showMinecraft=True))
            show.assert_called_once_with('window/show',post=True,timeout=.25)


if __name__=='__main__':unittest.main()
