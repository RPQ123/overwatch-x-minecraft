"""Bind a read-only original Shift-state reader to the exact live offline Genji."""
import argparse,json,struct,zlib
from observe_overwatch import ROOT,ResearchProcess
from observe_native_weapon_states import WeaponStates
from provided_plugin_symbols import provided_plugin

def prepare(process,pid):
    r=WeaponStates(process);s=r.sample_weapon();instance,graph,_=next(k for k in r.graph_cache if k[2]==0x05800000000001db)
    nodes=r.stu_list(graph+0x50);speed=r.pointer(r.bindings.field(nodes[6],0x43d14192)[1])
    if r.bindings.metadata(speed)[1]!=zlib.crc32(b'stuconfigvarint'):raise ValueError('Native MoveTo speed is not the measured integer config')
    rate=r.unpack('<i',speed+16)[0]
    if not 1<=rate<=100:raise ValueError('Native MoveTo speed bounds')
    modify=r.pointer(r.bindings.field(nodes[26],0x89174668)[1]);amount=r.pointer(r.bindings.field(modify,0xc43222bc)[1]);path=r.bindings.dynamic_path(amount)
    if path!=['0d800000000001dc']:raise ValueError('Native dash damage binding changed')
    bag=r.pointer(instance+0x98);values=[]
    for bucket in range(16):
        for rid,value in struct.iter_unpack('<QQ',r.vector(bag+0xa0+bucket*0x30,16)):
            if rid==0x0d800000000001dc:values.append(value)
    if len(values)!=1 or r.pointer(values[0])!=process.base+0x1608248:raise ValueError('Native dash damage value changed')
    admin=r.pointer(process.base+0x17b7f90);model=r.entity(process.read(r.pointer(admin+0x10),65536),s['modelId'])
    if r.bindings.metadata(nodes[5])[1]!=zlib.crc32(b'stustatescriptstateability'):raise ValueError('Native Shift ability definition changed')
    cooldown=r.pointer(r.bindings.field(nodes[5],0xcb5a4101)[1])
    if r.bindings.dynamic_path(cooldown)!=['0d8000000000003d']:raise ValueError('Native Shift cooldown output changed')
    definitions=r.stu_list(graph+0x60);cooldown_states=[]
    for state, in struct.iter_unpack('<Q',r.vector(instance+0xa0,8,4096)):
        if not state:continue
        index=r.unpack('<i',state+0x70)[0]
        if not 0<=index<len(definitions):raise ValueError('Native ability state index bounds')
        if definitions[index]==nodes[5]:cooldown_states.append((state,index))
    if len(cooldown_states)!=1 or r.pointer(cooldown_states[0][0])!=process.base+0x15d7c98:raise ValueError('Original Shift cooldown state changed')
    base,image,pdb=provided_plugin(process);logger=base+image.symbol_rva(pdb.exact('statescript_logger::s_scriptStates'))
    times=[__import__('ctypes').create_string_buffer(8) for _ in range(4)]
    import ctypes
    k=process.kernel;k.GetProcessTimes.argtypes=[ctypes.c_void_p,*([ctypes.c_void_p]*4)];k.GetProcessTimes.restype=ctypes.c_int
    if not k.GetProcessTimes(process.handle,*times):raise ctypes.WinError(ctypes.get_last_error())
    record={'version':1,'pid':pid,'creation':struct.unpack('<Q',times[0].raw)[0],'adminAddress':process.base+0x17b7f90,'admin':admin,'localId':s['localId'],'model':model,'modelId':s['modelId'],'script':instance,'bag':bag,'resource':0x05800000000001db,'logger':logger,'node':6,'speed':speed,'speedVtable':r.pointer(speed),'damage':values[0],'damageVtable':process.base+0x1608248}
    record.update(graph=graph,cooldownState=cooldown_states[0][0],cooldownStateIndex=cooldown_states[0][1],cooldownDefinition=nodes[5],cooldownVtable=process.base+0x15d7c98)
    controller=r.entity(process.read(r.pointer(admin+0x10),65536),s['localId'])
    reference=r.component(controller,0x20);hero_info=r.component(controller,0x3f)
    if r.unpack('<I',reference+0x94)[0]!=s['modelId'] or r.unpack('<Q',hero_info+0x98)[0]!=0x02e0000000000029:raise ValueError('Current controller is not this Genji model')
    record.update(version=2,controller=controller,reference=reference,heroInfo=hero_info)
    if r.unpack('<I',admin+0x220)[0]!=s['localId'] or r.unpack('<I',model+0x94)[0]!=s['modelId'] or r.unpack('<I',reference+0x94)[0]!=s['modelId'] or r.unpack('<Q',hero_info+0x98)[0]!=0x02e0000000000029 or r.pointer(r.pointer(r.pointer(instance+0x10)+0x450)+8)!=model:raise ValueError('Native hero changed while binding dash')
    path=ROOT/f'native-host/build/native-dash-request-{pid}.json';temp=path.with_suffix('.tmp');temp.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');temp.replace(path);return {'path':str(path),'nativeSpeed':rate,'damagePath':'0d800000000001dc','readOnly':True}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pid',type=int,required=True);a=parser.parse_args();p=ResearchProcess(a.pid)
    try:print(json.dumps(prepare(p,a.pid)))
    finally:p.close()
