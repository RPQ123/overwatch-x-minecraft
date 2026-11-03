"""Passive charge survives actual same-pawn MC transfers; no test charge grants."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,time,urllib.request,subprocess
from pathlib import Path
from calibrate_hero_actions import select
from calibrate_hero_roster import api,report,drive
from observe_overwatch import ROOT,ResearchProcess
from native_charge import inspect
from verify_genji_elimination_reset import post

DIMENSIONS={'overworld':'minecraft:overworld','nether':'minecraft:the_nether','end':'minecraft:the_end','twilight':'twilightforest:twilight_forest'}

def main(pid,folder):
    folder.mkdir(parents=True,exist_ok=False);result=dict(passed=False,meterGrantsUsed=False,rows=[])
    def save():(folder/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    def meter():
        p=ResearchProcess(pid)
        try:return inspect(p)
        finally:p.close()
    try:
        assert api('health')['worldName'].startswith('Overwatch Twilight Switch ')
        for hero in ('Pharah','Mercy','DVa'):
            actor=select(pid,hero)
            for short,dimension in DIMENSIONS.items():
                prior=meter()
                with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:32133/world/switch-test/'+short,method='POST'),timeout=3):pass
                deadline=time.monotonic()+15
                while True:
                    h=api('health');c=api('combat');b=report(ROOT/f'native-host/build/body-sync-{pid}.json');q=c.get('nativeCharge',{})
                    if api('world')['dimension']==dimension and b.get('worldStable') and q.get('ready') and q.get('modelId')==actor['modelId']==b.get('modelId') and (q.get('worldId',0)&0xffffffffffffffff)==b.get('worldId'):break
                    assert time.monotonic()<deadline,'Passive meter did not rebind current world'
                    time.sleep(.05)
                start=meter();assert start['chargeValue']>=prior['chargeValue'] and start['costValue']==prior['costValue'],'Same pawn lost charge/cost across world'
                then=time.monotonic();time.sleep(4);end=meter();rate=(end['chargeValue']-start['chargeValue'])/(time.monotonic()-then)
                assert 3.5<rate<6.5 and end['modelId']==actor['modelId'] and h['player']['health']==20 and h['player']['alive']
                row=dict(hero=hero,dimension=dimension,prior=prior,before=start,after=end,rate=rate,scope=q,passed=True);result['rows'].append(row);save();print(json.dumps(dict(hero=hero,dimension=dimension,rate=rate,passed=True)),flush=True)
        result['passed']=True
    except Exception as e:result['error']=repr(e)
    finally:
        try:
            post('cleanup')
            with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:32133/world/switch-test/overworld',method='POST'),timeout=3):pass
            result['cleaned']=True
        except Exception as e:result['cleanupError']=repr(e)
        save();print(json.dumps({k:result.get(k) for k in ('passed','error','cleaned')}),flush=True)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--pid',type=int,required=True);a.add_argument('--output',type=Path,required=True);v=a.parse_args();main(v.pid,v.output)
