"""Bind the original McCree Wait state and reflected roll configuration, read-only."""
import argparse,ctypes,json,math,struct,zlib
from observe_overwatch import ROOT,ResearchProcess
from observe_native_weapon_states import WeaponStates
from provided_plugin_symbols import provided_plugin

RESOURCE=0x05800000000001f0
HERO=0x02e0000000000042
SPEED_VAR=0x0d80000000000670

def prepare(process,pid):
    r=WeaponStates(process);sample=r.sample_weapon();b=r.bindings
    admin=r.pointer(process.base+0x17b7f90);table=process.read(r.pointer(admin+0x10),65536)
    controller=r.entity(table,sample['localId']);reference=r.component(controller,0x20)
    model=r.entity(table,sample['modelId']);info=r.component(controller,0x3f)
    if r.unpack('<Q',info+0x98)[0]!=HERO:raise ValueError('Roll requires the original McCree model')
    matches=[key for key in r.graph_cache if key[2]==RESOURCE]
    if len(matches)!=1:raise ValueError('Expected one original roll graph')
    script,graph,_=matches[0];nodes=r.stu_list(graph+0x50);bag=r.pointer(script+0x98)
    def field(obj,name):return b.field(obj,zlib.crc32(name.lower().encode()))[1]
    def data(at,stride):
        storage,flag=r.unpack('<QQ',at)
        if not storage or flag not in (1,2):raise ValueError('Roll expression storage')
        a,c=r.unpack('<QQ',storage);items,count=(a,c) if flag==1 else (c,a)
        if not 0<=count<=128 or (count and not items):raise ValueError('Roll expression bounds')
        return process.read(items,count*stride) if count else b''
    if b.metadata(nodes[4])[1]!=zlib.crc32(b'stustatescriptstatewait'):raise ValueError('Roll timer node differs')
    timeout=r.pointer(field(nodes[4],'m_timeout'))
    if b.metadata(timeout)[1]!=zlib.crc32(b'stuconfigvarfloat'):raise ValueError('Roll timeout type')
    seconds=r.unpack('<f',timeout+16)[0]
    if not math.isfinite(seconds) or not 0<seconds<=2:raise ValueError('Roll timeout bounds')
    expected={8:bytes((31,0,30,1,30,0,174,102,30,2,30,0,173,102,101,170,102,0)),
              11:bytes((31,0,30,0,70,0,70,1,70,0,171,102,170,102,0))}
    for index,bytecode in expected.items():
        if b.metadata(nodes[index])[1]!=zlib.crc32(b'stustatescriptactionmovementmod'):raise ValueError('Roll movement action differs')
        ops=r.stu_list(field(nodes[index],'m_ops'))
        if len(ops)!=1 or b.metadata(ops[0])[1]!=0x7449ba63:raise ValueError('Roll movement operation differs')
        expr=r.pointer(field(ops[0],'m_val'))
        if b.metadata(expr)[1]!=0xec502a81 or data(expr+0x20,1)!=bytecode:raise ValueError('Roll direction expression differs')
        dynamic=data(expr+0x30,8)
        if len(dynamic)!=8 or b.dynamic_path(struct.unpack('<Q',dynamic)[0])!=[f'{SPEED_VAR:016x}']:raise ValueError('Roll speed expression path')
        floats=data(expr+0x40,4)
        if floats!=(struct.pack('<ff',1,0) if index==11 else b''):raise ValueError('Roll direction constants')
        configs=r.stu_list(field(expr,'m_configVars'))
        names=['stuconfigvargetentityforwardvector'] if index==11 else ['stuconfigvargetthrottle','stuconfigvargetentityforwardvector','stuconfigvargetentityleftvector']
        if len(configs)!=len(names):raise ValueError('Roll direction inputs')
        for config,name in zip(configs,names):
            if b.metadata(config)[1]!=zlib.crc32(name.encode()) or b.metadata(r.pointer(field(config,'m_entity')))[1]!=zlib.crc32(b'stuconfigvargetowner'):raise ValueError('Roll direction owner')
    values=[value for bucket in range(16) for rid,value in struct.iter_unpack('<QQ',r.vector(bag+0xa0+bucket*0x30,16)) if rid==SPEED_VAR]
    if len(values)!=1 or r.pointer(values[0])!=process.base+0x1608248:raise ValueError('Roll speed variable type')
    raw=process.read(values[0]+0xa0,16);kind=struct.unpack_from('<I',raw,12)[0]
    if kind not in (2,3):raise ValueError('Roll speed is not numeric')
    speed=struct.unpack_from('<i' if kind==2 else '<f',raw)[0]
    if not math.isfinite(speed) or not 0<speed<=100:raise ValueError('Roll speed bounds')
    base,image,pdb=provided_plugin(process);logger=base+image.symbol_rva(pdb.exact('statescript_logger::s_scriptStates'))
    times=[ctypes.create_string_buffer(8) for _ in range(4)]
    process.kernel.GetProcessTimes.argtypes=[ctypes.c_void_p,*([ctypes.c_void_p]*4)]
    if not process.kernel.GetProcessTimes(process.handle,*times):raise ctypes.WinError(ctypes.get_last_error())
    if r.unpack('<I',reference+0x94)[0]!=sample['modelId'] or r.unpack('<Q',info+0x98)[0]!=HERO or r.pointer(r.pointer(r.pointer(script+0x10)+0x450)+8)!=model:raise ValueError('Roll owner changed during binding')
    record={'version':1,'pid':pid,'creation':struct.unpack('<Q',times[0].raw)[0],
        'adminAddress':process.base+0x17b7f90,'admin':admin,'localId':sample['localId'],
        'reference':reference,'model':model,'modelId':sample['modelId'],'heroInfo':info,'hero':HERO,
        'script':script,'bag':bag,'graph':graph,'resource':RESOURCE,'node':4,'logger':logger,
        'speed':values[0],'numericVtable':process.base+0x1608248,'timeout':timeout,'timeoutVtable':r.pointer(timeout)}
    path=ROOT/f'native-host/build/native-roll-request-{pid}.json';tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');tmp.replace(path)
    return {'hero':HERO,'modelId':sample['modelId'],'path':str(path),'speed':speed,'seconds':seconds,'readOnly':True}

if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--pid',type=int,required=True);args=a.parse_args();p=ResearchProcess(args.pid)
    try:print(json.dumps(prepare(p,args.pid)))
    finally:p.close()
