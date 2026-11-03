"""Four real DPS pawns x four fully modded worlds; real first shots and light.

Native input follows confirmation by900ms. No binding wait before that shot.
Uses only the opted-in Switch lab and reversible target fixtures.
"""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,time,urllib.request,subprocess
from pathlib import Path
from observe_overwatch import ROOT,ResearchProcess
from calibrate_hero_actions import select
from calibrate_hero_roster import api
from verify_genji_elimination_reset import post
from verify_native_light_angles import point
from verify_bastion_tank_movement import DIMENSIONS
from verify_world_hero_switch import ready,native
from verify_switch_readiness import fast_select,check_light

def main(pid,folder):
    folder.mkdir(parents=True,exist_ok=False);result={'pid':pid,'passed':False,'rows':[]}
    try:
        p=ResearchProcess(pid);p.close();assert api('health')['worldName'].startswith('Overwatch Twilight Switch ')
        select(pid,'Genji')
        for short,dimension in DIMENSIONS.items():
            post('cleanup')
            with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:32133/world/switch-test/'+short,method='POST'),timeout=3):pass
            ready(pid,dimension=dimension);point(180,0);post('flight-open');time.sleep(.3);assert not api('combat')['testError'];post('cleanup');time.sleep(.15)
            for i,name in enumerate(('Pharah','Reaper','Soldier76','Tracer')):
                # This offline picker's original pawn enters at yaw180/pitch0.
                # Place the first-shot target on that real entry direction;
                # arbitrary pre-picker angles are not retained by native equip.
                point(180,0);post('melee');time.sleep(.15);before=api('combat');assert before['targetHealth']==20 and not before['testError']
                row={'hero':name,'dimension':dimension,'before':before};result['rows'].append(row)
                actor=fast_select(pid,name,shot=True);row['actor']=actor;row['after']=after=api('combat')
                assert after['admitted']>before['admitted'] and after['targetHealth']<20 and not after['feedError'],(name,after['targetHealth'])
                post('replay');time.sleep(.1);row['replay']=api('combat');assert row['replay']['targetHealth']==after['targetHealth'] and row['replay']['damageApplied']==after['damageApplied']
                row['nativeHealth']=native(pid);assert row['nativeHealth']['hp']==row['nativeHealth']['maximum']>0
                point(i*90,(-25,0,25,0)[i]);row['lighting']=check_light(pid,actor);assert after['particleMode']=='ALL' and api('health')['player']['health']==20
                image=folder/f'{short}-{name}.png';subprocess.run(['um','win','shot','--exe','GameClientApp.patched.exe',str(image),'--scale','.33'],cwd=ROOT,capture_output=True,check=True,timeout=15)
                row['passed']=True;post('cleanup');time.sleep(.15)
                (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'hero':name,'dimension':dimension,'health':after['targetHealth'],'passed':True}),flush=True)
        result['passed']=len(result['rows'])==16
    except Exception as e:result['error']=repr(e)
    finally:
        try:post('cleanup');time.sleep(.25);result['cleaned']=api('combat')['wallBlocks']==0 and 'targetHealth' not in api('combat')
        except Exception as e:result['cleanupError']=repr(e)
        (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result.get(k) for k in ('passed','error','cleaned')}),flush=True)
    return result['passed'] and result.get('cleaned',False)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--pid',type=int,required=True);a.add_argument('--output',type=Path,required=True);args=a.parse_args();raise SystemExit(0 if main(args.pid,args.output) else 1)
