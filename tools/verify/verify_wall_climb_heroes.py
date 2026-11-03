"""Actual Genji/Hanzo climb + ledge adaptation and a non-climber control."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,time,subprocess,math
from observe_overwatch import ROOT
from calibrate_hero_actions import select
from calibrate_hero_roster import api,drive,report
from verify_genji_elimination_reset import post

def main(pid,heroes):
    result=dict(pid=pid,heroes=[])
    for hero in heroes:
        d=dict(hero=hero,passed=False);result['heroes'].append(d)
        try:
            select(pid,hero);time.sleep(1.5);post('flight-open');time.sleep(.3)
            if api('combat').get('testError'):raise ValueError('No safe air floor')
            post('climb-wall');time.sleep(.3)
            if api('combat').get('testError'):raise ValueError('No safe climb wall')
            d['before']=dict(player=api('health')['player'],climb=api('combat')['climb'],body=report(ROOT/f'native-host/build/body-sync-{pid}.json'))
            drive('focus','key 0x75','sleep 350')
            p=subprocess.Popen(['um','win','drive','--proc','GameClientApp.patched.exe','focus','key 0x57 down','key 0x20 down','sleep 1200','key 0x20 up','key 0x57 up','sleep 350'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            rows=[];start=time.monotonic()
            while p.poll() is None or time.monotonic()-start<2:
                if time.monotonic()-start>8:p.kill();raise ValueError('Climb input deadline')
                rows.append(dict(t=time.monotonic()-start,player=api('health')['player'],climb=api('combat')['climb']));time.sleep(.03)
            stdout,stderr=p.communicate(timeout=1)
            if p.returncode:raise ValueError((stdout+stderr).decode(errors='replace'))
            d['rows']=rows;d['after']=dict(player=api('health')['player'],climb=api('combat')['climb'],body=report(ROOT/f'native-host/build/body-sync-{pid}.json'))
            before=d['before'];after=d['after'];d['rise']=max(r['player']['feetY'] for r in rows)-before['player']['feetY'];d['nativeClimbTicks']=after['body']['climbTicks']-before['body']['climbTicks'];d['starts']=after['climb']['starts']-before['climb']['starts']
            d['passed']=after['player']['alive'] and not after['body']['failures']
            if hero in ('Genji','Hanzo'):d['passed'] &= d['rise']>=3.8 and d['nativeClimbTicks']>0 and d['starts']>0
            else:d['passed'] &= d['rise']<2 and d['nativeClimbTicks']==0 and d['starts']==0
            subprocess.run(['um','win','shot','--exe','GameClientApp.patched.exe',str(ROOT/f'research/climb-{hero}-{pid}.png'),'--scale','.33'],cwd=ROOT,capture_output=True,check=True)
        except Exception as e:d['error']=str(e)
        finally:
            drive('focus','key 0x57 up','key 0x20 up')
            if not api('health')['player']['flying']:drive('focus','key 0x75','sleep 100')
            post('cleanup');time.sleep(.15);d['cleaned']=api('combat').get('wallBlocks')==0
            (ROOT/f'research/wall-climb-{hero}-{pid}-{time.time_ns()}.json').write_text(json.dumps(d,indent=2)+'\n')
            result['passed']=all(v['passed'] and v['cleaned'] for v in result['heroes']);(ROOT/f'research/wall-climb-{pid}.json').write_text(json.dumps(result,indent=2)+'\n')
            print(json.dumps({k:d[k] for k in ('hero','passed','rise','nativeClimbTicks','starts','error','cleaned') if k in d}),flush=True)
    return result['passed']
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pid',type=int,required=True);p.add_argument('--heroes',nargs='+',default=['Hanzo','Genji','Soldier76']);a=p.parse_args();raise SystemExit(0 if main(a.pid,a.heroes) else 1)
