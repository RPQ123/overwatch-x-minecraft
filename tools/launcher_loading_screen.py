"""Launcher-owned fullscreen cover. The game HWNDs stay in their render paths."""
from __future__ import annotations

import ctypes
from ctypes import wintypes as w
import tkinter as tk


ALPHA = 254 / 255  # Leave DWM a translucent pixel contribution from the live surfaces.
BACKGROUND = '#0b111d'
TEXT = '#f1f5fc'
DIM = '#8798b3'
ACCENT = '#f99e1a'
FONT = 'Microsoft YaHei UI'


def place_cover(window, owner):
    from window_layout import MonitorInfo, user32
    user32.GetAncestor.argtypes = [w.HWND, w.UINT]
    user32.GetAncestor.restype = w.HWND
    user32.MonitorFromWindow.argtypes = [w.HWND, w.DWORD]
    user32.MonitorFromWindow.restype = w.HANDLE
    user32.GetMonitorInfoW.argtypes = [w.HANDLE, ctypes.POINTER(MonitorInfo)]
    user32.GetMonitorInfoW.restype = w.BOOL
    handle = user32.GetAncestor(window.winfo_id(), 2)
    owner_handle = user32.GetAncestor(owner.winfo_id(), 2)
    monitor = user32.MonitorFromWindow(owner_handle, 2)
    info = MonitorInfo()
    info.size = ctypes.sizeof(info)
    x, y, width, height = (user32.GetSystemMetrics(index) for index in (76, 77, 78, 79))
    if (not handle or not owner_handle or not monitor or width <= 0 or height <= 0
            or not user32.GetMonitorInfoW(monitor, ctypes.byref(info))):
        raise RuntimeError('无法取得启动加载画面的桌面范围。')
    rect = w.RECT()
    if not user32.GetWindowRect(handle, ctypes.byref(rect)):
        raise ctypes.WinError(ctypes.get_last_error())
    if (rect.left, rect.top, rect.right-rect.left, rect.bottom-rect.top) != (x, y, width, height):
        if not user32.SetWindowPos(handle, w.HWND(-1), x, y, width, height, 0x0010 | 0x0040):
            raise ctypes.WinError(ctypes.get_last_error())
    return (info.monitor.left-x, info.monitor.top-y, info.monitor.right-x, info.monitor.bottom-y)


class LoadingScreen:
    def __init__(self, owner, logo, cancel, focus):
        self.owner = owner
        self.window = tk.Toplevel(owner, bg=BACKGROUND)
        self.closed = False
        self.fading = False
        self.fade_job = None
        self.last = None
        try:
            self.window.withdraw()
            self.window.overrideredirect(True)
            self.window.attributes('-topmost', True)
            self.window.attributes('-alpha', ALPHA)
            self.window.bind('<Escape>', lambda _: cancel())
            self.window.protocol('WM_DELETE_WINDOW', cancel)
            self.canvas = tk.Canvas(self.window, bg=BACKGROUND, highlightthickness=0)
            self.canvas.pack(fill='both', expand=True)
            self.canvas.tag_bind('cancel', '<Button-1>', lambda _: cancel())
            self.canvas.tag_bind('focus', '<Button-1>', lambda _: focus())
            self.logo = None
            if logo.is_file():
                from PIL import Image, ImageTk
                with Image.open(logo) as source:
                    source.thumbnail((160, 112), Image.Resampling.LANCZOS)
                    self.logo = ImageTk.PhotoImage(source, master=self.window)
            self.window.geometry('1x1+0+0')
            self.window.deiconify()
            self.window.update_idletasks()
            self.update(0, 1, '正在检查本地文件')
            self.window.update_idletasks()
            # Flush the mapped backdrop before the coordinator can create a game HWND.
            ctypes.WinDLL('dwmapi').DwmFlush()
        except BaseException:
            self.close()
            raise

    def update(self, completed, total, step, *, focus_required=False):
        bounds = place_cover(self.window, self.owner)
        state = (bounds, completed, total, step, focus_required)
        if state == self.last:
            return
        self.last = state
        left, top, right, bottom = bounds
        x, y = (left + right) // 2, (top + bottom) // 2
        length = min(600, (right-left)*3//5)
        canvas = self.canvas
        canvas.delete('all')
        if self.logo:
            canvas.create_image(x, y-145, image=self.logo)
        canvas.create_text(x, y-53, text='守望先锋 × 我的世界', fill=TEXT, font=(FONT, 28, 'bold'))
        canvas.create_text(x, y-10, text='O W M C   /   1 . 0 . 0', fill=DIM, font=('Bahnschrift', 12))
        canvas.create_rectangle(x-length//2, y+28, x+length//2, y+34, fill='#243450', outline='')
        if completed:
            start = x-length//2
            canvas.create_rectangle(start, y+28, start+length*completed/total, y+34, fill=ACCENT, outline='')
        canvas.create_text(x, y+68, text=step, fill=TEXT, font=(FONT, 13))
        if focus_required:
            canvas.create_text(x, y+109, text='点击进入游戏', fill=ACCENT, font=(FONT, 13, 'bold'), tags='focus')
        canvas.create_text(x, bottom-36, text='取消启动', fill=DIM, font=(FONT, 11), tags='cancel')

    def fade(self, complete):
        if self.fading or self.closed:
            return
        self.fading = True

        def advance(index):
            self.fade_job = None
            if self.closed:
                return
            if index == 7:
                complete()
            else:
                self.window.attributes('-alpha', ALPHA * (7-index) / 7)
                self.fade_job = self.window.after(25, lambda: advance(index+1))
        advance(1)

    def restore_opacity(self):
        self.fading = False
        self.window.attributes('-alpha', ALPHA)

    def close(self):
        if not self.closed:
            self.closed = True
            if self.fade_job is not None:
                self.window.after_cancel(self.fade_job)
            self.window.destroy()


def show_loading_error(owner, step, detail, log, retry, exit_launcher):
    window = tk.Toplevel(owner, bg=BACKGROUND)
    window.title('OWMC 加载失败')
    window.transient(owner)
    window.resizable(False, False)
    tk.Label(window, text=step, bg=BACKGROUND, fg=ACCENT, font=(FONT, 15, 'bold'),
             anchor='w').pack(fill='x', padx=24, pady=(20, 8))
    for text in (detail[:1000], f'日志位置  {log}'):
        tk.Label(window, text=text, bg=BACKGROUND, fg=TEXT, font=(FONT, 11), anchor='w',
                 wraplength=560, justify='left').pack(fill='x', padx=24, pady=(0, 8))
    buttons = tk.Frame(window, bg=BACKGROUND)
    buttons.pack(anchor='e', padx=24, pady=(4, 20))
    tk.Button(buttons, text='重试', width=10, command=retry).pack(side='left', padx=(0, 8))
    tk.Button(buttons, text='退出', width=10, command=exit_launcher).pack(side='left')
    window.protocol('WM_DELETE_WINDOW', exit_launcher)
    window.lift()
    window.focus_set()
    return window
