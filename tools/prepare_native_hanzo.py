"""Read-only Hanzo weapon Volley26/76 and original Q graph0101 cast Begin/End.

Never invokes native scripts or generates input. Q definition identity is checked
before binding a separately scoped logger for the casting state stack.
"""
import ctypes,json,struct
from observe_overwatch import ROOT
from observe_native_weapon_states import WeaponStates
from provided_plugin_symbols import provided_plugin

HERO=0x02e0000000000005
# 半藏（SKILL-BRIEFS-20261025.md §6）：graph b9 的 Volley26 散射父箭、Volley76 龙击起始箭。
GRAPHS=[('hanzoSkills',0x05800000000000b9,None,[('scatter',26,0x860ee5fc),('dragon',76,0x860ee5fc)]),
        ('hanzoQCast',0x0580000000000101,68,[('cast',19,0xf7d6498c),('windup',27,0x7fb4bf64),('recovery',28,0x7fb4bf64)])]

def verify_q_graph(r,nodes):
    """Original Q identity, charge consumption, cast stack and measured timing configs.

    Historical Q logger: windup ends 20328, cast stack ends 21428;
    Q dispatch is 18928. The timer configs are 1.4 + 1.1 seconds.
    No button injection, native evaluator or guessed zero-valued variable.
    """
    b=r.bindings
    def config(index,field,kind):
        _,address,category,declared=b.field(nodes[index],field);value=r.pointer(address)
        if category!=2 or b.metadata(value)[1]!=kind:raise ValueError('Original Hanzo Q configuration type changed')
        return value
    if b.metadata(nodes[1])[1]!=0xff77458c:raise ValueError('Original Hanzo Q button state changed')
    button=config(1,0x3c9341f5,0x5c7964ff)
    if r.unpack('<I',button+16)[0]!=0x79:raise ValueError('Original Hanzo Q logical button changed')
    stack=config(19,0xec9f34a6,0xf8cc195d)
    if b.dynamic_path(stack)!=['0d80000000000004','0d80000000000021']:raise ValueError('Original Hanzo cast stack path changed')
    charge=config(17,0xec9f34a6,0xf8cc195d);zero=config(17,0x5180e750,0x7b13a0d4)
    if b.dynamic_path(charge)!=['0d80000000000004','0d80000000000156'] or r.unpack('<f',zero+16)[0]!=0:
        raise ValueError('Original Hanzo Q charge consumption changed')
    windup=config(33,0x6b7c7d86,0x7b13a0d4);recovery=config(34,0xdb0e39db,0x7b13a0d4)
    durations=[r.unpack('<f',at+16)[0] for at in (windup,recovery)]
    if any(abs(a-b)>.00001 for a,b in zip(durations,[1.4,1.1])):raise ValueError('Original Hanzo Q timing changed')
    return dict(button=0x79,castNode=19,windupSeconds=durations[0],recoverySeconds=durations[1],
                nominalCastSeconds=sum(durations),source='typed original graph 0101; historical Q logger corroboration')

def prepare(process,pid):
    r=WeaponStates(process);s=r.sample_weapon(False,True);b=r.bindings
    admin=r.pointer(process.base+0x17b7f90);table=process.read(r.pointer(admin+16),65536)
    controller=r.entity(table,s['localId']);model=r.entity(table,s['modelId']);ref=r.component(controller,0x20);info=r.component(controller,0x3f)
    if r.unpack('<Q',info+0x98)[0]!=HERO:raise ValueError('Hanzo skill bindings require current Hanzo')
    base,image,pdb=provided_plugin(process);logger=base+image.symbol_rva(pdb.exact('statescript_logger::s_scriptStates'))
    times=[ctypes.create_string_buffer(8) for _ in range(4)];process.kernel.GetProcessTimes.argtypes=[ctypes.c_void_p,*([ctypes.c_void_p]*4)]
    if not process.kernel.GetProcessTimes(process.handle,*times):raise ctypes.WinError(ctypes.get_last_error())
    creation=struct.unpack('<Q',times[0].raw)[0];paths=[]
    for purpose,resource,size,profile in GRAPHS:
        matches=[k for k in r.graph_cache if k[2]==resource]
        if len(matches)!=1:raise ValueError(f'Original {purpose} graph is not unique')
        script,graph,_=matches[0];nodes=r.stu_list(graph+0x50)
        if size is not None and len(nodes)!=size:raise ValueError(f'Original {purpose} graph size changed')
        q_definition=verify_q_graph(r,nodes) if purpose=='hanzoQCast' else None
        states={}
        for name,index,kind in profile:
            if b.metadata(nodes[index])[1]!=kind:raise ValueError(f'Original {purpose} phase changed')
            states[name]=dict(index=index,address=nodes[index],vtable=r.pointer(nodes[index]))
        if r.unpack('<I',ref+0x94)[0]!=s['modelId'] or r.pointer(r.pointer(r.pointer(script+0x10)+0x450)+8)!=model:raise ValueError(f'{purpose} owner changed during binding')
        out=dict(version=1,pid=pid,creation=creation,adminAddress=process.base+0x17b7f90,admin=admin,localId=s['localId'],
                 reference=ref,model=model,modelId=s['modelId'],heroInfo=info,hero=HERO,script=script,graph=graph,bag=r.pointer(script+0x98),
                 resource=resource,logger=logger,states=states)
        if q_definition is not None:out['qDefinition']=q_definition
        p=ROOT/f'native-host/build/native-{purpose}-request-{pid}.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(out,indent=2)+'\n');tmp.replace(p)
        paths.append(str(p))
    return dict(hero=HERO,modelId=s['modelId'],readOnly=True,paths=paths)

if __name__=='__main__':
    import argparse
    from observe_overwatch import ResearchProcess
    a=argparse.ArgumentParser();a.add_argument('--pid',required=True,type=int);args=a.parse_args();p=ResearchProcess(args.pid)
    try:print(json.dumps(prepare(p,args.pid)))
    finally:p.close()
