"""Disable the supplied spawner's original local hero-selection availability flag.

The original hands, weapon, skills and HUD are not replaced or masked.
"""
import argparse,ctypes,json
from ctypes import wintypes
from observe_overwatch import ROOT,ResearchProcess
from observe_native_weapon_states import WeaponStates

def hide(process,pid):
    r=WeaponStates(process);s=r.sample_weapon(require_volley=False);admin=r.pointer(process.base+0x17b7f90)
    controller=r.entity(process.read(r.pointer(admin+0x10),65536),s['localId']);info=r.component(controller,0x3f)
    address=info+0xc3;before=process.read(address,1)
    if before not in (b'\x00',b'\x01') or r.pointer(info+8)!=controller:raise ValueError('Original PlayerInfo flag differs')
    k=process.kernel;k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
    k.WriteProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.WriteProcessMemory.restype=wintypes.BOOL
    k.CloseHandle.argtypes=[wintypes.HANDLE];k.CloseHandle.restype=wintypes.BOOL
    handle=k.OpenProcess(0x428,False,pid)
    if not handle:raise ctypes.WinError(ctypes.get_last_error())
    try:
        if r.pointer(process.base+0x17b7f90)!=admin or r.unpack('<I',admin+0x220)[0]!=s['localId'] or r.pointer(info+8)!=controller or process.read(address,1)!=before:raise ValueError('Original player changed')
        if before!=b'\x00':
            value=ctypes.c_ubyte(0);written=ctypes.c_size_t()
            if not k.WriteProcessMemory(handle,address,ctypes.byref(value),1,ctypes.byref(written)) or written.value!=1:raise ctypes.WinError(ctypes.get_last_error())
        record={'pid':pid,'localId':s['localId'],'heroSelectionAvailableBefore':bool(before[0]),'heroSelectionAvailableAfter':bool(process.read(address,1)[0]),'nativeCalls':False,'field':'Component_3F_PlayerInfo.hero_select_enabled','offset':195}
        (ROOT/f'research/native-hero-prompt-{pid}.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');return record
    finally:k.CloseHandle(handle)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pid',type=int,required=True);a=p.parse_args();process=ResearchProcess(a.pid)
    try:print(json.dumps(hide(process,a.pid)))
    finally:process.close()
