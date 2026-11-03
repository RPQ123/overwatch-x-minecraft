"""Hide only the guarded offline client's own console, never its render HWND.

A GUI executable may call AllocConsole after CreateProcess, so CREATE_NO_WINDOW
alone is insufficient. A short-lived, console-free helper can attach to that
console without changing the supervisor's standard handles or user's terminal.
"""
from __future__ import annotations
import argparse
import ctypes
from ctypes import wintypes as w
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import psutil
from modpack.config import paths
from observe_overwatch import ROOT,ResearchProcess


class ConsoleUnavailable(OSError):
    pass


class WinConsole:
    def __init__(self):
        self.kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        self.user=ctypes.WinDLL('user32',use_last_error=True)
        self.kernel.GetConsoleWindow.argtypes=[];self.kernel.GetConsoleWindow.restype=w.HWND
        self.kernel.AttachConsole.argtypes=[w.DWORD];self.kernel.AttachConsole.restype=w.BOOL
        self.kernel.FreeConsole.argtypes=[];self.kernel.FreeConsole.restype=w.BOOL
        self.kernel.GetConsoleProcessList.argtypes=[ctypes.POINTER(w.DWORD),w.DWORD]
        self.kernel.GetConsoleProcessList.restype=w.DWORD
        self.user.IsWindowVisible.argtypes=[w.HWND];self.user.IsWindowVisible.restype=w.BOOL
        self.user.ShowWindow.argtypes=[w.HWND,ctypes.c_int];self.user.ShowWindow.restype=w.BOOL

    def window(self):return self.kernel.GetConsoleWindow()
    def attach(self,pid):
        if not self.kernel.AttachConsole(pid):raise ConsoleUnavailable(ctypes.get_last_error(),'AttachConsole unavailable')
    def detach(self):
        if not self.kernel.FreeConsole():raise ctypes.WinError(ctypes.get_last_error())
    def owners(self):
        buffer=(w.DWORD*64)();count=self.kernel.GetConsoleProcessList(buffer,len(buffer))
        if not 0<count<=len(buffer):raise ValueError('Console owner list unavailable or exceeds bound')
        return set(buffer[:count])
    def visible(self,hwnd):return bool(self.user.IsWindowVisible(hwnd))
    def hide(self,hwnd):self.user.ShowWindow(hwnd,0)  # SW_HIDE, console HWND only.

    def native_windows(self,pid):
        result=[]
        callback_type=ctypes.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
        self.user.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)]
        self.user.GetClassNameW.argtypes=[w.HWND,w.LPWSTR,ctypes.c_int]
        @callback_type
        def collect(hwnd,_):
            owner=w.DWORD();self.user.GetWindowThreadProcessId(hwnd,ctypes.byref(owner))
            if owner.value==pid:
                name=ctypes.create_unicode_buffer(256)
                if self.user.GetClassNameW(hwnd,name,len(name)):
                    result.append((name.value,int(hwnd)))
            return True
        self.user.EnumWindows.argtypes=[callback_type,w.LPARAM]
        self.user.EnumWindows(collect,0)
        return result

    def show_render(self,hwnd):
        # Only reveals the original render HWND. Never hides or minimizes it.
        self.user.ShowWindow(hwnd,4)
        self.user.ShowWindow(hwnd,4)


def native_startupinfo():
    """AllocConsole honors this initial state without a visible first frame."""
    startup=subprocess.STARTUPINFO()
    startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow=0
    return startup


def reveal_native_render(pid,created,backend=None,*,native=None):
    native=native or verified_owner(pid,created);backend=backend or WinConsole()
    if not native.is_running() or native.create_time()!=created:
        raise ValueError('Render window owner identity changed')
    visible=False
    for name,hwnd in backend.native_windows(pid):
        if name!='TankWindowClass':continue
        if not native.is_running() or native.create_time()!=created:
            raise ValueError('Render window owner identity changed before show')
        if not backend.visible(hwnd):backend.show_render(hwnd)
        visible=backend.visible(hwnd) or visible
    return visible


def hide_native_window_console(pid,created,backend,*,native):
    """Fallback only for a console HWND directly owned by the verified game.

    Some desktop/console hosts reject AttachConsole with ERROR_ACCESS_DENIED.
    A conhost/user-terminal HWND has a different owner and is never touched.
    """
    hidden=[]
    for name,hwnd in backend.native_windows(pid):
        if name!='ConsoleWindowClass':continue
        if not native.is_running() or native.create_time()!=created:
            raise ValueError('Console window owner identity changed')
        if backend.visible(hwnd):backend.hide(hwnd)
        if backend.visible(hwnd):raise RuntimeError('Console hide readback differs')
        hidden.append(hwnd)
    return dict(status='native-owned-console-hidden' if hidden else 'pending',hidden=bool(hidden),hwnds=hidden)


def verified_owner(pid,created):
    native=psutil.Process(pid)
    if not native.is_running() or native.create_time()!=created:raise ValueError('Console owner identity changed')
    memory=ResearchProcess(pid)  # Includes the unchanged offline executable SHA256 guard.
    try:
        if memory.path.resolve()!=paths().get('owExecutable').resolve():raise ValueError('Unexpected console owner executable')
    finally:memory.close()
    return native


def hide_owned_console(pid,created,backend=None,*,native=None):
    native=native or verified_owner(pid,created);backend=backend or WinConsole()
    if not native.is_running() or native.create_time()!=created:raise ValueError('Console owner identity changed')
    if backend.window():return dict(status='helper-already-attached',hidden=False)
    try:backend.attach(pid)
    except ConsoleUnavailable as error:
        if error.errno in (6,87):return dict(status='pending',hidden=False)
        raise
    try:
        # Console windows are owned by conhost, not necessarily by the client
        # HWND PID. The actual attached process list proves the association.
        owners=backend.owners()
        if pid not in owners or not owners.issubset({pid,os.getpid()}):
            return dict(status='shared-console-preserved',hidden=False)
        hwnd=backend.window()
        if not hwnd:return dict(status='pending',hidden=False)
        if not native.is_running() or native.create_time()!=created:raise ValueError('Console owner identity changed before hide')
        visible=backend.visible(hwnd)
        if visible:backend.hide(hwnd)
        if backend.visible(hwnd):raise RuntimeError('Console hide readback differs')
        return dict(status='hidden' if visible else 'already-hidden',hidden=True,hwnd=int(hwnd))
    finally:backend.detach()


def start_console_guard(pid):
    """Independent of game readiness; no synchronous startup wait or console."""
    created=psutil.Process(pid).create_time()
    return subprocess.Popen([sys.executable,'-B',str(Path(__file__).resolve()),
                             '--pid',str(pid),'--created',repr(created),'--seconds','10'],
                            cwd=ROOT,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                            creationflags=subprocess.CREATE_NO_WINDOW)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid',type=int,required=True);parser.add_argument('--created',type=float,required=True)
    parser.add_argument('--seconds',type=float,default=10);args=parser.parse_args()
    if not 0<args.seconds<=10:raise ValueError('Console helper has a ten-second maximum')
    deadline=time.monotonic()+args.seconds
    result=dict(status='pending',hidden=False)
    try:
        backend=WinConsole();native=verified_owner(args.pid,args.created)
        while time.monotonic()<deadline:
            render_visible=reveal_native_render(args.pid,args.created,backend,native=native)
            try:result=hide_owned_console(args.pid,args.created,backend,native=native)
            except ConsoleUnavailable as error:
                if error.errno!=5:raise
                result=hide_native_window_console(args.pid,args.created,backend,native=native)
            result['renderVisible']=render_visible
            if result['status']!='pending' and render_visible:break
            time.sleep(min(.01,max(0,deadline-time.monotonic())))
        if result['status']=='pending':result['status']='no-console-observed'
    except (OSError,ValueError,RuntimeError,psutil.Error) as error:
        result=dict(status='console-hide-unavailable',hidden=False,error=str(error),
                    warning='控制台隐藏未完成；未隐藏原版渲染窗口。')
    result.update(nativePid=args.pid,nativeCreated=args.created,helperPid=os.getpid())
    report=ROOT/'research/launcher'/f'native-console-{args.pid}-{int(args.created*1000)}.json'
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return 0 if result['status']!='console-hide-unavailable' else 1


if __name__=='__main__':raise SystemExit(main())
