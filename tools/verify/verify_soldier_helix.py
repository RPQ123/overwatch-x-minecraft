"""Actual beta Helix: one authoritative blast, three visible strands, real cover.

Requires the disposable fully modded Switch world. Never creates an attack from
the fixture; actual RMB produces the native factory event. Existing native CD.
"""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,time,subprocess
from pathlib import Path
from calibrate_hero_actions import select
from calibrate_hero_roster import api,drive,report
from verify_genji_elimination_reset import post
from verify_native_light_angles import point
from verify_bastion_tank_movement import stable
from observe_overwatch import ROOT,ResearchProcess

def main(pid,folder):
    folder.mkdir(parents=True,exist_ok=False);r={'pid':pid,'passed':False};rec=None
    try:
        p=ResearchProcess(pid);p.close();assert api('health')['worldName'].startswith('Overwatch Twilight Switch ')
        select(pid,'Soldier76');stable(pid,api('world')['dimension']);point(180,0);post('flight-open');time.sleep(.3)
        assert not api('combat').get('testError') and api('health')['player']['flying']
        post('start');time.sleep(.2);r['before']=api('combat');assert r['before']['targetHealth']==20
        rec=subprocess.Popen(['um','win','record','--pid',str(api('health')['sourcePid']),'--exe','GameClientApp.patched.exe','--out',str(folder/'actual'),'--seconds','7','--fps','60'],stdout=open(folder/'record.log','w'),stderr=subprocess.STDOUT)
        time.sleep(.8);drive('focus','mdown 1280 720 right','sleep 100','mup right','sleep 450');r['open']=api('combat')
        assert abs(r['open']['targetHealth']-8)<.0001 and abs(r['open']['damageApplied']-r['before']['damageApplied']-12)<.0001
        assert r['open']['admitted']==r['before']['admitted']+1 and r['open']['rocketExplosions']==r['before']['rocketExplosions']+1
        assert r['open']['helixModelsShown']>r['before']['helixModelsShown'] and r['open']['helixRenderFrames']>r['before']['helixRenderFrames']
        post('replay');time.sleep(.2);r['replay']=api('combat');assert r['replay']['targetHealth']==r['open']['targetHealth'] and r['replay']['rocketExplosions']==r['open']['rocketExplosions']
        drive('focus','mdown 1280 720 right','sleep 100','mup right','sleep 300');r['cooldown']=api('combat');assert r['cooldown']['admitted']==r['open']['admitted']
        rec.wait(timeout=10);assert rec.returncode==0;rec=None
        time.sleep(2);post('start');post('wall');time.sleep(.2);r['coverBefore']=api('combat');drive('focus','mdown 1280 720 right','sleep 100','mup right','sleep 500');r['covered']=api('combat')
        assert r['covered']['targetHealth']==20 and r['covered']['blockHits']>r['coverBefore']['blockHits'] and r['covered']['admitted']==r['coverBefore']['admitted']+1
        post('open');time.sleep(.2);drive('focus','mdown 1280 720','sleep 150','mup','sleep 300');r['primary']=api('combat');assert r['primary']['targetHealth']<20
        r['passed']=True
    except Exception as e:r['error']=repr(e)
    finally:
        if rec:
            try:rec.wait(timeout=12)
            except Exception:rec.kill()
        try:post('cleanup');time.sleep(.25);r['cleaned']=api('combat')['wallBlocks']==0 and 'targetHealth' not in api('combat')
        except Exception as e:r['cleanupError']=repr(e)
        (folder/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r.get(k) for k in ('passed','error','cleaned')}),flush=True)
    return r['passed'] and r.get('cleaned',False)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--pid',required=True,type=int);a.add_argument('--output',required=True,type=Path);args=a.parse_args();raise SystemExit(0 if main(args.pid,args.output) else 1)
