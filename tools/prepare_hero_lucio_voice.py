"""语音挂接：只读绑定已实测073a:9起手动画，比0号音障Aura早660ms。"""
import json
from observe_overwatch import ROOT,ResearchProcess
from observe_native_weapon_states import WeaponStates

HERO=0x02e0000000000079


def prepare(process,pid):
    from prepare_hero_lucio import prepare as original
    base=ROOT/f'native-host/build/native-lucioBarrier-request-{pid}.json'
    reader=WeaponStates(process);sample=reader.sample_weapon(False,True)
    data=json.loads(base.read_text(encoding='utf-8')) if base.exists() else {}
    if data.get('modelId')!=sample['modelId'] or data.get('pid')!=pid:
        original(process,pid);data=json.loads(base.read_text(encoding='utf-8'))
    if data['hero']!=HERO or data['resource']!=0x058000000000073a or reader.unpack('<Q',data['heroInfo']+0x98)[0]!=HERO:
        raise ValueError('Lucio voice owner/graph changed')
    if reader.pointer(data['script']+0x160)!=data['graph']:raise ValueError('Lucio voice graph changed')
    nodes=reader.stu_list(data['graph']+0x50)
    if len(nodes)!=41:raise ValueError('Lucio voice node count changed')
    states={}
    for name,index,kind in [('castBegin',9,0x7fb4bf64),('barrier',0,0xd78490d1)]:
        if reader.bindings.metadata(nodes[index])[1]!=kind:raise ValueError('Lucio original node type changed')
        states[name]=dict(index=index,address=nodes[index],vtable=reader.pointer(nodes[index]))
    data['states']=states
    if reader.unpack('<I',data['reference']+0x94)[0]!=sample['modelId']:raise ValueError('Lucio voice model changed')
    target=ROOT/f'native-host/build/native-heroVoiceLucioBegin-request-{pid}.json';temporary=target.with_suffix('.tmp')
    temporary.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8');temporary.replace(target)
    return dict(readOnly=True,hero=HERO,modelId=sample['modelId'],path=str(target))


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pid',type=int,required=True);args=parser.parse_args()
    process=ResearchProcess(args.pid)
    try:print(json.dumps(prepare(process,args.pid)))
    finally:process.close()
