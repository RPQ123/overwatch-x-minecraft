"""Read-only owner binding for original Bastion/Mei self-healing phases.

The beta client has no server ModifyHealth implementation. MC distributes the
declared amount over the declared interval while the actual node is active.
This server adaptation is explicit; no key press creates a healing phase.
"""
import ctypes,json,struct,math
from observe_overwatch import ROOT
from observe_native_weapon_states import WeaponStates
from native_armory_binding import primitive
from provided_plugin_symbols import provided_plugin

PROFILES={0x02e0000000000015:(0x0580000000000153,2),0x02e00000000000dd:(0x05800000000005fe,30)}

def prepare(process,pid):
    r=WeaponStates(process);s=r.sample_weapon(False,True);b=r.bindings
    admin=r.pointer(process.base+0x17b7f90);table=process.read(r.pointer(admin+16),65536)
    controller=r.entity(table,s['localId']);model=r.entity(table,s['modelId']);reference=r.component(controller,0x20);info=r.component(controller,0x3f)
    hero=r.unpack('<Q',info+0x98)[0]
    if hero not in PROFILES:raise ValueError('No measured self-heal profile')
    resource,index=PROFILES[hero];matches=[k for k in r.graph_cache if k[2]==resource]
    if len(matches)!=1:raise ValueError('Original self-heal graph unavailable')
    script,graph,_=matches[0];nodes=r.stu_list(graph+0x50);node=nodes[index];bag=r.pointer(script+0x98)
    if b.metadata(node)[1]!=0x619d9e95:raise ValueError('Original ModifyHealth type differs')
    health=r.pointer(b.field(node,0x89174668)[1]);amount=r.pointer(b.field(health,0xc43222bc)[1]);interval=r.pointer(b.field(node,0xd525b22b)[1]);target=r.pointer(b.field(node,0xebda16f6)[1])
    if b.metadata(health)[1]!=0x06a06f4e or b.metadata(amount)[1]!=0x3ae7427e or b.metadata(target)[1]!=0x261676f0:raise ValueError('Self-heal target/amount declarations differ')
    value=b.literal_int(amount)
    if not 0<value<=1000:raise ValueError('Healing amount bounds')
    params=dict(health=health,amount=amount,amountVtable=r.pointer(amount),interval=interval,intervalVtable=r.pointer(interval),target=target,targetVtable=r.pointer(target))
    if hero&0xffff==0x15:
        if b.metadata(interval)[1]!=0x3ae7427e or b.literal_int(interval)!=1:raise ValueError('Repair interval differs')
    else:
        if b.metadata(interval)[1]!=0xec502a81:raise ValueError('Cryo interval expression differs')
        def array(at,stride):
            storage,flag=r.unpack('<QQ',at)
            if flag not in (1,2):raise ValueError('Interval expression storage')
            a,c=r.unpack('<QQ',storage);items,count=(a,c) if flag==1 else(c,a)
            if not 0<count<=256:raise ValueError('Interval expression count')
            return items,count,process.read(items,count*stride)
        code,n,ops=array(interval+0x20,1);constants,count,raw=array(interval+0x40,4);dynamics,dcount,dyn=array(interval+0x30,8)
        if ops!=bytes([31,0,70,0,101,0]) or count!=1 or dcount!=1:raise ValueError('Cryo interval is not measured duration minus .1')
        config=struct.unpack('<Q',dyn)[0]
        if b.dynamic_path(config)!=['0d80000000000237'] or struct.unpack('<f',raw)[0]!=struct.unpack('<f',struct.pack('<f',.1))[0]:raise ValueError('Cryo duration path/constant differs')
        numeric,duration,bucket=primitive(r,bag,0x0d80000000000237)
        if not math.isfinite(duration) or not .2<=duration<=10:raise ValueError('Cryo duration bounds')
        params.update(code=code,constants=constants,dynamics=dynamics,dynamicConfig=config,dynamicVtable=r.pointer(config),duration=numeric,durationBucket=bucket,numericVtable=r.pointer(numeric))
    base,image,pdb=provided_plugin(process);logger=base+image.symbol_rva(pdb.exact('statescript_logger::s_scriptStates'))
    times=[ctypes.create_string_buffer(8) for _ in range(4)];process.kernel.GetProcessTimes.argtypes=[ctypes.c_void_p,*([ctypes.c_void_p]*4)]
    if not process.kernel.GetProcessTimes(process.handle,*times):raise ctypes.WinError(ctypes.get_last_error())
    record=dict(version=1,pid=pid,creation=struct.unpack('<Q',times[0].raw)[0],adminAddress=process.base+0x17b7f90,admin=admin,localId=s['localId'],reference=reference,model=model,modelId=s['modelId'],heroInfo=info,hero=hero,script=script,bag=bag,graph=graph,resource=resource,logger=logger,
        states={'heal':dict(index=index,address=node,vtable=r.pointer(node))},healing=params)
    if r.pointer(r.pointer(r.pointer(script+0x10)+0x450)+8)!=model or r.unpack('<I',reference+0x94)[0]!=s['modelId']:raise ValueError('Healing owner changed')
    path=ROOT/f'native-host/build/native-sustain-request-{pid}.json';tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(record,indent=2)+'\n');tmp.replace(path)
    return dict(hero=hero,modelId=s['modelId'],amount=value,readOnly=True,path=str(path))
