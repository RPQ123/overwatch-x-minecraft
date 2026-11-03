"""Actual original quick melee against near MC targets and solid cover."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,subprocess,time
from observe_overwatch import ROOT
from calibrate_hero_actions import select
from calibrate_hero_roster import api,drive
from verify_genji_elimination_reset import post

def main(pid,heroes):
    result=dict(pid=pid,heroes=[])
    post('flight-open');time.sleep(.5)
    if api('combat').get('testError'):raise ValueError('No empty melee test volume')
    post('cleanup');time.sleep(.15)
    for name in heroes:
        row=dict(hero=name);result['heroes'].append(row)
        try:
            row['model']=select(pid,name)['modelId'];deadline=time.monotonic()+10
            if name=='Torbjorn':drive('focus','key 0x31','sleep 1200') # Original gun selection; hammer has its own attack.
            while True:
                c=api('combat')
                if not c.get('meleeError') and 'yaw' in c:break
                if time.monotonic()>deadline:raise ValueError('Current native melee binding unavailable: '+str(c.get('meleeError')))
                time.sleep(.1)
            time.sleep(1)
            post('melee');time.sleep(.2);row['fixture']=api('combat')
            if row['fixture'].get('testError') or row['fixture'].get('targetHealth')!=20:raise ValueError('Near target unavailable')
            post('wall');time.sleep(.2);drive('focus','key 0x56','sleep 750');row['covered']=api('combat')
            post('open');time.sleep(.2);drive('focus','key 0x56','sleep 750');row['open']=api('combat')
            time.sleep(.5);row['idle']=api('combat')
            row['passed']=row['covered'].get('targetHealth')==20 and row['open'].get('targetHealth',20)<20 and row['idle'].get('targetHealth')==row['open'].get('targetHealth') and row['open'].get('melee',{}).get('source')=='native TrackTargets'
            subprocess.run(['um','win','shot','--exe','GameClientApp.patched.exe',str(ROOT/f'research/melee-{name}-{pid}.png'),'--scale','.33'],cwd=ROOT,capture_output=True,check=True)
        except Exception as e:row.update(passed=False,error=str(e))
        finally:
            post('cleanup');time.sleep(.15);row['cleaned']=api('combat').get('wallBlocks')==0
            (ROOT/f'research/native-melee-{name}-{pid}-{time.time_ns()}.json').write_text(json.dumps(row,indent=2)+'\n')
            result['passed']=all(r.get('passed') and r.get('cleaned') for r in result['heroes'])
            (ROOT/f'research/native-melee-{pid}-result.json').write_text(json.dumps(result,indent=2)+'\n')
            print(json.dumps({k:row[k] for k in ('hero','passed','error','cleaned') if k in row}),flush=True)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--pid',required=True,type=int);a.add_argument('--heroes',nargs='+',default=['Genji','McCree','Pharah','Reaper','Soldier76','Tracer','Bastion','Hanzo','Junkrat','Mei','Torbjorn','Widowmaker']);args=a.parse_args();main(args.pid,args.heroes)
