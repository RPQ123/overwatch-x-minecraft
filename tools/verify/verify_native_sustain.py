"""Actual native skill -> MC self-heal, stop/cap/switch acceptance; restores injury."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,time,subprocess
from observe_overwatch import ROOT
from calibrate_hero_actions import select
from calibrate_hero_roster import drive
from launch_passthrough_session import api

def sample():return dict(wall=time.monotonic(),player=api('health')['player'],sustain=api('combat').get('sustain'),error=api('combat').get('sustainError'))
def samples(seconds):
    out=[];start=time.monotonic()
    while time.monotonic()-start<seconds:out.append(sample());time.sleep(.08)
    return out
def action(commands,seconds):
    p=subprocess.Popen(['um','win','drive','--proc','GameClientApp.patched.exe','focus',*commands],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    rows=samples(seconds);stdout,stderr=p.communicate(timeout=5)
    if p.returncode:raise ValueError((stdout+stderr).decode(errors='replace')[-800:])
    return rows
def require(value,message):
    if not value:raise ValueError(message)
def main(pid):
    result=dict(pid=pid,passed=False,rows={})
    try:
        select(pid,'Bastion');time.sleep(1);api('combat/test/sustain-hurt',True);time.sleep(.3)
        idle=samples(.8);result['rows']['idle']=idle;require(max(x['player']['health'] for x in idle)<=2.01,'Idle/natural regeneration changed lab health')
        repair=action(['key 0x45 down','sleep 1900','key 0x45 up'],2.7);result['rows']['repair']=repair
        active=[x for x in repair if x['sustain'] and x['sustain']['active']];require(len(active)>=8,'Original repair never became active')
        require(all(not x['error'] and abs(x['sustain']['rateMcHp']-5)<.001 for x in active),'Repair native source/rate differs')
        require(7<=repair[-1]['player']['health']<=13,'Repair did not heal the actual MC player at declared50 HP/sec')
        stopped=samples(.6);result['rows']['stopped']=stopped;require(max(x['player']['health'] for x in stopped)-min(x['player']['health'] for x in stopped)<.01,'Release left healing active')
        api('combat/test/cleanup',True);time.sleep(.3)
        cap=action(['key 0x45 down','sleep 700','key 0x45 up'],1.5);result['rows']['cap']=cap;require(all(x['player']['health']<=20 for x in cap),'Repair exceeded maximum MC health')
        select(pid,'Mei');time.sleep(.8);api('combat/test/sustain-hurt',True);time.sleep(.3)
        cryo=action(['key 0x10','sleep 5100'],5.8);result['rows']['cryo']=cryo
        active=[x for x in cryo if x['sustain'] and x['sustain']['active']];require(len(active)>=20,'Original Cryo healing never became active')
        require(all(not x['error'] and abs(x['sustain']['rateMcHp']-15/3.9)<.001 for x in active),'Cryo native source/rate differs')
        require(16<=cryo[-1]['player']['health']<=17.05,'Cryo did not distribute original150 HP with its total cap')
        end=samples(.6);result['rows']['cryoEnd']=end;require(max(x['player']['health'] for x in end)-min(x['player']['health'] for x in end)<.01,'Cryo End left healing active')
        select(pid,'McCree');time.sleep(.3);switched=samples(.7);result['rows']['switch']=switched
        require(all(not (x['sustain'] or {}).get('active') for x in switched),'Cross-hero healing survived model replacement')
        result['passed']=True
    except Exception as e:result['error']=str(e)
    finally:
        try:drive('key 0x45 up','key 0x10 up');api('combat/test/cleanup',True);result['final']=sample()
        except Exception as e:result['cleanupError']=str(e);result['passed']=False
        path=ROOT/f'research/native-sustain-{pid}-{time.time_ns()}.json';path.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(path=str(path),passed=result['passed'],error=result.get('error'),cleanupError=result.get('cleanupError'))))
    return result['passed']
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pid',type=int,required=True);a=p.parse_args();raise SystemExit(0 if main(a.pid) else 1)
