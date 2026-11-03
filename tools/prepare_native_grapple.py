"""Read-only Widowmaker Shift/E bindings: original cast/fire/throw states. Never activates abilities.

Calibrated in research/sprint-20261024/widow-kit-calibration2 and -calibration5.
Grappling Hook graph 058000000000005a (91 nodes): StateStack81 begins the cast,
DataFlowMapping57 spans it (~1.26s), StateAnim61 begins the hook fire (+150ms).
Venom Mine graph 0580000000000056 (27 nodes): State24 spans the cast (~1s), WeaponVolley1
is the throw (+200ms, begins and ends on one tick). MC owns hook/mine physics; this only
publishes the original phases."""
import ctypes,json,struct
from observe_overwatch import ROOT
from observe_native_weapon_states import WeaponStates
from provided_plugin_symbols import provided_plugin

HERO=0x02e000000000000a
GRAPHS=[('grapple',0x058000000000005a,91,[('cast',81,0xf7d6498c),('window',57,0x85c28a9a),('fire',61,0x7fb4bf64)]),
        ('venom',0x0580000000000056,27,[('cast',24,0xa7213568),('throw',1,0x860ee5fc),('anim',2,0x7fb4bf64)])]

def prepare(process,pid):
    r=WeaponStates(process);s=r.sample_weapon(False,True);b=r.bindings
    admin=r.pointer(process.base+0x17b7f90);table=process.read(r.pointer(admin+16),65536)
    controller=r.entity(table,s['localId']);model=r.entity(table,s['modelId']);ref=r.component(controller,0x20);info=r.component(controller,0x3f)
    if r.unpack('<Q',info+0x98)[0]!=HERO:raise ValueError('Grapple/Venom requires current Widowmaker')
    base,image,pdb=provided_plugin(process);logger=base+image.symbol_rva(pdb.exact('statescript_logger::s_scriptStates'))
    times=[ctypes.create_string_buffer(8) for _ in range(4)];process.kernel.GetProcessTimes.argtypes=[ctypes.c_void_p,*([ctypes.c_void_p]*4)]
    if not process.kernel.GetProcessTimes(process.handle,*times):raise ctypes.WinError(ctypes.get_last_error())
    creation=struct.unpack('<Q',times[0].raw)[0];paths=[]
    for purpose,resource,size,profile in GRAPHS:
        matches=[k for k in r.graph_cache if k[2]==resource]
        if len(matches)!=1:raise ValueError(f'Original {purpose} graph is not unique')
        script,graph,_=matches[0];nodes=r.stu_list(graph+0x50)
        if len(nodes)!=size:raise ValueError(f'Original {purpose} graph size changed')
        states={}
        for name,index,kind in profile:
            if b.metadata(nodes[index])[1]!=kind:raise ValueError(f'Original {purpose} phase changed')
            states[name]=dict(index=index,address=nodes[index],vtable=r.pointer(nodes[index]))
        if r.unpack('<I',ref+0x94)[0]!=s['modelId'] or r.pointer(r.pointer(r.pointer(script+0x10)+0x450)+8)!=model:raise ValueError(f'{purpose} owner changed during binding')
        out=dict(version=1,pid=pid,creation=creation,adminAddress=process.base+0x17b7f90,admin=admin,localId=s['localId'],
                 reference=ref,model=model,modelId=s['modelId'],heroInfo=info,hero=HERO,script=script,graph=graph,bag=r.pointer(script+0x98),
                 resource=resource,logger=logger,states=states)
        p=ROOT/f'native-host/build/native-{purpose}-request-{pid}.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(out,indent=2)+'\n');tmp.replace(p)
        paths.append(str(p))
    return dict(hero=HERO,modelId=s['modelId'],readOnly=True,paths=paths)

if __name__=='__main__':
    import argparse
    from observe_overwatch import ResearchProcess
    a=argparse.ArgumentParser();a.add_argument('--pid',required=True,type=int);args=a.parse_args();p=ResearchProcess(args.pid)
    try:print(json.dumps(prepare(p,args.pid)))
    finally:p.close()
