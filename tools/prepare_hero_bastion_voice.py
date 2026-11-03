"""语音挂接：只读绑定012f:123变形动画Begin；105只作晚1.5秒的Tank形态见证。"""
import json
from observe_overwatch import ROOT,ResearchProcess
from observe_native_weapon_states import WeaponStates

HERO=0x02e0000000000015
GRAPH=0x058000000000012f
PROFILE=[('transform',123,0x7fb4bf64),('tank',105,0xa7213568)]


def prepare(process,pid):
    from prepare_native_skills import prepare as original
    base=ROOT/f'native-host/build/native-skills-request-{pid}.json'
    reader=WeaponStates(process);sample=reader.sample_weapon(False,True)
    data=json.loads(base.read_text(encoding='utf-8')) if base.exists() else {}
    if data.get('modelId')!=sample['modelId'] or data.get('hero')!=HERO or data.get('pid')!=pid:
        original(process,pid);data=json.loads(base.read_text(encoding='utf-8'))
    if data.get('hero')!=HERO or data.get('resource')!=GRAPH or reader.unpack('<Q',data['heroInfo']+0x98)[0]!=HERO:
        raise ValueError('Bastion voice owner/graph changed')
    if reader.pointer(data['script']+0x160)!=data['graph']:raise ValueError('Bastion voice graph changed')
    nodes=reader.stu_list(data['graph']+0x50)
    if len(nodes)!=192:raise ValueError('Bastion voice original node count changed')
    states={}
    for name,index,kind in PROFILE:
        if reader.bindings.metadata(nodes[index])[1]!=kind:raise ValueError('Bastion voice original node type changed')
        states[name]=dict(index=index,address=nodes[index],vtable=reader.pointer(nodes[index]))
    data['states']=states
    if reader.unpack('<I',data['reference']+0x94)[0]!=sample['modelId']:raise ValueError('Bastion voice model changed')
    target=ROOT/f'native-host/build/native-heroVoiceBastionBegin-request-{pid}.json';temporary=target.with_suffix('.tmp')
    temporary.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8');temporary.replace(target)
    return dict(readOnly=True,hero=HERO,modelId=sample['modelId'],path=str(target))


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pid',type=int,required=True);args=parser.parse_args()
    process=ResearchProcess(args.pid)
    try:print(json.dumps(prepare(process,args.pid)))
    finally:process.close()
