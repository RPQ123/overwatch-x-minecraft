"""Load only the workspace render probe into the verified offline OW research process."""
from pathlib import Path
import argparse
import ctypes
from ctypes import wintypes
import json
import hashlib
import math
import struct
import time
from observe_overwatch import ROOT, ResearchProcess, PoseReader

DLL = ROOT / "native-host/build/owmc-render-probe.dll"
class ModuleEntry(ctypes.Structure):
    _fields_ = [("dwSize", wintypes.DWORD), ("th32ModuleID", wintypes.DWORD),
                ("th32ProcessID", wintypes.DWORD), ("GlblcntUsage", wintypes.DWORD),
                ("ProccntUsage", wintypes.DWORD), ("modBaseAddr", ctypes.c_void_p),
                ("modBaseSize", wintypes.DWORD), ("hModule", wintypes.HMODULE),
                ("szModule", wintypes.WCHAR * 256), ("szExePath", wintypes.WCHAR * 260)]

def bind(kernel, name, result, arguments):
    function = getattr(kernel, name)
    function.restype, function.argtypes = result, arguments
    return function

def attach(pid, native_projection=False, trace=False, scene=False, patch=False, motion=False, camera_trace=False,creative=False,layer_trace=False,layer_stream=False,selection_trace=False):
    if selection_trace:camera_trace=True
    if layer_stream:
        raise RuntimeError('Continuous native-layer V2/V3 is retired after two real crashes. Use the independently tested passthrough route in docs/PASSTHROUGH.md; do not reload these DLLs.')
    if creative:patch=True
    DLL = ROOT / ("native-host/build/owhero-layer-stream-v3.dll" if layer_stream else "native-host/build/owhero-layer-probe-v1.dll" if layer_trace else "native-host/build/owmc-render-probe-v9.dll" if creative else "native-host/build/owmc-selection-trace-v1.dll" if selection_trace else "native-host/build/owmc-camera-trace.dll" if camera_trace else "native-host/build/owmc-depth-trace.dll" if trace else
                  "native-host/build/owmc-movement-probe-v2.dll" if motion else
                  "native-host/build/owmc-render-probe-v7.dll" if patch else
                  "native-host/build/owmc-render-probe-v4.dll" if scene else
                  "native-host/build/owmc-render-probe-v2.dll" if native_projection
                  else "native-host/build/owmc-render-probe.dll")
    # Verify path and complete executable hash before obtaining write/thread rights.
    verified = ResearchProcess(pid)
    verified.close()
    if not DLL.is_file() or (not layer_stream and not layer_trace and not trace and not motion and not camera_trace and not (DLL.parent / ("patch-mesh.bin" if patch else "stone-mesh.bin")).is_file()):
        raise FileNotFoundError("Build/test the local probe and export its real Minecraft mesh first")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    close = bind(kernel, "CloseHandle", wintypes.BOOL, [wintypes.HANDLE])
    create_snapshot = bind(kernel, "CreateToolhelp32Snapshot", wintypes.HANDLE, [wintypes.DWORD, wintypes.DWORD])
    first = bind(kernel, "Module32FirstW", wintypes.BOOL, [wintypes.HANDLE, ctypes.POINTER(ModuleEntry)])
    next_module = bind(kernel, "Module32NextW", wintypes.BOOL, [wintypes.HANDLE, ctypes.POINTER(ModuleEntry)])
    get_module = bind(kernel, "GetModuleHandleW", wintypes.HMODULE, [wintypes.LPCWSTR])
    get_address = bind(kernel, "GetProcAddress", ctypes.c_void_p, [wintypes.HMODULE, ctypes.c_char_p])
    get_owner = bind(kernel, "GetModuleHandleExW", wintypes.BOOL, [wintypes.DWORD, ctypes.c_void_p, ctypes.POINTER(wintypes.HMODULE)])
    module_name = bind(kernel, "GetModuleFileNameW", wintypes.DWORD, [wintypes.HMODULE, wintypes.LPWSTR, wintypes.DWORD])
    loader = get_address(get_module("kernel32.dll"), b"LoadLibraryW")
    owner = wintypes.HMODULE()
    if not loader or not get_owner(6, loader, ctypes.byref(owner)):
        raise ctypes.WinError(ctypes.get_last_error())
    name = ctypes.create_unicode_buffer(32768)
    if not module_name(owner, name, len(name)):
        raise ctypes.WinError(ctypes.get_last_error())
    owner_name = Path(name.value).name.lower()
    snapshot = create_snapshot(0x8 | 0x10, pid)
    if snapshot == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    remote_owner = None
    render_ranges = []
    previous_anchor_module = None
    try:
        module = ModuleEntry(); module.dwSize = ctypes.sizeof(module)
        success = first(snapshot, ctypes.byref(module))
        while success:
            if Path(module.szExePath).resolve() == DLL.resolve():
                raise ValueError("Probe is already loaded; stop it or normally restart OW before rebuilding/reloading")
            if module.szModule.lower().startswith(("owmc-render-probe","owhero-layer-stream")):
                render_ranges.append((module.modBaseAddr,module.modBaseAddr+module.modBaseSize))
            if patch and Path(module.szExePath).resolve()==(DLL.parent/'owmc-render-probe-v6.dll').resolve():
                previous_anchor_module=module.modBaseAddr
            if module.szModule.lower() == owner_name:
                if Path(module.szExePath).resolve() != Path(name.value).resolve():
                    raise ValueError("Remote loader module differs from this machine's verified module")
                remote_owner = module.modBaseAddr
            success = next_module(snapshot, ctypes.byref(module))
    finally:
        close(snapshot)
    if remote_owner is None:
        raise ValueError("Matching system loader module not found in the research process")
    if not trace and not motion and not camera_trace and render_ranges:
        # Loaded but stopped code is allowed; an active old renderer is not.
        with_process = ResearchProcess(pid)
        try:
            reader = PoseReader(with_process)
            engine = reader.pointer(with_process.base + 0x181e3e0)
            a = reader.pointer(engine + 0x900); b = reader.pointer(a + 0x2e0)
            c = reader.pointer(b); swap = reader.pointer(c + 8)
            table = reader.pointer(swap)
            callback = reader.pointer(table + 8*8)
            if any(start <= callback < end for start,end in render_ranges):
                raise ValueError("An old render probe is still active; request --stop and wait for restoration before attaching another")
        finally:
            with_process.close()
    remote_loader = remote_owner + loader - owner.value
    if patch and not creative and previous_anchor_module is not None:
        old_file=DLL.parent/'owmc-render-probe-v6.dll'
        # Our own exact V6 symbol, not a game offset. Reject a rebuilt binary.
        if hashlib.sha256(old_file.read_bytes()).hexdigest()!='9c9b1fd7da951b9476702a13e922e663b0761714ce06848d84bede988fd002f8':
            raise ValueError('Cannot preserve anchor from an unrecognized own V6 binary')
        observer=ResearchProcess(pid)
        try: position=struct.unpack('<3f',observer.read(previous_anchor_module+0x12b100,12))
        finally:observer.close()
        if not all(math.isfinite(v) and abs(v)<1e6 for v in position):raise ValueError('Invalid old patch anchor')
        (DLL.parent/'preserved-anchor.bin').write_bytes(struct.pack('<8sQIIfff',b'OWMCAN01',int(time.time()*1000),pid,0,*position))
    open_process = bind(kernel, "OpenProcess", wintypes.HANDLE, [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD])
    allocate = bind(kernel, "VirtualAllocEx", ctypes.c_void_p, [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_size_t, wintypes.DWORD, wintypes.DWORD])
    write = bind(kernel, "WriteProcessMemory", wintypes.BOOL, [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)])
    create_thread = bind(kernel, "CreateRemoteThread", wintypes.HANDLE, [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_size_t,
                        ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)])
    wait = bind(kernel, "WaitForSingleObject", wintypes.DWORD, [wintypes.HANDLE, wintypes.DWORD])
    free = bind(kernel, "VirtualFreeEx", wintypes.BOOL, [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_size_t, wintypes.DWORD])
    process = open_process(0x400 | 0x10 | 0x20 | 0x8 | 0x2, False, pid)
    if not process:
        raise ctypes.WinError(ctypes.get_last_error())
    buffer = None; thread = None; finished = False
    started_ns = time.time_ns()
    try:
        path = ctypes.create_unicode_buffer(str(DLL.resolve()))
        buffer = allocate(process, None, ctypes.sizeof(path), 0x3000, 0x04)
        copied = ctypes.c_size_t()
        if not buffer or not write(process, buffer, path, ctypes.sizeof(path), ctypes.byref(copied)) or copied.value != ctypes.sizeof(path):
            raise ctypes.WinError(ctypes.get_last_error())
        thread = create_thread(process, None, 0, remote_loader, buffer, 0, None)
        if not thread:
            raise ctypes.WinError(ctypes.get_last_error())
        if wait(thread, 30000) != 0:
            raise TimeoutError("Native loader did not finish; don't reload the probe")
        finished = True
    finally:
        if buffer and (finished or thread is None): free(process, buffer, 0, 0x8000)
        if thread: close(thread)
        close(process)
    report = DLL.parent / (f"hero-stream-{pid}.json" if layer_stream else f"hero-layer-{pid}.json" if layer_trace else f"selection-trace-{pid}.json" if selection_trace else f"camera-trace-{pid}.json" if camera_trace else f"motion-{pid}.json" if motion else f"trace-{pid}.json" if trace else f"host-{pid}.json")
    for _ in range(48 if trace or camera_trace or layer_trace else 20):
        if report.is_file() and report.stat().st_mtime_ns >= started_ns:
            try:
                result = json.loads(report.read_text())
                if result.get("pid") == pid and (not native_projection or result.get("projectionSource") == "native-crosshair-matrices"):
                    if (scene or patch) and result.get("passSource") != "native-stencil-boundary":
                        time.sleep(.25);continue
                    if (scene or patch) and (not result.get("enabled") or result.get("failures",0)):
                        raise RuntimeError("Native scene renderer disabled; inspect the report before retrying")
                    if (scene or patch) and not result.get("draws",0):
                        time.sleep(.25);continue
                    if patch and (not result.get("patchMode") or not result.get("patchFresh")):
                        time.sleep(.25);continue
                    if patch and (not result.get("collisionAttached") or result.get("collisionWriteFailures",0)):
                        raise RuntimeError("Native collision adapter did not attach cleanly; inspect report")
                    if patch and result.get('projectionSource')!='native-scene-upload':
                        raise RuntimeError('Original scene projection did not attach; inspect camera upload hooks')
                    if creative and (not result.get('creativeMode') or not result.get('creativeEntered')):
                        time.sleep(.25);continue
                    if layer_trace and (not result.get('restored') or result.get('failures') or not result.get('boundaryCaptured') or not result.get('finalCaptured')):
                        raise RuntimeError('Original layer capture incomplete; inspect the report before continuing')
                    if layer_stream:
                        if result.get('failures') or not result.get('enabled'):raise RuntimeError('Native hero stream disabled; inspect report')
                        if not result.get('published') or not result.get('handDraws') or not result.get('hudDraws'):
                            time.sleep(.25);continue
                    print(json.dumps({k:v for k,v in result.items() if k not in ("events","captures","draws") or not isinstance(v,list)})); return
            except json.JSONDecodeError:
                pass
        time.sleep(.25)
    raise RuntimeError("DLL loader completed but renderer report is unavailable; inspect process/modules before retrying")

def stop(pid, reanchor=False, motion=False,layer=False):
    verified=ResearchProcess(pid)
    verified.close()
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    open_event = bind(kernel, "OpenEventW", wintypes.HANDLE, [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR])
    set_event = bind(kernel, "SetEvent", wintypes.BOOL, [wintypes.HANDLE])
    close = bind(kernel, "CloseHandle", wintypes.BOOL, [wintypes.HANDLE])
    event_name = f"Local\\OWHeroStreamStop_{pid}" if layer else f"Local\\OWMCMotionStop_{pid}" if motion else f"Local\\OWMCProbe{'Place' if reanchor else 'Stop'}_{pid}"
    event = open_event(2, False, event_name)
    if not event: raise ctypes.WinError(ctypes.get_last_error())
    try:
        if not set_event(event): raise ctypes.WinError(ctypes.get_last_error())
    finally: close(event)
    print("Movement observation stop requested; original movement tables will be restored." if motion else
          "Probe anchor placement requested; applied on the next valid rendering frame." if reanchor else
          "Render probe stop requested; original rendering tables are restored by its worker.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid", type=int, required=True)
    control=parser.add_mutually_exclusive_group()
    control.add_argument("--stop", action="store_true")
    control.add_argument("--stop-motion", action="store_true")
    control.add_argument("--stop-layer",action="store_true")
    control.add_argument("--reanchor", action="store_true", help="Place the proof block ahead of the current native camera")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--native-projection", action="store_true", help="Use the tested v2 probe with original host matrices")
    modes.add_argument("--trace", action="store_true", help="Observe three frames then restore the existing render callbacks")
    modes.add_argument("--scene", action="store_true", help="Use tested v3 scene-depth and pre-interface boundary")
    modes.add_argument("--patch", action="store_true", help="Draw live real MC patch snapshots with original scene depth")
    modes.add_argument("--motion-trace",action="store_true",help="Observe movement stages without player writes; preserves moving samples, automatically stops after ten minutes")
    modes.add_argument("--selection-trace",action="store_true",help="Bounded read-only selection camera pass trace")
    modes.add_argument("--camera-trace",action="store_true",help="Observe original shader camera buffers for three frames and restore callbacks")
    modes.add_argument("--layer-trace",action="store_true",help="Observe three frames of original color/depth/HUD boundaries without changing the image")
    modes.add_argument("--layer-stream",action="store_true",help="Export native first-person hands and HUD on transparent backgrounds; keeps original display")
    modes.add_argument("--creative",action="store_true",help="Use original map camera with the isolated 32x32 creative superflat guest")
    args = parser.parse_args()
    if args.pid <= 0: parser.error("A valid exact research PID is required")
    try: stop(args.pid,args.reanchor,args.stop_motion,args.stop_layer) if args.stop or args.reanchor or args.stop_motion or args.stop_layer else attach(args.pid, args.native_projection, args.trace, args.scene,args.patch,args.motion_trace,args.camera_trace,args.creative,args.layer_trace,args.layer_stream,args.selection_trace)
    except (OSError, ValueError, RuntimeError) as error: parser.exit(1, f"Host probe unavailable: {error}\n")
