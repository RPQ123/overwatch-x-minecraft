"""Read-only Shadow Step binding: original query/confirm/cast/animations."""
import ctypes,json,struct
from observe_overwatch import ROOT
from observe_native_weapon_states import WeaponStates
from provided_plugin_symbols import provided_plugin
from native_armory_binding import primitive
from inspect_native_control_skills import ref as config_ref

def prepare(process,pid):
    r=WeaponStates(process);s=r.sample_weapon(False,True);b=r.bindings
    admin=r.pointer(process.base+0x17b7f90);table=process.read(r.pointer(admin+16),65536)
    controller=r.entity(table,s['localId']);model=r.entity(table,s['modelId']);ref=r.component(controller,0x20);info=r.component(controller,0x3f)
    if r.unpack('<Q',info+0x98)[0]!=0x02e0000000000002:raise ValueError('Shadow Step requires current Reaper')
    matches=[k for k in r.graph_cache if k[2]==0x05800000000000f2]
    if len(matches)!=1:raise ValueError('Original Shadow Step graph is not unique')
    script,graph,_=matches[0];nodes=r.stu_list(graph+0x50);states={}
    if len(nodes)!=89:raise ValueError('Shadow Step graph size changed')
    for name,index,kind,vt in [('aim',2,0x72509d3b,0x151a868),('confirm',47,0xeaee2743,0x1517770),('cast',52,0xf7d6498c,0x150b738),('out',25,0x7fb4bf64,0x15138c0),('in',26,0x7fb4bf64,0x15138c0),('waitOut',17,0x65f158da,0x150bd08),('waitIn',18,0x65f158da,0x150bd08),('aimAnimation',53,0x7fb4bf64,0x15138c0),('priority',16,0xf7d6498c,0x150b738),('ready',5,0xa7213568,0x1500590)]:
        if b.metadata(nodes[index])[1]!=kind or r.pointer(nodes[index])!=process.base+vt:raise ValueError('Shadow Step original phase changed')
        states[name]=dict(index=index,address=nodes[index],vtable=r.pointer(nodes[index]))
    _,at,category,declared=b.field(nodes[2],0xc2af3a28);distance=b.pointer(at)
    if (category,declared)!=(2,0xbfd9aadd) or b.literal_int(distance)!=35:raise ValueError('Original Shadow Step range changed')
    for index,rid,expected in [(25,0x0d800000000006ba,1.5),(26,0x0d800000000006bb,1)]:
        if b.dynamic_path(config_ref(b,nodes[index],0x4d475080,0x7fb4bf64,0xbfd9aadd))!=[f'{rid:016x}'] or primitive(r,r.pointer(script+0x98),rid)[1]!=expected:raise ValueError('Original Shadow Step animation timing changed')
    for field,rid,declared in [(0xec9f34a6,0x0d8000000000003d,0xf8cc195d),(0x5180e750,0x0d800000000001d8,0xbfd9aadd)]:
        if b.dynamic_path(config_ref(b,nodes[60],field,0x4698e4b6,declared))!=[f'{rid:016x}']:raise ValueError('Original Shadow Step cooldown assignment changed')
    if primitive(r,r.pointer(script+0x98),0x0d800000000001d8)[1]!=10:raise ValueError('Original Shadow Step cooldown changed')
    base,image,pdb=provided_plugin(process);logger=base+image.symbol_rva(pdb.exact('statescript_logger::s_scriptStates'))
    fn,prefix=image.function_prefix(pdb.exact('?StartStopState@StatescriptInstance@@QEAAXH_N@Z'))
    action,actionPrefix=image.function_prefix(pdb.exact('?ExecuteNode@StatescriptInstance@@QEAAXH@Z'))
    if action!=0x7abc0 or process.read(base+action,32)!=actionPrefix:raise ValueError('Original action wrapper changed')
    if fn!=0x7acd0 or process.read(base+fn,32)!=prefix:raise ValueError('Original state wrapper changed')
    times=[ctypes.create_string_buffer(8) for _ in range(4)];process.kernel.GetProcessTimes.argtypes=[ctypes.c_void_p,*([ctypes.c_void_p]*4)]
    if not process.kernel.GetProcessTimes(process.handle,*times):raise ctypes.WinError(ctypes.get_last_error())
    creation=struct.unpack('<Q',times[0].raw)[0];bag=r.pointer(script+0x98)
    out=dict(version=1,pid=pid,creation=creation,adminAddress=process.base+0x17b7f90,admin=admin,localId=s['localId'],reference=ref,model=model,modelId=s['modelId'],heroInfo=info,hero=0x02e0000000000002,script=script,graph=graph,bag=bag,resource=0x05800000000000f2,logger=logger,states=states)
    if r.unpack('<I',ref+0x94)[0]!=s['modelId'] or r.pointer(r.pointer(r.pointer(script+0x10)+0x450)+8)!=model:raise ValueError('Shadow Step changed during binding')
    values=[creation,admin,s['localId'],s['modelId'],model,script,bag,graph,logger,nodes[52],nodes[25],r.pointer(nodes[52]),r.pointer(nodes[25]),base+fn]
    wire=struct.pack('<8sII14Q32s9Q32s',b'OWSHAD01',2,pid,*values,prefix,nodes[2],nodes[47],nodes[26],nodes[17],nodes[18],nodes[53],nodes[16],nodes[5],base+action,actionPrefix)
    p=ROOT/f'native-host/build/native-shadow-request-{pid}.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(out,indent=2)+'\n');tmp.replace(p)
    p=p.with_suffix('.bin');tmp=p.with_suffix('.tmp');tmp.write_bytes(wire);tmp.replace(p)
    return dict(hero=out['hero'],modelId=s['modelId'],readOnly=True,path=str(p))
