"""Explicit offline lab: prove current typed cooldown data gates a second Shift."""
import ctypes,json,struct,time
from ctypes import wintypes
from observe_overwatch import ROOT,ResearchProcess
from observe_native_weapon_states import WeaponStates
from calibrate_hero_roster import drive,api

def binding(p):
    r=WeaponStates(p);s=r.sample_weapon(all_scripts=True);a=r.pointer(p.base+0x17b7f90);t=p.read(r.pointer(a+0x10),65536);c=r.entity(t,s['localId']);m=r.entity(t,s['modelId'])
    if r.unpack('<Q',r.component(c,0x3f)+0x98)[0]!=0x02e0000000000029:raise ValueError('Not original Genji')
    i,g,_=next(k for k in r.graph_cache if k[2]==0x05800000000001db);defs=r.stu_list(g+0x60);states=[]
    for st, in struct.iter_unpack('<Q',r.vector(i+0xa0,8,4096)):
        if not st:continue
        ix=r.unpack('<i',st+0x70)[0]
        if r.unpack('<i',defs[ix]+0x68)[0]==5:states.append(st)
    if len(states)!=1 or r.pointer(states[0])!=p.base+0x15d7c98:raise ValueError('Ability state type differs')
    st=states[0]
    return r,dict(modelId=s['modelId'],script=i,state=st,remaining=r.unpack('<f',st+0x150)[0],flags=r.unpack('<B',st+0x15c)[0],tick=max((v['nativeTick'] for v in s['records'].values() if v['script']=='05800000000001db' and v['node']==6),default=0))

def main():
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--pid',type=int,required=True);args=parser.parse_args();p=ResearchProcess(args.pid);handle=None;out={}
    try:
        out['initial']=binding(p)[1];drive('focus','key 0x10','sleep 650');r,b=binding(p);out['first']=b
        if b['remaining']<=0:raise ValueError('First dash did not establish a cooldown')
        k=p.kernel;k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE;k.WriteProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.WriteProcessMemory.restype=wintypes.BOOL;k.CloseHandle.argtypes=[wintypes.HANDLE]
        handle=k.OpenProcess(0x428,False,args.pid)
        if not handle:raise ctypes.WinError(ctypes.get_last_error())
        def write(at,raw):
            if binding(p)[1]['modelId']!=b['modelId']:raise ValueError('Original owner changed')
            value=ctypes.create_string_buffer(raw);written=ctypes.c_size_t()
            if not k.WriteProcessMemory(handle,at,value,len(raw),ctypes.byref(written)) or written.value!=len(raw):raise ctypes.WinError(ctypes.get_last_error())
        write(b['state']+0x150,struct.pack('<f',0));write(b['state']+0x144,b'\x01');write(b['state']+0x146,b'\x01')
        out['reset']=binding(p)[1];drive('focus','key 0x10','sleep 500');out['second']=binding(p)[1];out['guest']=api('combat');out['secondDash']=out['second']['tick']>b['tick']
        print(json.dumps({key:out[key] for key in ('first','reset','second','secondDash')},indent=2))
    finally:
        (ROOT/'research/genji-reset-data-test.json').write_text(json.dumps(out,indent=2)+'\n')
        if handle:p.kernel.CloseHandle(handle)
        p.close()

if __name__=='__main__':main()
