"""Requested modern Flashbang cooldown in the exact current beta E variable bag."""
import ctypes,struct
from ctypes import wintypes
from observe_native_weapon_states import WeaponStates
from native_armory_binding import primitive,projectile_resources

def inspect(process):
    r=WeaponStates(process);s=r.sample_weapon(False,True)
    admin=r.pointer(process.base+0x17b7f90);table=process.read(r.pointer(admin+16),65536)
    controller=r.entity(table,s['localId']);model=r.entity(table,s['modelId']);ref=r.component(controller,0x20)
    if r.unpack('<Q',r.component(controller,0x3f)+0x98)[0]!=0x02e0000000000042:raise ValueError('Current McCree required')
    matches=[k for k in r.graph_cache if k[2]==0x05800000000001e9]
    if len(matches)!=1:raise ValueError('Flashbang graph scope differs')
    script,graph,_=matches[0];nodes=r.stu_list(graph+0x50);bag=r.pointer(script+0x98)
    if len(nodes)!=18 or [v[0] for v in projectile_resources(r,nodes[7])]!=[0x040000000000037d]:raise ValueError('Original flashbang declaration differs')
    obj,value,bucket=primitive(r,bag,0x0d800000000001d8);kind=r.unpack('<I',obj+0xac)[0]
    if value not in (10,12) or kind not in (2,3):raise ValueError('Flashbang cooldown differs from beta/modern profile')
    if r.unpack('<I',ref+0x94)[0]!=s['modelId'] or r.pointer(r.pointer(r.pointer(script+16)+0x450)+8)!=model:raise ValueError('Flashbang owner changed')
    return dict(modelId=s['modelId'],localId=s['localId'],script=script,graph=graph,bag=bag,object=obj,kind=kind,cooldown=value,bucket=bucket)

def apply(process,pid):
    before=inspect(process)
    if before['cooldown']==12:return dict(modelId=before['modelId'],before=12,after=12,bytesWritten=0)
    k=process.kernel;k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
    k.GetProcessTimes.argtypes=[wintypes.HANDLE]+[ctypes.c_void_p]*4;k.GetProcessTimes.restype=wintypes.BOOL
    k.WriteProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.WriteProcessMemory.restype=wintypes.BOOL
    k.CloseHandle.argtypes=[wintypes.HANDLE]
    def creation(handle):
        v=[ctypes.c_uint64() for _ in range(4)]
        if not k.GetProcessTimes(handle,*[ctypes.byref(x) for x in v]):raise ctypes.WinError(ctypes.get_last_error())
        return v[0].value
    handle=k.OpenProcess(0x428,False,pid)
    if not handle:raise ctypes.WinError(ctypes.get_last_error())
    try:
        if creation(handle)!=creation(process.handle) or inspect(process)!=before:raise ValueError('Flashbang process/owner changed')
        payload=ctypes.c_int32(12) if before['kind']==2 else ctypes.c_float(12);done=ctypes.c_size_t()
        if not k.WriteProcessMemory(handle,before['object']+0xa0,ctypes.byref(payload),4,ctypes.byref(done)) or done.value!=4:raise ctypes.WinError(ctypes.get_last_error())
        after=inspect(process)
        if {k:v for k,v in before.items() if k!='cooldown'}!={k:v for k,v in after.items() if k!='cooldown'} or after['cooldown']!=12:raise ValueError('Flashbang cooldown readback differs')
        return dict(modelId=before['modelId'],before=10,after=12,bytesWritten=4)
    finally:k.CloseHandle(handle)
