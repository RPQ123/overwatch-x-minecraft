"""Record original hands through rapid yaw/pitch changes; no movement/fire input."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,subprocess,time
from pathlib import Path
from observe_overwatch import ROOT
from calibrate_hero_actions import select
from calibrate_hero_roster import api,drive,report
from verify_world_hero_switch import ready
from verify_native_light_angles import point

def main(pid,base):
    base=base.resolve()
    if ROOT/'research' not in base.parents:raise ValueError('Private evidence required')
    select(pid,'McCree');ready(pid);point(0,0);before=api('health');record=None;out=dict(pid=pid,visualAcceptance='pending-recording-review')
    try:
        record=subprocess.Popen(['um','win','record','--pid',str(pid),'--exe','GameClientApp.patched.exe','--out',str(base),'--seconds','8','--fps','60','--no-audio'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        commands=['focus','sleep 1000']
        for _ in range(12):commands+=['rel 300 0','sleep 120']
        commands+=['rel 0 -850','sleep 200','rel 0 1700','sleep 200','rel 0 -1700','sleep 200','rel 0 850','sleep 300']
        out['input']=drive(*commands)
    finally:
        if record:
            stdout,stderr=record.communicate(timeout=25);out.update(recordingExit=record.returncode,recordingStdout=stdout.decode(errors='replace'),recordingStderr=stderr.decode(errors='replace'))
        point(0,0);out['before']=before;out['after']=api('health');out['native']=report(ROOT/f'native-host/build/world-live-{pid}.json')
        out['controlChecksPassed']=record is not None and record.returncode==0 and all(abs(out['after']['player'][k]-before['player'][k])<.1 for k in ['x','feetY','z']) and not out['native']['failures']
        base.with_suffix('.checks.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(controlChecksPassed=out['controlChecksPassed'],recording=str(base.with_suffix('.mkv')))))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--pid',type=int,required=True);a.add_argument('--output',type=Path,required=True);args=a.parse_args();main(args.pid,args.output)
