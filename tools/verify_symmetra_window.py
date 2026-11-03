"""Read-only Symmetra test window diagnosis; never focuses/resizes a window.

Imported without touching Win32. probe() is used only after exact Suite identity
validation, before creating its input driver, and again before lifecycle input.
"""
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[1]
ACCEPTED = ((2560, 1440), (1920, 1080))


def diagnose(snapshot):
    report = dict(snapshot, readOnly=True, resolutionChanged=False, inputSent=False)
    windows = snapshot.get('windows', [])
    candidates = [w for w in windows if w.get('class', '').casefold() == 'tankwindowclass'
                  and w.get('title', '').casefold().startswith('overwatch')]
    report['acceptedClientSizes'] = [list(v) for v in ACCEPTED]
    if len(candidates) != 1:
        report.update(ready=False, cause='RENDER_WINDOW_NOT_UNIQUE', certainty='observed', candidateCount=len(candidates))
        return report
    window = candidates[0]
    actual = tuple(snapshot.get('driverClientSize') or window.get('clientSize', []))
    disagree = snapshot.get('driverClientSize') and list(actual) != window.get('clientSize')
    report.update(clientSize=list(actual), selectedHwnd=window['hwnd'],
                  aspect16by9=len(actual) == 2 and actual[0]*9 == actual[1]*16,
                  ready=actual in ACCEPTED and not window.get('minimized', False) and not disagree)
    if report['ready']:
        report.update(cause='ACCEPTED_CLIENT', certainty='observed')
        return report
    monitor = window.get('monitorBounds', [])
    monitor_size = [monitor[2]-monitor[0], monitor[3]-monitor[1]] if len(monitor) == 4 else []
    if window.get('minimized'):
        cause, certainty = 'MINIMIZED_WINDOW', 'observed'
    elif snapshot.get('driverClientSize') and list(actual) != window.get('clientSize'):
        cause, certainty = 'DRIVER_AND_WIN32_CLIENT_DISAGREE', 'observed; DPI/window-selection cause unresolved'
    elif list(actual) == monitor_size and actual not in ACCEPTED:
        cause, certainty = 'CLIENT_MATCHES_UNSUPPORTED_MONITOR_MODE', 'observed; who changed display mode unresolved'
    elif window.get('outerSize') in [list(v) for v in ACCEPTED] and window.get('decorated'):
        cause, certainty = 'DECORATED_CLIENT_SMALLER_THAN_OUTER_WINDOW', 'observed'
    elif report['aspect16by9']:
        cause, certainty = 'SIXTEEN_BY_NINE_SIZE_OUTSIDE_ACCEPTED_PAIR', 'observed'
    else:
        cause, certainty = 'UNSUPPORTED_CLIENT_CAUSE_UNDETERMINED', 'unresolved; do not infer a resize/remote actor'
    report.update(cause=cause, certainty=certainty)
    return report


def probe(args, phase, driver_size=None):
    import ctypes
    from ctypes import wintypes as w
    import psutil

    expected = (ROOT/'overwatch-2015/Overwatch Beta 0.8.0.24919/GameClientApp.patched.exe').resolve()
    def identity():
        p = psutil.Process(args.pid)
        if abs(p.create_time()-args.created) > .001 or Path(p.exe()).resolve() != expected:
            raise ValueError('Window diagnosis native identity mismatch')
    identity()
    user = ctypes.WinDLL('user32', use_last_error=True)
    def bind(name, types, result):
        fn = getattr(user, name); fn.argtypes = types; fn.restype = result; return fn
    pid_for = bind('GetWindowThreadProcessId', [w.HWND, ctypes.POINTER(w.DWORD)], w.DWORD)
    client = bind('GetClientRect', [w.HWND, ctypes.POINTER(w.RECT)], w.BOOL)
    outer = bind('GetWindowRect', [w.HWND, ctypes.POINTER(w.RECT)], w.BOOL)
    visible = bind('IsWindowVisible', [w.HWND], w.BOOL)
    iconic = bind('IsIconic', [w.HWND], w.BOOL)
    get_class = bind('GetClassNameW', [w.HWND, w.LPWSTR, ctypes.c_int], ctypes.c_int)
    get_title = bind('GetWindowTextW', [w.HWND, w.LPWSTR, ctypes.c_int], ctypes.c_int)
    get_style = bind('GetWindowLongPtrW', [w.HWND, ctypes.c_int], ctypes.c_ssize_t)
    foreground = bind('GetForegroundWindow', [], w.HWND)
    metrics = bind('GetSystemMetrics', [ctypes.c_int], ctypes.c_int)
    monitor_for = bind('MonitorFromWindow', [w.HWND, w.DWORD], w.HANDLE)
    class Monitor(ctypes.Structure):
        _fields_ = [('size', w.DWORD), ('bounds', w.RECT), ('work', w.RECT), ('flags', w.DWORD)]
    monitor_info = bind('GetMonitorInfoW', [w.HANDLE, ctypes.POINTER(Monitor)], w.BOOL)
    dpi = bind('GetDpiForWindow', [w.HWND], w.UINT) if hasattr(user, 'GetDpiForWindow') else None
    report = dict(phase=phase, wallMs=int(time.time()*1000), pid=args.pid, creation=args.created,
                  windows=[], readErrors=[], remoteSession=bool(metrics(0x1000)),
                  primaryScreenSize=[metrics(0), metrics(1)], virtualDesktop=[metrics(i) for i in (76,77,78,79)])
    if driver_size is not None:
        report['driverClientSize'] = list(driver_size)
    owner = w.DWORD(); pid_for(foreground(), ctypes.byref(owner)); report['foregroundPid'] = owner.value
    callback_type = ctypes.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
    @callback_type
    def visit(hwnd, _):
        owner = w.DWORD(); pid_for(hwnd, ctypes.byref(owner))
        if owner.value != args.pid:
            return True
        try:
            name = ctypes.create_unicode_buffer(256); title = ctypes.create_unicode_buffer(512)
            if not get_class(hwnd, name, len(name)):
                raise ctypes.WinError(ctypes.get_last_error())
            get_title(hwnd, title, len(title))
            c = w.RECT(); r = w.RECT()
            if not client(hwnd, ctypes.byref(c)) or not outer(hwnd, ctypes.byref(r)):
                raise ctypes.WinError(ctypes.get_last_error())
            style = get_style(hwnd, -16)
            item = dict(hwnd=int(hwnd), title=title.value, **{'class':name.value}, visible=bool(visible(hwnd)),
                        minimized=bool(iconic(hwnd)), clientSize=[c.right-c.left,c.bottom-c.top],
                        outerSize=[r.right-r.left,r.bottom-r.top], styleHex=hex(style & 0xffffffff),
                        decorated=bool(style & 0x00c00000), dpi=dpi(hwnd) if dpi else None)
            m = Monitor(); m.size = ctypes.sizeof(m)
            if monitor_info(monitor_for(hwnd, 2), ctypes.byref(m)):
                item['monitorBounds'] = [m.bounds.left,m.bounds.top,m.bounds.right,m.bounds.bottom]
            report['windows'].append(item)
        except Exception as error:
            report['readErrors'].append(repr(error))
        return True
    enumerate_windows = bind('EnumWindows', [callback_type, w.LPARAM], w.BOOL)
    if not enumerate_windows(visit, 0):
        raise ctypes.WinError(ctypes.get_last_error())
    identity()
    settings = ROOT/'passthrough-settings.json'
    try:
        content = json.loads(settings.read_text(encoding='utf-8'))
        report['configured'] = {k:content[k] for k in ['width','height','nativeFullscreen','nativeDisplayTemporary'] if k in content}
        report['settingsMtime'] = settings.stat().st_mtime
    except (OSError, ValueError) as error:
        report['readErrors'].append('settings: '+repr(error))
    return diagnose(report)
