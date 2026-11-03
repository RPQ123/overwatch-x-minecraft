"""Bind reflected base and current computed locomotion to the native hero's mover."""
import argparse,ctypes,json,math,struct,zlib
from observe_overwatch import ROOT,ResearchProcess
from native_weapon_binding import WeaponBindingReader

FIELDS=('m_speedRunForward','m_speedRunBackward','m_speedRunStrafe','m_speedCrouchForward','m_speedCrouchBackward','m_speedCrouchStrafe')

def prepare(process,pid):
    r=WeaponBindingReader(process);admin=r.pointer(process.base+0x17b7f90)
    table=process.read(r.pointer(admin+0x10),65536);local=r.unpack('<I',admin+0x220)[0];controller=r.entity(table,local)
    reference=r.component(controller,0x20);model_id=r.unpack('<I',reference+0x94)[0];model=r.entity(table,model_id)
    hero_info=r.component(controller,0x3f);hero=r.unpack('<Q',hero_info+0x98)[0]
    entry=r.pointer(model+0x30)&~63;definition=r.pointer(entry)
    if r.metadata(definition)[1]!=zlib.crc32(b'stuentitydefinition'):raise ValueError('Native entity definition type differs')
    header,flag=r.unpack('<QQ',definition+0x28)
    if flag!=2:raise ValueError('Native component map format differs')
    buckets,ends,items=r.unpack('<i4xQQ',header)
    if not 1<=buckets<=256:raise ValueError('Native component map bucket bound')
    count=r.unpack('<i',ends+4*(buckets-1))[0]
    if not 1<=count<=256:raise ValueError('Native component map size bound')
    matches=[obj for kind,obj in struct.iter_unpack('<I4xQ',process.read(items,count*16)) if kind==zlib.crc32(b'stucharactermovercomponent')]
    if len(matches)!=1:raise ValueError('Expected one original character mover definition')
    mover=matches[0];info,kind,size=r.metadata(mover)
    if kind!=zlib.crc32(b'stucharactermovercomponent'):raise ValueError('Mover metadata differs')
    expected={zlib.crc32(name.lower().encode()):name for name in FIELDS};fields={};seen=set()
    while info:
        if info in seen or len(seen)>32:raise ValueError('Mover metadata inheritance')
        seen.add(info);parent,args=r.unpack('<QQ',info+0x20);n=r.unpack('<i',info+0x54)[0]
        if not 0<=n<=512:raise ValueError('Mover field bound')
        for i in range(n):
            key,offset,constraint=r.unpack('<IiQ',args+i*0xa0+8)
            if key not in expected:continue
            getter=r.pointer(r.pointer(constraint)+0x30)
            if process.read(getter,4)!=bytes.fromhex('8b4128c3') or r.unpack('<I',constraint+0x28)[0]!=zlib.crc32(b'f32'):raise ValueError('Mover speed is not reflected f32')
            if not 8<=offset<=size-4 or offset%4:raise ValueError('Mover field offset')
            value=r.unpack('<f',mover+offset)[0]
            if not 0<value<=30:raise ValueError('Native locomotion speed bound')
            fields[expected[key]]={'address':mover+offset,'offset':offset,'fieldHash':key,'value':value}
        info=parent
    if set(fields)!=set(FIELDS):raise ValueError('Missing native directional/crouch speed fields')
    runtime=r.component(model,0x15)
    if r.pointer(runtime+8)!=model or r.unpack('<B',runtime+0x10)[0]!=0x15:raise ValueError('Runtime mover owner differs')
    # Original directional-speed selection at10b3270..10b32c5 reads these
    # computed fields, including the current scope/sprint/root modifiers.
    effective=r.unpack('<6f',runtime+0x300)
    if any(not math.isfinite(v) or not 0<=v<=fields[name]['value']*3 for name,v in zip(FIELDS,effective)):
        raise ValueError('Native computed directional speed bounds')
    times=[ctypes.create_string_buffer(8) for _ in range(4)]
    process.kernel.GetProcessTimes.argtypes=[ctypes.c_void_p,*([ctypes.c_void_p]*4)]
    if not process.kernel.GetProcessTimes(process.handle,*times):raise ctypes.WinError(ctypes.get_last_error())
    record={'version':2,'pid':pid,'creation':struct.unpack('<Q',times[0].raw)[0],'adminAddress':process.base+0x17b7f90,'admin':admin,'localId':local,'reference':reference,'modelId':model_id,'model':model,'heroInfo':hero_info,'hero':hero,'entry':entry,'definition':definition,'mover':mover,'moverVtable':r.pointer(mover),'runtimeMover':runtime,'runtimeMoverVtable':r.pointer(runtime),'fields':fields,'unit':'native-metres-per-second','nativeCalls':False}
    if r.pointer(process.base+0x17b7f90)!=admin or r.unpack('<I',admin+0x220)[0]!=local or r.unpack('<I',reference+0x94)[0]!=model_id or r.unpack('<Q',hero_info+0x98)[0]!=hero:raise ValueError('Native hero changed while binding locomotion')
    path=ROOT/f'native-host/build/native-locomotion-request-{pid}.json';temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');temp.replace(path)
    return record

if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--pid',required=True,type=int);args=a.parse_args();p=ResearchProcess(args.pid)
    try:print(json.dumps(prepare(p,args.pid),indent=2))
    finally:p.close()
