"""Minimal Core Audio session enumeration and creation notifications for the loading guard."""
from __future__ import annotations

from contextlib import contextmanager
import ctypes as c
from ctypes import wintypes as w
import queue
import uuid


HRESULT = c.c_long
PTR = c.c_void_p
GUID = c.c_ubyte * 16
CLSID_DEVICE_ENUM = 'bcde0395-e52f-467c-8e3d-c4579291692e'
IID_DEVICE_ENUM = 'a95664d2-9614-4f35-a746-de8db63617e6'
IID_SESSION_MANAGER = '77aa99a0-1bd6-484f-8bc7-2c654c9a9b6f'
IID_SESSION_CONTROL = 'bfb7ff88-7239-4fc9-8fa2-07c950be9c6d'
IID_NOTIFICATION = '641dd20b-4d41-49cc-aba3-174b9477bb08'
IID_VOLUME = '87ce5498-68d6-44e5-9215-6da47ef883d8'
IID_UNKNOWN = '00000000-0000-0000-c000-000000000046'
DEVICE_INVALIDATED = 0x88890004


def guid(name):
    return GUID.from_buffer_copy(uuid.UUID(name).bytes_le)


class AudioError(OSError):
    def __init__(self, result):
        self.code = result & 0xffffffff
        super().__init__(f'Core Audio HRESULT 0x{self.code:08x}')


def checked(result):
    if result < 0:
        raise AudioError(result)
    return result


class Com:
    def __init__(self, pointer):
        self.pointer = pointer.value if isinstance(pointer, PTR) else pointer

    def call(self, slot, types=(), *args, result=HRESULT):
        table = c.cast(self.pointer, c.POINTER(c.POINTER(PTR))).contents
        return c.WINFUNCTYPE(result, PTR, *types)(table[slot])(self.pointer, *args)

    def interface(self, name):
        value = PTR()
        checked(self.call(0, (PTR, PTR), c.byref(guid(name)), c.byref(value)))
        return Com(value)

    def out(self, slot, types=(), *args):
        value = PTR()
        checked(self.call(slot, (*types, PTR), *args, c.byref(value)))
        return Com(value)

    def close(self):
        if self.pointer:
            self.call(2, result=w.ULONG)
            self.pointer = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


class Notification:
    """Callback retains the new COM pointer and wakes the MTA worker."""
    def __init__(self, announce):
        query = c.WINFUNCTYPE(HRESULT, PTR, PTR, c.POINTER(PTR))
        ref = c.WINFUNCTYPE(w.ULONG, PTR)
        notify = c.WINFUNCTYPE(HRESULT, PTR, PTR)
        self.refs = 1

        @query
        def query_interface(this, iid, output):
            if not output:
                return c.c_long(0x80004003).value
            if c.string_at(iid, 16) in (bytes(guid(IID_UNKNOWN)), bytes(guid(IID_NOTIFICATION))):
                output[0] = this
                self.refs += 1
                return 0
            output[0] = None
            return c.c_long(0x80004002).value

        @ref
        def add_ref(_):
            self.refs += 1
            return self.refs

        @ref
        def release(_):
            self.refs -= 1
            return self.refs

        @notify
        def on_created(_, session):
            if session:
                announce(session)
            return 0

        self.callbacks = (query_interface, add_ref, release, on_created)
        self.table = (PTR * 4)(*(c.cast(fn, PTR) for fn in self.callbacks))
        self.object = c.cast(self.table, PTR)
        self.pointer = c.cast(c.pointer(self.object), PTR)


class AudioSession:
    def __init__(self, device, control, free):
        self.device, self.control, self.free = device, control, free

    def process_id(self):
        pid = w.DWORD()
        status = checked(self.control.call(14, (PTR,), c.byref(pid)))
        return pid.value, status == 0

    def identifier(self, *, instance=False):
        value = PTR()
        checked(self.control.call(13 if instance else 12, (PTR,), c.byref(value)))
        try:
            return c.wstring_at(value) if value.value else ''
        finally:
            self.free(value)

    def volume(self):
        return SessionVolume(self.control.interface(IID_VOLUME))


class SessionVolume:
    def __init__(self, com):
        self.com = com

    def muted(self):
        value = w.BOOL()
        checked(self.com.call(6, (PTR,), c.byref(value)))
        return bool(value.value)

    def mute(self, value):
        checked(self.com.call(5, (w.BOOL, PTR), bool(value), None))
        if self.muted() != value:
            raise RuntimeError('音频会话静音回读不一致。')

    def close(self):
        self.com.close()


class CoreAudio:
    """Operate only on a non-UI MTA thread. Callers choose the scoped sessions."""
    def __init__(self, wake=None):
        self.wake = wake
        self.pending = queue.SimpleQueue()
        self.managers = {}
        self.callbacks = []
        self.closing = False

    def __enter__(self):
        self.ole = c.WinDLL('ole32')
        self.ole.CoInitializeEx.argtypes = [PTR, w.DWORD]
        self.ole.CoInitializeEx.restype = HRESULT
        self.ole.CoCreateInstance.argtypes = [PTR, PTR, w.DWORD, PTR, c.POINTER(PTR)]
        self.ole.CoCreateInstance.restype = HRESULT
        self.ole.CoTaskMemFree.argtypes = [PTR]
        checked(self.ole.CoInitializeEx(None, 0))  # COINIT_MULTITHREADED
        enum = PTR()
        try:
            checked(self.ole.CoCreateInstance(c.byref(guid(CLSID_DEVICE_ENUM)), None, 23,
                                              c.byref(guid(IID_DEVICE_ENUM)), c.byref(enum)))
            self.devices = Com(enum)
        except BaseException:
            self.ole.CoUninitialize()
            raise
        return self

    def _announce(self, device, pointer):
        if not self.closing:
            control = Com(pointer)
            control.call(1, result=w.ULONG)
            if self.closing:
                control.close()
                return
            self.pending.put((device, control))
            if self.wake:
                self.wake.set()

    def refresh(self):
        seen = set()
        with self.devices.out(3, (c.c_int, w.DWORD), 0, 1) as devices:  # active render endpoints
            count = w.UINT()
            checked(devices.call(3, (PTR,), c.byref(count)))
            for index in range(count.value):
                with devices.out(4, (w.UINT,), index) as device:
                    value = PTR()
                    checked(device.call(5, (PTR,), c.byref(value)))
                    try:
                        name = c.wstring_at(value)
                    finally:
                        self.ole.CoTaskMemFree(value)
                    seen.add(name)
                    if name in self.managers:
                        continue
                    manager = device.out(3, (PTR, w.DWORD, PTR), c.byref(guid(IID_SESSION_MANAGER)), 23, None)
                    listener = None
                    try:
                        if self.wake:
                            listener = Notification(lambda pointer, endpoint=name: self._announce(endpoint, pointer))
                            self.callbacks.append(listener)
                            checked(manager.call(6, (PTR,), listener.pointer))
                        with manager.out(5) as sessions:
                            total = c.c_int()
                            checked(sessions.call(3, (PTR,), c.byref(total)))  # arms notifications
                        self.managers[name] = (manager, listener)
                    except BaseException:
                        self._close_manager(manager, listener)
                        raise
        for name in self.managers.keys() - seen:
            self._close_manager(*self.managers.pop(name))

    def _close_manager(self, manager, listener):
        if listener:
            manager.call(7, (PTR,), listener.pointer)
        manager.close()

    @contextmanager
    def _session(self, device, control):
        with control:
            with control.interface(IID_SESSION_CONTROL) as extended:
                yield AudioSession(device, extended, self.ole.CoTaskMemFree)

    def sessions(self, *, enumerate_all=True):
        while not self.pending.empty():
            device, control = self.pending.get_nowait()
            try:
                with self._session(device, control) as session:
                    yield session
            except AudioError as failure:
                if failure.code != DEVICE_INVALIDATED:
                    raise
        if not enumerate_all:
            return
        for name, (manager, _) in tuple(self.managers.items()):
            try:
                with manager.out(5) as enumerator:
                    count = c.c_int()
                    checked(enumerator.call(3, (PTR,), c.byref(count)))
                    for index in range(count.value):
                        with self._session(name, enumerator.out(4, (c.c_int,), index)) as session:
                            yield session
            except AudioError as failure:
                if failure.code != DEVICE_INVALIDATED:
                    raise
                self._close_manager(*self.managers.pop(name))

    def __exit__(self, *_):
        self.closing = True
        try:
            for manager, listener in self.managers.values():
                self._close_manager(manager, listener)
            while not self.pending.empty():
                _, control = self.pending.get_nowait()
                control.close()
            self.devices.close()
        finally:
            self.ole.CoUninitialize()
