"""Exact-window borderless fixtures; no real window API is invoked."""
from contextlib import ExitStack
from pathlib import Path
import unittest
from unittest.mock import Mock,patch
import window_layout as layout

class FullscreenTests(unittest.TestCase):
    def setUp(self):
        self.stack=ExitStack();self.addCleanup(self.stack.close)
        self.user=Mock();self.stack.enter_context(patch.object(layout,'user32',self.user))
        self.native=Mock();self.path=Path('C:/fixture/ow.exe')
        self.identity=self.stack.enter_context(patch.object(layout,'_native_identity',return_value=(self.native,100,self.path)))
        self.check=self.stack.enter_context(patch.object(layout,'_check_identity'))
        self.windows=self.stack.enter_context(patch.object(layout,'windows_for_pid',return_value=[layout.Window(12,10,1600,900,'Overwatch')]))
        self.classes=self.stack.enter_context(patch.object(layout,'_window_class',return_value='tankWindowClass'))
        self.styles={-16:0x10cf0000,-20:0x20309};self.bounds=(-1920,0,0,1080);self.rect=(10,10,1610,910)
        self.user.MonitorFromWindow.return_value=33
        def info(handle,out):
            value=out._obj;value.monitor.left,value.monitor.top,value.monitor.right,value.monitor.bottom=self.bounds;return True
        def rect(hwnd,out):
            value=out._obj;value.left,value.top,value.right,value.bottom=self.rect;return True
        def style(hwnd,index,after):
            old=self.styles[index];self.styles[index]=after;return old
        def position(hwnd,insert,x,y,w,h,flags):self.rect=(x,y,x+w,y+h);return True
        self.user.GetMonitorInfoW.side_effect=info;self.user.GetWindowRect.side_effect=rect
        self.user.GetWindowLongPtrW.side_effect=lambda hwnd,index:self.styles[index]
        self.user.SetWindowLongPtrW.side_effect=style;self.user.SetWindowPos.side_effect=position
    def test_current_monitor_borderless_not_exclusive_or_topmost(self):
        value=layout.native_borderless_fullscreen(10)
        self.assertTrue(value['changed']);self.assertEqual(value['monitorBounds'],[-1920,0,0,1080])
        self.assertFalse(value['exclusiveFullscreen']);self.assertFalse(value['topmost'])
        args=self.user.SetWindowPos.call_args.args
        self.assertEqual(args[2:6],(-1920,0,1920,1080));self.assertTrue(args[-1]&layout.SWP_FRAMECHANGED)
        self.assertEqual(self.styles[-16]&layout.WS_OVERLAPPEDWINDOW,0);self.assertTrue(self.styles[-16]&layout.WS_POPUP)
        self.user.ShowWindow.assert_not_called()
    def test_repeat_is_idempotent_no_style_or_resize(self):
        layout.native_borderless_fullscreen(10);self.user.SetWindowLongPtrW.reset_mock();self.user.SetWindowPos.reset_mock()
        self.assertFalse(layout.native_borderless_fullscreen(10)['changed'])
        self.user.SetWindowLongPtrW.assert_not_called();self.user.SetWindowPos.assert_not_called()
    def test_actual_native_class_capitalization(self):
        self.classes.return_value='TankWindowClass'
        self.assertTrue(layout.native_borderless_fullscreen(10)['changed'])
    def test_console_and_wrong_class_refused(self):
        self.classes.return_value='ConsoleWindowClass'
        with self.assertRaisesRegex(ValueError,'render window'):layout.native_borderless_fullscreen(10)
        self.user.SetWindowLongPtrW.assert_not_called();self.user.SetWindowPos.assert_not_called()
    def test_foreign_title_refused(self):
        self.windows.return_value=[layout.Window(12,10,1600,900,'Elevated: console')]
        with self.assertRaisesRegex(ValueError,'render window'):layout.native_borderless_fullscreen(10)
        self.user.SetWindowPos.assert_not_called()
    def test_duplicate_render_windows_refused(self):
        self.windows.return_value*=2
        with self.assertRaisesRegex(ValueError,'one exact'):layout.native_borderless_fullscreen(10)
        self.user.SetWindowPos.assert_not_called()
    def test_pid_reused_before_mutation_refused(self):
        self.check.side_effect=ValueError('identity changed')
        with self.assertRaisesRegex(ValueError,'identity changed'):layout.native_borderless_fullscreen(10)
        self.user.SetWindowLongPtrW.assert_not_called();self.user.SetWindowPos.assert_not_called()
    def test_readback_mismatch_fails(self):
        self.user.SetWindowPos.side_effect=lambda *args:True
        with self.assertRaisesRegex(RuntimeError,'readback'):layout.native_borderless_fullscreen(10)
    def test_mc_size_position_preserved_and_ow_not_restored(self):
        ow=layout.Window(12,10,1600,900,'Overwatch');mc=layout.Window(22,20,960,540,'Minecraft')
        self.windows.side_effect=lambda pid:[ow if pid==10 else mc]
        self.user.GetSystemMetrics.side_effect=lambda axis:2560 if axis==0 else 1440
        with patch.object(layout,'_pid_is_alive',return_value=True),patch.object(layout,'native_borderless_fullscreen',return_value={'changed':False}) as full:
            result=layout.arrange(10,20,native_fullscreen=True)
        full.assert_called_once_with(10);self.assertEqual(result['minecraft']['arrangedWidth'],960)
        self.user.ShowWindow.assert_not_called();self.user.SetWindowPos.assert_not_called()
    def test_legacy_arrange_does_not_restore_maximized_ow(self):
        ow=layout.Window(12,10,2560,1440,'Overwatch');mc=layout.Window(22,20,960,540,'Minecraft')
        self.windows.side_effect=lambda pid:[ow if pid==10 else mc]
        self.user.GetSystemMetrics.side_effect=lambda axis:2560 if axis==0 else 1440
        with patch.object(layout,'_pid_is_alive',return_value=True):layout.arrange(10,20)
        self.user.ShowWindow.assert_not_called()
        args=self.user.SetWindowPos.call_args.args;self.assertEqual(args[0].value,12);self.assertTrue(args[-1]&0x3)

    def test_hidden_guest_is_positioned_once_without_show_or_activation(self):
        ow=layout.Window(12,10,2560,1440,'Overwatch');mc=layout.Window(22,20,960,540,'Minecraft')
        self.windows.side_effect=lambda pid,**kwargs:[ow if pid==10 else mc]
        self.user.GetSystemMetrics.side_effect=lambda axis:2560 if axis==0 else 1440
        with patch.object(layout,'_pid_is_alive',return_value=True),patch.object(layout,'native_borderless_fullscreen'):
            layout.arrange(10,20,960,540,native_fullscreen=True,show_minecraft=False)
            calls=self.user.SetWindowPos.call_count
            layout.arrange(10,20,960,540,native_fullscreen=True,show_minecraft=False)
        self.assertEqual(calls,1);self.assertEqual(self.user.SetWindowPos.call_count,1)
        flags=self.user.SetWindowPos.call_args.args[-1]
        self.assertTrue(flags&layout.SWP_NOACTIVATE);self.assertFalse(flags&layout.SWP_SHOWWINDOW)
        self.user.ShowWindow.assert_not_called()

if __name__=='__main__':unittest.main()
