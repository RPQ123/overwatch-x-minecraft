"""Initialize original hero health pools in the full-health creative MC session.

The supplied plugin copies this component into its HUD each tick; writing the
HUD variable alone is overwritten. No game function, input or code is changed.
"""
import argparse,ctypes,json,struct,time,urllib.request
from ctypes import wintypes
from observe_overwatch import ROOT,ResearchProcess
from native_health_binding import inspect_health,health_plan

def fill(process,pid,check_only=False):
    with urllib.request.urlopen('http://127.0.0.1:32133/health',timeout=2) as response:guest=json.load(response)
    player=guest.get('player') or {}
    # F5 survival uses MC health continuously; a supervisor rebind must never
    # refill an injured pawn. The normal creative initializer stays unchanged.
    try:
        with urllib.request.urlopen('http://127.0.0.1:32133/survival',timeout=2) as response:survival=json.load(response)
    except urllib.error.HTTPError as error:
        if error.code!=404:raise
        survival={}
    if survival.get('enabled'):
        return {'pid':pid,'survivalManaged':True,'mcHealth':player.get('health'),'nativeCalls':False}
    if not player.get('alive') or not player.get('invulnerable') or player.get('health')!=20:raise ValueError('Full-health creative MC session required')
    r,binding,verify=inspect_health(process);health=binding['health'];pools=binding['pools']
    before=[process.read(health+pool['offset'],320) for pool in pools]
    desired=health_plan(before,[pool['amount'] for pool in pools])
    changes=[(health+pool['offset'],raw[:12],wanted) for pool,raw,wanted in zip(pools,before,desired) if raw[:12]!=wanted]
    handle=None
    try:
        if not check_only and changes:
            k=process.kernel;k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
            k.WriteProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.WriteProcessMemory.restype=wintypes.BOOL
            k.CloseHandle.argtypes=[wintypes.HANDLE];k.CloseHandle.restype=wintypes.BOOL
            # Keep the exact-path/SHA-verified read handle alive across opening
            # this second handle. Only enabled/max/current base-slot payloads move.
            handle=k.OpenProcess(0x400|0x10|0x20|0x8,False,pid)
            if not handle:raise ctypes.WinError(ctypes.get_last_error())
            def write(address,data):
                value=ctypes.create_string_buffer(data);written=ctypes.c_size_t()
                if not k.WriteProcessMemory(handle,address,value,len(data),ctypes.byref(written)) or written.value!=len(data):raise ctypes.WinError(ctypes.get_last_error())
            verify()
            for pool,raw in zip(pools,before):
                if process.read(health+pool['offset'],320)!=raw:raise ValueError('Native health changed before initialization')
            applied=[]
            try:
                for address,old,new in changes:
                    verify();applied.append((address,old));write(address,new)
                verify()
                for address,_,new in changes:
                    if process.read(address,len(new))!=new:raise ValueError('Native health initialization did not persist')
            except BaseException:
                # Never roll back into memory belonging to a departed hero.
                verify(False)
                for address,old in reversed(applied):write(address,old)
                raise
            time.sleep(.1)
        verify()
        after=[r.unpack('<Iff',health+pool['offset']) for pool in pools]
        return {'pid':pid,'hero':binding['hero'],'modelId':binding['modelId'],
                'nativeHealthBefore':sum(struct.unpack_from('<f',raw,8)[0] for raw in before),
                'nativeHealthAfter':sum(part[2] for part in after),'nativeMaximum':sum(part[1] for part in after),
                'configuredPools':[pool['amount'] for pool in pools],'nativePoolsAfter':after,
                'mcHealth':player['health'],'checkOnly':check_only,'nativeCalls':False}
    finally:
        if handle:process.kernel.CloseHandle(handle)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pid',type=int,required=True);parser.add_argument('--check-only',action='store_true');args=parser.parse_args();process=ResearchProcess(args.pid)
    try:
        result=fill(process,args.pid,args.check_only);(ROOT/f'research/native-health-fill-{args.pid}.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
    finally:process.close()
