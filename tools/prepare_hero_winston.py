"""Read-only24919 Winston bindings. Auto-discovered by the existing supervisor.

Only authenticated native cast32/movement14, cast20/Pet22, Primal StateStack10 and
fist Anim63/62 with TrackTargets69/70 authorize MC effects. First samples are baselines.
Offline definitions: tools/audit_winston.py. This file never launches a game.
"""
import ctypes
import json
import struct

HERO=0x02e0000000000009
GRAPHS=[
    ('winstonJump',0x058000000000010a,65,[('cast',32,0x7fb4bf64),('movement',14,0x8de7e50f),('ability',58,0xf53c5da8)]),
    ('winstonBarrier',0x05800000000000fa,33,[('cast',20,0x7fb4bf64),('pet',22,0x4cced352),('ability',26,0xf53c5da8)]),
    ('winstonPrimal',0x0580000000000109,74,[('rage',10,0xf7d6498c),('pool',7,0xc17b255d)]),
    ('winstonFists',0x05800000000000fe,152,[('left',69,0x498b421a),('right',70,0x498b421a),('leftSwing',63,0x7fb4bf64),('rightSwing',62,0x7fb4bf64)]),
]

def prepare(process,pid):
    from observe_overwatch import ROOT
    from observe_native_weapon_states import WeaponStates
    from provided_plugin_symbols import provided_plugin
    r=WeaponStates(process);sample=r.sample_weapon(False,True)
    admin=r.pointer(process.base+0x17b7f90);table=process.read(r.pointer(admin+16),65536)
    controller=r.entity(table,sample['localId']);model=r.entity(table,sample['modelId'])
    ref,info=r.component(controller,0x20),r.component(controller,0x3f)
    if r.unpack('<Q',info+0x98)[0]!=HERO:raise ValueError('Winston owner required')
    base,image,pdb=provided_plugin(process);logger=base+image.symbol_rva(pdb.exact('statescript_logger::s_scriptStates'))
    times=[ctypes.create_string_buffer(8) for _ in range(4)]
    process.kernel.GetProcessTimes.argtypes=[ctypes.c_void_p,*([ctypes.c_void_p]*4)]
    if not process.kernel.GetProcessTimes(process.handle,*times):raise ctypes.WinError(ctypes.get_last_error())
    creation=struct.unpack('<Q',times[0].raw)[0];pending=[]
    for purpose,resource,count,profile in GRAPHS:
        matches=[k for k in r.graph_cache if k[2]==resource]
        if len(matches)!=1:raise ValueError(purpose+' graph is not unique')
        script,graph,_=matches[0];nodes=r.stu_list(graph+0x50)
        if len(nodes)!=count:raise ValueError(purpose+' graph size differs')
        states={}
        for name,index,kind in profile:
            if r.bindings.metadata(nodes[index])[1]!=kind:raise ValueError(purpose+' type differs')
            states[name]=dict(index=index,address=nodes[index],vtable=r.pointer(nodes[index]))
        if (r.unpack('<I',ref+0x94)[0]!=sample['modelId'] or r.unpack('<Q',info+0x98)[0]!=HERO
            or r.pointer(r.pointer(r.pointer(script+0x10)+0x450)+8)!=model):raise ValueError('Winston owner changed')
        data=dict(version=1,pid=pid,creation=creation,adminAddress=process.base+0x17b7f90,admin=admin,
            localId=sample['localId'],reference=ref,model=model,modelId=sample['modelId'],heroInfo=info,hero=HERO,
            script=script,graph=graph,bag=r.pointer(script+0x98),resource=resource,logger=logger,states=states)
        pending.append((ROOT/f'native-host/build/native-{purpose}-request-{pid}.json',data))
    if r.unpack('<I',ref+0x94)[0]!=sample['modelId'] or r.unpack('<Q',info+0x98)[0]!=HERO:raise ValueError('Winston changed before publication')
    for path,data in pending:
        tmp=path.with_suffix('.winston.tmp');tmp.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8');tmp.replace(path)
    return dict(hero=HERO,modelId=sample['modelId'],readOnly=True,paths=[str(p) for p,_ in pending])

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pid',type=int);parser.add_argument('--describe',action='store_true');a=parser.parse_args()
    if a.describe:print(json.dumps(dict(hero=HERO,graphs=GRAPHS)))
    else:
        if a.pid is None:parser.error('--pid required')
        from observe_overwatch import ResearchProcess
        p=ResearchProcess(a.pid)
        try:print(json.dumps(prepare(p,a.pid)))
        finally:p.close()
