"""Bind measured original skill states, read-only; never activate abilities."""
import ctypes,json,struct,math
from observe_overwatch import ROOT,ResearchProcess
from observe_native_weapon_states import WeaponStates
from provided_plugin_symbols import provided_plugin

PROFILES={
    0x02e0000000000006:(0x05800000000001c2,{'ultimate':(21,0xf7d6498c),'coreAnimation':(30,0x7fb4bf64),'coreArmor':(19,0xc17b255d),'coreEffect':(20,0xffbfa88d),'coreTimer':(17,0x970ec198)}),
    0x02e000000000000a:(0x0580000000000067,{'ultimate':(18,0xf7d6498c),'infraAnimation':(6,0x7fb4bf64),'infraEffect':(13,0xffbfa88d),'infraTimer':(10,0x970ec198)}),
    0x02e0000000000002:(0x0580000000000044,{'ultimate':(49,0xa7213568),'firing':(48,0x860ee5fc),'animation':(9,0x7fb4bf64)}),
    0x02e0000000000015:(0x058000000000012f,{'recon':(8,0xa7213568),'sentry':(9,0xa7213568),'tank':(105,0xa7213568)}),
    0x02e0000000000029:(0x05800000000003a3,{'deflect':(30,0x67471c66)}),
    0x02e0000000000008:(0x058000000000002b,{'barrage':(12,0xf7d6498c),'windup':(13,0x65f158da),'firing':(2,0x860ee5fc)}),
    0x02e000000000006e:(0x0580000000000259,{'ultimate':(15,0xf7d6498c),'visor':(12,0x498b421a)}),
    0x02e0000000000042:(0x058000000000022f,{'ultimate':(18,0xa7213568),'tracking':(27,0x498b421a),'fire':(44,0xeb923a6a),'shotAnimation':(69,0x7fb4bf64)}),
}

def prepare(process,pid):
    r=WeaponStates(process);s=r.sample_weapon(False,True);b=r.bindings
    admin=r.pointer(process.base+0x17b7f90);table=process.read(r.pointer(admin+16),65536)
    controller=r.entity(table,s['localId']);model=r.entity(table,s['modelId'])
    reference=r.component(controller,0x20);info=r.component(controller,0x3f)
    hero=r.unpack('<Q',info+0x98)[0]
    if hero not in PROFILES:raise ValueError('No measured native skill profile')
    resource,profile=PROFILES[hero];matches=[k for k in r.graph_cache if k[2]==resource]
    if len(matches)!=1:raise ValueError('Original skill graph unavailable')
    script,graph,_=matches[0];nodes=r.stu_list(graph+0x50);states={}
    for name,(index,kind) in profile.items():
        if index>=len(nodes) or b.metadata(nodes[index])[1]!=kind:raise ValueError('Original skill node type differs')
        states[name]=dict(index=index,address=nodes[index],vtable=r.pointer(nodes[index]))
    if r.pointer(r.pointer(r.pointer(script+0x10)+0x450)+8)!=model or r.unpack('<I',reference+0x94)[0]!=s['modelId']:raise ValueError('Skill owner changed')
    base,image,pdb=provided_plugin(process);logger=base+image.symbol_rva(pdb.exact('statescript_logger::s_scriptStates'))
    times=[ctypes.create_string_buffer(8) for _ in range(4)];process.kernel.GetProcessTimes.argtypes=[ctypes.c_void_p,*([ctypes.c_void_p]*4)]
    if not process.kernel.GetProcessTimes(process.handle,*times):raise ctypes.WinError(ctypes.get_last_error())
    record=dict(version=1,pid=pid,creation=struct.unpack('<Q',times[0].raw)[0],adminAddress=process.base+0x17b7f90,
        admin=admin,localId=s['localId'],reference=reference,model=model,modelId=s['modelId'],heroInfo=info,hero=hero,
        script=script,bag=r.pointer(script+0x98),graph=graph,resource=resource,logger=logger,states=states)
    if hero==0x02e000000000000a:
        _,field,category,declared=b.field(nodes[6],0x4d475080);duration=b.pointer(field)
        if (category,declared)!=(2,0xbfd9aadd) or b.metadata(duration)[1]!=0x3ae7427e or b.literal_int(duration)!=15:
            raise ValueError('Original Infra-Sight duration differs')
        from native_armory_binding import primitive as infra_primitive
        _,value,_=infra_primitive(r,record['bag'],0x0d80000000000237)
        if value!=15:raise ValueError('Original Infra-Sight variable differs')
        record['infraDuration']=dict(field=field,object=duration,vtable=r.pointer(duration),value=15)
    if hero==0x02e0000000000002:
        parameters={}
        for name,index,key,expected in [('range',48,0x308e35d5,8),('duration',9,0x4d475080,3)]:
            _,at,category,declared=b.field(nodes[index],key);obj=b.pointer(at)
            if (category,declared)!=(2,0xbfd9aadd) or b.metadata(obj)[1]!=0x3ae7427e or b.literal_int(obj)!=expected:raise ValueError('Original Death Blossom parameter changed')
            parameters[name]=dict(node=index,definition=nodes[index],field=at,object=obj,vtable=r.pointer(obj),value=expected)
        record['reaperParameters']=parameters
    if hero==0x02e0000000000042:
        fn,prefix=image.function_prefix(pdb.exact('?StartStopState@StatescriptInstance@@QEAAXH_N@Z'))
        if fn!=0x7acd0 or process.read(base+fn,32)!=prefix:raise ValueError('Original UI animation wrapper differs')
        if r.unpack('<Q',r.pointer(nodes[69]+0x100)+0x18)[0]!=0x0c8000000000019f:raise ValueError('Original Deadeye shot animation alias differs')
        record['deadeyePresentation']={'function':base+fn,'prefix':prefix.hex()}
        from native_armory_binding import primitive
        geometry={}
        for name,index,key,expected in [('radius',27,0x71ef3ca4,70),('angle',27,0x9d812041,105),('rate',91,0x4c76fa6d,160),('cap',91,0xac0b10be,1000)]:
            _,at,category,declared=b.field(nodes[index],key);obj=b.pointer(at)
            if category!=2 or declared!=0xbfd9aadd or b.metadata(obj)[1]!=0x3ae7427e or b.literal_int(obj)!=expected:raise ValueError('Original Deadeye geometry differs')
            geometry[name]=dict(node=index,definition=nodes[index],field=at,object=obj,vtable=r.pointer(obj),value=expected)
        obj,value,bucket=primitive(r,record['bag'],0x0d80000000000237)
        if value!=10:raise ValueError('Original Deadeye duration differs')
        geometry['duration']=dict(object=obj,vtable=r.pointer(obj),bucket=bucket,value=value)
        record['deadeyeGeometry']=geometry
    if hero==0x02e000000000006e:
        node=nodes[12];geometry={}
        for name,key in [('radius',0x71ef3ca4),('angle',0x9d812041)]:
            kind,address,category,declared=b.field(node,key)
            if (kind,category,declared)!=(0x498b421a,2,0xbfd9aadd):raise ValueError('Visor tracking declaration differs')
            obj=b.pointer(address);typ=b.metadata(obj)[1]
            value=b.literal_int(obj) if typ==0x3ae7427e else b.literal_float_expression(obj)['value']
            if value!=45:raise ValueError('Original Visor tracking geometry changed')
            geometry[name]=dict(field=address,object=obj,vtable=r.pointer(obj),value=value,
                                valueAddress=obj+16 if typ==0x3ae7427e else b.literal_float_expression(obj)['valueAddress'],integer=typ==0x3ae7427e)
        record['visorGeometry']=geometry
    if hero==0x02e0000000000029:
        kind,address,category,declared=b.field(nodes[30],0x81060d8d)
        if (kind,category,declared)!=(0x67471c66,5,0xcda846fe):raise ValueError('Original Deflect box declaration differs')
        storage,flag=r.unpack('<QQ',address)
        if not storage or flag not in (1,2):raise ValueError('Deflect box storage')
        first,second=r.unpack('<QQ',storage);items,count=(first,second) if flag==1 else(second,first)
        if count!=3:raise ValueError('Original Deflect box count differs')
        boxes=[]
        # The beta's reflected inline box is16 bytes (two vector configs), not
        # the24-byte modern retail type. Preserve both original corner vectors.
        for i in range(count):
            a,c=r.unpack('<QQ',items+i*16)
            if any(b.metadata(v)[1]!=0xdbf9195c for v in (a,c)):raise ValueError('Deflect corner vector type')
            corners=[r.unpack('<fff',v+16) for v in (a,c)]
            if not all(math.isfinite(x) and abs(x)<=8 for v in corners for x in v):raise ValueError('Deflect corner bounds')
            boxes.append(dict(first=a,second=c,firstVtable=r.pointer(a),secondVtable=r.pointer(c),corners=corners))
        record['deflectBoxes']=dict(field=address,items=items,count=count,boxes=boxes)
    path=ROOT/f'native-host/build/native-skills-request-{pid}.json';tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');tmp.replace(path)
    return dict(hero=hero,modelId=s['modelId'],path=str(path),readOnly=True,states=list(states))

if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser();a.add_argument('--pid',required=True,type=int);args=a.parse_args();p=ResearchProcess(args.pid)
    try:print(json.dumps(prepare(p,args.pid)))
    finally:p.close()
