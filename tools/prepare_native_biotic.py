"""Bind actual Soldier E cast/Volley and validated field constants; no native calls."""
import ctypes,json,struct
from observe_overwatch import ROOT
from observe_native_weapon_states import WeaponStates
from inspect_native_biotic_field import inspect,FIELD_SCRIPT,ABILITY,HERO
from provided_plugin_symbols import provided_plugin
from native_map_snapshot import lookup_map

def prepare(process,pid):
    profile=inspect(process)
    r=WeaponStates(process);s=r.sample_weapon(False,True);b=r.bindings
    admin=r.pointer(process.base+0x17b7f90);table=process.read(r.pointer(admin+16),65536)
    controller=r.entity(table,s['localId']);model=r.entity(table,s['modelId'])
    reference=r.component(controller,0x20);info=r.component(controller,0x3f)
    if r.unpack('<Q',info+0x98)[0]!=HERO or s['modelId']!=profile['modelId']:raise ValueError('Biotic owner changed')
    matches=[k for k in r.graph_cache if k[2]==ABILITY]
    if len(matches)!=1:raise ValueError('Biotic graph changed')
    script,graph,_=matches[0];nodes=r.stu_list(graph+0x50)
    states={}
    for name,index,kind in [('deploy',6,0x860ee5fc),('cast',20,0xf7d6498c),('windup',11,0x65f158da)]:
        node=nodes[index]
        if b.metadata(node)[1]!=kind:raise ValueError('Biotic native phase type changed')
        states[name]=dict(index=index,address=node,vtable=r.pointer(node))
    base,image,pdb=provided_plugin(process)
    logger=base+image.symbol_rva(pdb.exact('statescript_logger::s_scriptStates'))
    resource_map=base+image.symbol_rva(pdb.exact('stu_resources::_constructed_stus'))
    field_entry=lookup_map(process,resource_map,FIELD_SCRIPT,'Q',20000)
    if field_entry is None:raise ValueError('Biotic graph is not already loaded')
    field_graph=r.pointer(field_entry);field_nodes=r.stu_list(field_graph+0x50);parameters={}
    for name,index,expected in [('duration',2,5),('radius',3,5),('amount',4,40)]:
        node=field_nodes[index];kind,address,category,declared=b.field(node,0x5180e750);obj=r.pointer(address)
        if kind!=0x4698e4b6 or address!=node+0xa0 or b.metadata(obj)[1]!=0x3ae7427e or b.literal_int(obj)!=expected:raise ValueError('Biotic constant changed')
        parameters[name]=dict(index=index,node=node,nodeVtable=r.pointer(node),field=address,valueObject=obj,valueVtable=r.pointer(obj),value=expected)
    times=[ctypes.create_string_buffer(8) for _ in range(4)]
    process.kernel.GetProcessTimes.argtypes=[ctypes.c_void_p,*([ctypes.c_void_p]*4)]
    if not process.kernel.GetProcessTimes(process.handle,*times):raise ctypes.WinError(ctypes.get_last_error())
    record=dict(version=1,pid=pid,creation=struct.unpack('<Q',times[0].raw)[0],adminAddress=process.base+0x17b7f90,admin=admin,localId=s['localId'],reference=reference,model=model,modelId=s['modelId'],heroInfo=info,hero=HERO,script=script,bag=r.pointer(script+0x98),graph=graph,resource=ABILITY,logger=logger,states=states,fieldGraph=field_graph,fieldGraphVtable=r.pointer(field_graph),fieldParameters=parameters)
    if r.pointer(r.pointer(r.pointer(script+0x10)+0x450)+8)!=model or r.unpack('<I',reference+0x94)[0]!=s['modelId'] or lookup_map(process,resource_map,FIELD_SCRIPT,'Q',20000)!=field_entry or r.pointer(field_entry)!=field_graph:raise ValueError('Biotic owner/resource changed during binding')
    path=ROOT/f'native-host/build/native-biotic-request-{pid}.json';tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');tmp.replace(path)
    return dict(hero=HERO,modelId=s['modelId'],readOnly=True,path=str(path),adapter='native-cast-volley-to-mc-deployment')
