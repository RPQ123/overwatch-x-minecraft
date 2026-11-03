"""Read original Pharah Jump Jet timer and hover fuel, with current owner proof."""
import struct
from observe_native_weapon_states import WeaponStates

def snapshot(process):
    r=WeaponStates(process);s=r.sample_weapon(False,True);admin=r.pointer(process.base+0x17b7f90);table=process.read(r.pointer(admin+16),65536)
    controller=r.entity(table,s['localId']);model=r.entity(table,s['modelId'])
    if r.unpack('<Q',r.component(controller,0x3f)+0x98)[0]!=0x02e0000000000008:raise ValueError('Pharah required')
    script,graph,_=next(k for k in r.graph_cache if k[2]==0x0580000000000027)
    nodes=r.stu_list(graph+0x50);definitions=r.stu_list(graph+0x60);states=[]
    for state, in struct.iter_unpack('<Q',r.vector(script+0xa0,8,4096)):
        if not state:continue
        index=r.unpack('<i',state+0x70)[0]
        if not 0<=index<len(definitions):raise ValueError('Ability state index bounds')
        if definitions[index]==nodes[12]:states.append(state)
    if len(states)!=1 or r.pointer(states[0])!=process.base+0x15d7c98 or r.pointer(states[0]+0x78)!=script:raise ValueError('Original Jump Jet ability differs')
    remaining=r.unpack('<f',states[0]+0x150)[0]
    if not 0<=remaining<=10.1:raise ValueError('Original Jet cooldown bounds')
    fuel=next(v.get('value') for v in s['observedVariables']['0580000000000025'] if v['rid']=='0d80000000000057')
    jet=[v for v in s['records'].values() if v['script']=='0580000000000027' and v['node']==1]
    if r.unpack('<I',admin+0x220)[0]!=s['localId'] or r.pointer(r.pointer(r.pointer(script+0x10)+0x450)+8)!=model:raise ValueError('Hero changed')
    return dict(model=s['modelId'],jetRemaining=remaining,jetTick=jet[0]['nativeTick'] if jet else 0,fuelCommitted=fuel)
