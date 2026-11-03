"""Actual Tracer Blink after real dimension transfer and hero recreation in clones."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,math,subprocess,time,urllib.request
from calibrate_hero_actions import select
from calibrate_hero_roster import api,drive,report
from observe_overwatch import ROOT,ResearchProcess
from observe_native_weapon_states import WeaponStates
from verify_genji_elimination_reset import post
from verify_world_hero_switch import ready,require

DIMENSIONS=[('overworld','minecraft:overworld'),('nether','minecraft:the_nether'),
            ('end','minecraft:the_end'),('twilight','twilightforest:twilight_forest')]

def charges(pid):
    p=ResearchProcess(pid)
    try:
        r=WeaponStates(p);r.sample_weapon(False,True)
        script=next(k[0] for k in r.graph_cache if k[2]==0x0580000000000024)
        return next(v['value'] for v in r.varbag(r.pointer(script+0x98)) if v['rid']=='0d8000000000000b')
    finally:p.close()

def settled(pid,dimension):
    row=ready(pid,dimension=dimension);deadline=time.monotonic()+12
    while True:
        c=api('combat');h=api('health')
        if c.get('blink',{}).get('ready') and h['player']['onGround'] and not h['player']['flying']:return row
        if time.monotonic()>deadline:raise ValueError('Blink/ground did not settle: '+str(c.get('blink')))
        time.sleep(.1)

def position(h):
    p=h['player'];return (p['x'],p['feetY'],p['z'])

def blink(pid,dimension,label):
    row=settled(pid,dimension);row['label']=label
    baseline=api('combat')['blink'];before=api('health');time.sleep(.6)
    idle=api('combat')['blink'];idleHealth=api('health')
    require(idle['starts']==baseline['starts'] and math.dist(position(before),position(idleHealth))<.05,'Phantom displacement after lifecycle change')
    require(idle['nativeCaptures']==0,'Old native Blink capture crossed world/model identity')
    row['idle']=idle;row['before']=idleHealth
    deadline=time.monotonic()+5
    while charges(pid)<1:
        if time.monotonic()>deadline:raise ValueError('Original Blink did not recharge')
        time.sleep(.15)
    row['chargeBefore']=charges(pid)
    drive('focus','hold 0x10 100','sleep 650')
    row['after']=api('health');row['blink']=api('combat')['blink'];row['chargeAfter']=charges(pid)
    b=row['blink']
    require(b['starts']==baseline['starts']+1 and b['nativeCaptures']==1,'Missing/duplicate native Blink')
    require(7.3<b['requestedDistance']<7.7 and abs(b['actualDistance']-b['requestedDistance'])<.03,'Blink distance/collision mismatch in open corridor')
    require(row['chargeAfter']==row['chargeBefore']-1,'Original native Blink charge did not decrease once')
    a=position(row['before']);z=position(row['after'])
    row['actualMove']=math.hypot(z[0]-a[0],z[2]-a[2]);row['verticalMove']=z[1]-a[1]
    (ROOT/f'research/blink-world-switch-{pid}-last-action.json').write_text(json.dumps(row,indent=2)+'\n')
    require(abs(row['actualMove']-b['actualDistance'])<.03,'MC player did not follow native Blink')
    require(abs(row['verticalMove'])<.05,'Blink lab left its flat platform')
    return row

def fire(pid):
    # Target setup removes the platform; preserve creative fixture flight first.
    if not api('health')['player']['flying']:drive('focus','hold 0x75 150','sleep 250')
    drive('focus','move 1280 720','sleep 250');c=api('combat')
    drive('focus',f'rel 0 {round(-c["pitch"]/.1)}','sleep 350')
    post('start');time.sleep(.3);require(api('combat').get('targetHealth')==20,'No temporary target')
    drive('focus','mdown 1280 720','sleep 180','mup','sleep 500')
    first=api('combat');post('replay');time.sleep(.2);again=api('combat')
    require(first.get('targetHealth',20)<20 and first.get('targetHealth')==again.get('targetHealth') and first['damageApplied']==again['damageApplied'] and first['rejected']==0,'Post-transition pistol damage/replay failed')
    return {'first':first,'replay':again}

def main(pid):
    path=ROOT/f'research/blink-world-switch-{pid}-{time.time_ns()}.json';result={'pid':pid,'passed':False,'rows':[]}
    try:
        require(api('health')['worldName'].startswith('Overwatch Twilight Switch '),'Use a backed-up isolated Switch clone')
        select(pid,'Tracer');ready(pid)
        for short,dimension in DIMENSIONS:
            with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:32133/world/switch-test/'+short,method='POST'),timeout=3):pass
            ready(pid,dimension=dimension)
            post('flight-open');time.sleep(.5);require(not api('combat').get('testError'),'Air lab unavailable')
            c=api('combat');turn=(180-c['yaw']+180)%360-180
            drive('focus',f'rel {round(turn/.1)} {round(-c["pitch"]/.1)}','hold 0x75 150','sleep 500')
            row=blink(pid,dimension,'same-hero-dimension-change')
            select(pid,'McCree');ready(pid);select(pid,'Tracer');ready(pid)
            # Return toward the platform center instead of stepping off its edge.
            c=api('combat');turn=(0-c['yaw']+180)%360-180
            drive('focus',f'rel {round(turn/.1)} {round(-c["pitch"]/.1)}','sleep 350')
            row['recreated']=blink(pid,dimension,'new-native-model')
            row['pistol']=fire(pid)
            subprocess.run(['um','win','shot','--exe','GameClientApp.patched.exe',str(path.with_suffix(''))+'-'+short+'.png','--scale','.33'],cwd=ROOT,capture_output=True,check=True,timeout=20)
            post('cleanup');time.sleep(.3);result['rows'].append(row)
            path.write_text(json.dumps(result,indent=2)+'\n')
            print(json.dumps({'dimension':dimension,'blinkBeforeAndAfterRecreation':True,'pistolReplay':True}),flush=True)
        result['passed']=True
    except Exception as e:result['error']=str(e)
    finally:
        try:
            post('cleanup');time.sleep(.3);c=api('combat');result['cleaned']=c['wallBlocks']==0 and 'targetHealth' not in c
            if not result['cleaned']:result['passed']=False
        except Exception as e:result['cleanupError']=str(e);result['passed']=False
        path.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({'path':str(path),'passed':result['passed'],'rows':len(result['rows']),'error':result.get('error'),'cleaned':result.get('cleaned')}),flush=True)
    return result['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pid',type=int,required=True)
    raise SystemExit(0 if main(p.parse_args().pid) else 1)
