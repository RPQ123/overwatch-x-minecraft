"""Launcher-owned full desktop cover with an ordinary progress window fallback."""
from __future__ import annotations

import ctypes
from ctypes import wintypes as w
import tkinter as tk
from tkinter import ttk


BACKGROUND = '#0b111d'
TEXT = '#f1f5fc'
ACCENT = '#f99e1a'
FONT = 'Microsoft YaHei UI'
ALPHA = 254 / 255


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
    if not handle or not owner_handle or not monitor or min(width, height) <= 0 or not user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
        raise RuntimeError('无法取得加载遮罩的桌面范围。')
    rect = w.RECT()
    if not user32.GetWindowRect(handle, ctypes.byref(rect)):
        raise ctypes.WinError(ctypes.get_last_error())
    bounds = (x, y, x + width, y + height)
    if (rect.left, rect.top, rect.right, rect.bottom) != bounds:
        if not user32.SetWindowPos(handle, w.HWND(-1), x, y, width, height, 0x0010 | 0x0040):
            raise ctypes.WinError(ctypes.get_last_error())
        if not user32.GetWindowRect(handle, ctypes.byref(rect)) or (rect.left, rect.top, rect.right, rect.bottom) != bounds:
            raise RuntimeError('加载遮罩位置与桌面范围不一致。')
    area = info.monitor
    return ((area.left + area.right) // 2 - x, (area.top + area.bottom) // 2 - y)


class LoadingScreen:
    def __init__(self, owner, cancel, *, fullscreen=True, logo=None):
        self.owner = owner
        self.fullscreen = fullscreen
        self.window = tk.Toplevel(owner, bg=BACKGROUND)
        self.closed = False
        self.center = None
        try:
            self.window.title('OWMC 正在启动')
            if fullscreen:
                self.window.withdraw()
                self.window.overrideredirect(True)
                self.window.attributes('-topmost', True)
                self.window.attributes('-alpha', ALPHA)
                self.window.geometry('1x1+0+0')
                self.window.bind('<KeyPress>', lambda _: 'break')
                self.window.bind('<KeyRelease>', lambda _: 'break')
            else:
                self.window.resizable(False, False)
                self.window.transient(owner)
            self.window.bind('<Escape>', lambda _: cancel())
            self.window.protocol('WM_DELETE_WINDOW', cancel)
            self.content = tk.Frame(self.window, bg=BACKGROUND)
            if fullscreen and logo is not None and logo.is_file():
                try:
                    from PIL import Image, ImageTk
                    with Image.open(logo) as source:
                        source.thumbnail((160, 112), Image.Resampling.LANCZOS)
                        self.logo = ImageTk.PhotoImage(source, master=self.window)
                    tk.Label(self.content, image=self.logo, bg=BACKGROUND).pack()
                except (OSError, ImportError, tk.TclError) as failure:
                    print(f'加载图标不可用，已继续：{failure}', flush=True)
            tk.Label(self.content, text='守望先锋 × 我的世界', font=(FONT, 18, 'bold'),
                     fg=TEXT, bg=BACKGROUND).pack(padx=32, pady=(22, 14))
            self.bar = ttk.Progressbar(self.content, length=420, mode='determinate')
            self.bar.pack(fill='x', padx=32)
            self.step = tk.Label(self.content, text='正在检查本地文件', font=(FONT, 11),
                                 fg=TEXT, bg=BACKGROUND, wraplength=420)
            self.step.pack(padx=32, pady=(10, 6))
            if fullscreen:
                tk.Label(self.content, text='启动中尝试静音，暂时锁定游戏按键',
                         fg=TEXT, bg=BACKGROUND, font=(FONT, 10)).pack(pady=(0, 8))
            tk.Button(self.content, text='取消启动', command=cancel).pack(pady=(4, 16))
            if fullscreen:
                self.window.deiconify()
                self.window.update_idletasks()
                self.update(0, 1, '正在检查本地文件')
                self.take_focus()
            else:
                self.content.pack()
        except BaseException:
            self.close()
            raise

    def take_focus(self):
        if self.fullscreen:
            self.window.focus_force()
        else:
            self.window.focus_set()

    @staticmethod
    def input_held():
        from window_layout import user32
        user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
        user32.GetAsyncKeyState.restype = ctypes.c_short
        return any(user32.GetAsyncKeyState(key) & 0x8000 for key in range(1, 255))

    def update(self, completed, total, step):
        if self.fullscreen:
            center = place_cover(self.window, self.owner)
            if self.center != center:
                self.content.place(x=center[0], y=center[1], anchor='center')
                self.center = center
        self.bar.configure(maximum=total, value=completed)
        self.step.configure(text=step)

    def close(self):
        if not self.closed:
            self.closed = True
            if self.fullscreen:
                try:
                    self.window.withdraw()
                except tk.TclError:
                    pass
            try:
                self.window.destroy()
            except tk.TclError:
                pass  # The owner may already have destroyed all its windows.


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
