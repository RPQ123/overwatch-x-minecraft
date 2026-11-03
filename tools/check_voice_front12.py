"""离线检查保留素材及前12人探针映射；只执行抽取的纯函数，绝不驱动游戏。"""
import ast
from collections import Counter
import json
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
HEROES = ['genji','mccree','pharah','reaper','soldier76','tracer','bastion','hanzo','junkrat','mei','torbjorn','widowmaker']

def check():
    path=ROOT/'research/sprint-20261024/verify_hero_voice.py'
    tree=ast.parse(path.read_text(encoding='utf-8'))
    probes=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
                and any(isinstance(t,ast.Name) and t.id=='SKILL_PROBES' for t in n.targets))
    functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'skill_probe','skill_signal_snapshot'}]
    sandbox={'time':SimpleNamespace(sleep=lambda _:None)}
    exec(compile(ast.Module(body=functions,type_ignores=[]),str(path),'exec'),sandbox)
    commands=[]
    suite=SimpleNamespace(driver=SimpleNamespace(send=commands.append))
    assert probes['Pharah']==('ability:concussive_blast','E','mei-lab')
    sandbox['skill_probe'](suite,'Pharah',probes['Pharah'][1]);assert commands==['hold 0x45 120'];commands.clear()
    assert probes['Tracer'][0:2]==('ult_cast','Q')
    sandbox['skill_probe'](suite,'Tracer',probes['Tracer'][1]);assert commands==['hold 0x51 120'];commands.clear()
    assert probes['Torbjorn']==('ability:turret_deploy','turret','ground-lab')
    sandbox['skill_probe'](suite,'Torbjorn',probes['Torbjorn'][1]);assert commands==['rel 0 250','hold 0x10 120']
    snapshot=sandbox['skill_signal_snapshot']({'concussive':{'detonations':1,'pushed':0},'torb':{'deploys':2,'packsThrown':0}},
        {'signals':{'concussive':{'lastOffered':1}},'admitted':{'ability:concussive_blast':1}})
    assert snapshot['runtime']['concussive']['detonations']==1 and snapshot['runtime']['torb']['deploys']==2
    assert snapshot['voice']['concussive']['lastOffered']==1
    rows=json.loads((ROOT/'research/voice-catalog-20261025/download.json').read_text(encoding='utf-8'))
    defaults=json.loads((ROOT/'research/voice-20261026b/download-default.json').read_text(encoding='utf-8'))
    assert rows==defaults and len(rows)==761
    from prune_voice_defaults import HANZO_ULT_HASH
    assert [r['hash'] for r in rows if r['hero']=='hanzo' and r['event']=='ult_cast']==[HANZO_ULT_HASH]
    assert sum(r['hero']=='pharah' and r['event']=='ability:concussive_blast' for r in rows)==3
    assert not any(r['event'] in {'pain','idle','jump','reload'} or r['event'].startswith('status:') for r in rows)
    # 从实际准备器确认六位英雄旧Q/E仍在默认包；麦克雷另外的准备器保留其专用入口。
    import early_chinese_voice_assets as early
    import four_dps_voice_assets as four
    import mccree_voice_assets as mccree
    for event in ['genji.dragonblade','pharah.barrage','soldier76.visor','soldier76.bioticfield','tracer.pulse','reaper.blossom','reaper.shadow']:
        assert event in early.CLIPS or event in four.CLIPS,event
    assert 'deadeye.ogg' in mccree.FILES and 'mccree.flashbang' in early.CLIPS
    assert 'hero.tracer.select' not in early.CLIPS and 'hero.bastion.select' not in early.CLIPS
    retained={h:dict(sorted(Counter(r['event'] for r in rows if r['hero']==h and (r['event']=='ult_cast' or r['event'].startswith('ability:'))).items())) for h in HEROES}
    return dict(passed=True,defaultClips=len(rows),pharahAbility=3,pharahMapping='unchanged E -> concussive_blast',
                tracerProbe='retained legacy Q',torbjornProbe='ground look + Shift',failureSignalSnapshot='PASS',
                retainedEvents=retained,live=False)

if __name__=='__main__':
    result=check();out=ROOT/'research/voice-20261027';out.mkdir(parents=True,exist_ok=True)
    (out/'front12-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='retainedEvents'},ensure_ascii=False))
