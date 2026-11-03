"""Read-only original Tracer magazine through the declared Volley ammo output."""
from observe_native_weapon_states import WeaponStates
from native_armory_binding import primitive,projectile_resources

def inspect(process):
    r=WeaponStates(process);s=r.sample_weapon(False,True);rows=[]
    admin=r.pointer(process.base+0x17b7f90);table=process.read(r.pointer(admin+16),65536);controller=r.entity(table,s['localId'])
    if r.unpack('<Q',r.component(controller,0x3f)+0x98)[0]!=0x02e0000000000003:raise ValueError('Original Tracer required')
    for (script,graph,resource),definition in r.graph_cache.items():
        for index in definition['volleyNodes']:
            node=r.stu_list(graph+0x50)[index]
            if not any(v[0]==0x0400000000000018 for v in projectile_resources(r,node)):continue
            path=r.bindings.ammo_output(node)['resourcePath']
            if path!=['0d80000000000035']:raise ValueError('Original Tracer ammo scope changed')
            obj,value,bucket=primitive(r,r.pointer(script+0x98),int(path[0],16))
            if not 0<=value<=40:raise ValueError('Tracer magazine outside declared observed bounds')
            rows.append(dict(modelId=s['modelId'],ammo=value,script=f'{resource:016x}',node=index,numeric=obj,readOnly=True))
    if len(rows)!=1:raise ValueError('Tracer magazine is not unique')
    if r.unpack('<I',r.component(controller,0x20)+0x94)[0]!=s['modelId']:raise ValueError('Tracer changed while reading ammo')
    return rows[0]
