"""Opt-in Wraith-only native callback experiment; restores its control file."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,time
from observe_overwatch import ROOT,ResearchProcess
from observe_native_weapon_states import WeaponStates
from calibrate_hero_actions import select,record_action,names
from calibrate_hero_roster import report,api

def main(pid,mask=2):
    p=ResearchProcess(pid);p.close();flag=ROOT/f'native-host/build/native-skill-authority-{pid}.txt';before=flag.read_bytes() if flag.exists() else None
    creation=report(ROOT/f'native-host/build/native-emissions-{pid}.json')['creation'];payload=f'{creation} {mask}\n'.encode();flag.write_bytes(payload)
    result=dict(pid=pid,experimental=True,mask=mask)
    try:
        deadline=time.monotonic()+4
        while report(ROOT/f'native-host/build/weapon-gate-{pid}.json').get('skillMask')!=mask:
            if time.monotonic()>deadline:raise ValueError('Scoped native experiment did not enable')
            time.sleep(.1)
        select(pid,'Genji');result['model']=select(pid,'Reaper')['modelId'];time.sleep(1)
        p=ResearchProcess(pid)
        try:
            r=WeaponStates(p);result['action']=record_action(pid,r,'wraith-authority',['key 0x10','sleep 5500'],names())
        finally:p.close()
        result['gate']=report(ROOT/f'native-host/build/weapon-gate-{pid}.json');result['combat']=api('combat');result['player']=api('health')['player']
        changes=[v for row in result['action']['changes'] for v in row['changes'] if v['script']=='0580000000000020'];result['physicalBegan']=any(v['node']==5 and not v['finished'] for v in changes);result['physicalEnded']=any(v['node']==5 and v['finished'] for v in changes)
    except Exception as e:result['error']=str(e)
    finally:
        if flag.exists() and flag.read_bytes()==payload:
            if before is None:flag.unlink()
            else:flag.write_bytes(before)
        (ROOT/f'research/reaper-native-authority-{pid}-{time.time_ns()}.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:result[k] for k in ('pid','error','physicalBegan','physicalEnded') if k in result}))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--pid',required=True,type=int);a.add_argument('--mask',type=int,choices=[1,2,3],default=2);args=a.parse_args();main(args.pid,args.mask)
