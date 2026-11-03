"""Real repeated native hero recreation across the low12-bit entity ID wrap."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,struct,subprocess,time
from observe_overwatch import ROOT,ResearchProcess,PoseReader
from calibrate_hero_actions import select
from calibrate_hero_roster import ROSTER,api,report
from fill_native_health import fill
from inspect_native_scripts import ScriptReader

def main(pid,rounds,until_collision=False):
    path=ROOT/'research/hero-bucket-stress-result.json'
    try:prior=json.loads(path.read_text())
    except (OSError,ValueError):prior={}
    results=prior.get('results',[]) if prior.get('pid')==pid else [];collision=bool(prior.get('collisionObserved')) if prior.get('pid')==pid else False
    first_cycle=max((v['cycle'] for v in results),default=-1)+1
    for cycle in range(rounds):
        for name,_,_ in ROSTER:
            result={'cycle':first_cycle+cycle,'hero':name}
            try:
                selected=select(pid,name);deadline=time.monotonic()+4
                while True:
                    body=report(ROOT/f'native-host/build/body-sync-{pid}.json')
                    if body.get('modelId')==selected['modelId'] and body.get('worldStable') and body.get('enabled') and not body.get('failures'):break
                    if time.monotonic()>deadline:raise ValueError('Body failed to follow current model')
                    time.sleep(.1)
                p=ResearchProcess(pid)
                try:
                    result['healthBeforeSupervisor']=fill(p,pid,check_only=True)
                    if result['healthBeforeSupervisor']['nativeHealthAfter']<=0:raise ValueError('New native model has zero health')
                    deadline=time.monotonic()+4;result['health']=result['healthBeforeSupervisor']
                    while result['health']['nativeHealthAfter']!=result['health']['nativeMaximum']:
                        if time.monotonic()>deadline:raise ValueError('Supervisor did not finish current health initialization')
                        time.sleep(.1);result['health']=fill(p,pid,check_only=True)
                    r=ScriptReader(p);a=r.pointer(p.base+0x17b7f90);local=r.unpack('<I',a+0x220)[0];table=r.pointer(a+16)
                    bucket,count,_=r.unpack('<Qii',table+(local&4095)*16)
                    if not 1<=count<=4096:raise ValueError('Current native bucket count')
                    entries=list(struct.iter_unpack('<IIQ',p.read(bucket,count*16)));index=next(i for i,v in enumerate(entries) if v[0]==local)
                    result.update(localId=local,modelId=selected['modelId'],bucketCount=count,recordIndex=index)
                    model=r.entity(p.read(table,65536),selected['modelId']);bag=r.pointer(r.component(model,0x23)+0xc0+0x2e0);deadline=time.monotonic()+2
                    while True:
                        variables={v['rid']:v.get('value') for v in r.varbag(bag)}
                        result['hudHealth']=variables.get('0d800000000006c4',0);result['hudMaximum']=variables.get('0d800000000006c9',0)
                        if abs(result['hudHealth']-result['health']['nativeHealthAfter'])<.01 and abs(result['hudMaximum']-result['health']['nativeMaximum'])<.01:break
                        if time.monotonic()>deadline:raise ValueError('Original HUD health mirror is stale/zero despite valid native pool')
                        time.sleep(.05)
                finally:p.close()
                player=api('health')['player'];result['mcHealth']=player['health'];result['mcAlive']=player['alive']
                result['passed']=result['health']['nativeHealthAfter']==result['health']['nativeMaximum']>0 and player['alive'] and player['health']>0
                body=report(ROOT/f'native-host/build/body-sync-{pid}.json');result['bucketPromotions']=body.get('bucketPromotions',0)
                if (index>0 or result['bucketPromotions']>0) and not collision:
                    collision=True;subprocess.run(['um','win','shot','--exe','GameClientApp.patched.exe',str(ROOT/'research/hero-bucket-collision-live.png'),'--scale','0.33'],cwd=ROOT,check=True,stdout=subprocess.PIPE)
            except Exception as error:result['passed']=False;result['error']=str(error)
            results.append(result);(ROOT/'research/hero-bucket-stress-result.json').write_text(json.dumps(dict(pid=pid,results=results,collisionObserved=collision,passed=all(x['passed'] for x in results)),indent=2)+'\n')
            print(json.dumps({k:result[k] for k in ('cycle','hero','passed','localId','recordIndex','bucketCount','error') if k in result}),flush=True)
            if not result['passed']:return
            if until_collision and collision:return

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--pid',type=int,required=True);parser.add_argument('--rounds',type=int,default=2);parser.add_argument('--until-collision',action='store_true');args=parser.parse_args();main(args.pid,args.rounds,args.until_collision)
