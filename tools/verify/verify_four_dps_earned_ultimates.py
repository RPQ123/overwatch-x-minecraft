"""Earn each DPS Q using real native gun damage, then cast/drain/end.

No F11, test meter grant, timer reset or direct damage. Actual MC targets are
disposable fixtures in the fully modded Switch lab; normal native reloads apply.
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
from calibrate_hero_roster import api,drive
from verify_genji_elimination_reset import post
from verify_native_light_angles import point
from verify_bastion_tank_movement import stable
from observe_overwatch import ROOT,ResearchProcess

def main(pid,folder,heroes=('Reaper','Tracer','Soldier76','Pharah')):
    folder.mkdir(parents=True,exist_ok=False);out={'pid':pid,'passed':False,'meterGrantsUsed':False,'heroes':[]}
    def save():(folder/'result.json').write_text(json.dumps(out,indent=2)+'\n')
    try:
        p=ResearchProcess(pid);p.close();assert api('health')['worldName'].startswith('Overwatch Twilight Switch ')
        out['requestedHeroes']=list(heroes)
        for name in heroes:
            select(pid,'Genji');select(pid,name);stable(pid,api('world')['dimension']);point(180,0);post('flight-open');time.sleep(.3);post('melee');time.sleep(.2)
            row={'hero':name,'initial':api('combat'),'attacks':[]};out['heroes'].append(row);save();cost=row['initial']['nativeCharge']['cost'];assert row['initial']['nativeCharge']['charge']<cost*.15
            total=0.;stalls=0
            for turn in range(60):
                before=api('combat')
                if before['nativeCharge']['charge']==cost:break
                if before['targetHealth']<=0:post('melee');time.sleep(.15);before=api('combat')
                drive('focus','mdown 1280 720','sleep 850','mup','sleep 200');after=api('combat');lost=before['targetHealth']-after['targetHealth'];assert lost>=0
                total+=lost;stalls=stalls+1 if lost==0 else 0
                if stalls==2:drive('focus','key 0x52','sleep 2200')
                assert stalls<4,'Native primary/reload stopped producing actual damage'
                row['attacks'].append({'beforeCharge':before['nativeCharge'],'afterCharge':after['nativeCharge'],'beforeHealth':before['targetHealth'],'afterHealth':after['targetHealth'],'lost':lost});save()
            row['earned']=api('combat');row['actualDamageForCharge']=total
            assert row['earned']['nativeCharge']['charge']==cost and total*10>=cost*.8,'Real damage did not earn Q'
            subprocess.run(['um','win','shot','--exe','GameClientApp.patched.exe',str(folder/(name+'-earned.png')),'--scale','.33'],cwd=ROOT,capture_output=True,check=True,timeout=15)
            post('melee');time.sleep(.15);row['beforeQ']=api('combat');commands=['focus','key 0x51']
            if name=='Soldier76':commands+=['sleep 800','mdown 1280 720','sleep 200','mup']
            command=subprocess.Popen(['um','win','drive','--proc','GameClientApp.patched.exe',*commands],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE);start=time.monotonic();samples=[]
            # Observe actual End. The beta Visor outlasts an8s generic window;
            # the deadline is a harness bound, not a fabricated skill duration.
            while time.monotonic()-start<8 or samples and samples[-1]['nativeCharge'].get('active') and time.monotonic()-start<20:
                samples.append(api('combat'));time.sleep(.04)
            stdout,stderr=command.communicate(timeout=3);assert command.returncode==0 and b'-> fail' not in stdout
            row['qSamples']=samples;row['afterQ']=api('combat');assert min(v['nativeCharge'].get('charge',cost) for v in samples)==0 and not row['afterQ']['nativeCharge'].get('active')
            assert row['afterQ']['nativeCharge']['charge']<100,'Ultimate damage credited next Q'
            if name=='Reaper':assert row['afterQ']['reaper']['starts']==row['beforeQ']['reaper']['starts']+1
            elif name=='Tracer':assert row['afterQ']['pulse']['launches']==row['beforeQ']['pulse'].get('launches',0)+1
            elif name=='Pharah':assert row['afterQ']['barragePresentationLaunches']==row['beforeQ']['barragePresentationLaunches']+90
            else:assert any(v['nativeCharge'].get('visorActive') for v in samples)
            drive('focus','key 0x52','sleep 2200');post('melee');time.sleep(.15);drive('focus','mdown 1280 720','sleep 200','mup','sleep 450');row['primaryAfterQ']=api('combat');assert row['primaryAfterQ']['targetHealth']<20
            row['passed']=True;post('cleanup');save();print(json.dumps({'hero':name,'damage':total,'cost':cost,'passed':True}),flush=True)
        out['passed']=True
    except Exception as e:out['error']=repr(e)
    finally:
        try:drive('focus','mup');post('cleanup');time.sleep(.3);out['cleaned']=api('combat')['wallBlocks']==0 and 'targetHealth' not in api('combat')
        except Exception as e:out['cleanupError']=repr(e)
        save();print(json.dumps({k:out.get(k) for k in ('passed','error','cleaned')}),flush=True)
    return out['passed'] and out.get('cleaned',False)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--pid',type=int,required=True);a.add_argument('--output',type=Path,required=True);a.add_argument('--heroes',nargs='+',choices=['Reaper','Tracer','Soldier76','Pharah'],default=['Reaper','Tracer','Soldier76','Pharah']);args=a.parse_args();raise SystemExit(0 if main(args.pid,args.output,args.heroes) else 1)
