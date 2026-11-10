"""Ordinary launcher progress window; DWM never sees a full desktop cover."""
from __future__ import annotations

import ctypes
import tkinter as tk
from tkinter import ttk


BACKGROUND = '#0b111d'
TEXT = '#f1f5fc'
ACCENT = '#f99e1a'
FONT = 'Microsoft YaHei UI'


class LoadingScreen:
    def __init__(self, owner, cancel):
        self.window = tk.Toplevel(owner, bg=BACKGROUND)
        self.closed = False
        try:
            self.window.title('OWMC 正在启动')
            self.window.resizable(False, False)
            self.window.transient(owner)
            self.window.bind('<Escape>', lambda _: cancel())
            self.window.protocol('WM_DELETE_WINDOW', cancel)
            tk.Label(self.window, text='守望先锋 × 我的世界', font=(FONT, 18, 'bold'),
                     fg=TEXT, bg=BACKGROUND).pack(padx=32, pady=(22, 14))
            self.bar = ttk.Progressbar(self.window, length=420, mode='determinate')
            self.bar.pack(fill='x', padx=32)
            self.step = tk.Label(self.window, text='正在检查本地文件', font=(FONT, 11),
                                 fg=TEXT, bg=BACKGROUND, wraplength=420)
            self.step.pack(padx=32, pady=(10, 6))
            tk.Button(self.window, text='取消启动', command=cancel).pack(pady=(4, 16))
        except BaseException:
            self.close()
            raise

    def take_focus(self):
        self.window.focus_set()

    @staticmethod
    def input_held():
        from window_layout import user32
        user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
        user32.GetAsyncKeyState.restype = ctypes.c_short
        return any(user32.GetAsyncKeyState(key) & 0x8000 for key in range(1, 255))

    def update(self, completed, total, step):
        self.bar.configure(maximum=total, value=completed)
        self.step.configure(text=step)

    def close(self):
        if not self.closed:
            self.closed = True
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
