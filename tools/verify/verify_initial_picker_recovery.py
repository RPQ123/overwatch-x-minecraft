"""Normally restart MC before the first hero confirmation, then verify real fire."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,hashlib,json,subprocess,time,urllib.request
import psutil
from calibrate_hero_actions import select
from calibrate_hero_roster import api,drive,report
from launch_passthrough_session import first_person_ready,PROFILE
from observe_overwatch import ROOT
from verify_genji_elimination_reset import post
from verify_world_hero_switch import native,ready,require,shot

def main(pid):
    path=ROOT/f'research/initial-picker-recovery-{pid}-{time.time_ns()}.json'
    result={'pid':pid,'passed':False,'gapSamples':[]}
    try:
        s=report(ROOT/'research/session-status.json');h=api('health')
        require(h['worldName'].startswith('Overwatch Twilight Switch '),'Use an isolated backed-up Switch clone')
        require(s.get('nativePid')==pid and s.get('phase')=='hero-selection' and s.get('state') is None and s.get('loadedFiles') and not first_person_ready(pid),'Test requires the initial picker before any confirmation')
        guest=psutil.Process(h['sourcePid']);require(str(PROFILE) in guest.cmdline(),'Wrong guest profile')
        drive('focus','click 218 1224','sleep 650') # Preview the original hero; do not confirm.
        require(not first_person_ready(pid),'Hero preview unexpectedly entered gameplay')
        body=report(ROOT/f'native-host/build/body-sync-{pid}.json');require(body['writes']==0,'Gameplay already wrote the body')
        result['before']={'status':s,'health':h,'body':body,'native':native(pid)}
        subprocess.run(['um','win','shot','--exe','GameClientApp.patched.exe',str(path.with_suffix(''))+'-before.png','--scale','.33'],cwd=ROOT,capture_output=True,check=True,timeout=20)
        with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:32133/shutdown',method='POST'),timeout=3):pass
        deadline=time.monotonic()+105
        while True:
            n=native(pid);b=report(ROOT/f'native-host/build/body-sync-{pid}.json')
            require(n['hp']>0 and b['enabled'] and not b['failures'],'Native actor/body failed during initial-picker restart')
            result['gapSamples'].append({'native':n,'body':b})
            try:
                now=api('health');s=report(ROOT/'research/session-status.json');v=report(ROOT/f'native-host/build/world-live-{pid}.json')
                if now['sourcePid']!=h['sourcePid'] and (now.get('player') or {}).get('alive') and s.get('guestRecovery',{}).get('sourcePid')==now['sourcePid'] and b.get('sourcePid')==now['sourcePid'] and b.get('worldStable') and v.get('lastMcGeneration')==b.get('guestGeneration'):
                    result['after']={'status':s,'health':now,'body':b,'native':n,'presentation':v};break
            except (OSError,ValueError):pass
            if time.monotonic()>deadline:raise ValueError('Initial-picker supervisor did not reopen/recompose Minecraft')
            time.sleep(.3)
        after=result['after'];s=after['status']
        require(s['guestRecovery']['restarts']==1 and s['phase']=='hero-selection' and not s['ready'] and s['state'] is None and not s.get('error'),'Initial picker phase/retry state lost')
        require(not guest.is_running() and not first_person_ready(pid) and after['body']['writes']==0,'Initial selection or source process was replaced incorrectly')
        require(s['loadedFiles']['guest\\build\\libs\\owmc-guest-0.1.0.jar']==hashlib.sha256((PROFILE/'mods/owmc-guest-0.1.0.jar').read_bytes()).hexdigest(),'Reopened guest manifest differs')
        subprocess.run(['um','win','shot','--exe','GameClientApp.patched.exe',str(path.with_suffix(''))+'-after.png','--scale','.33'],cwd=ROOT,capture_output=True,check=True,timeout=20)
        select(pid,'Genji');ready(pid);post('flight-open');time.sleep(.4)
        require(not api('combat').get('testError'),'Air fixture unavailable')
        post('cleanup');time.sleep(.2);result['fire']=shot(pid,'Genji')
        result['passed']=True
    except Exception as e:result['error']=str(e)
    finally:
        try:
            post('cleanup');time.sleep(.3);c=api('combat');result['cleaned']=c['wallBlocks']==0 and 'targetHealth' not in c
            if not result['cleaned']:result['passed']=False
        except Exception as e:result['cleanupError']=str(e);result['passed']=False
        path.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({'path':str(path),'passed':result['passed'],'error':result.get('error'),'cleaned':result.get('cleaned')}),flush=True)
    return result['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pid',type=int,required=True)
    raise SystemExit(0 if main(p.parse_args().pid) else 1)
