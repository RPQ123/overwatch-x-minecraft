"""Read-only Mei Q (Blizzard) binding, same scheme as prepare_native_grapple.py. Original doc:: original cast/fire/throw states. Never activates abilities.

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

HERO=0x02e0000000000065
# 狂鼠（SKILL-BRIEFS-20261025.md §5）：主武器 022b WeaponVolley31；Shift 地雷 096a Volley12/Anim6；E 夹子 09ba Volley7/Anim14。
# 节点总数未校准为常量，所以 size=None 只核对每个节点的原版类型。
GRAPHS=[('junkPrimary',0x058000000000022b,None,[('volley',31,0x860ee5fc)]),
        ('junkMine',0x058000000000096a,None,[('throw',12,0x860ee5fc),('anim',6,0x7fb4bf64)]),
        ('junkTrap',0x05800000000009ba,None,[('throw',7,0x860ee5fc),('anim',14,0x7fb4bf64)]),
        # 0232 flat 原版 node32+0x88 -> ConfigVarEntityDefinition -> 039c；附属脚本0233。
        # 只准入其真实 logger 新 tick；没有事件时不从 Q 键或固定延时制造轮胎。
        ('junkTire',0x0580000000000232,98,[('create',32,0x1bb99c36),('control',10,0x74cb0002),('view',11,0x3a846155),('windup',7,0x7fb4bf64)])]

def prepare(process,pid):
    r=WeaponStates(process);s=r.sample_weapon(False,True);b=r.bindings
    admin=r.pointer(process.base+0x17b7f90);table=process.read(r.pointer(admin+16),65536)
    controller=r.entity(table,s['localId']);model=r.entity(table,s['modelId']);ref=r.component(controller,0x20);info=r.component(controller,0x3f)
    if r.unpack('<Q',info+0x98)[0]!=HERO:raise ValueError('Junkrat bindings require current Junkrat')
    base,image,pdb=provided_plugin(process);logger=base+image.symbol_rva(pdb.exact('statescript_logger::s_scriptStates'))
    times=[ctypes.create_string_buffer(8) for _ in range(4)];process.kernel.GetProcessTimes.argtypes=[ctypes.c_void_p,*([ctypes.c_void_p]*4)]
    if not process.kernel.GetProcessTimes(process.handle,*times):raise ctypes.WinError(ctypes.get_last_error())
    creation=struct.unpack('<Q',times[0].raw)[0];paths=[]
    for purpose,resource,size,profile in GRAPHS:
        matches=[k for k in r.graph_cache if k[2]==resource]
        if len(matches)!=1:raise ValueError(f'Original {purpose} graph is not unique')
        script,graph,_=matches[0];nodes=r.stu_list(graph+0x50)
        if size is not None and len(nodes)!=size:raise ValueError(f'Original {purpose} graph size changed')
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
