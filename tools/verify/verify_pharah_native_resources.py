"""Real Shift retry plus original hover depletion/recovery; no resource writes."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,time,subprocess
from observe_overwatch import ROOT,ResearchProcess
from calibrate_hero_roster import drive,api
from calibrate_hero_actions import select
from verify_genji_elimination_reset import post
from inspect_pharah_abilities import snapshot

def main(pid):
    result={'pid':pid};process=None
    try:
        select(pid,'Pharah');time.sleep(2);post('flight-open');time.sleep(.5)
        fixture=api('combat')
        if fixture.get('testError') or not api('health')['player']['flying']:raise ValueError('Resource lab setup failed')
        drive('focus','key 0x75','sleep 400');process=ResearchProcess(pid);result['initial']=snapshot(process)
        drive('focus','key 0x10','sleep 300');result['first']=snapshot(process)
        drive('focus','key 0x10','sleep 100');result['retry']=snapshot(process)
        drive('focus','hold 0x20 3000');result['depleted']=snapshot(process)
        time.sleep(3);result['recovered']=snapshot(process)
        result['spaceBefore']=api('health')['player']
        # The CLI's post-release teardown can outlast the first fuel recovery
        # tick. Sample the original fuel during the actual hold, not only after
        # the input subprocess exits, and keep every observation as evidence.
        hold=subprocess.Popen(['um','win','drive','--proc','GameClientApp.patched.exe','focus','hold 0x20 2500'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        result['spaceFuelTrace']=[];deadline=time.monotonic()+10
        while hold.poll() is None:
            if time.monotonic()>deadline:raise TimeoutError('Space fuel sampling deadline')
            result['spaceFuelTrace'].append(snapshot(process));time.sleep(.05)
        stdout,stderr=hold.communicate(timeout=1)
        if hold.returncode or b'-> fail' in stdout:raise ValueError((stdout+stderr).decode(errors='replace'))
        result['spaceHover']=snapshot(process);result['spaceAfter']=api('health')['player']
        result['passed']=result['first']['jetRemaining']>0 and result['first']['jetTick']>result['initial']['jetTick'] and result['retry']['jetTick']==result['first']['jetTick'] and result['retry']['jetRemaining']<result['first']['jetRemaining'] and result['depleted']['fuelCommitted']==0 and result['recovered']['fuelCommitted']==100
        result['passed'] &= min(v['fuelCommitted'] for v in result['spaceFuelTrace'])==0 and not result['spaceAfter']['flying'] and result['spaceAfter']['feetY']>result['spaceBefore']['feetY']+.5
        print(json.dumps(result,indent=2))
    finally:
        if process:process.close()
        if not api('health')['player']['flying']:drive('focus','key 0x75','sleep 100')
        post('cleanup');time.sleep(.15);result['cleaned']=api('combat').get('wallBlocks')==0
        (ROOT/'research/pharah-native-resources-result.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--pid',required=True,type=int);main(parser.parse_args().pid)
