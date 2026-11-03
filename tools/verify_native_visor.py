"""Real original Tactical Visor -> actual MC target, occlusion/end/replay checks."""
import argparse,json,time
from calibrate_hero_roster import api,drive,report,ROOT
from calibrate_hero_actions import select
from verify_world_hero_switch import ready
from verify_genji_elimination_reset import post
from observe_overwatch import ResearchProcess
from native_charge import grant_for_test

def require(ok,message):
    if not ok:raise ValueError(message)

def main(pid):
    out=dict(pid=pid,passed=False);path=ROOT/f'research/native-visor-{pid}-{time.time_ns()}.json'
    def sample():return api('combat')
    def fire():drive('focus','mdown 1280 720','sleep 120','mup','sleep 350');return sample()
    def offset_target():
        post('start');time.sleep(.15);require(not sample().get('testError'),'No empty target corridor')
        drive('focus','rel 120 0','sleep 200')
    try:
        select(pid,'Soldier76');ready(pid);post('flight-open');time.sleep(.4);require(not sample().get('testError'),'No loaded air lab');post('cleanup')
        c=sample();drive('focus',f'rel 0 {round(-c["pitch"]/.1)}','sleep 300')
        deadline=time.monotonic()+12
        while not (sample().get('nativeCharge',{}).get('ready') and sample().get('nativeCharge',{}).get('skillsReady') and not sample().get('feedError')):
            require(time.monotonic()<deadline,'Charge binding did not settle');time.sleep(.1)
        out['passiveBefore']=sample();time.sleep(1.2);out['passiveAfter']=sample()
        require(out['passiveAfter']['nativeCharge']['charge']>out['passiveBefore']['nativeCharge']['charge'],'No passive charging')
        post('start');time.sleep(.2);out['primaryBefore']=sample();out['primaryAfter']=fire()
        require(out['primaryAfter'].get('targetHealth',20)<20,'Original rifle damage missing')
        require(out['primaryAfter']['nativeCharge']['charge']-out['primaryBefore']['nativeCharge']['charge']>=17,'No actual damage credit')
        offset_target();out['inactiveBefore']=sample();out['inactiveAfter']=fire()
        require(out['inactiveAfter']['admitted']>out['inactiveBefore']['admitted'] and out['inactiveAfter'].get('targetHealth')==20,'Inactive rifle did not miss off-axis target')
        p=ResearchProcess(pid)
        try:out['labGrant']=grant_for_test(p,pid)
        finally:p.close()
        drive('focus','key 0x51');start=time.monotonic();rows=[];out['timeline']=rows
        def until(seconds):
            while time.monotonic()-start<seconds:
                rows.append(dict(t=time.monotonic()-start,combat=sample()));time.sleep(.05)
        deadline=time.monotonic()+4
        while not sample().get('nativeCharge',{}).get('visorActive'):
            require(time.monotonic()<deadline,'Original target-acquisition Begin not observed');until(time.monotonic()-start+.05)
        out['activeBefore']=sample();out['activeAfter']=fire()
        require(out['activeBefore']['nativeCharge']['visorActive'] and out['activeAfter']['nativeCharge']['visorActive'],'Shot was outside the actual native aim window')
        require(out['activeAfter'].get('targetHealth',20)<20 and out['activeAfter']['visorLocks']>out['activeBefore']['visorLocks'],'Native Visor did not aim actual bullets at off-axis MC target')
        post('replay');time.sleep(.2);out['replay']=sample();require(out['replay'].get('targetHealth')==out['activeAfter'].get('targetHealth') and out['replay']['visorLocks']==out['activeAfter']['visorLocks'],'Replayed Visor shot repeated')
        offset_target();post('wall');time.sleep(.2);out['coveredBefore']=sample();out['coveredAfter']=fire()
        require(out['coveredBefore']['nativeCharge']['visorActive'] and out['coveredAfter']['nativeCharge']['visorActive'],'Cover test did not run during actual native aiming')
        require(out['coveredAfter'].get('targetHealth')==20 and out['coveredAfter']['visorLocks']==out['coveredBefore']['visorLocks'],'Visor aimed through solid wall')
        until(9.5);offset_target();out['endedBefore']=sample();out['endedAfter']=fire()
        require(out['endedAfter'].get('targetHealth')==20 and out['endedAfter']['visorLocks']==out['endedBefore']['visorLocks'],'Visor persisted after native End')
        require(not out['endedAfter']['nativeCharge']['active'] and out['endedAfter']['nativeCharge']['charge']>0,'Charge did not restart after End')
        # The original stack begins before its delayed native charge drain.
        # Check the actual acquired-target phase, not the pre-drain windup.
        active=[r['combat']['nativeCharge'] for r in rows if r['combat'].get('nativeCharge',{}).get('visorActive')]
        require(active and max(c['charge'] for c in active)==0,'Native ultimate drain/active charge pause failed')
        out['timeline']=rows;out['passed']=True
    except Exception as error:out['error']=str(error)
    finally:
        drive('focus','mup');post('cleanup');time.sleep(.2);out['cleaned']=sample()['wallBlocks']==0 and 'targetHealth' not in sample()
        path.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(path=str(path),passed=out['passed'],error=out.get('error'),cleaned=out.get('cleaned'))))
    return out['passed'] and out['cleaned']

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--pid',type=int,required=True);args=a.parse_args();raise SystemExit(0 if main(args.pid) else 1)
