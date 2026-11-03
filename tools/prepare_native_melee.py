"""Bind the actual shared quick-melee TrackTargets action and its live damage."""
import ctypes,json,struct
from observe_overwatch import ROOT
from observe_native_weapon_states import WeaponStates
from native_armory_binding import primitive
from native_hero_profiles import camera_definition
from provided_plugin_symbols import provided_plugin

def prepare(process,pid):
    r=WeaponStates(process);s=r.sample_weapon(False,True);b=r.bindings
    admin=r.pointer(process.base+0x17b7f90);table=process.read(r.pointer(admin+16),65536)
    controller=r.entity(table,s['localId']);model=r.entity(table,s['modelId']);reference=r.component(controller,0x20);info=r.component(controller,0x3f)
    hero=r.unpack('<Q',info+0x98)[0]
    if hero&0xffff not in (2,3,5,6,8,9,10,0x15,0x29,0x42,0x65,0x6e,0xdd):raise ValueError('No calibrated quick melee profile')
    matches=[k for k in r.graph_cache if k[2]==0x0580000000000043]
    if len(matches)!=1:raise ValueError('Original shared melee graph unavailable')
    script,graph,resource=matches[0];nodes=r.stu_list(graph+0x50);bag=r.pointer(script+0x98)
    if b.metadata(nodes[13])[1]!=0x498b421a or b.metadata(nodes[12])[1]!=0x619d9e95:raise ValueError('Original melee node types differ')
    health=r.pointer(b.field(nodes[12],0x89174668)[1]);amount=r.pointer(b.field(health,0xc43222bc)[1])
    if b.dynamic_path(amount)!=['0d800000000001dc']:raise ValueError('Original melee damage path differs')
    value,damage,bucket=primitive(r,bag,0x0d800000000001dc)
    radius=r.pointer(b.field(nodes[13],0x71ef3ca4)[1]);offset=r.pointer(b.field(nodes[13],0x74f86711)[1])
    if b.metadata(offset)[1]!=0xdbf9195c or b.metadata(radius)[1]!=0x3ae7427e or b.literal_int(radius)!=1 or r.unpack('<fff',offset+16)!=(0.,1.5,1.5):raise ValueError('Original melee sphere calibration differs')
    base,image,pdb=provided_plugin(process);logger=base+image.symbol_rva(pdb.exact('statescript_logger::s_scriptStates'))
    times=[ctypes.create_string_buffer(8) for _ in range(4)];process.kernel.GetProcessTimes.argtypes=[ctypes.c_void_p,*([ctypes.c_void_p]*4)]
    if not process.kernel.GetProcessTimes(process.handle,*times):raise ctypes.WinError(ctypes.get_last_error())
    record=dict(version=1,pid=pid,creation=struct.unpack('<Q',times[0].raw)[0],adminAddress=process.base+0x17b7f90,admin=admin,localId=s['localId'],
        reference=reference,model=model,modelId=s['modelId'],heroInfo=info,hero=hero,script=script,bag=bag,graph=graph,resource=resource,logger=logger,
        states={name:dict(index=index,address=nodes[index],vtable=r.pointer(nodes[index])) for name,index in [('strike',13),('modify',12)]},
        damage=value,damageBucket=bucket,numericVtable=r.pointer(value),damageConfig=amount,health=health,radius=radius,radiusVtable=r.pointer(radius),offset=offset,offsetVtable=r.pointer(offset),eye=camera_definition(b,model)['eyeHeight'])
    if r.pointer(r.pointer(r.pointer(script+0x10)+0x450)+8)!=model or r.unpack('<I',reference+0x94)[0]!=s['modelId']:raise ValueError('Melee owner changed')
    path=ROOT/f'native-host/build/native-melee-request-{pid}.json';tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(record,indent=2)+'\n');tmp.replace(path)
    return dict(hero=hero,modelId=s['modelId'],damage=damage,radius=1,offset=[0,1.5,1.5],path=str(path),readOnly=True)
