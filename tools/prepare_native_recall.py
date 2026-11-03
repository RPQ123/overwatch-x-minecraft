"""Pin original Recall ownership and animation completion; no native calls here."""
import ctypes,json,struct
from observe_overwatch import ROOT
from observe_native_weapon_states import WeaponStates
from inspect_native_recall import inspect,HERO,RESOURCE
from provided_plugin_symbols import provided_plugin
from native_armory_binding import primitive
from inspect_native_control_skills import ref as config_ref

def prepare(process,pid):
    proof=inspect(process);r=WeaponStates(process);s=r.sample_weapon(False,True)
    if s['modelId']!=proof['modelId']:raise ValueError('Recall owner changed')
    admin=r.pointer(process.base+0x17b7f90);table=process.read(r.pointer(admin+16),65536)
    controller=r.entity(table,s['localId']);model=r.entity(table,s['modelId']);ref=r.component(controller,0x20);info=r.component(controller,0x3f)
    matches=[k for k in r.graph_cache if k[2]==RESOURCE]
    if len(matches)!=1:raise ValueError('Recall graph is not unique')
    script,graph,_=matches[0];nodes=r.stu_list(graph+0x50);states={}
    if r.bindings.metadata(nodes[1])[1]!=0x7211cf70 or r.pointer(nodes[1])!=process.base+0x151c678:raise ValueError('Original Recall history state changed')
    for name,index,kind,vt in [('cast',31,0xa7213568,0x1500590),('animation',9,0x7fb4bf64,0x15138c0)]:
        if r.bindings.metadata(nodes[index])[1]!=kind or r.pointer(nodes[index])!=process.base+vt:raise ValueError('Recall original phase changed')
        states[name]=dict(index=index,address=nodes[index],vtable=r.pointer(nodes[index]))
    # The real state-output topology, not the visually similar Stack27 leaf:
    # Recall root31 owns the history state4, animation9 and priority-stack27.
    _,at,category,declared=r.bindings.field(graph+8,0x9d751e7c)
    if (category,declared)!=(3,0x38a4b0b7):raise ValueError('Recall graph links changed')
    children=set()
    for link in r.stu_list(at):
        output,input_=r.unpack('<QQ',link+8)
        if r.pointer(output+24)==nodes[31]:
            if r.bindings.metadata(output)[1]!=0x24ab1f0b or r.bindings.metadata(input_)[1]!=0x11d7f052:raise ValueError('Recall root plug type changed')
            children.add(r.pointer(input_+24))
    if children!={nodes[4],nodes[9],nodes[27]}:raise ValueError('Recall root lifecycle topology changed')
    base,image,pdb=provided_plugin(process);logger=base+image.symbol_rva(pdb.exact('statescript_logger::s_scriptStates'))
    fn,prefix=image.function_prefix(pdb.exact('?StartStopState@StatescriptInstance@@QEAAXH_N@Z'))
    if fn!=0x7acd0 or process.read(base+fn,32)!=prefix:raise ValueError('Original state wrapper changed')
    times=[ctypes.create_string_buffer(8) for _ in range(4)];process.kernel.GetProcessTimes.argtypes=[ctypes.c_void_p,*([ctypes.c_void_p]*4)]
    if not process.kernel.GetProcessTimes(process.handle,*times):raise ctypes.WinError(ctypes.get_last_error())
    creation=struct.unpack('<Q',times[0].raw)[0];bag=r.pointer(script+0x98)
    ammo_matches=[k for k in r.graph_cache if k[2]==0x0580000000000016]
    if len(ammo_matches)!=1:raise ValueError('Original Tracer magazine script is not unique')
    ammo_script,ammo_graph,_=ammo_matches[0];ammo_bag=r.pointer(ammo_script+0x98);ammo_nodes=r.stu_list(ammo_graph+0x50)
    ammo,current,ammo_bucket=primitive(r,ammo_bag,0x0d80000000000035);maximum,full,max_bucket=primitive(r,ammo_bag,0x0d800000000000c6)
    reload=ammo_nodes[30]
    if ammo_bucket!=5 or max_bucket!=6 or full!=40 or not 0<=current<=full or r.bindings.metadata(reload)[1]!=0x4698e4b6:raise ValueError('Original Tracer reload maximum changed')
    for field,path in [(0xec9f34a6,['0d80000000000035']),(0x5180e750,['0d800000000000c6'])]:
        declared=0xf8cc195d if field==0xec9f34a6 else 0xbfd9aadd
        if r.bindings.dynamic_path(config_ref(r.bindings,reload,field,0x4698e4b6,declared))!=path:raise ValueError('Original reload assignment changed')
    out=dict(version=1,pid=pid,creation=creation,adminAddress=process.base+0x17b7f90,admin=admin,localId=s['localId'],reference=ref,model=model,modelId=s['modelId'],heroInfo=info,hero=HERO,script=script,graph=graph,bag=bag,resource=RESOURCE,logger=logger,states=states)
    if r.unpack('<I',ref+0x94)[0]!=s['modelId'] or r.pointer(r.pointer(r.pointer(script+0x10)+0x450)+8)!=model:raise ValueError('Recall changed during binding')
    values=[creation,admin,s['localId'],s['modelId'],model,script,bag,graph,logger,nodes[31],nodes[9],r.pointer(nodes[31]),r.pointer(nodes[9]),base+fn]
    wire=struct.pack('<8sII14Q32s6Q',b'OWRECL01',2,pid,*values,prefix,ammo_script,ammo_bag,ammo,maximum,ammo_graph,reload)
    p=ROOT/f'native-host/build/native-recall-request-{pid}.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');tmp.replace(p)
    p=p.with_suffix('.bin');tmp=p.with_suffix('.tmp');tmp.write_bytes(wire);tmp.replace(p)
    return dict(hero=HERO,modelId=s['modelId'],readOnly=True,completion='actual animation End on existing logic owner',path=str(p))
