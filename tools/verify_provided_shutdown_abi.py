"""Observe the exact interface, optionally restore adapters and request WM_CLOSE.

No forced native termination is used. Timeout/fault remains failed evidence.
Minecraft is retained for subsequent controlled cold starts.
"""
from modpack.config import paths
import argparse
import contextlib
import ctypes
from ctypes import wintypes
import json
import io
from pathlib import Path
import struct
import time
import psutil

from observe_overwatch import ResearchProcess, ROOT
from provided_plugin_symbols import provided_plugin
from repair_provided_shutdown_abi import TARGET, CORRECTED, VTABLE, SLOT, ZERO, digest
from native_crash_evidence import wait_native_crash_reports
from stop_passthrough_session import stop_supervisor
from stop_passthrough import stop, read_report, restoration_complete


def snapshot(process):
    plugin, _, _ = provided_plugin(process)
    def q(address):
        return struct.unpack("<Q", process.read(address, 8))[0]
    if digest(TARGET.read_bytes()) != CORRECTED:
        raise ValueError("Corrected plugin is not installed")
    admin = q(process.base + 0x17b7f90)
    instance = q(plugin + 0x2d0338)
    if q(instance) != plugin + VTABLE or q(instance + 8) != admin:
        raise ValueError("System singleton does not belong to current admin")
    items, count, capacity = struct.unpack("<Qii", process.read(admin + 0xd8, 16))
    if not 1 <= count <= capacity <= 512:
        raise ValueError("System array bounds")
    matches = [q(items + i * 8) for i in range(count)
               if q(q(items + i * 8)) == plugin + VTABLE]
    if matches != [instance]:
        raise ValueError("System interface is not unique")
    if q(plugin + SLOT) != plugin + ZERO or process.read(plugin + ZERO, 3) != b"\x33\xc0\xc3":
        raise ValueError("Mapped ASLR-adjusted interface differs")
    return dict(pluginBase=plugin, instance=instance, admin=admin, systemCount=count,
                slot=q(plugin + SLOT), expected=plugin + ZERO, diskSha256=CORRECTED)


def close_window(pid):
    user = ctypes.WinDLL("user32", use_last_error=True)
    callback = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user.IsWindowVisible.argtypes = [wintypes.HWND]
    user.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    candidates = []
    @callback
    def visit(hwnd, _):
        owner = wintypes.DWORD()
        rect = wintypes.RECT()
        user.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid and user.IsWindowVisible(hwnd) and user.GetClientRect(hwnd, ctypes.byref(rect)):
            area = (rect.right - rect.left) * (rect.bottom - rect.top)
            if area > 0:
                candidates.append((area, hwnd))
        return True
    user.EnumWindows.argtypes = [callback, wintypes.LPARAM]
    if not user.EnumWindows(visit, 0) or not candidates:
        raise RuntimeError("No exact native window to request normal close")
    hwnd = max(candidates)[1]
    user.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    if not user.PostMessageW(hwnd, 0x0010, 0, 0):
        raise ctypes.WinError(ctypes.get_last_error())
    return int(hwnd)


def acknowledge_shutdown_pause(pid, created, render_hwnd):
    """Acknowledge only this verified console's original atexit pause."""
    user = ctypes.WinDLL("user32", use_last_error=True)
    user.IsWindow.argtypes = [wintypes.HWND]
    if user.IsWindow(render_hwnd):
        raise RuntimeError("Render window still exists; no console input allowed")
    native = psutil.Process(pid)
    if native.create_time() != created or Path(native.exe()).resolve() != paths().get('owExecutable'):
        raise ValueError("Closing native identity changed")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.AttachConsole.argtypes = [wintypes.DWORD]
    kernel.GetConsoleProcessList.argtypes = [ctypes.POINTER(wintypes.DWORD), wintypes.DWORD]
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                  ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    class Coord(ctypes.Structure):
        _fields_ = [("x", ctypes.c_short), ("y", ctypes.c_short)]
    class SmallRect(ctypes.Structure):
        _fields_ = [(name, ctypes.c_short) for name in ("left", "top", "right", "bottom")]
    class Screen(ctypes.Structure):
        _fields_ = [("size", Coord), ("cursor", Coord), ("attributes", wintypes.WORD),
                    ("window", SmallRect), ("maximum", Coord)]
    class Key(ctypes.Structure):
        _fields_ = [("down", wintypes.BOOL), ("repeat", wintypes.WORD), ("vk", wintypes.WORD),
                    ("scan", wintypes.WORD), ("char", ctypes.c_wchar), ("control", wintypes.DWORD)]
    class Event(ctypes.Union):
        _fields_ = [("key", Key), ("padding", ctypes.c_byte * 16)]
    class Input(ctypes.Structure):
        _fields_ = [("type", wintypes.WORD), ("event", Event)]
    kernel.GetConsoleScreenBufferInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Screen)]
    kernel.ReadConsoleOutputCharacterW.argtypes = [wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD,
                                                  Coord, ctypes.POINTER(wintypes.DWORD)]
    kernel.WriteConsoleInputW.argtypes = [wintypes.HANDLE, ctypes.POINTER(Input), wintypes.DWORD,
                                         ctypes.POINTER(wintypes.DWORD)]
    kernel.FreeConsole()
    if not kernel.AttachConsole(pid):
        raise ctypes.WinError(ctypes.get_last_error())
    handles = []
    try:
        ids = (wintypes.DWORD * 32)()
        count = kernel.GetConsoleProcessList(ids, len(ids))
        if not 1 <= count <= len(ids) or pid not in ids[:count]:
            raise ValueError("Attached console does not own this native identity")
        for name, access in (("CONOUT$", 0x80000000), ("CONIN$", 0xc0000000)):
            handle = kernel.CreateFileW(name, access, 3, None, 3, 0, None)
            if handle == ctypes.c_void_p(-1).value:
                raise ctypes.WinError(ctypes.get_last_error())
            handles.append(handle)
        screen = Screen()
        if not kernel.GetConsoleScreenBufferInfo(handles[0], ctypes.byref(screen)):
            raise ctypes.WinError(ctypes.get_last_error())
        first = max(0, screen.cursor.y - 60)
        length = min(65535, max(0, screen.cursor.y - first + 1) * screen.size.x)
        if length < 1:
            raise ValueError("Console bounds")
        text = ctypes.create_unicode_buffer(length + 1)
        received = wintypes.DWORD()
        if not kernel.ReadConsoleOutputCharacterW(handles[0], text, length, Coord(0, first), ctypes.byref(received)):
            raise ctypes.WinError(ctypes.get_last_error())
        visible = text[:received.value]
        if ("Process exit initiazed: 0" not in visible or "shutdown" not in visible
                or not any(marker in visible for marker in ("请按任意键", "Press any key", "press any key"))):
            raise ValueError("No verified original shutdown pause; no input sent")
        # Recheck the exact process after console observation, before input.
        if psutil.Process(pid).create_time() != created:
            raise ValueError("PID reused before console acknowledgement")
        events = (Input * 2)()
        for index in range(2):
            events[index].type = 1
            events[index].event.key = Key(index == 0, 1, 0x0d, 0x1c, "\r", 0)
        sent = wintypes.DWORD()
        if not kernel.WriteConsoleInputW(handles[1], events, 2, ctypes.byref(sent)) or sent.value != 2:
            raise OSError("Exact console acknowledgement failed")
        return dict(acknowledged=True, consolePids=list(ids[:count]),
                    observedText=visible, globalKeyboardInput=False)
    finally:
        for handle in handles:
            kernel.CloseHandle(handle)
        kernel.FreeConsole()


def verify(pid, folder, close=False):
    folder.mkdir(parents=True, exist_ok=False)
    process = ResearchProcess(pid)
    native = psutil.Process(pid)
    created = native.create_time()
    out = dict(pid=pid, creation=created, executable=str(process.path), passed=False,
               requestedNormalClose=close, forcedTermination=False)
    def save():
        (folder / "result.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    try:
        out["mapped"] = snapshot(process)
        save()
        if close:
            stop_supervisor()
            out["restoration"] = {}
            for prefix, options in [("native-emissions", dict(emissions=True)),
                                    ("weapon-gate", dict(weapon=True)),
                                    ("body-sync", dict(body=True)), ("world-live", {})]:
                path = ROOT / f"native-host/build/{prefix}-{pid}.json"
                value = read_report(path)
                if not restoration_complete(value, pid, compositor=prefix == "world-live"):
                    with contextlib.redirect_stdout(io.StringIO()):
                        value = stop(pid, **options)
                if not restoration_complete(value, pid, compositor=prefix == "world-live"):
                    raise RuntimeError("Incomplete adapter restoration: " + prefix)
                out["restoration"][prefix] = value
                save()
            # Correction must still hold AFTER the logic/render adapters restore.
            out["afterRestoration"] = snapshot(process)
            out["closeHwnd"] = close_window(pid)
            save()
            try:
                out["exitCode"] = native.wait(timeout=3)
            except psutil.TimeoutExpired:
                out["shutdownPause"] = acknowledge_shutdown_pause(pid, created, out["closeHwnd"])
                save()
                out["exitCode"] = native.wait(timeout=20)
            out["crashReports"] = wait_native_crash_reports(pid, created, process.path, seconds=2)
            if out["crashReports"] or out["exitCode"] != 0:
                raise RuntimeError("Normal close returned an error or a matching crash report")
        out["passed"] = True
    except Exception as failure:
        out["error"] = repr(failure)
    finally:
        process.close()
        save()
    print(json.dumps({key: out.get(key) for key in ("pid", "passed", "error", "exitCode", "forcedTermination")}))
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--close", action="store_true")
    args = parser.parse_args()
    result = verify(args.pid, args.output, args.close)
    raise SystemExit(0 if result["passed"] else 1)
