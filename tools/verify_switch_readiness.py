"""Actual first attacks/skills after hero and dimension changes, no binding wait.

Requires the opted-in isolated Twilight Switch lab. Attacks are native input;
the fixture only places a stationary target and reversible empty-air floor.
"""
import argparse,json,math,subprocess,time,urllib.request
from pathlib import Path
from calibrate_hero_roster import api,drive,report,observe,ROSTER
from calibrate_hero_actions import select
from observe_overwatch import ROOT,ResearchProcess
from verify_genji_elimination_reset import post
from verify_native_light_angles import point
from verify_world_hero_switch import ready,native
from launch_passthrough_session import first_person_ready
from native_map_light import owned_live_light,locate_live

def fast_select(pid,name,shot=False,skill=False):
    suffix,x=next((s,x) for n,s,x in ROSTER if n==name)
    commands=['focus','mup','key 0x48','sleep 350',f'click {x} 1224','sleep 500','click 1280 1358',f'sleep {1700 if skill else 900}']
    if shot:commands+=['mdown 1280 720','sleep 120','mup','sleep 650']
    if skill:commands+=['focus','move 1280 720','hold 0x10 150','sleep 650']
    input_log=drive(*commands)
    if '-> fail' in input_log:raise ValueError('Native input refused: '+input_log)
    actor=observe(pid)
    if actor['hero']!=0x02e0000000000000+suffix or not first_person_ready(pid):raise ValueError('Actual selection/first-person mismatch')
    return actor

def check_light(pid,actor):
    end=time.monotonic()+4
    while True:
        light=report(ROOT/f'native-host/build/world-live-{pid}.json')
        if light.get('viewLightOwned') and light.get('viewLightModelId')==actor['modelId'] and light.get('viewLightVerifiedEpoch')==light.get('viewLightEpoch'):break
        if time.monotonic()>end:raise ValueError('Current light scope did not acknowledge')
        time.sleep(.03)
    p=ResearchProcess(pid)
    try:
        actual=owned_live_light(p,pid)
        try:cpu=locate_live(p,allow_hollywood=True)
        except ValueError:cpu=None # Transient native packet; explicit epoch confirmation above.
    finally:p.close()
    key=(.5,-2**-.5,-.5)
    expected=[sum(key[j]*light['basis'][j*3+i] for j in range(3)) for i in range(3)]
    error=max(abs(a-b) for a,b in zip(expected,actual['direction']))
    if error>.025 or cpu and cpu['node']!=actual['node']:raise ValueError('Actual Sun/camera binding differs')
    return dict(report=light,actual=actual,cpu=cpu,directionError=error)

def main(pid,folder,cycles=2,dimensions=False,skills=False):
    folder.mkdir(parents=True,exist_ok=True);out=dict(pid=pid,passed=False,rows=[],skills=[],firstShotDelayMs=900,firstSkillDelayMs=1700)
    p=ResearchProcess(pid);p.close()
    try:
        if not api('health')['worldName'].startswith('Overwatch Twilight Switch '):raise ValueError('Use the isolated regression world')
        select(pid,'McCree');ready(pid);point(180,0)
        routes=['overworld','nether','end','twilight'] if dimensions else [None]
        if dimensions and api('world')['dimension']=='minecraft:overworld':routes=['nether','end','twilight','overworld']
        for short in routes:
            if short:
                with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:32133/world/switch-test/'+short,method='POST'),timeout=3):pass
                # Immediately replace the hero while real MC transfer runs.
                fast_select(pid,'Genji');ready(pid,dimension={'overworld':'minecraft:overworld','nether':'minecraft:the_nether','end':'minecraft:the_end','twilight':'twilightforest:twilight_forest'}[short])
                fast_select(pid,'McCree')
            for name in ('Genji','McCree')*cycles:
                point(180,0);post('start');time.sleep(.15);before=api('combat')
                if before.get('testError') or before.get('targetHealth')!=20:raise ValueError('Target not in loaded empty corridor')
                prior=report(ROOT/f'native-host/build/native-emissions-{pid}.json')
                actor=fast_select(pid,name,shot=True);after=api('combat')
                row=dict(hero=name,dimension=api('world')['dimension'],actor=actor,before=before,after=after,beforeNative=prior,native=report(ROOT/f'native-host/build/native-emissions-{pid}.json'))
                out['rows'].append(row)
                post('replay');time.sleep(.1);row['replay']=api('combat')
                expected=9.5 if name=='Genji' else 13
                row['passed']=after.get('targetHealth')==expected and row['replay'].get('targetHealth')==expected and after['damageApplied']==row['replay']['damageApplied'] and row['native']['factoryCalls']-prior['factoryCalls']==(3 if name=='Genji' else 1)
                if not row['passed']:raise ValueError('First native shot was lost/missed/duplicated')
                row['lighting']=check_light(pid,actor);row['health']=native(pid)
                if row['health']['hp']!=row['health']['maximum'] or row['health']['hp']<=0:raise ValueError('Wrong native health after switch')
                path=folder/f'{len(out["rows"]):02d}-{short or "repeat"}-{name}.png'
                subprocess.run(['um','win','shot','--exe','GameClientApp.patched.exe',str(path),'--scale','.33'],cwd=ROOT,capture_output=True,check=True,timeout=15)
                row['image']=str(path.relative_to(ROOT));post('cleanup');time.sleep(.15)
                print(json.dumps(dict(hero=name,dimension=row['dimension'],firstShot=True,lightEpoch=row['lighting']['report']['viewLightEpoch'])),flush=True)
            if skills:
                for name in ('Genji','McCree'):
                    # Ground the player on a reversible air-only floor before
                    # selection. The first Shift follows confirmation directly.
                    post('flight-open');time.sleep(.25)
                    if api('combat').get('testError'):raise ValueError('Safe skill platform unavailable')
                    if api('health')['player']['flying']:drive('focus','key 0x75','sleep 300')
                    if not api('health')['player']['onGround']:raise ValueError('Player not grounded on skill platform')
                    before=api('combat');position=api('health')['player']
                    actor=fast_select(pid,name,skill=True);after=api('combat');player=api('health')['player']
                    label='dash' if name=='Genji' else 'roll';counter='begins' if name=='Genji' else 'starts'
                    distance=math.dist([position[k] for k in ('x','feetY','z')],[player[k] for k in ('x','feetY','z')])
                    row=dict(hero=name,dimension=api('world')['dimension'],before=before,after=after,distance=distance,modelId=actor['modelId'])
                    out['skills'].append(row)
                    if after[label][counter]<=before[label][counter] or distance<3:raise ValueError('First Shift did not drive actual MC movement')
                    print(json.dumps(dict(hero=name,skill=label,distance=distance)),flush=True)
                    post('cleanup');time.sleep(.15)
        out['passed']=True
    except Exception as e:out['error']=str(e)
    finally:
        try:post('cleanup');time.sleep(.3);c=api('combat');out['cleaned']=c['wallBlocks']==0 and 'targetHealth' not in c
        except Exception as e:out['cleanupError']=str(e);out['passed']=False
        (folder/'result.json').write_text(json.dumps(out,indent=2)+'\n')
        print(json.dumps({k:out.get(k) for k in ('passed','error','cleaned')}),flush=True)
    return out['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pid',type=int,required=True);p.add_argument('--output',required=True);p.add_argument('--cycles',type=int,default=2);p.add_argument('--dimensions',action='store_true');p.add_argument('--skills',action='store_true');a=p.parse_args()
    folder=(ROOT/a.output).resolve()
    if ROOT/'research' not in folder.parents:raise SystemExit('Use private research output')
    raise SystemExit(0 if main(a.pid,folder,a.cycles,a.dimensions,a.skills) else 1)
