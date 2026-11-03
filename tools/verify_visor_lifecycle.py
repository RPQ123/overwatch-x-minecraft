"""Real native Visor, four dimensions and replacement heroes; no synthetic shots.

Uses only the opted-in disposable Switch lab and reversible air/target fixtures.
Explicit four-byte ultimate grants shorten this test; natural charge is checked
separately by verify_native_visor.py. Native Q still owns activation and drain.
"""
import argparse,json,time,urllib.request,subprocess
from observe_overwatch import ROOT,ResearchProcess
from calibrate_hero_roster import api,drive
from calibrate_hero_actions import select
from verify_genji_elimination_reset import post
from verify_native_light_angles import point
from verify_world_hero_switch import ready,native
from verify_switch_readiness import fast_select,check_light
from native_charge import grant_for_test

DIMENSIONS={'overworld':'minecraft:overworld','nether':'minecraft:the_nether',
    'end':'minecraft:the_end','twilight':'twilightforest:twilight_forest'}

def require(ok,message):
    if not ok:raise ValueError(message)

def wait_aiming(seconds=4):
    deadline=time.monotonic()+seconds
    while True:
        value=api('combat')
        if value.get('nativeCharge',{}).get('visorActive'):return value
        require(time.monotonic()<deadline,'Native Visor acquisition did not enter')
        time.sleep(.03)

def cleanup():
    # HTTP202 only queues a server task; it is not a cleanup acknowledgement.
    post('cleanup');deadline=time.monotonic()+2
    while True:
        value=api('combat')
        if value['wallBlocks']==0 and 'targetHealth' not in value:return True
        require(time.monotonic()<deadline,'Test objects remained after server cleanup')
        time.sleep(.03)

def grant_and_activate(pid):
    p=ResearchProcess(pid)
    try:grant=grant_for_test(p,pid)
    finally:p.close()
    drive('focus','hold 0x51 120');wait_aiming();return grant

def target(angle=12):
    post('start');time.sleep(.12);before=api('combat')
    require(before.get('targetHealth')==20 and not before.get('testError'),'Target needs empty loaded corridor')
    drive('focus',f'rel {round(angle/.1)} 0','sleep 100')

def fire():
    before=api('combat');drive('focus','mdown 1280 720','sleep 120','mup','sleep 200');after=api('combat')
    require(after['admitted']>before['admitted'] and after['rejected']==before['rejected'],'Original rifle did not produce admitted bullets')
    return dict(before=before,after=after)

def check_hit(row):
    before,after=row['before'],row['after']
    require(before['nativeCharge']['visorActive'] and after['nativeCharge']['visorActive'],'Hit must be inside actual native acquisition window')
    count=after['admitted']-before['admitted']
    require(after['visorLocks']-before['visorLocks']==count,'Each actual rifle bullet must lock exactly once')
    require(abs(after.get('targetHealth',20)-(20-count*1.7))<.0001,'Native17HP bullet damage did not match actual MC target')

def main(pid,folder):
    folder.mkdir(parents=True,exist_ok=True);path=folder/'visor-lifecycle.json'
    out=dict(pid=pid,passed=False,rows=[])
    routes=list(DIMENSIONS)
    if api('world')['dimension']==DIMENSIONS[routes[0]]:routes=routes[1:]+routes[:1]
    try:
        require(api('health')['worldName'].startswith('Overwatch Twilight Switch '),'Use the isolated creative Switch lab')
        for short in routes:
            row={'dimension':DIMENSIONS[short]};out['rows'].append(row)
            with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:32133/world/switch-test/'+short,method='POST'),timeout=3):pass
            select(pid,'Genji');ready(pid,dimension=DIMENSIONS[short]);select(pid,'Soldier76');ready(pid)
            point(180,0);post('flight-open');time.sleep(.25);require(not api('combat').get('testError'),'Air lab unavailable');post('cleanup')
            target();row['inactive']=fire();require(row['inactive']['after'].get('targetHealth')==20,'Inactive native rifle unexpectedly tracked')
            row['grant']=grant_and_activate(pid);row['active']=fire();check_hit(row['active'])
            post('replay');time.sleep(.1);row['replay']=api('combat')
            require(row['replay']['visorLocks']==row['active']['after']['visorLocks'] and row['replay'].get('targetHealth')==row['active']['after'].get('targetHealth'),'Journal replay repeated the lock/damage')
            target();post('wall');time.sleep(.15);row['covered']=fire()
            a,b=row['covered']['before'],row['covered']['after']
            require(a['nativeCharge']['visorActive'] and b['nativeCharge']['visorActive'],'Covered shot missed the native aiming window')
            require(b.get('targetHealth')==20 and b['visorLocks']==a['visorLocks'],'Native Visor locked through real blocks')
            row['beforeReplacement']=api('combat');require(row['beforeReplacement']['nativeCharge']['visorActive'],'Replacement must begin while Q is still active')
            old=row['beforeReplacement']['locomotion']['modelId']
            actor=fast_select(pid,'McCree');ready(pid);post('cleanup');point(180,0);target();row['mccree']=fire()
            require(actor['modelId']!=old and row['mccree']['after'].get('targetHealth')==20 and not row['mccree']['after']['nativeCharge'].get('visorActive'),'Visor leaked into replacement McCree')
            actor=fast_select(pid,'Soldier76');ready(pid);post('cleanup');point(180,0);target();row['newSoldier']=fire()
            require(actor['modelId']!=old and row['newSoldier']['after'].get('targetHealth')==20 and not row['newSoldier']['after']['nativeCharge'].get('visorActive'),'Historical Q replayed on replacement Soldier')
            row['native']=native(pid);row['light']=check_light(pid,actor)
            require(row['native']['hp']==row['native']['maximum']>0 and api('health')['player']['health']==20,'Current native/MC health invalid')
            row['cleaned']=cleanup()
            row['passed']=True;path.write_text(json.dumps(out,indent=2)+'\n')
            print(json.dumps({'dimension':row['dimension'],'passed':True,'nativeVisorLocks':row['active']['after']['visorLocks']-row['active']['before']['visorLocks']}),flush=True)
        out['passed']=True
    except Exception as failure:out['error']=str(failure);raise
    finally:
        drive('focus','mup');out['finalCleaned']=cleanup();path.write_text(json.dumps(out,indent=2)+'\n')

def earned(pid,folder):
    """Reach native Q from normal passive/real damage credit, no lab grant."""
    folder.mkdir(parents=True,exist_ok=True);path=folder/'visor-earned-charge.json'
    out=dict(pid=pid,passed=False,explicitTestGrantsUsed=False,targets=[])
    try:
        require(api('health')['worldName'].startswith('Overwatch Twilight Switch '),'Use the isolated creative Switch lab')
        select(pid,'McCree');ready(pid);select(pid,'Soldier76');ready(pid);point(180,0)
        post('flight-open');time.sleep(.25);require(not api('combat').get('testError'),'Air lab unavailable');cleanup()
        out['initial']=api('combat');require(out['initial']['nativeCharge']['charge']<out['initial']['nativeCharge']['cost'],'Fresh model was already fully charged')
        for _ in range(10):
            if api('combat')['nativeCharge']['charge']>=api('combat')['nativeCharge']['cost']:break
            post('melee');time.sleep(.15);before=api('combat');require(before.get('targetHealth')==20 and not before.get('testError'),'Normal20HP target unavailable')
            drive('focus','key 0x52','sleep 1500','mdown 1280 720','sleep 1600','mup','sleep 200')
            after=api('combat');row={'before':before,'after':after};out['targets'].append(row);path.write_text(json.dumps(out,indent=2)+'\n')
            require(after['admitted']>before['admitted'] and after['damageApplied']>before['damageApplied'],'Original rifle did not damage the actual target')
            require(after['nativeCharge']['charge']>before['nativeCharge']['charge'],'Actual damage did not earn native charge')
            print(json.dumps({'normalTarget':len(out['targets']),'charge':after['nativeCharge']['charge'],'cost':after['nativeCharge']['cost']}),flush=True)
        out['charged']=api('combat');require(out['charged']['nativeCharge']['charge']==out['charged']['nativeCharge']['cost'],'Normal gameplay credit did not reach native Q')
        cleanup();point(180,0);target();drive('focus','hold 0x51 120');out['begin']=wait_aiming();out['hit']=fire();check_hit(out['hit'])
        require(out['hit']['after']['nativeCharge']['charge']==0,'Naturally earned Q did not drain')
        image=folder/'visor-earned-active.png';subprocess.run(['um','win','shot','--exe','GameClientApp.patched.exe',str(image),'--scale','.33'],cwd=ROOT,capture_output=True,check=True,timeout=15);out['activeImage']=str(image)
        deadline=time.monotonic()+10
        while api('combat')['nativeCharge']['active']:
            require(time.monotonic()<deadline,'Native Q did not end');time.sleep(.05)
        time.sleep(.4);out['ended']=api('combat');require(out['ended']['nativeCharge']['charge']>0 and not out['ended']['nativeCharge']['visorActive'],'Normal charge did not resume after End')
        out['afterEndMiss']=fire();a,b=out['afterEndMiss']['before'],out['afterEndMiss']['after']
        require(b.get('targetHealth')==a.get('targetHealth') and b['visorLocks']==a['visorLocks'] and not b['nativeCharge']['visorActive'],'Expired Visor still tracked an off-axis target')
        out['passed']=True
    except Exception as failure:out['error']=str(failure);raise
    finally:
        drive('focus','mup');out['finalCleaned']=cleanup();path.write_text(json.dumps(out,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pid',type=int,required=True);p.add_argument('--output',required=True);p.add_argument('--earned-only',action='store_true');args=p.parse_args();folder=(ROOT/args.output).resolve()
    if ROOT/'research' not in folder.parents:p.error('Private research output required')
    (earned if args.earned_only else main)(args.pid,folder)
