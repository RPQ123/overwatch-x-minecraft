"""Actual native E reflects a vanilla arrow, respects cover/cooldown and credits a kill."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,subprocess,time
from observe_overwatch import ROOT,ResearchProcess
from calibrate_hero_actions import select
from calibrate_hero_roster import api,drive
from verify_genji_elimination_reset import post
from test_genji_reset_data import binding

def wait_phase(active,seconds=3):
    deadline=time.monotonic()+seconds
    while True:
        c=api('combat')
        if c.get('deflect',{}).get('active') is active:return c
        if time.monotonic()>deadline:raise ValueError('Original Deflect phase did not become '+str(active)+': '+str(c.get('deflectError')))
        time.sleep(.03)

def main(pid):
    d=dict(pid=pid,passed=False);recording=None
    try:
        select(pid,'Genji');time.sleep(2);post('flight-open');time.sleep(.5)
        if api('combat').get('testError'):raise ValueError('No safe empty space')
        post('cleanup');post('start');time.sleep(.2);post('deflect-arrow');time.sleep(.7);d['inactive']=api('combat')
        post('start');time.sleep(.2);post('wall');drive('focus','key 0x45');wait_phase(True);post('deflect-arrow');time.sleep(.7);d['covered']=api('combat')
        post('cleanup');wait_phase(False);time.sleep(9)
        drive('focus','key 0x10','sleep 600');p=ResearchProcess(pid)
        try:d['dashBefore']=binding(p)[1]
        finally:p.close()
        post('start');time.sleep(.2)
        recording=subprocess.Popen(['um','win','record','--pid',str(pid),'--exe','GameClientApp.patched.exe','--out',str(ROOT/f'research/genji-deflect-{pid}'),'--seconds','11','--fps','30'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        drive('focus','key 0x45');d['begin']=wait_phase(True);post('deflect-lethal');time.sleep(.8);d['reflected']=api('combat')
        p=ResearchProcess(pid)
        try:d['dashAfter']=binding(p)[1]
        finally:p.close()
        wait_phase(False);post('start');time.sleep(.2);drive('focus','key 0x45','sleep 150');post('deflect-arrow');time.sleep(.7);d['cooldown']=api('combat')
        d['passed']=d['inactive'].get('targetHealth')==20 and d['inactive'].get('deflect',{}).get('reflections')==0
        d['passed'] &= d['covered'].get('targetHealth')==20 and d['covered'].get('deflect',{}).get('reflections')==0
        d['passed'] &= d['reflected'].get('deflect',{}).get('reflections')==1 and d['reflected'].get('targetHealth')==0 and d['reflected'].get('deflect',{}).get('healthLost')==1
        d['passed'] &= d['dashBefore']['remaining']>0 and d['dashAfter']['remaining']==0 and d['reflected'].get('dashResetsApplied')==1
        d['passed'] &= not d['cooldown'].get('deflect',{}).get('active') and d['cooldown'].get('deflect',{}).get('reflections')==1 and d['cooldown'].get('targetHealth')==20
        post('cleanup');select(pid,'McCree');time.sleep(.5);d['switch']=api('combat');d['passed'] &= not d['switch'].get('deflect',{}).get('active')
    except Exception as e:d['error']=str(e)
    finally:
        drive('focus','mup','mup right');post('cleanup');time.sleep(.2);d['cleaned']=api('combat').get('wallBlocks')==0
        if recording:
            out,err=recording.communicate(timeout=15);d['recordingExit']=recording.returncode;d['recordingLog']=(out+err).decode(errors='replace')[-1000:]
        (ROOT/f'research/native-deflect-{pid}-{time.time_ns()}.json').write_text(json.dumps(d,indent=2)+'\n')
        print(json.dumps({k:d[k] for k in ('pid','passed','error','cleaned') if k in d}))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--pid',required=True,type=int);args=a.parse_args();main(args.pid)
