"""Block empty-weapon slot inputs only in the SHA-pinned offline OW window.

Windows low-level input filtering in the existing supervisor, not a game hook
or a second native callback owner. Other applications (including MC) pass through.
The OS releases these hooks when the supervisor exits.
"""
import ctypes,threading,atexit,json,time
from ctypes import wintypes as W
from observe_overwatch import ResearchProcess, PoseReader, ROOT

def slot_input(kind,message,key=0):
    return (kind=='key' and message in (0x100,0x101,0x104,0x105) and (0x30<=key<=0x39 or 0x60<=key<=0x69)) or (kind=='mouse' and message in (0x20a,0x20e,0x207,0x208))

class CursorInfo(ctypes.Structure):
    _fields_=[('cbSize',W.DWORD),('flags',W.DWORD),('hCursor',W.HANDLE),('ptScreenPos',W.POINT)]

def weapon_report_ready(report,pid,model,hero,now):
    return (report.get('pid')==pid and report.get('hero')==hero and report.get('modelId')==model
            and report.get('probeVersion',0)>=27 and report.get('enabled') is True and not report.get('failures')
            and report.get('weaponSlotModel')==model and report.get('weaponSlotCount',0)>=2
            and report.get('weaponSlotSelected') in (1,2) and not report.get('weaponSlotRefused')
            and 0<=now-report.get('weaponSlotWallMs',0)<=1500)

def native_weapon_selection(reader):
    """Fresh positive FPS/controller/model proof; failure keeps slot filtering."""
    process=reader.memory;admin=reader.pointer(process.base+0x17b7f90)
    local,=reader.unpack('<I',admin+0x220)
    table=process.read(reader.pointer(admin+0x10),65536)
    controller=reader.entity(table,local);reference=reader.component(controller,0x20)
    info=reader.component(controller,0x3f);hero,=reader.unpack('<Q',info+0x98)
    model,=reader.unpack('<I',reference+0x94);body=reader.entity(table,model)
    if reader.pointer(controller+0x28)!=admin or reader.pointer(body+0x28)!=admin:return False
    items=reader.pointer(admin+0xb0)
    pointers,count,capacity=reader.unpack('<Qii',items+0x4f*24)
    if not 1<=count<=capacity<=256:return False
    component=reader.pointer(pointers);camera=reader.pointer(component+0x40)
    active=reader.pointer(camera+0x260);default=reader.pointer(component+0x50)
    # The existing native logic owner derives slot indices from the actual
    # weapon definition array. A hero ID alone never grants slot input.
    pid=process_pid(process)
    report=json.loads((ROOT/f'native-host/build/body-sync-{pid}.json').read_text(encoding='utf-8'))
    ready=weapon_report_ready(report,pid,model,hero,time.time()*1000)
    return (ready and active==default
            and reader.pointer(active)==process.base+0x15c7000
            and reader.pointer(process.base+0x17b7f90)==admin
            and reader.unpack('<I',admin+0x220)[0]==local
            and reader.unpack('<I',reference+0x94)[0]==model
            and reader.unpack('<Q',info+0x98)[0]==hero
            and reader.pointer(camera+0x260)==active)

def process_pid(process):
    process.kernel.GetProcessId.argtypes=[W.HANDLE];process.kernel.GetProcessId.restype=W.DWORD
    return process.kernel.GetProcessId(process.handle)

class NativeSlotGuard:
    def __init__(self,pid):
        self.pid=pid;self.allowed_weapons=0;self.proof=None;self.keys=0;self.mouse=0;self.error='';self.thread_id=0;self.ready=threading.Event()
        self.user=ctypes.WinDLL('user32',use_last_error=True);self.kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        self.user.GetForegroundWindow.restype=W.HWND
        self.user.GetWindowThreadProcessId.argtypes=[W.HWND,ctypes.POINTER(W.DWORD)]
        self.kernel.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];self.kernel.OpenProcess.restype=W.HANDLE
        self.kernel.WaitForSingleObject.argtypes=[W.HANDLE,W.DWORD];self.kernel.WaitForSingleObject.restype=W.DWORD
        self.kernel.CloseHandle.argtypes=[W.HANDLE]
        self.handle=self.kernel.OpenProcess(0x100400,False,pid)
        if not self.handle:raise ctypes.WinError(ctypes.get_last_error())
        try:
            proof=ResearchProcess(pid)
            try:
                self.kernel.GetProcessTimes.argtypes=[W.HANDLE]+[ctypes.c_void_p]*4
                def creation(handle):
                    times=[ctypes.c_uint64() for _ in range(4)]
                    if not self.kernel.GetProcessTimes(handle,*[ctypes.byref(v) for v in times]):raise ctypes.WinError(ctypes.get_last_error())
                    return times[0].value
                if creation(self.handle)!=creation(proof.handle):raise ValueError('Slot input target process changed')
            except Exception:
                proof.close();raise
            self.proof=proof;self.reader=PoseReader(proof)
        except Exception:self.kernel.CloseHandle(self.handle);self.handle=None;raise
        self.thread=threading.Thread(target=self._run,name='owmc-slot-guard',daemon=True);self.thread.start()
        if not self.ready.wait(3) or self.error:self.close();raise RuntimeError(self.error or 'Slot input guard startup timed out')
        atexit.register(self.close)
    def _target(self):
        pid=W.DWORD();window=self.user.GetForegroundWindow();self.user.GetWindowThreadProcessId(window,ctypes.byref(pid))
        return pid.value==self.pid and self.kernel.WaitForSingleObject(self.handle,0)==0x102 and window==self.user.GetForegroundWindow()
    def _weapon_selection(self,key):
        if key not in (0x31,0x32):return False
        try:
            cursor=CursorInfo();cursor.cbSize=ctypes.sizeof(cursor)
            allowed=(self.user.GetCursorInfo(ctypes.byref(cursor)) and not cursor.flags&1
                     and native_weapon_selection(self.reader) and self._target())
            if allowed:self.allowed_weapons+=1
            return bool(allowed)
        except (OSError,ValueError,RuntimeError):return False
    def _run(self):
        result=ctypes.c_ssize_t;callback=ctypes.WINFUNCTYPE(result,ctypes.c_int,W.WPARAM,W.LPARAM)
        self.user.SetWindowsHookExW.argtypes=[ctypes.c_int,callback,W.HINSTANCE,W.DWORD];self.user.SetWindowsHookExW.restype=W.HANDLE
        self.user.CallNextHookEx.argtypes=[W.HANDLE,ctypes.c_int,W.WPARAM,W.LPARAM];self.user.CallNextHookEx.restype=result
        self.user.UnhookWindowsHookEx.argtypes=[W.HANDLE]
        self.kernel.GetModuleHandleW.argtypes=[W.LPCWSTR];self.kernel.GetModuleHandleW.restype=W.HMODULE
        def key(code,msg,data):
            if code>=0:
                vk=ctypes.cast(data,ctypes.POINTER(W.DWORD))[0]
                if slot_input('key',msg,vk) and self._target() and not self._weapon_selection(vk):self.keys+=1;return 1
            return self.user.CallNextHookEx(None,code,msg,data)
        def mouse(code,msg,data):
            if code>=0 and slot_input('mouse',msg) and self._target():self.mouse+=1;return 1
            return self.user.CallNextHookEx(None,code,msg,data)
        callbacks=[callback(key),callback(mouse)];hooks=[]
        try:
            self.thread_id=self.kernel.GetCurrentThreadId();message=W.MSG();self.user.PeekMessageW(ctypes.byref(message),None,0,0,0)
            for kind,proc in zip((13,14),callbacks):
                hook=self.user.SetWindowsHookExW(kind,proc,self.kernel.GetModuleHandleW(None),0)
                if not hook:raise ctypes.WinError(ctypes.get_last_error())
                hooks.append(hook)
            self.ready.set()
            while self.user.GetMessageW(ctypes.byref(message),None,0,0)>0:
                self.user.TranslateMessage(ctypes.byref(message));self.user.DispatchMessageW(ctypes.byref(message))
        except Exception as error:self.error=str(error);self.ready.set()
        finally:
            for hook in hooks:self.user.UnhookWindowsHookEx(hook)
    def snapshot(self):return dict(pid=self.pid,ready=self.thread.is_alive() and not self.error,blockedKeyEvents=self.keys,allowedWeaponEvents=self.allowed_weapons,blockedMouseEvents=self.mouse,error=self.error)
    def close(self):
        if self.thread_id and self.thread.is_alive():self.user.PostThreadMessageW(self.thread_id,0x12,0,0);self.thread.join(1)
        if self.handle and not self.thread.is_alive():
            self.kernel.CloseHandle(self.handle);self.handle=None
            if self.proof:self.proof.close();self.proof=None
