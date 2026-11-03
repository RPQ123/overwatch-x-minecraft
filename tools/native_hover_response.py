"""Remove only the measured native Pharah hover startup Wait (.2s), not fuel/physics."""
import ctypes,struct,math
from ctypes import wintypes
from observe_native_weapon_states import WeaponStates

HERO=0x02e0000000000008
RESOURCE=0x0580000000000025

def delay_value(kind,raw):
    if kind!=0x7b13a0d4 or len(raw)!=4:raise ValueError('Hover wait must be the measured float config')
    value=struct.unpack('<f',raw)[0]
    if not math.isfinite(value) or (value!=0 and abs(value-.2)>1e-7):raise ValueError('Hover startup delay differs from measured .2s/0s')
    return value

def inspect(process):
    r=WeaponStates(process);s=r.sample_weapon(False,True)
    admin=r.pointer(process.base+0x17b7f90);table=process.read(r.pointer(admin+16),65536)
    controller=r.entity(table,s['localId']);model=r.entity(table,s['modelId']);reference=r.component(controller,0x20);info=r.component(controller,0x3f)
    if r.unpack('<Q',info+0x98)[0]!=HERO:raise ValueError('Pharah hover owner required')
    matches=[k for k in r.graph_cache if k[2]==RESOURCE]
    if len(matches)!=1:raise ValueError('Native hover graph differs')
    script,graph,_=matches[0];nodes=r.stu_list(graph+0x50)
    if len(nodes)!=37:raise ValueError('Native hover graph count differs')
    kind,field,category,declared=r.bindings.field(nodes[2],0xdb0e39db)
    if kind!=0x65f158da or category!=2:raise ValueError('Hover startup Wait declaration differs')
    value=r.pointer(field);_,value_type,size=r.bindings.metadata(value)
    if size!=24:raise ValueError('Hover startup Wait float layout differs')
    current=delay_value(value_type,process.read(value+16,4))
    if r.pointer(r.pointer(r.pointer(script+0x10)+0x450)+8)!=model or r.unpack('<I',reference+0x94)[0]!=s['modelId'] or r.pointer(model+0x28)!=admin:raise ValueError('Hover owner changed')
    return dict(hero=HERO,localId=s['localId'],modelId=s['modelId'],model=model,script=script,graph=graph,node=nodes[2],field=field,value=value,configType=value_type,delay=current)

def apply(process,pid):
    before=inspect(process)
    if before['delay']==0:return dict(modelId=before['modelId'],before=0,after=0,bytesWritten=0)
    k=process.kernel;k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
    k.GetProcessTimes.argtypes=[wintypes.HANDLE]+[ctypes.c_void_p]*4;k.GetProcessTimes.restype=wintypes.BOOL
    k.GetProcessId.argtypes=[wintypes.HANDLE];k.GetProcessId.restype=wintypes.DWORD
    k.WriteProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.WriteProcessMemory.restype=wintypes.BOOL
    k.CloseHandle.argtypes=[wintypes.HANDLE]
    def creation(handle):
        values=[ctypes.c_uint64() for _ in range(4)]
        if not k.GetProcessTimes(handle,*[ctypes.byref(v) for v in values]):raise ctypes.WinError(ctypes.get_last_error())
        return values[0].value
    handle=k.OpenProcess(0x428,False,pid)
    if not handle:raise ctypes.WinError(ctypes.get_last_error())
    try:
        if k.GetProcessId(process.handle)!=pid or creation(handle)!=creation(process.handle) or inspect(process)!=before:raise ValueError('Hover process/owner changed before write')
        zero=ctypes.c_float(0);written=ctypes.c_size_t()
        if not k.WriteProcessMemory(handle,before['value']+16,ctypes.byref(zero),4,ctypes.byref(written)) or written.value!=4:raise ctypes.WinError(ctypes.get_last_error())
        after=inspect(process)
        if {k:v for k,v in before.items() if k!='delay'}!={k:v for k,v in after.items() if k!='delay'} or after['delay']!=0:raise ValueError('Hover delay write readback/owner differs')
        return dict(modelId=before['modelId'],before=before['delay'],after=0,bytesWritten=4)
    finally:k.CloseHandle(handle)
