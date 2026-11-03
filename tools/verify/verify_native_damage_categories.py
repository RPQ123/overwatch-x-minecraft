"""Real native ray, melee and Tesla damage must retain vanilla Enderman semantics."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,subprocess,time
from calibrate_hero_actions import select
from calibrate_hero_roster import api,drive,report
from observe_overwatch import ROOT,ResearchProcess
from verify_genji_elimination_reset import post

def require(ok,message):
    if not ok:raise ValueError(message)

def selected(pid,name):
    actor=select(pid,name);deadline=time.monotonic()+18
    while True:
        s=report(ROOT/'research/session-status.json');c=api('combat')
        if s.get('ready') and not s.get('error') and s.get('hero',{}).get('modelId')==actor['modelId'] and not c.get('meleeError'):return actor
        if time.monotonic()>deadline:raise ValueError('Current native bindings unavailable: '+str(s.get('error')))
        time.sleep(.2)

def fixture(action):
    post(action);time.sleep(.3);c=api('combat')
    require(not c.get('testError') and c.get('targetType')=='minecraft:enderman' and c.get('targetHealth')==40,'Real healthy Enderman fixture unavailable')
    return c

def replay_unchanged(after):
    post('replay');time.sleep(.4);again=api('combat')
    require(again.get('targetHealth')==after.get('targetHealth') and again.get('targetDamageReceipts')==after.get('targetDamageReceipts') and again['damageApplied']==after['damageApplied'],'Replay duplicated actual target damage')
    return again

def main(pid):
    p=ResearchProcess(pid);p.close();result={'pid':pid,'passed':False};prefix=ROOT/f'research/native-damage-categories-{pid}-{time.time_ns()}'
    try:
        selected(pid,'McCree');post('flight-open');time.sleep(.4)
        require(not api('combat').get('testError') and api('health')['player']['flying'],'Safe creative air lab unavailable')
        post('cleanup');before=fixture('enderman');result['rayBefore']=before
        drive('focus','mdown 1280 720','sleep 120','mup','sleep 700');after=api('combat');result['rayAfter']=after
        rows=after.get('targetDamageReceipts',[])
        require(after['admitted']>before['admitted'] and after['entityHits']>before['entityHits'] and after['targetHealth']==40 and rows and all(r['projectile'] and not r['explosion'] and r['healthLost']==0 for r in rows),'Original McCree ray bypassed vanilla projectile immunity or never hit')
        result['rayReplay']=replay_unchanged(after);post('cleanup')
        before=fixture('enderman-melee');result['meleeBefore']=before
        drive('focus','key 0x56','sleep 800');after=api('combat');result['meleeAfter']=after
        rows=after.get('targetDamageReceipts',[])
        require(after['melee']['accepted']>before['melee']['accepted'] and after['targetHealth']==35 and len(rows)==1 and rows[0]['type']=='owmcguest.native_melee' and not rows[0]['projectile'] and not rows[0]['explosion'] and rows[0]['healthLost']==5,'Original quick melee inherited projectile immunity or changed its measured50HP')
        time.sleep(.5);result['meleeIdle']=api('combat');require(result['meleeIdle']['targetHealth']==35,'Melee repeated while idle')
        subprocess.run(['um','win','shot','--exe','GameClientApp.patched.exe',str(prefix)+'-melee.png','--scale','.33'],cwd=ROOT,capture_output=True,check=True,timeout=20)
        post('cleanup');selected(pid,'Winston');before=fixture('enderman');result['beamBefore']=before
        drive('focus','mdown 1280 720','sleep 600','mup','sleep 500');after=api('combat');result['beamAfter']=after
        rows=after.get('targetDamageReceipts',[])
        require(after['admitted']>before['admitted'] and 0<after['targetHealth']<40 and rows and all(r['type']=='owmcguest.native_beam' and not r['projectile'] and not r['explosion'] and r['healthLost']>0 for r in rows),'Original Tesla beam inherited projectile immunity or was not admitted')
        time.sleep(.5);after=api('combat');result['beamReleased']=after;time.sleep(.5);result['beamIdle']=api('combat')
        require(result['beamIdle']['targetHealth']==after['targetHealth'],'Native Tesla release did not stop damage')
        result['beamReplay']=replay_unchanged(result['beamIdle'])
        subprocess.run(['um','win','shot','--exe','GameClientApp.patched.exe',str(prefix)+'-beam.png','--scale','.33'],cwd=ROOT,capture_output=True,check=True,timeout=20)
        post('cleanup');selected(pid,'Pharah');before=fixture('enderman');result['rocketBefore']=before
        drive('focus','mdown 1280 720','sleep 120','mup','sleep 900');after=api('combat');result['rocketAfter']=after
        rows=after.get('targetDamageReceipts',[]);travel=sum((after['target'+axis]-before['target'+axis])**2 for axis in ('X','Y','Z'))
        require(after['rocketExplosions']==before['rocketExplosions']+1 and travel>25,'Actual rocket did not detonate or original Enderman teleport did not leave the air blast')
        require(after['targetHealth']==40 and len(rows)==1 and rows[0]['projectile'] and not rows[0]['explosion'] and rows[0]['healthLost']==0 and after['rocketDirectHealthLost']==before['rocketDirectHealthLost'] and after['rocketSplashHealthLost']==before['rocketSplashHealthLost'],'Splash used stale pre-teleport bounds or direct damage bypassed projectile immunity')
        result['rocketReplay']=replay_unchanged(after)
        native=report(ROOT/f'native-host/build/native-emissions-{pid}.json');result['native']=native
        require(native['enabled'] and native['failures']==0 and native['refused']==0 and api('combat')['rejected']==0,'Native transport admission failed')
        result['passed']=True
    except Exception as error:result['error']=str(error)
    finally:
        try:
            drive('focus','mup','key 0x56 up');post('cleanup');time.sleep(.2);c=api('combat')
            result['cleaned']=c['wallBlocks']==0 and 'targetHealth' not in c
            require(result['cleaned'],'Temporary Enderman/blocks remain')
        except Exception as error:result['cleanupError']=str(error);result['passed']=False
        # Caller lands after reviewing the air test; no artificial game entities survive.
        path=prefix.with_suffix('.json');path.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({'path':str(path),'passed':result['passed'],'error':result.get('error'),'cleaned':result.get('cleaned')},indent=2))
    return result['passed']

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pid',type=int,required=True)
    raise SystemExit(0 if main(parser.parse_args().pid) else 1)
