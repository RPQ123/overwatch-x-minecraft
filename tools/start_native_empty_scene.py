"""Cold-scene probe: set the original world-state dropdown to Running with no map.

Only a fresh, exact provided client with zero wanted/loaded map and no local
controller is eligible. No map unloading or asset rewriting occurs. This is an
experiment, not evidence that all original systems support a zero-map scene.
"""
import argparse,ctypes,json,struct,time
from ctypes import wintypes
from observe_overwatch import ROOT,ResearchProcess,PoseReader

def start(pid):
    raise RuntimeError('Quarantined: spawning the original hero after resource load in a cold zero-map scene exited client 31452 on 2026-10-15. A Running state alone does not initialize a renderer world. Do not repeat this route.')
    process=ResearchProcess(pid);reader=PoseReader(process);kernel=process.kernel;handle=None
    try:
        times=[wintypes.FILETIME() for _ in range(4)]
        kernel.GetProcessTimes.argtypes=[wintypes.HANDLE]+[ctypes.POINTER(wintypes.FILETIME)]*4
        if not kernel.GetProcessTimes(process.handle,*[ctypes.byref(t) for t in times]):raise ctypes.WinError(ctypes.get_last_error())
        created=((times[0].dwHighDateTime<<32)|times[0].dwLowDateTime)/1e7-11644473600
        if not 0<=time.time()-created<300:raise ValueError('Only a newly launched cold client is eligible')
        ea=reader.pointer(process.base+0x17b7f90)
        if reader.unpack('<I',ea+0x220)[0]:raise ValueError('A local controller already exists')
        systems,count,capacity=reader.unpack('<Qii',ea+0xd8)
        if not 1<=count<=capacity<=128:raise ValueError('System list bounds')
        matches=[s for s, in struct.iter_unpack('<Q',process.read(systems,count*8)) if reader.pointer(s)==process.base+0x15c3118]
        if len(matches)!=1:raise ValueError('World engine ambiguous')
        world=matches[0]
        def unchanged():return reader.pointer(process.base+0x17b7f90)==ea and reader.pointer(world+8)==ea and reader.unpack('<B',world+0x10)==(2,) and reader.unpack('<QQ',world+0x18)==(0,0) and reader.unpack('<I',ea+0x220)==(0,)
        if not unchanged():raise ValueError('Only a cold world without any selected or loaded map is eligible')
        kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenProcess.restype=wintypes.HANDLE
        kernel.WriteProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
        handle=kernel.OpenProcess(0x28,False,pid)
        if not handle:raise ctypes.WinError(ctypes.get_last_error())
        if not unchanged():raise ValueError('Cold world changed before state commit')
        value=ctypes.create_string_buffer(b'\x08');written=ctypes.c_size_t()
        if not kernel.WriteProcessMemory(handle,world+0x10,value,1,ctypes.byref(written)) or written.value!=1:raise ctypes.WinError(ctypes.get_last_error())
        record={'pid':pid,'operation':'cold-zero-map-world-state-dropdown','worldState':reader.unpack('<B',world+0x10)[0],'wantedLoaded':reader.unpack('<QQ',world+0x18),'heroVerified':False,'audioVerified':False,'timeUnixMs':int(time.time()*1000)}
        (ROOT/f'research/native-empty-scene-{pid}.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(json.dumps(record,indent=2))
    finally:
        if handle:kernel.CloseHandle(handle)
        process.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pid',type=int,required=True);args=parser.parse_args();start(args.pid)
