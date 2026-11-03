"""Bind Tracer's actual Pulse Bomb animation/Volley; MC supplies sticky physics."""
import ctypes,json,struct
from observe_overwatch import ROOT
from observe_native_weapon_states import WeaponStates
from inspect_native_pulse_bomb import inspect,HERO,SCRIPT
from provided_plugin_symbols import provided_plugin

def prepare(process,pid):
    proof=inspect(process);r=WeaponStates(process);s=r.sample_weapon(False,True)
    if s['modelId']!=proof['modelId']:raise ValueError('Pulse owner changed')
    admin=r.pointer(process.base+0x17b7f90);table=process.read(r.pointer(admin+16),65536)
    controller=r.entity(table,s['localId']);model=r.entity(table,s['modelId'])
    ref=r.component(controller,0x20);info=r.component(controller,0x3f)
    matches=[k for k in r.graph_cache if k[2]==SCRIPT]
    if len(matches)!=1:raise ValueError('Pulse graph is not unique')
    script,graph,_=matches[0];nodes=r.stu_list(graph+0x50);states={}
    for name,index,kind in [('cast',3,0x7fb4bf64),('deploy',1,0x860ee5fc)]:
        if r.bindings.metadata(nodes[index])[1]!=kind:raise ValueError('Pulse phase changed')
        states[name]=dict(index=index,address=nodes[index],vtable=r.pointer(nodes[index]))
    base,image,pdb=provided_plugin(process);logger=base+image.symbol_rva(pdb.exact('statescript_logger::s_scriptStates'))
    times=[ctypes.create_string_buffer(8) for _ in range(4)];process.kernel.GetProcessTimes.argtypes=[ctypes.c_void_p,*([ctypes.c_void_p]*4)]
    if not process.kernel.GetProcessTimes(process.handle,*times):raise ctypes.WinError(ctypes.get_last_error())
    out=dict(version=1,pid=pid,creation=struct.unpack('<Q',times[0].raw)[0],adminAddress=process.base+0x17b7f90,admin=admin,localId=s['localId'],reference=ref,model=model,modelId=s['modelId'],heroInfo=info,hero=HERO,script=script,graph=graph,bag=r.pointer(script+0x98),resource=SCRIPT,logger=logger,states=states)
    if r.unpack('<I',ref+0x94)[0]!=s['modelId'] or r.pointer(r.pointer(r.pointer(script+0x10)+0x450)+8)!=model:raise ValueError('Pulse changed during binding')
    p=ROOT/f'native-host/build/native-pulse-request-{pid}.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');tmp.replace(p)
    return dict(hero=HERO,modelId=s['modelId'],readOnly=True,path=str(p),lossless=False)
