"""Explicit authorized real-game Pharah test; never injects synthetic shots."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,subprocess,time,urllib.request
from observe_overwatch import ROOT,ResearchProcess
from calibrate_hero_roster import observe,drive

def api(route,post=False):
    with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:32133/'+route,method='POST' if post else 'GET'),timeout=3) as r:return json.load(r)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pid',type=int,required=True);args=parser.parse_args()
    native=observe(args.pid)
    if native['hero']!=0x02e0000000000008:raise ValueError('Select native Pharah first')
    before=api('combat')
    if before.get('testError') or before.get('testStoneRemaining')!=23:raise ValueError('No intact empty-volume rocket fixture')
    if before.get('beamTargets')!={'rocketNear':20.0,'rocketOutside':20.0}:raise ValueError('Splash targets must start healthy')
    result={'pid':args.pid,'before':before,'nativeBefore':native}
    recording=subprocess.Popen(['um','win','record','--pid',str(args.pid),'--exe','GameClientApp.patched.exe','--out',str(ROOT/'research/pharah-explosion-live'),'--seconds','5','--fps','60'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        time.sleep(1);result['input']=drive('focus','mdown 1280 720','sleep 150','mup','sleep 700')
        after=api('combat');result['after']=after;result['nativeAfter']=observe(args.pid)
        api('combat/test/replay',True);time.sleep(.3);replay=api('combat');result['replay']=replay
        keys=('rocketExplosions','rocketBlocksDestroyed','damageApplied','testStoneRemaining','testProtectedRemaining')
        result['replayUnchanged']=all(after.get(k)==replay.get(k) for k in keys)
        result['terrainPassed']=(after['rocketExplosions']-before['rocketExplosions']==1 and after['testStoneRemaining']<23 and after['testProtectedRemaining']==2 and result['replayUnchanged'])
        result['splashPassed']=(0<after['beamTargets']['rocketNear']<20 and after['beamTargets']['rocketOutside']==20 and after['beamTargets']==replay['beamTargets'])
        result['nativeReport']=json.loads((ROOT/f'native-host/build/native-emissions-{args.pid}.json').read_text())
    finally:
        stdout,stderr=recording.communicate(timeout=20);result['recordingExit']=recording.returncode
        if recording.returncode:result['recordingError']=stderr.decode(errors='replace')[-1000:]
        path=ROOT/'research/pharah-explosion-live-result.json';path.write_text(json.dumps(result,indent=2)+'\n');print(path,flush=True)
    print(json.dumps({k:result[k] for k in ('terrainPassed','splashPassed','replayUnchanged','recordingExit')}),flush=True)

if __name__=='__main__':main()
