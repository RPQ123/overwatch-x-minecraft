"""语音挂接：只读绑定半藏b9:79大招消息入口，b9:76仅作发射时间对照；不按键、不激活技能。"""
import argparse
import json
from observe_overwatch import ROOT,ResearchProcess
from observe_native_weapon_states import WeaponStates

HERO=0x02e0000000000005
GRAPH=0x05800000000000b9
PURPOSE='heroVoiceHanzoBegin'
PROFILE=[('castBegin',79,0xbe49a4c2),('release',76,0x860ee5fc)]


def prepare(process,pid):
    from prepare_native_hanzo import prepare as prepare_original
    base=ROOT/f'native-host/build/native-hanzoSkills-request-{pid}.json'
    reader=WeaponStates(process);sample=reader.sample_weapon(False,True)
    data=json.loads(base.read_text(encoding='utf-8')) if base.exists() else {}
    if data.get('pid')!=pid or data.get('modelId')!=sample['modelId']:
        prepare_original(process,pid);data=json.loads(base.read_text(encoding='utf-8'))
    if data.get('hero')!=HERO or data.get('resource')!=GRAPH or data.get('modelId')!=sample['modelId']:
        raise ValueError('Hanzo voice scope does not match current hero/model/graph')
    if reader.unpack('<Q',data['heroInfo']+0x98)[0]!=HERO or reader.pointer(data['script']+0x160)!=data['graph']:
        raise ValueError('Hanzo original owner/graph changed')
    nodes=reader.stu_list(data['graph']+0x50);states={}
    if len(nodes)!=117:raise ValueError('Hanzo original graph node count changed')
    for name,index,kind in PROFILE:
        if reader.bindings.metadata(nodes[index])[1]!=kind:raise ValueError('Hanzo voice original node type changed: '+name)
        states[name]=dict(index=index,address=nodes[index],vtable=reader.pointer(nodes[index]))
    data['states']=states
    if reader.unpack('<I',data['reference']+0x94)[0]!=sample['modelId']:
        raise ValueError('Hanzo model changed during voice binding')
    destination=ROOT/f'native-host/build/native-{PURPOSE}-request-{pid}.json'
    temporary=destination.with_suffix('.tmp');temporary.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8');temporary.replace(destination)
    return dict(hero=HERO,modelId=sample['modelId'],readOnly=True,paths=[str(destination)],
                signal='b9 EntryGameMessage79 new nativeTick; Volley76 is witness only')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pid',type=int,required=True);args=parser.parse_args()
    process=ResearchProcess(args.pid)
    try:print(json.dumps(prepare(process,args.pid)))
    finally:process.close()
