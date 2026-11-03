"""Actual short/mid/full native bow releases and matching MC health loss."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,time
from observe_overwatch import ROOT
from calibrate_hero_actions import select
from calibrate_hero_roster import api,drive
from verify_genji_elimination_reset import post

def main(pid):
    d=dict(pid=pid,passed=False,releases=[])
    try:
        select(pid,'Hanzo');time.sleep(2);post('flight-open');time.sleep(.5)
        if api('combat').get('testError'):raise ValueError('No safe air volume')
        post('cleanup');time.sleep(.2)
        for ms in (150,400,1000):
            post('start');time.sleep(.2);before=api('combat');drive('focus','mdown 1280 720',f'sleep {ms}','mup','sleep 500');after=api('combat')
            shot=after.get('lastShot',{});row=dict(holdMs=ms,before=before,after=after);d['releases'].append(row)
            if shot.get('resource')==0:raise ValueError('No original bow factory')
            row['damage']=shot.get('nativeDamage');row['health']=after.get('targetHealth');row['passed']=row['damage'] is not None and abs(row['health']-(20-row['damage']*.1))<.0001 and shot.get('effect',{}).get('gravity',0)>0
        values=[v['damage'] for v in d['releases']];d['passed']=all(v['passed'] for v in d['releases']) and values[0]<values[1]<values[2]
    except Exception as e:d['error']=str(e)
    finally:
        drive('focus','mup');post('cleanup');time.sleep(.2);d['cleaned']=api('combat').get('wallBlocks')==0
        (ROOT/f'research/hanzo-charge-{pid}-{time.time_ns()}.json').write_text(json.dumps(d,indent=2)+'\n')
        print(json.dumps(dict(pid=pid,passed=d['passed'],error=d.get('error'),releases=[(v['holdMs'],v.get('damage'),v.get('health')) for v in d['releases']],cleaned=d['cleaned'])))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--pid',type=int,required=True);args=a.parse_args();main(args.pid)
