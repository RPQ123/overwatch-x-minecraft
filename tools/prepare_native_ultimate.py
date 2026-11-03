"""Bind the actual charge gate, Dragonblade damage and original execution logger."""
import argparse,json,struct
from observe_overwatch import ROOT,ResearchProcess
from inspect_native_ultimate import inspect
from prepare_native_dash import prepare as prepare_dash

def prepare(process,pid):
    prepare_dash(process,pid);r,u=inspect(process)
    record=json.loads((ROOT/f'native-host/build/native-dash-request-{pid}.json').read_text())
    wi,wg,_=next(k for k in r.graph_cache if k[2]==0x0580000000000304)
    nodes=r.stu_list(wg+0x50)
    for n in (57,58):
        if r.bindings.metadata(nodes[n])[1]!=0x498b421a:raise ValueError('Original sword tracking node changed')
    sword_animation=[]
    for index,alias in ((47,0x0c8000000000003f),(48,0x0c80000000000039)):
        if r.bindings.metadata(nodes[index])[1]!=0x7fb4bf64:raise ValueError('Original sword animation node changed')
        _,field,category,kind=r.bindings.field(nodes[index],0xf9045e7a)
        config=r.pointer(field)
        if category!=2 or kind!=0xbfd9aadd or r.bindings.metadata(config)[1]!=0xee7800e7 or r.unpack('<Q',config+0x18)[0]!=alias:
            raise ValueError('Original sword animation alias changed')
        sword_animation.append(dict(index=index,address=nodes[index],vtable=r.pointer(nodes[index]),field=field,config=config,configVtable=r.pointer(config),alias=alias))
    for n in (60,61):
        modify=r.pointer(r.bindings.field(nodes[n],0x89174668)[1]);amount=r.pointer(r.bindings.field(modify,0xc43222bc)[1])
        if r.bindings.dynamic_path(amount)!=['0d80000000000d6f']:raise ValueError('Original sword damage path changed')
    def primitive(bag,rid):
        found=[]
        for bucket in range(16):
            for key,value in struct.iter_unpack('<QQ',r.vector(bag+0xa0+bucket*0x30,16)):
                if key==rid:found.append(value)
        if len(found)!=1 or r.pointer(found[0])!=process.base+0x1608248:raise ValueError('Numeric primitive changed')
        return found[0]
    entity_bag_address=r.component(record['model'],0x23)+0xc0+0x2e0;entity_bag=r.pointer(entity_bag_address)
    record.update(ultimateScript=u['script'],ultimateBag=r.pointer(u['script']+0x98),weaponScript=wi,weaponBag=r.pointer(wi+0x98),
        entityBagAddress=entity_bag_address,entityBag=entity_bag,charge=u['chargeAddress']-0xa0,
        cost=primitive(entity_bag,0x0d80000000000152),swordDamage=primitive(r.pointer(wi+0x98),0x0d80000000000d6f),numericVtable=process.base+0x1608248,
        swordAnimation=sword_animation)
    if r.unpack('<I',record['admin']+0x220)[0]!=record['localId'] or r.unpack('<I',record['model']+0x94)[0]!=record['modelId'] or r.pointer(r.pointer(r.pointer(wi+0x10)+0x450)+8)!=record['model']:raise ValueError('Native hero changed while binding ultimate')
    path=ROOT/f'native-host/build/native-ultimate-request-{pid}.json';temp=path.with_suffix('.tmp');temp.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');temp.replace(path)
    return {'path':str(path),'originalCost':u['cost'],'readOnlyBinding':True}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pid',type=int,required=True);a=p.parse_args();process=ResearchProcess(a.pid)
    try:print(json.dumps(prepare(process,a.pid)))
    finally:process.close()
