"""Find possible game owners without opening unrelated Windows processes."""
import ctypes
from ctypes import wintypes as w
from pathlib import Path

import psutil


class ProcessEntry(ctypes.Structure):
    _fields_ = [('size', w.DWORD), ('usage', w.DWORD), ('pid', w.DWORD),
                ('heap', ctypes.c_size_t), ('module', w.DWORD), ('threads', w.DWORD),
                ('parent', w.DWORD), ('priority', w.LONG), ('flags', w.DWORD),
                ('image', w.WCHAR * 260)]


def process_images():
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateToolhelp32Snapshot.argtypes = (w.DWORD, w.DWORD)
    kernel.CreateToolhelp32Snapshot.restype = w.HANDLE
    for function in (kernel.Process32FirstW, kernel.Process32NextW):
        function.argtypes = (w.HANDLE, ctypes.POINTER(ProcessEntry))
        function.restype = w.BOOL
    kernel.CloseHandle.argtypes = (w.HANDLE,)
    kernel.CloseHandle.restype = w.BOOL
    handle = kernel.CreateToolhelp32Snapshot(0x00000002, 0)  # TH32CS_SNAPPROCESS.
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        entry = ProcessEntry(size=ctypes.sizeof(ProcessEntry))
        if not kernel.Process32FirstW(handle, ctypes.byref(entry)):
            raise ctypes.WinError(ctypes.get_last_error())
        result = []
        while True:
            if entry.pid:
                result.append((entry.pid, entry.image.casefold()))
            if not kernel.Process32NextW(handle, ctypes.byref(entry)):
                if ctypes.get_last_error() != 18:  # ERROR_NO_MORE_FILES
                    raise ctypes.WinError(ctypes.get_last_error())
                return result
    finally:
        kernel.CloseHandle(handle)


def native_image(name, target):
    name = name.casefold()
    return name == target.name.casefold() or (name.startswith('gameclientapp') and name.endswith('.exe'))


JAVA_IMAGES = {'java.exe', 'javaw.exe'}


def game_images():
    try:
        return process_images()
    except OSError as failure:
        raise RuntimeError('Windows 未能列出进程，暂时无法确认游戏是否已退出。请正常关闭游戏后重试。') from failure


def game_processes(*, native=None, profiles=(), java=None):
    """Match exact paths or --gameDir. Keep unverified OW candidates separate from foreign software."""
    images = game_images()
    profiles = {profile.resolve() for profile in profiles}
    native = native.resolve() if native is not None else None
    owned_java = {java.resolve(), java.with_name('javaw.exe').resolve()} if java is not None else set()
    result = []
    for pid, image in images:
        ow_candidate = native is not None and native_image(image, native)
        if not ow_candidate and not (profiles and image in JAVA_IMAGES):
            continue
        executable = None
        try:
            process = psutil.Process(pid)
            path = Path(process.exe())
            if not path.is_absolute():
                raise psutil.AccessDenied(pid)
            executable = path.resolve()
            if ow_candidate:
                match = executable == native
            elif executable.name.casefold() in JAVA_IMAGES:
                arguments = process.cmdline()
                if arguments is None:
                    raise psutil.AccessDenied(pid)
                match = any(flag == '--gameDir' and Path(value).resolve() in profiles
                            for flag, value in zip(arguments, arguments[1:]))
            else:
                continue  # The snapshot PID has already been reused by another image.
            if match and process.is_running():
                result.append(process)
        except psutil.NoSuchProcess:
            continue
        except (psutil.AccessDenied, OSError) as failure:
            if ow_candidate or executable in owned_java:
                game = '原版 OW' if ow_candidate else '本包的 Java'
                raise RuntimeError(f'发现可能冲突的{game}（PID {pid}），无法核对身份。请先正常退出该游戏，再重试。') from failure
    return result
