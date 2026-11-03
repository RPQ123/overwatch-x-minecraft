"""Queue a verified built-in map using the supplied client's normal map state machine.

This performs the same two scalar assignments as Prometheus's Map menu. It does
not unload entities manually, call native code or patch map files. Scene changes
must be attempted only with the lab render callbacks restored.
"""
import argparse,ctypes,json,struct,time
from ctypes import wintypes
from observe_overwatch import ROOT,ResearchProcess,PoseReader

MAPS={'arena':0x08000000000001c2,'hollywood':0x08000000000002af}

def switch(pid,name):
    if name=='arena':raise RuntimeError('Quarantined: AutomationStressArena caused the supplied client to exit during world loading on 2026-10-15. Do not repeat this route.')
    process=ResearchProcess(pid);reader=PoseReader(process);handle=None
    try:
        for prefix in ('host-pose','world-live'):
            path=ROOT/f'native-host/build/{prefix}-{pid}.json'
            if path.is_file():
                report=json.loads(path.read_text())
                if report.get('enabled') or not report.get('restored'):raise ValueError('Restore existing lab callbacks before switching scenes')
        inventory=json.loads((ROOT/'research/native-map-inventory.json').read_text())
        target=MAPS[name]
        if inventory['pid']!=pid or not inventory['pdbDllIdentityMatched'] or not any(int(m['mapId'],16)==target for m in inventory['maps']):raise ValueError('Target is not in this original process verified map inventory')
        def world():
            ea=reader.pointer(process.base+0x17b7f90);items,count,capacity=reader.unpack('<Qii',ea+0xd8)
            if not 0<count<=capacity<=128:raise ValueError('World system list bounds')
            found=[]
            for i in range(count):
                obj=reader.pointer(items+8*i)
                if reader.unpack('<Q',obj)[0]==process.base+0x15c3118:
                    if reader.unpack('<Q',obj+8)[0]!=ea:raise ValueError('World system owner changed')
                    found.append(obj)
            if len(found)!=1:raise ValueError('World engine system missing/ambiguous')
            return ea,found[0]
        ea,obj=world();state=reader.unpack('<B',obj+0x10)[0];wanted,loaded=reader.unpack('<QQ',obj+0x18)
        if state!=8:raise ValueError(f'World is not running: {state}')
        if loaded==target:print('Already in requested map');return
        kernel=process.kernel;kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenProcess.restype=wintypes.HANDLE
        kernel.WriteProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
        handle=kernel.OpenProcess(0x20|0x8|0x400,False,pid)
        if not handle:raise ctypes.WinError(ctypes.get_last_error())
        def write(address,data):
            buffer=ctypes.create_string_buffer(data);written=ctypes.c_size_t()
            if not kernel.WriteProcessMemory(handle,address,buffer,len(data),ctypes.byref(written)) or written.value!=len(data):raise ctypes.WinError(ctypes.get_last_error())
        if world()!=(ea,obj) or reader.unpack('<B',obj+0x10)[0]!=state or reader.unpack('<QQ',obj+0x18)!=(wanted,loaded):raise ValueError('World changed during queue preflight')
        record={'pid':pid,'target':name,'mapId':f'{target:016x}','previousMapId':f'{loaded:016x}','previousWanted':f'{wanted:016x}','operation':'native-map-menu-state-transition','timeUnixMs':int(time.time()*1000),'completed':False}
        out=ROOT/f'research/native-map-switch-{pid}.json';out.write_text(json.dumps(record,indent=2)+'\n')
        write(obj+0x18,struct.pack('<Q',target))
        if reader.unpack('<B',obj+0x10)[0]!=state:raise ValueError('World state changed before commit')
        write(obj+0x10,b'\x02')
        print(json.dumps(record))
        start=time.monotonic();last=None
        while time.monotonic()-start<30:
            current_ea,current=world();s=reader.unpack('<B',current+0x10)[0];w,l=reader.unpack('<QQ',current+0x18)
            current_state=(s,w,l)
            if current_state!=last:print(json.dumps({'state':s,'wanted':f'{w:016x}','loaded':f'{l:016x}'}),flush=True);last=current_state
            if s==8 and l==target:
                record['completed']=True;record['durationSeconds']=time.monotonic()-start;out.write_text(json.dumps(record,indent=2)+'\n');return
            time.sleep(.1)
        raise TimeoutError('Native map transition still pending; inspect original process, do not queue another')
    finally:
        if handle:process.kernel.CloseHandle(handle)
        process.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pid',required=True,type=int);parser.add_argument('--map',required=True,choices=MAPS);args=parser.parse_args();switch(args.pid,args.map)
