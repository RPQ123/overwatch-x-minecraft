"""Original Bastion Tank mobility lifecycle in the isolated four-dimension lab.

Explicit meter grants shorten the test. No Tank cannon damage is manufactured.
The reversible lane supplies real floor/wall collision and is restored on exit.
"""
import argparse
import json
import math
import subprocess
import time
import urllib.request

from observe_overwatch import ROOT, ResearchProcess
from calibrate_hero_roster import api, drive, report
from calibrate_hero_actions import select
from native_charge import grant_for_test
from verify_genji_elimination_reset import post
from verify_native_light_angles import point
from verify_native_motor import action
from verify_switch_readiness import check_light
from verify_world_hero_switch import ready, native
from verify_visor_lifecycle import cleanup

DIMENSIONS={'overworld':'minecraft:overworld','nether':'minecraft:the_nether',
            'end':'minecraft:the_end','twilight':'twilightforest:twilight_forest'}


def require(value,message):
    if not value:raise ValueError(message)


def wait_form(form,seconds=5):
    deadline=time.monotonic()+seconds
    while True:
        motor=api('combat').get('motor',{})
        if motor.get('ready') and motor.get('form')==form:return motor
        require(time.monotonic()<deadline,'Native motor did not settle in '+form+': '+str(motor))
        time.sleep(.04)


def grant(pid):
    p=ResearchProcess(pid)
    try:return grant_for_test(p,pid)
    finally:p.close()


def stable(pid,dimension):
    current=ready(pid,dimension=dimension)
    deadline=time.monotonic()+5
    while True:
        charge=api('combat').get('nativeCharge',{})
        body=report(ROOT/f'native-host/build/body-sync-{pid}.json')
        if (charge.get('ready') and charge.get('modelId')==current['native']['modelId']==body.get('modelId')
                and (charge['worldId']&0xffffffffffffffff)==body.get('worldId')
                and body.get('sourcePid')==api('health')['sourcePid']):return current
        require(time.monotonic()<deadline,'Current MC world/body/hero scope did not agree')
        time.sleep(.04)


def main(pid,folder,dimensions):
    result=dict(pid=pid,passed=False,rows=[],cannonImplemented=False,explicitLabGrants=True)
    folder.mkdir(parents=True,exist_ok=True)
    try:
        p=ResearchProcess(pid);p.close()
        require(api('health')['worldName'].startswith('Overwatch Twilight Switch '),'Use the isolated Switch lab')
        for short in dimensions:
            dimension=DIMENSIONS[short];row=dict(dimension=dimension);result['rows'].append(row)
            cleanup()
            with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:32133/world/switch-test/'+short,method='POST'),timeout=3):pass
            select(pid,'Soldier76');stable(pid,dimension);actor=select(pid,'Bastion');stable(pid,dimension)
            row['modelId']=actor['modelId'];point(180,0)
            post('flight-open');time.sleep(.3);require(not api('combat').get('testError'),'Safe air lab unavailable')
            post('roll-lane');time.sleep(.2);require(not api('combat').get('testError') and api('combat')['wallBlocks']>0,'Collision lane unavailable')
            if api('health')['player']['flying']:drive('focus','key 0x75','sleep 400')
            require(api('health')['player']['onGround'],'Player not grounded on real lane')
            wait_form('recon');row['grant']=grant(pid)
            row['tankMove']=action(['hold 0x51 120','sleep 1900','hold 0x57 600','sleep 200'])
            require(1<row['tankMove']['displacement']<4 and row['tankMove']['peakOriginalSpeed']>2,'Original Tank motion did not reach MC')
            row['tankForm']=wait_form('tank')
            row['collision']=action(['hold 0x57 2100','sleep 200'])
            # Wall lies eight blocks along the lane; both movements together
            # must stop before it, even while native W velocity remains nonzero.
            a=row['tankMove']['before'];b=row['collision']['after']
            distance=math.hypot(a['x']-b['x'],a['z']-b['z']);row['wallDistance']=distance
            require(6<distance<8 and b['onGround'],'Tank bypassed the MC wall or fell through the floor')
            before=api('health')['player'];time.sleep(.3);after=api('health')['player']
            row['releaseDrift']=math.hypot(after['x']-before['x'],after['z']-before['z'])
            require(row['releaseDrift']<.03,'Released Tank input drifted')
            subprocess.run(['um','win','shot','--exe','GameClientApp.patched.exe',str(folder/(short+'-tank.png')),'--scale','.33'],cwd=ROOT,capture_output=True,check=True,timeout=15)
            row['afterEndForm']=wait_form('recon',15)
            row['afterEndMove']=action(['hold 0x53 400','sleep 200'])
            require(.5<row['afterEndMove']['displacement']<3,'Original Tank End left stale movement lock/displacement')
            row['sentry']=action(['key 0x10','sleep 1600','hold 0x57 400','sleep 200'])
            require(row['sentry']['displacement']<.03 and wait_form('sentry'),'Sentry movement lock regressed')
            select(pid,'McCree');fresh=select(pid,'Bastion');stable(pid,dimension);wait_form('recon')
            require(fresh['modelId']!=actor['modelId'],'Hero model was not replaced')
            row['secondGrant']=grant(pid);drive('focus','hold 0x51 120','sleep 1900');wait_form('tank')
            select(pid,'McCree');fresh=select(pid,'Bastion');stable(pid,dimension)
            row['freshForm']=wait_form('recon');row['light']=check_light(pid,fresh);row['health']=native(pid)
            require(row['health']['hp']==row['health']['maximum']>0,'Wrong native health after active-Q replacement')
            if not api('health')['player']['flying']:drive('focus','key 0x75','sleep 150')
            cleanup();post('start');time.sleep(.2);row['shotBefore']=api('combat')
            require(row['shotBefore'].get('targetHealth')==20,'Fresh Recon target unavailable')
            drive('focus','mdown 1280 720','sleep 120','mup','sleep 250');row['shotAfter']=api('combat')
            require(row['shotAfter'].get('targetHealth',20)<20 and row['shotAfter']['admitted']>row['shotBefore']['admitted'],'Fresh Recon attack did not recover')
            post('replay');time.sleep(.1);row['replay']=api('combat')
            require(row['replay'].get('targetHealth')==row['shotAfter'].get('targetHealth') and row['replay']['damageApplied']==row['shotAfter']['damageApplied'],'Replay applied damage twice')
            row['passed']=True;cleanup()
            (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n')
            print(json.dumps(dict(dimension=dimension,passed=True,tankDistance=row['tankMove']['displacement'],wallDistance=distance)),flush=True)
        result['passed']=True
    except Exception as e:result['error']=str(e)
    finally:
        try:
            drive('mup','key 0x57 up','key 0x53 up','key 0x51 up');cleanup()
            select(pid,'Soldier76')
            if api('world')['dimension']!='minecraft:overworld':
                with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:32133/world/switch-test/overworld',method='POST'),timeout=3):pass
                stable(pid,'minecraft:overworld')
            if api('health')['player']['flying']:drive('focus','key 0x75','sleep 150')
            deadline=time.monotonic()+10
            while not api('health')['player']['onGround']:
                require(time.monotonic()<deadline,'Player did not ground after cleanup');time.sleep(.1)
            result['final']=stable(pid,'minecraft:overworld');result['cleaned']=api('combat')['wallBlocks']==0 and 'targetHealth' not in api('combat')
            require(result['cleaned'],'Test objects remained')
        except Exception as e:result['cleanupError']=str(e);result['passed']=False
        (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:result.get(k) for k in ('passed','error','cleaned','cleanupError')}),flush=True)
    return result['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pid',type=int,required=True);p.add_argument('--output',required=True);p.add_argument('--dimensions',nargs='+',choices=list(DIMENSIONS),default=list(DIMENSIONS));a=p.parse_args()
    folder=(ROOT/a.output).resolve()
    if ROOT/'research' not in folder.parents:p.error('Use private research output')
    raise SystemExit(0 if main(a.pid,folder,a.dimensions) else 1)
