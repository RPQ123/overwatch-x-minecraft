"""Covered startup fixtures. All game processes and HWNDs are inert."""
import json
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import launcher_loading_screen as screen
import launch_passthrough_session as session
import project_launcher as launcher
import startup_cover as cover
import window_layout as layout


REQUEST = '1'*32


def report(wall=1000, step=0, **changes):
    return dict(pid=14, enabled=True, failures=0, viewMode=2, generation=42, lastMcGeneration=(1<<64)-1,
                sampleWallMs=wall, frames=20+step, blended=12+step, unmaskedFrames=2,
                colorUploads=10+step, lastMcFrame=50+step, probeVersion=session.COMPOSITOR_VERSION) | changes


def health(**changes):
    return dict(sourcePid=15, generation=-1, published=60, mode='full-world-frame-proof', worldName='fixture',
                failed=False, player={'alive': True}, hostPoseConnected=True, hostPoseFlags=1, hostGeneration=42) | changes


def snapshot(now_ms, **changes):
    receipt = dict(requestId=REQUEST, supervisorPid=13, nativePid=14, guestPid=15, observedMs=now_ms,
                   nativeHwnd=19, guestHwnd=20, nativeCreated=1., guestCreated=2.)
    return dict(status=dict(nativePid=14, phase='hero-selection', startupPresentation=receipt),
                nativeAlive=True, fresh=True, supervisorPids=[13]) | changes


class GateTests(unittest.TestCase):
    def test_picker_requires_two_advancing_masked_samples_from_current_session(self):
        gate = cover.CompositionGate()
        self.assertIsNone(gate.observe(health(), report(), 14, 15, 1000))
        self.assertIsNone(gate.observe(health(), report(), 14, 15, 1001))
        evidence = gate.observe(health(), report(1500, 4), 14, 15, 1500)
        self.assertEqual(evidence['maskedDelta'], 4)
        self.assertEqual(evidence['viewMode'], 2)
        self.assertEqual(evidence['guestGeneration'], (1<<64)-1)

    def test_rejects_neutral_held_unmasked_wrong_generation_and_stale_frames(self):
        for guest, native, now in (
            (health(), report(1500, 4, lastMcFrame=0), 1500),
            (health(), report(1500, 4, lastMcFrame=50), 1500),
            (health(), report(1500, 4, unmaskedFrames=6), 1500),
            (health(), report(1500, 4, lastMcGeneration=9), 1500),
            (health(hostGeneration=9), report(1500, 4), 1500),
            (health(), report(1500, 4, colorUploads=10), 1500),
            (health(), report(1500, 4, presentOk=0, presentOccluded=4), 1500),
            (health(sourcePid=99), report(1500, 4), 1500),
            (health(), report(1500, 4, viewMode=0), 1500),
            (health(), report(1500, 4), 3100),
        ):
            with self.subTest(native=native, now=now):
                gate = cover.CompositionGate()
                gate.observe(health(), report(), 14, 15, 1000)
                self.assertIsNone(gate.observe(guest, native, 14, 15, now))

    def test_stale_published_handoff_does_not_accept_another_action_or_owner(self):
        self.assertIsNotNone(cover.presentation_receipt(snapshot(2000), REQUEST, 2500))
        self.assertIsNone(cover.presentation_receipt(snapshot(2000), '2'*32, 2500))
        self.assertIsNone(cover.presentation_receipt(snapshot(2000, supervisorPids=[19]), REQUEST, 2500))
        self.assertIsNone(cover.presentation_receipt(snapshot(2000), REQUEST, 4000))
        self.assertIsNone(cover.presentation_receipt(snapshot(2000, status={'phase':'hero-selection'}), REQUEST, 2500))

    def test_progress_counts_only_observed_parallel_milestones(self):
        done, total, step = cover.loading_progress(False, {})
        self.assertEqual(done, 0)
        self.assertEqual(step, '正在检查本地文件')
        timeline = {'events': [{'name': name} for name in ('mc_jvm_spawned', 'native_spawned', 'native_client_ready')]}
        done, self_total, step = cover.loading_progress(True, timeline)
        self.assertEqual((done, self_total), (4, total))
        self.assertIn('Minecraft', step)
        self.assertIn('英雄', step)
        self.assertEqual(cover.loading_progress(True, timeline), (done, total, step))

    def test_timeout_and_cancellation_are_bound_to_one_live_ui_ticket(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            ticket = cover.LoadingTicket.create(root, REQUEST, time.perf_counter_ns()+20*10**9)
            self.assertEqual(ticket.state(), 'pending')
            with patch.object(cover.time, 'perf_counter_ns', return_value=ticket.deadline_ns):
                with self.assertRaisesRegex(cover.LoadingCancelled, str(cover.LOAD_SECONDS)):
                    ticket.checkpoint()
            ticket.finish('cancelled')
            self.assertEqual(ticket.state(), 'cancelled')
            with self.assertRaises(cover.LoadingCancelled):
                ticket.finish('released')


class WindowFixtures(unittest.TestCase):
    def test_progress_does_not_set_dwm_alpha_topmost_or_desktop_geometry(self):
        for build, dpi, origin in ((19045,120,(-1920,-240)), (22631,144,(-2560,0))):
            with self.subTest(build=build,dpi=dpi,origin=origin), \
                 patch.object(screen.tk,'Toplevel') as top, patch.object(screen.tk,'Label'), \
                 patch.object(screen.tk,'Button'), patch.object(screen.tk,'Frame'), \
                 patch.object(screen.ttk,'Progressbar') as bar:
                owner=Mock(winfo_rootx=Mock(return_value=origin[0]),winfo_rooty=Mock(return_value=origin[1]))
                progress=screen.LoadingScreen(owner,Mock(),fullscreen=False)
                progress.update(2,5,'正在连接画面')
                bar.return_value.configure.assert_called_once_with(maximum=5,value=2)
                for name in ('attributes','geometry','overrideredirect','grab_set'):
                    getattr(top.return_value,name).assert_not_called()
                owner.winfo_rootx.assert_not_called()
                progress.close()
                top.return_value.destroy.assert_called_once()

    def test_full_cover_spans_negative_origin_and_centers_on_owner_monitor(self):
        user=Mock()
        user.GetAncestor.side_effect=[10,11]
        user.GetSystemMetrics.side_effect=[-1920,-240,4480,1680]
        def monitor(_, output):
            rect=output._obj.monitor
            rect.left,rect.top,rect.right,rect.bottom=0,0,2560,1440
            return True
        def placed(_, output):
            rect=output._obj
            rect.left,rect.top,rect.right,rect.bottom=-1920,-240,2560,1440
            return True
        user.GetMonitorInfoW.side_effect=monitor
        def read(handle, output):
            return True if user.GetWindowRect.call_count==1 else placed(handle,output)
        user.GetWindowRect.side_effect=read
        with patch.object(layout,'user32',user):
            self.assertEqual(screen.place_cover(Mock(),Mock()),(3200,960))
        self.assertEqual(user.SetWindowPos.call_args.args[2:6],(-1920,-240,4480,1680))

    def test_exact_pair_stacks_without_hide_minimize_or_resize(self):
        pair = (layout.Window(19,14,1920,1080,'OW'), layout.Window(20,15,960,540,'MC'))
        user = Mock()
        user.GetForegroundWindow.return_value = 0
        user.SetForegroundWindow.return_value = True
        with patch.object(layout,'render_pair',return_value=pair), patch.object(layout,'user32',user):
            self.assertTrue(layout.focus_render_pair(14,15,19,20))
            self.assertFalse(layout.focus_render_pair(14,15,19,20,foreground_only=True))
            with self.assertRaises(ValueError):
                layout.focus_render_pair(14,15,19,21)
        flags = layout.SWP_NOACTIVATE | layout.SWP_NOSENDCHANGING | 0x0001 | 0x0002 | 0x4000
        self.assertEqual(user.SetWindowPos.call_args.args, (20,19,0,0,0,0,flags))
        user.ShowWindow.assert_not_called()

class HandOffFixtures(unittest.TestCase):
    def ui(self):
        ui = object.__new__(launcher.LauncherUI)
        ui.loading = Mock()
        ui.loading_watch = None
        ui.loading_ticket = Mock(request_id=REQUEST)
        ui.loading_error = None
        ui.loading_log = Path('action.log')
        ui.loading_deadline_ns = time.perf_counter_ns()+360*10**9
        ui.startup_result = {'ready': True}
        ui.loading_step = '正在连接画面'
        ui.window = Mock()
        ui.backend = Mock()
        ui.action_var = Mock()
        ui.last_snapshot = snapshot(round(time.time()*1000))
        return ui

    def test_timeout_closes_cover_cancels_and_opens_retry_exit_dialog(self):
        ui = self.ui()
        ui.loading_deadline_ns = 1
        ticket, view = ui.loading_ticket, ui.loading
        with patch.object(screen, 'show_loading_error') as error:
            ui.update_loading()
        ticket.finish.assert_called_once_with('cancelled')
        view.close.assert_called_once()
        ui.window.attributes.assert_called_once_with('-topmost', False)
        self.assertEqual(error.call_args.args[1], '正在连接画面')
        self.assertIn(str(cover.LOAD_SECONDS), error.call_args.args[2])
        self.assertEqual(error.call_args.args[-2:], (ui.retry_loading, ui.close))

    def test_focus_refusal_releases_and_allows_manual_focus(self):
        ui = self.ui()
        ticket, view = ui.loading_ticket, ui.loading
        def refused(*args):
            view.close.assert_called_once()
            return False
        ui.backend.focus_loading_pair.side_effect = refused
        with patch.object(screen.LoadingScreen,'input_held',return_value=False):
            ui.try_loading_focus()
        ui.action_var.set.assert_called_once_with('游戏窗口已打开，请单击 OW 窗口进入。')
        ticket.finish.assert_called_once_with('released')
        view.close.assert_called_once()
        self.assertIsNone(ui.loading)

    def test_win11_cover_yields_once_then_handoff_succeeds(self):
        second=10**9
        for occluded in (0,1):
            with self.subTest(occluded=occluded):
                ui=self.ui()
                full,ticket=ui.loading,ui.loading_ticket
                ui.loading_watch=cover.CoverWatchdog(0)
                ui.last_snapshot=dict(status={'phase':'starting'},loadingTimeline=dict(request={'requestId':REQUEST},
                    events=[dict(name='compositor_attach_started',monotonicNs=0)]))
                def update(ns,count,blocked=0):
                    ui.last_snapshot.update(snapshotNs=ns,loadingCoverReport=dict(enabled=True,presentOk=count,presentOccluded=blocked))
                    with patch.object(launcher.time,'perf_counter_ns',return_value=ns):ui.update_loading()
                with patch.object(screen,'LoadingScreen') as make, patch('launcher_ui_owner.log') as log:
                    update(second,0)
                    full.close.assert_not_called()
                    update(2*second if occluded else 4*second,0,occluded)
                    full.close.assert_called_once()
                    self.assertEqual(make.call_args.kwargs,{'fullscreen':False})
                    self.assertIn('遮挡' if occluded else '停滞',log.call_args.kwargs['reason'])
                    ticket.finish.assert_not_called()
                    update(5*second,18)
                    make.assert_called_once()
                    ui.last_snapshot=snapshot(round(time.time()*1000))
                    ui.try_loading_focus()
                    ticket.finish.assert_called_once_with('released')
                    make.return_value.close.assert_called_once()

    def test_win10_advancing_present_keeps_cover_until_verified_handoff(self):
        ui=self.ui()
        full,ticket=ui.loading,ui.loading_ticket
        ui.loading_watch=cover.CoverWatchdog(0)
        timeline=dict(request={'requestId':REQUEST},events=[dict(name='compositor_attach_started',monotonicNs=0)])
        for sec in range(1,8):
            now=sec*10**9
            ui.last_snapshot=dict(status={'phase':'starting'},loadingTimeline=timeline,snapshotNs=now,
                                  loadingCoverReport=dict(enabled=True,presentOk=sec*60,presentOccluded=0))
            with patch.object(launcher.time,'perf_counter_ns',return_value=now):ui.update_loading()
        full.close.assert_not_called()
        ticket.finish.assert_not_called()
        ui.last_snapshot=snapshot(round(time.time()*1000))
        with patch.object(screen.LoadingScreen,'input_held',return_value=False):ui.try_loading_focus()
        full.close.assert_called_once()
        ticket.finish.assert_called_once_with('released')

    def test_pre_compositor_wait_and_stale_snapshot_cannot_keep_cover(self):
        watch=cover.CoverWatchdog(0)
        timeline=dict(events=[dict(name='native_bootstrap_started',monotonicNs=0)])
        self.assertIsNone(watch.reason(timeline,{},2*10**9,2*10**9))
        self.assertIn('引导',watch.reason(timeline,{},3*10**9,3*10**9))
        self.assertIn('状态',watch.reason(timeline,{},None,6*10**9))

    def test_cover_geometry_error_is_cosmetic_and_does_not_cancel_ticket(self):
        ui=self.ui()
        ui.last_snapshot={}
        ui.loading_watch=cover.CoverWatchdog(time.perf_counter_ns())
        full,ticket=ui.loading,ui.loading_ticket
        full.update.side_effect=OSError('DPI changed')
        with patch.object(screen,'LoadingScreen') as make, patch('launcher_ui_owner.log') as log:
            ui.update_loading()
            full.close.assert_called_once()
            self.assertEqual(make.call_args.kwargs,{'fullscreen':False})
            self.assertIn('无法更新',log.call_args.kwargs['reason'])
            ticket.finish.assert_not_called()
            ui.close()
            ticket.finish.assert_called_once_with('cancelled')

    def test_display_presence_and_snapshot_errors_reach_chinese_failure_dialog(self):
        import native_display_mode as display
        for listing, phrase in (([(7,'gameclientapp.exe')],'仍在运行'),(OSError('snapshot failed'),'无法确认')):
            ui=self.ui()
            with patch('process_images.process_images',side_effect=[listing]), \
                 patch.object(screen,'show_loading_error') as dialog:
                try:display.verified_launch()
                except (RuntimeError,ValueError) as failure:ui.fail_loading(str(failure))
                else:self.fail('display lease unexpectedly admitted')
                self.assertIn(phrase,dialog.call_args.args[2])
                self.assertIn('正常',dialog.call_args.args[2])

    def test_held_input_avoids_forcing_game_focus(self):
        ui = self.ui()
        ticket=ui.loading_ticket
        with patch.object(screen.LoadingScreen,'input_held',return_value=True):
            ui.try_loading_focus()
        ui.backend.focus_loading_pair.assert_not_called()
        ticket.finish.assert_called_once_with('released')

    def test_stalled_present_offers_window_without_claiming_composition(self):
        ticket=Mock(request_id=REQUEST,state=Mock(return_value='pending'))
        timeline=Mock()
        status={}
        native=Mock(pid=14,create_time=Mock(return_value=1.0))
        guest=Mock(pid=15,create_time=Mock(return_value=2.0))
        with patch.object(session.psutil,'Process',side_effect=[native,guest]), \
             patch('window_layout.guest_window_owner',return_value=guest), \
             patch('window_layout.render_pair',return_value=(SimpleNamespace(handle=19),SimpleNamespace(handle=20))), \
             patch.object(session.time,'monotonic',return_value=100) as clock, \
             patch.object(session.time,'time',return_value=1.5), \
             patch.object(session,'stage_ready',return_value=True), patch.object(session,'write_status'), \
             patch.object(session,'api',return_value=health()), \
             patch.object(session,'read_report',return_value=report(1500,presentOk=0,presentOccluded=5,poses=0)), \
             patch.object(session,'WINDOW_REVEALS',set()), patch.object(session,'wait') as wait:
            def observe(_, advance, *args, **kwargs):
                self.assertIsNone(advance())
                clock.return_value=116
                self.assertIsNone(advance())
                self.assertIs(status['startupPresentation']['frameVerified'],False)
                ticket.state.return_value='released'
                self.assertTrue(advance())
            wait.side_effect=observe
            session.await_loading_handoff(14,health(),ticket,status,timeline)
        self.assertEqual(timeline.mark.call_args_list[0].args,('loading_presentation_skipped',))
        self.assertEqual(timeline.mark.call_args_list[0].kwargs['report']['presentOccluded'],5)
        self.assertIn('OW 尚未成功出画',status['startupPresentationNotice'])
        self.assertNotIn('startupPresentation',status)

    def test_presenting_ow_with_uncomposed_guest_frames_gets_distinct_advice(self):
        self.assertIn('OW 已出画，MC 已发布帧，画面尚未接入',
                      cover.presentation_notice({'presentOk':30,'sourceFrames':24,'lastMcFrame':0},{}))
        self.assertIn('确认 MC 已进入世界',cover.presentation_notice({'presentOk':30},{}))
        self.assertIn('已接入 MC 帧',cover.presentation_notice({'presentOk':30,'lastMcFrame':5},{}))

    def test_collision_and_localized_errors(self):
        sock=Mock()
        sock.__enter__=Mock(return_value=sock)
        sock.__exit__=Mock()
        with patch.object(session.socket,'socket',return_value=sock):
            sock.connect_ex.return_value=10061
            session.require_bridge_port()
            sock.connect_ex.return_value=0
            with self.assertRaisesRegex(RuntimeError,'32133 已被占用'):
                session.require_bridge_port()
        for text, expected in (
            ('No completed observation; do not reload. Three-frame stop needs active presents.','启动阶段尚未完成'),
            ('[WinError 5] Access is denied','本地可写'),
            ('[WinError 126] Missing module','VC++'),
            ('DXGI_ERROR_DEVICE_REMOVED','显卡'),
            ('Waiting for the real saved Minecraft world: fixture','Minecraft'),
            ('some internal traceback','游戏启动未完成'),
        ):
            with self.subTest(text=text):
                self.assertIn(expected,cover.startup_failure_text(text))

    def test_failed_timeline_releases_overlay_before_reporting_error(self):
        ui = self.ui()
        ui.loading_deadline_ns = time.perf_counter_ns()+10*10**9
        ui.startup_result = {'ready': True}
        ui.last_snapshot['loadingTimeline'] = dict(request={'requestId':REQUEST}, status='failed',
            events=[{'name':'mc_jvm_spawned'}, {'name':'startup_failed','error':'fixture launch failed'}])
        view = ui.loading
        with patch.object(screen, 'show_loading_error') as error:
            error.side_effect = lambda *args: view.close.assert_called_once()
            ui.update_loading()
        self.assertIn('游戏启动未完成', error.call_args.args[2])

    def test_coordinator_joins_cancelled_supervisor_before_normal_cleanup(self):
        with tempfile.TemporaryDirectory() as name:
            backend = launcher.SessionBackend(Path(name))
            backend.running = Mock(return_value=False)
            backend.project_processes = Mock(side_effect=[[], [Mock()]])
            backend.supervisors = Mock(return_value=[])
            backend.loading_timeline = Mock(return_value={'events':[{'name':'native_spawn_requested'}]})
            child = backend.loading_child = Mock(poll=Mock(return_value=None))
            backend.start = Mock(return_value={'result':'supervisor-started'})
            def cleanup(_):
                child.wait.assert_called_once_with(timeout=90)
            backend.robust_stop = Mock(side_effect=cleanup)
            ticket = Mock(request_id=REQUEST, state=Mock(return_value='cancelled'))
            ticket.checkpoint.side_effect = [None, None, cover.LoadingCancelled('fixture cancelled')]
            with self.assertRaisesRegex(cover.LoadingCancelled, 'fixture cancelled'):
                backend.start_covered('start', Path('action.log'), ticket)
            backend.robust_stop.assert_called_once()

    def test_composition_handoff_waits_for_ui_and_rejects_pre_layout_samples(self):
        native = Mock(create_time=Mock(return_value=1.), pid=14)
        guest = Mock(create_time=Mock(return_value=2.), pid=15)
        timeline = Mock()
        ticket = Mock(request_id=REQUEST)
        ticket.state.side_effect = ['pending','pending','pending','released']
        captured = []
        def wait(_, advance, *args, **kwargs):
            for _ in range(3):
                self.assertIsNone(advance())
            self.assertEqual(len(captured), 1)
            return advance()
        pair = (layout.Window(19,14,1920,1080,'OW'), layout.Window(20,15,960,540,'MC'))
        with patch.object(layout,'guest_window_owner',return_value=guest), patch.object(layout,'render_pair',return_value=pair), \
             patch.object(session.psutil,'Process',side_effect=[native,guest]), patch.object(session,'wait',side_effect=wait), \
             patch.object(session,'paths'), patch.object(session,'stage_ready',return_value=True), \
             patch.object(session,'read_report',side_effect=[report(900),report(1100,4),report(1600,8)]), \
             patch.object(session,'api',return_value=health()), patch.object(session.time,'time',side_effect=[1.,1.,1.1,1.6,1.6]), \
             patch.object(session,'write_status',side_effect=lambda value: captured.append(json.loads(json.dumps(value)))), \
             patch.object(session,'WINDOW_REVEALS',set()):
            record = {}
            session.await_loading_handoff(14,health(),ticket,record,timeline)
        self.assertEqual(captured[0]['startupPresentation']['lastMcFrame'], 58)
        self.assertNotIn('startupPresentation', record)
        timeline.mark.assert_any_call('loading_handoff')


if __name__ == '__main__':
    unittest.main()
