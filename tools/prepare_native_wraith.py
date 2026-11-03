"""Pin the original Wraith root/animation. No calls or legacy lab flags."""
import ctypes,json,struct
from observe_overwatch import ROOT
from observe_native_weapon_states import WeaponStates
from provided_plugin_symbols import provided_plugin

def prepare(process,pid):
    r=WeaponStates(process);s=r.sample_weapon(False,True);b=r.bindings
    admin=r.pointer(process.base+0x17b7f90);table=process.read(r.pointer(admin+16),65536)
    controller=r.entity(table,s['localId']);model=r.entity(table,s['modelId']);ref=r.component(controller,0x20);info=r.component(controller,0x3f)
    if r.unpack('<Q',info+0x98)[0]!=0x02e0000000000002:raise ValueError('Wraith requires current Reaper')
    matches=[k for k in r.graph_cache if k[2]==0x0580000000000020]
    if len(matches)!=1:raise ValueError('Original Wraith graph is not unique')
    script,graph,_=matches[0];nodes=r.stu_list(graph+0x50);states={}
    if len(nodes)!=28:raise ValueError('Wraith graph size changed')
    for name,index,kind,vt in [('cast',20,0xa7213568,0x1500590),('animation',3,0x7fb4bf64,0x15138c0)]:
        if b.metadata(nodes[index])[1]!=kind or r.pointer(nodes[index])!=process.base+vt:raise ValueError('Wraith original phase changed')
        states[name]=dict(index=index,address=nodes[index],vtable=r.pointer(nodes[index]))
    _,at,category,declared=b.field(nodes[3],0x4d475080);duration=b.pointer(at)
    if (category,declared)!=(2,0xbfd9aadd) or b.literal_int(duration)!=3:raise ValueError('Original Wraith duration changed')
    _,at,category,declared=b.field(graph+8,0x9d751e7c)
    if (category,declared)!=(3,0x38a4b0b7):raise ValueError('Wraith links changed')
    children=set()
    for link in r.stu_list(at):
        output,input_=r.unpack('<QQ',link+8)
        if r.pointer(output+24)==nodes[20]:
            if b.metadata(output)[1]!=0x24ab1f0b:raise ValueError('Wraith root plug changed')
            children.add(r.pointer(input_+24))
    if children!={nodes[2],nodes[3],nodes[18]}:raise ValueError('Wraith root lifecycle changed')
    base,image,pdb=provided_plugin(process);logger=base+image.symbol_rva(pdb.exact('statescript_logger::s_scriptStates'))
    fn,prefix=image.function_prefix(pdb.exact('?StartStopState@StatescriptInstance@@QEAAXH_N@Z'))
    if fn!=0x7acd0 or process.read(base+fn,32)!=prefix:raise ValueError('Original state wrapper changed')
    times=[ctypes.create_string_buffer(8) for _ in range(4)];process.kernel.GetProcessTimes.argtypes=[ctypes.c_void_p,*([ctypes.c_void_p]*4)]
    if not process.kernel.GetProcessTimes(process.handle,*times):raise ctypes.WinError(ctypes.get_last_error())
    creation=struct.unpack('<Q',times[0].raw)[0];bag=r.pointer(script+0x98)
    out=dict(version=1,pid=pid,creation=creation,adminAddress=process.base+0x17b7f90,admin=admin,localId=s['localId'],reference=ref,model=model,modelId=s['modelId'],heroInfo=info,hero=0x02e0000000000002,script=script,graph=graph,bag=bag,resource=0x0580000000000020,logger=logger,states=states)
    if r.unpack('<I',ref+0x94)[0]!=s['modelId'] or r.pointer(r.pointer(r.pointer(script+0x10)+0x450)+8)!=model:raise ValueError('Wraith changed during binding')
    values=[creation,admin,s['localId'],s['modelId'],model,script,bag,graph,logger,nodes[20],nodes[3],r.pointer(nodes[20]),r.pointer(nodes[3]),base+fn]
    wire=struct.pack('<8sII14Q32s',b'OWWRTH01',1,pid,*values,prefix)
    p=ROOT/f'native-host/build/native-wraith-request-{pid}.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(out,indent=2)+'\n');tmp.replace(p)
    p=p.with_suffix('.bin');tmp=p.with_suffix('.tmp');tmp.write_bytes(wire);tmp.replace(p)
    return dict(hero=out['hero'],modelId=s['modelId'],readOnly=True,path=str(p))
