"""Typed original hero ultimate meter; bounded feedback/test grants, no code calls."""
import ctypes,math,struct
from ctypes import wintypes
from observe_native_weapon_states import WeaponStates

def inspect(process):
    r=WeaponStates(process);s=r.sample_weapon(require_volley=False)
    admin=r.pointer(process.base+0x17b7f90);table=process.read(r.pointer(admin+0x10),65536)
    controller=r.entity(table,s['localId']);model=r.entity(table,s['modelId'])
    reference=r.component(controller,0x20);info=r.component(controller,0x3f)
    hero=r.unpack('<Q',info+0x98)[0];bag_address=r.component(model,0x23)+0xc0+0x2e0;bag=r.pointer(bag_address)
    values={}
    for bucket in range(16):
        for rid,value in struct.iter_unpack('<QQ',r.vector(bag+0xa0+bucket*0x30,16)):
            if rid not in (0x0d80000000000156,0x0d80000000000152):continue
            if rid in values or r.pointer(value)!=process.base+0x1608248:raise ValueError('Ultimate primitive identity')
            raw,_,kind=r.unpack('<QII',value+0xa0)
            if kind not in (2,3):raise ValueError('Ultimate numeric type')
            number=struct.unpack('<i' if kind==2 else '<f',struct.pack('<I',raw&0xffffffff))[0]
            if not math.isfinite(number):raise ValueError('Ultimate numeric bounds')
            values[rid]=(value,number,kind)
    if len(values)!=2:raise ValueError('Current hero has no two typed ultimate values')
    charge,cost=values[0x0d80000000000156],values[0x0d80000000000152]
    if not 0<=charge[1]<=cost[1]<=100000 or cost[1]<=0:raise ValueError('Ultimate cost/charge bounds')
    if r.unpack('<I',reference+0x94)[0]!=s['modelId'] or r.pointer(model+0x28)!=admin:raise ValueError('Ultimate owner changed')
    return dict(localId=s['localId'],modelId=s['modelId'],hero=hero,admin=admin,reference=reference,heroInfo=info,
                model=model,bagAddress=bag_address,bag=bag,charge=charge[0],chargeValue=charge[1],chargeType=charge[2],cost=cost[0],costValue=cost[1],numericVtable=process.base+0x1608248)

def grant_for_test(process,pid):
    before=inspect(process);k=process.kernel
    k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
    k.WriteProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.WriteProcessMemory.restype=wintypes.BOOL
    k.CloseHandle.argtypes=[wintypes.HANDLE];k.CloseHandle.restype=wintypes.BOOL
    handle=k.OpenProcess(0x428,False,pid)
    if not handle:raise ctypes.WinError(ctypes.get_last_error())
    try:
        current=inspect(process)
        # The running feedback worker may legitimately earn charge during the
        # read-only inspection. Its value is not the lab grant's owner identity.
        if {k:v for k,v in current.items() if k!='chargeValue'}!={k:v for k,v in before.items() if k!='chargeValue'}:raise ValueError('Ultimate owner/type/cost changed before lab grant')
        before=current
        value=ctypes.c_int32(int(before['costValue'])) if before['chargeType']==2 else ctypes.c_float(before['costValue']);written=ctypes.c_size_t()
        if not k.WriteProcessMemory(handle,before['charge']+0xa0,ctypes.byref(value),4,ctypes.byref(written)) or written.value!=4:raise ctypes.WinError(ctypes.get_last_error())
        return dict(before=before,after=inspect(process),labGrant=True,payloadBytesWritten=4)
    finally:k.CloseHandle(handle)
