"""Bind the original Tracer teleport actions and owner, without activating them."""
import ctypes,json,struct
from observe_overwatch import ROOT,ResearchProcess
from observe_native_weapon_states import WeaponStates
from provided_plugin_symbols import provided_plugin

def prepare(process,pid):
    r=WeaponStates(process);s=r.sample_weapon(False,True);b=r.bindings
    admin=r.pointer(process.base+0x17b7f90);table=process.read(r.pointer(admin+16),65536)
    controller=r.entity(table,s['localId']);model=r.entity(table,s['modelId'])
    if r.unpack('<Q',r.component(controller,0x3f)+0x98)[0]!=0x02e0000000000003:raise ValueError('Original Tracer required')
    matches=[k for k in r.graph_cache if k[2]==0x0580000000000024]
    if len(matches)!=1:raise ValueError('Original Blink graph missing')
    script,graph,_=matches[0];nodes=r.stu_list(graph+0x50)
    if any(b.metadata(nodes[i])[1]!=0xa5f89e3f for i in (5,10)) or r.pointer(nodes[5])!=r.pointer(nodes[10]):raise ValueError('Original teleport definitions changed')
    # Keep the original expression execution; no guessed distance/speed writes.
    if any(b.metadata(r.pointer(b.field(nodes[i],0x072cbdd4)[1]))[1]!=0xcc3a08f4 for i in (5,10)):raise ValueError('Teleport vector expression differs')
    if r.pointer(r.pointer(r.pointer(script+0x10)+0x450)+8)!=model or r.unpack('<I',admin+0x220)[0]!=s['localId']:raise ValueError('Blink owner changed')
    base,image,pdb=provided_plugin(process);logger=base+image.symbol_rva(pdb.exact('statescript_logger::s_scriptStates'))
    times=[ctypes.create_string_buffer(8) for _ in range(4)];process.kernel.GetProcessTimes.argtypes=[ctypes.c_void_p,*([ctypes.c_void_p]*4)]
    if not process.kernel.GetProcessTimes(process.handle,*times):raise ctypes.WinError(ctypes.get_last_error())
    values=[struct.unpack('<Q',times[0].raw)[0],admin,s['localId'],s['modelId'],model,script,r.pointer(script+0x98),graph,logger,nodes[5],nodes[10],r.pointer(nodes[5])]
    data=struct.pack('<8sII12Q',b'OWBLK001',1,pid,*values)
    path=ROOT/f'native-host/build/native-blink-request-{pid}.bin';tmp=path.with_suffix('.tmp');tmp.write_bytes(data);tmp.replace(path)
    result=dict(pid=pid,modelId=s['modelId'],readOnly=True,nativeCalls=False,actualNativeTeleport=True,path=str(path))
    path.with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n');return result

if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser();a.add_argument('--pid',required=True,type=int);args=a.parse_args();p=ResearchProcess(args.pid)
    try:print(json.dumps(prepare(p,args.pid)))
    finally:p.close()
