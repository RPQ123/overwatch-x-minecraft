"""Keep the original client and the real Minecraft client visible together."""
from __future__ import annotations
from modpack.config import paths

import argparse
import ctypes
import ctypes.wintypes as wintypes
from dataclasses import dataclass
from pathlib import Path

import psutil
from observe_overwatch import ROOT, ResearchProcess

user32 = ctypes.WinDLL("user32", use_last_error=True)
EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
user32.EnumWindows.argtypes = [EnumWindowsProc, wintypes.LPARAM]
user32.EnumWindows.restype = wintypes.BOOL
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.IsWindowVisible.restype = wintypes.BOOL
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.GetWindowRect.restype = wintypes.BOOL
user32.GetSystemMetrics.argtypes = [ctypes.c_int]
user32.GetSystemMetrics.restype = ctypes.c_int
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.ShowWindow.restype = wintypes.BOOL
user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                                ctypes.c_int, ctypes.c_int, ctypes.c_uint]
user32.SetWindowPos.restype = wintypes.BOOL

SW_SHOWNOACTIVATE = 4
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
SWP_NOSENDCHANGING = 0x0400
HWND_NOTOPMOST = wintypes.HWND(-2)
SWP_FRAMECHANGED = 0x0020
WS_OVERLAPPEDWINDOW = 0x00CF0000
WS_POPUP = 0x80000000
EX_DECORATIONS = 0x00020301


class MonitorInfo(ctypes.Structure):
    _fields_ = [('size', wintypes.DWORD), ('monitor', wintypes.RECT),
                ('work', wintypes.RECT), ('flags', wintypes.DWORD)]


def _window_class(hwnd):
    value = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    if not user32.GetClassNameW(hwnd, value, len(value)):
        raise ctypes.WinError(ctypes.get_last_error())
    return value.value


def _native_identity(pid):
    native = psutil.Process(pid)
    created = native.create_time()
    process = ResearchProcess(pid)
    try:
        path = process.path
        if path != paths().get('owExecutable'):
            raise ValueError('Borderless target is not the exact offline client')
    finally:
        process.close()
    return native, created, path


def _check_identity(native, created, path):
    if (not native.is_running() or native.create_time() != created
            or Path(native.exe()).resolve() != path):
        raise ValueError('Borderless native process identity changed')


def native_borderless_fullscreen(pid: int) -> dict:
    """One idempotent window operation; retain DXGI windowed and original HWND."""
    native, created, path = _native_identity(pid)
    candidates = [w for w in windows_for_pid(pid)
                  if w.title.casefold().startswith('overwatch')
                  and _window_class(w.handle).casefold() == 'tankwindowclass']
    if len(candidates) != 1:
        raise ValueError('Expected one exact Overwatch render window, excluding console')
    window = candidates[0]
    hwnd = wintypes.HWND(window.handle)
    user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
    user32.MonitorFromWindow.restype = wintypes.HANDLE
    user32.GetMonitorInfoW.argtypes = [wintypes.HANDLE, ctypes.POINTER(MonitorInfo)]
    user32.GetMonitorInfoW.restype = wintypes.BOOL
    monitor = user32.MonitorFromWindow(hwnd, 2)
    info = MonitorInfo(); info.size = ctypes.sizeof(info)
    if not monitor or not user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
        raise ctypes.WinError(ctypes.get_last_error())
    bounds = (info.monitor.left, info.monitor.top, info.monitor.right, info.monitor.bottom)
    if bounds[2] <= bounds[0] or bounds[3] <= bounds[1]:
        raise ValueError('Invalid current monitor bounds')
    user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
    user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
    user32.SetWindowLongPtrW.restype = ctypes.c_ssize_t
    style = user32.GetWindowLongPtrW(hwnd, -16)
    extended = user32.GetWindowLongPtrW(hwnd, -20)
    desired = (style & ~WS_OVERLAPPEDWINDOW) | WS_POPUP
    desired_extended = extended & ~(EX_DECORATIONS | 0x8)  # no topmost
    rect = wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        raise ctypes.WinError(ctypes.get_last_error())
    actual = (rect.left, rect.top, rect.right, rect.bottom)
    changed = (style, extended, actual) != (desired, desired_extended, bounds)
    _check_identity(native, created, path)
    if changed:
        for index, before, after in ((-16, style, desired), (-20, extended, desired_extended)):
            if before == after:
                continue
            ctypes.set_last_error(0)
            if not user32.SetWindowLongPtrW(hwnd, index, after) and ctypes.get_last_error():
                raise ctypes.WinError(ctypes.get_last_error())
        _check_identity(native, created, path)
        if not user32.SetWindowPos(hwnd, HWND_NOTOPMOST, bounds[0], bounds[1],
                                  bounds[2]-bounds[0], bounds[3]-bounds[1],
                                  SWP_NOACTIVATE | SWP_FRAMECHANGED | SWP_SHOWWINDOW):
            raise ctypes.WinError(ctypes.get_last_error())
        if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            raise ctypes.WinError(ctypes.get_last_error())
        if ((rect.left, rect.top, rect.right, rect.bottom) != bounds
                or user32.GetWindowLongPtrW(hwnd, -16) != desired
                or user32.GetWindowLongPtrW(hwnd, -20) != desired_extended):
            raise RuntimeError('Borderless window readback differs')
    return dict(pid=pid, creation=created, hwnd=window.handle, mode='borderless-fullscreen',
                monitorBounds=list(bounds), changed=changed, exclusiveFullscreen=False,
                topmost=False, newCallbackOwner=False)


@dataclass(frozen=True)
class Window:
    handle: int
    pid: int
    width: int
    height: int
    title: str


def _window_title(hwnd: wintypes.HWND) -> str:
    length = user32.GetWindowTextLengthW(hwnd)
    if not length:
        return ""
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, length + 1)
    return buffer.value


def windows_for_pid(pid: int, visible_only: bool = True) -> list[Window]:
    result: list[Window] = []

    @EnumWindowsProc
    def callback(hwnd: wintypes.HWND, _lparam: wintypes.LPARAM) -> bool:
        if visible_only and not user32.IsWindowVisible(hwnd):
            return True
        owner = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value != pid:
            return True
        rect = wintypes.RECT()
        if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return True
        width = max(0, rect.right - rect.left)
        height = max(0, rect.bottom - rect.top)
        if width < 200 or height < 120:
            return True
        result.append(Window(int(hwnd), pid, width, height, _window_title(hwnd)))
        return True

    if not user32.EnumWindows(callback, 0):
        raise ctypes.WinError(ctypes.get_last_error())
    return sorted(result, key=lambda item: item.width * item.height, reverse=True)


def _pid_is_alive(pid: int) -> bool:
    try:
        return psutil.Process(pid).is_running()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False


def arrange(native_pid: int, minecraft_pid: int, width: int = 0, height: int = 0,
            *, native_fullscreen: bool = False, show_minecraft: bool = True) -> dict:
    """Keep MC visible and switchable without changing its render resolution."""
    if not _pid_is_alive(native_pid) or not _pid_is_alive(minecraft_pid):
        raise RuntimeError("window layout requires live native and Minecraft processes")
    native = windows_for_pid(native_pid)
    minecraft = windows_for_pid(minecraft_pid) if show_minecraft else windows_for_pid(minecraft_pid,visible_only=False)
    if not native:
        raise RuntimeError(f"no visible native window for PID {native_pid}")
    if not minecraft:
        raise RuntimeError(f"no visible Minecraft window for PID {minecraft_pid}")
    ow, mc = native[0], minecraft[0]
    screen_width = max(640, user32.GetSystemMetrics(0))
    screen_height = max(480, user32.GetSystemMetrics(1))
    resize = int(width) > 0 and int(height) > 0
    width = max(480, min(int(width), screen_width - 32)) if resize else mc.width
    height = max(270, min(int(height), screen_height - 80)) if resize else mc.height
    x = screen_width - width - 16
    y = screen_height - height - 48
    flags = SWP_NOACTIVATE | SWP_NOSENDCHANGING
    if show_minecraft:flags |= SWP_SHOWWINDOW
    if not resize:
        flags |= 0x0001 | 0x0002  # SWP_NOSIZE | SWP_NOMOVE: preserve GLFW framebuffer
        x = y = 0
    rect=wintypes.RECT()
    if not user32.GetWindowRect(wintypes.HWND(mc.handle),ctypes.byref(rect)):
        raise ctypes.WinError(ctypes.get_last_error())
    needs_position=resize and (rect.left,rect.top,rect.right-rect.left,rect.bottom-rect.top)!=(x,y,width,height)
    needs_show=show_minecraft and not user32.IsWindowVisible(wintypes.HWND(mc.handle))
    if needs_position or needs_show:
        if not user32.SetWindowPos(wintypes.HWND(mc.handle), HWND_NOTOPMOST, x, y, width, height, flags):
            raise ctypes.WinError(ctypes.get_last_error())
    fullscreen = native_borderless_fullscreen(native_pid) if native_fullscreen else None
    # ShowWindow(SW_SHOWNOACTIVATE) can restore an already maximized/fullscreen
    # OW window. SetWindowPos with NOMOVE/NOSIZE only reveals it in legacy mode.
    if not native_fullscreen:
        if not user32.SetWindowPos(wintypes.HWND(ow.handle), HWND_NOTOPMOST, 0, 0, 0, 0,
                                  SWP_NOACTIVATE | SWP_SHOWWINDOW | 0x0001 | 0x0002):
            raise ctypes.WinError(ctypes.get_last_error())
    return {"native": ow.__dict__, "minecraft": {**mc.__dict__, "x": x, "y": y,
                                                     "arrangedWidth": width,
                                                     "arrangedHeight": height},
            "nativeFullscreen": fullscreen}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-pid", type=int, required=True)
    parser.add_argument("--minecraft-pid", type=int, required=True)
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=540)
    parser.add_argument("--native-fullscreen", action="store_true")
    args = parser.parse_args()
    import json
    print(json.dumps(arrange(args.native_pid, args.minecraft_pid, args.width, args.height,
                             native_fullscreen=args.native_fullscreen), ensure_ascii=False))
