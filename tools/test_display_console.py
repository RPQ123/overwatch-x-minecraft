"""Exact console ownership fixtures; never attach to a real OS console."""
import os
import unittest
from unittest.mock import Mock,patch
import display_console as console


class ConsoleTests(unittest.TestCase):
    def setUp(self):
        self.native=Mock();self.native.is_running.return_value=True;self.native.create_time.return_value=100
        self.verify=patch.object(console,'verified_owner',return_value=self.native)
        self.verify.start();self.addCleanup(self.verify.stop)
        self.backend=Mock();self.backend.window.side_effect=[None,33]
        self.backend.owners.return_value={7,os.getpid()};self.backend.visible.side_effect=[True,False]

    def test_only_owned_console_handle_is_hidden_and_detached(self):
        result=console.hide_owned_console(7,100,self.backend)
        self.assertTrue(result['hidden']);self.assertEqual(result['hwnd'],33)
        self.backend.attach.assert_called_once_with(7);self.backend.hide.assert_called_once_with(33)
        self.backend.detach.assert_called_once()

    def test_shared_user_terminal_is_never_hidden(self):
        self.backend.owners.return_value={7,os.getpid(),99}
        self.assertEqual(console.hide_owned_console(7,100,self.backend)['status'],'shared-console-preserved')
        self.backend.hide.assert_not_called();self.backend.detach.assert_called_once()

    def test_helper_with_its_own_console_never_detaches_or_hides_it(self):
        self.backend.window.side_effect=[55]
        self.assertEqual(console.hide_owned_console(7,100,self.backend)['status'],'helper-already-attached')
        self.backend.hide.assert_not_called();self.backend.attach.assert_not_called();self.backend.detach.assert_not_called()

    def test_late_allocconsole_is_pending_without_touching_a_window(self):
        self.backend.attach.side_effect=console.ConsoleUnavailable(6,'not allocated')
        self.assertEqual(console.hide_owned_console(7,100,self.backend)['status'],'pending')
        self.backend.hide.assert_not_called();self.backend.detach.assert_not_called()

    def test_reused_pid_before_hide_is_rejected_and_console_is_detached(self):
        self.native.create_time.side_effect=[100,101]
        with self.assertRaisesRegex(ValueError,'identity changed'):
            console.hide_owned_console(7,100,self.backend)
        self.backend.hide.assert_not_called();self.backend.detach.assert_called_once()

    def test_already_hidden_console_is_idempotent(self):
        self.backend.visible.side_effect=[False,False]
        self.assertEqual(console.hide_owned_console(7,100,self.backend)['status'],'already-hidden')
        self.backend.hide.assert_not_called();self.backend.detach.assert_called_once()

    def test_failed_hide_readback_does_not_touch_render_windows(self):
        self.backend.visible.side_effect=[True,True]
        with self.assertRaisesRegex(RuntimeError,'readback'):
            console.hide_owned_console(7,100,self.backend)
        self.backend.hide.assert_called_once_with(33);self.backend.detach.assert_called_once()

    def test_native_startup_has_no_visible_console_first_frame(self):
        info=console.native_startupinfo()
        self.assertTrue(info.dwFlags&console.subprocess.STARTF_USESHOWWINDOW)
        self.assertEqual(info.wShowWindow,0)

    def test_render_reveal_only_shows_guarded_render_window(self):
        self.backend.native_windows.return_value=[('ConsoleWindowClass',33),('TankWindowClass',44),('Other',55)]
        self.backend.visible.side_effect=[False,True]
        self.assertTrue(console.reveal_native_render(7,100,self.backend,native=self.native))
        self.backend.show_render.assert_called_once_with(44)
        self.backend.hide.assert_not_called()

    def test_fallback_hides_only_directly_owned_console_not_the_render_window(self):
        self.backend.native_windows.return_value=[('ConsoleWindowClass',33),('TankWindowClass',44)]
        self.backend.visible.side_effect=[True,False]
        self.assertTrue(console.hide_native_window_console(7,100,self.backend,native=self.native)['hidden'])
        self.backend.hide.assert_called_once_with(33)
        self.backend.show_render.assert_not_called()

    def test_render_reveal_refuses_reused_process(self):
        self.native.create_time.return_value=101
        with self.assertRaisesRegex(ValueError,'identity changed'):
            console.reveal_native_render(7,100,self.backend,native=self.native)
        self.backend.show_render.assert_not_called()


if __name__=='__main__':unittest.main()
