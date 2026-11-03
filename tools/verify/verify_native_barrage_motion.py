"""Unattended original Barrage input, MC root and post-action movement recovery."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,math,subprocess,time
from observe_overwatch import ROOT,ResearchProcess
from calibrate_hero_actions import select
from calibrate_hero_roster import api,drive
from verify_genji_elimination_reset import post
from verify_native_barrage import wait_ready
from native_charge import grant_for_test

def main(pid):
    result=dict(pid=pid,passed=False);recording=None
    try:
        select(pid,'Pharah');wait_ready();post('flight-open');time.sleep(.5)
        if api('combat').get('testError'):raise ValueError('No safe floor')
        if api('health')['player']['flying']:drive('focus','key 0x75','sleep 700')
        result['before']=api('health')['player']
        recording=subprocess.Popen(['um','win','record','--pid',str(pid),'--exe','GameClientApp.patched.exe','--out',str(ROOT/f'research/barrage-motion-{pid}'),'--seconds','9','--fps','30'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        p=ResearchProcess(pid)
        try:result['labGrant']=grant_for_test(p,pid)
        finally:p.close()
        command=subprocess.Popen(['um','win','drive','--proc','GameClientApp.patched.exe','focus','key 0x51','sleep 500','key 0x57 down','key 0x20 down','sleep 1300','key 0x20 up','key 0x57 up','sleep 2600'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        rows=[];start=time.monotonic()
        while command.poll() is None or time.monotonic()-start<4.5:
            if time.monotonic()-start>12:command.kill();raise ValueError('Movement input deadline')
            c=api('combat');rows.append(dict(t=time.monotonic()-start,player=api('health')['player'],charge=c.get('nativeCharge'),flight=c.get('flight')));time.sleep(.03)
        out,err=command.communicate(timeout=1)
        if command.returncode or b'-> fail' in out:raise ValueError((out+err).decode(errors='replace'))
        result['rows']=rows;locked=[v['player'] for v in rows if v.get('flight',{}).get('barrage') and v.get('charge',{}).get('active')]
        result['lockedSamples']=len(locked);result['lockedRange']=max((max(v[k] for v in locked)-min(v[k] for v in locked) for k in ('x','feetY','z')),default=999) if locked else 999
        before=api('health')['player'];drive('focus','hold 0x57 400','sleep 250');after=api('health')['player'];result['recoveredMove']=math.hypot(after['x']-before['x'],after['z']-before['z'])
        result['passed']=len(locked)>10 and result['lockedRange']<.04 and result['recoveredMove']>.5 and after['alive'] and not after['flying']
    except Exception as e:result['error']=str(e)
    finally:
        drive('focus','key 0x57 up','key 0x20 up')
        if not api('health')['player']['flying']:drive('focus','key 0x75','sleep 150')
        post('cleanup');time.sleep(.2);result['cleaned']=api('combat').get('wallBlocks')==0
        if recording:
            out,err=recording.communicate(timeout=15);result['recordingExit']=recording.returncode;result['recordingLog']=(out+err).decode(errors='replace')[-1200:]
        (ROOT/f'research/barrage-motion-{pid}-{time.time_ns()}.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:result[k] for k in ('pid','passed','error','lockedSamples','lockedRange','recoveredMove','cleaned') if k in result}))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--pid',type=int,required=True);args=a.parse_args();main(args.pid)
