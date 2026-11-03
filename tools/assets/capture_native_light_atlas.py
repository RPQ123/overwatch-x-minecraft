"""Capture all 21 actual beta heroes; presentation evidence, not skill acceptance."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,subprocess,time
from calibrate_hero_roster import ROOT,ROSTER,api,report,observe
from calibrate_hero_actions import select
from observe_overwatch import ResearchProcess
from native_bootstrap_maps import read_loaded_map,MAPS
from native_map_light import owned_live_light
from native_compositor_version import VERSION as COMPOSITOR_VERSION
from verify_native_light_angles import point

def main(pid,scene,folder,heroes=None):
    folder=folder.resolve()
    if ROOT/'research' not in folder.parents:raise ValueError('Private evidence output required')
    folder.mkdir(parents=True,exist_ok=True)
    p=ResearchProcess(pid);initial=api('health');origin=initial['player'];world=api('world')['dimension']
    out=dict(pid=pid,scene=scene,origin=origin,dimension=world,rows=[],passed=False,
             evidence='Real window pixels, original colors; native appearance only, not all-hero combat acceptance')
    try:
        loaded=read_loaded_map(p)
        if loaded!={'state':8,'mapId':MAPS[scene]}:raise ValueError('Actual native backing scene mismatch')
        for name,suffix,_ in ROSTER:
            if heroes and name not in heroes:continue
            actor=select(pid,name);deadline=time.monotonic()+12
            while True:
                body=report(ROOT/f'native-host/build/body-sync-{pid}.json')
                if body.get('hero')==actor['hero'] and body.get('modelId')==actor['modelId'] and body.get('worldStable') and body.get('writes',0) and not body.get('failures'):break
                if time.monotonic()>deadline:raise ValueError('Body binding failed for '+name)
                time.sleep(.15)
            point(0,0);time.sleep(.7)
            path=folder/(name+'.png')
            subprocess.run(['um','win','shot','--exe','GameClientApp.patched.exe',str(path),'--scale','.33'],cwd=ROOT,capture_output=True,check=True,timeout=20)
            h=api('health');c=api('combat');live=report(ROOT/f'native-host/build/world-live-{pid}.json')
            if any(abs(h['player'][k]-origin[k])>.1 for k in ('x','z','feetY')):raise ValueError('Player moved during capture '+name)
            if h['sourcePid']!=initial['sourcePid'] or api('world')['dimension']!=world or read_loaded_map(p)!=loaded:raise ValueError('Source/world changed')
            if abs(c['yaw'])>2 or abs(c['pitch'])>2 or observe(pid)['hero']!=actor['hero']:raise ValueError('Hero/view changed during shot')
            if not live.get('viewLightOwned') or live.get('failures') or live.get('probeVersion')!=COMPOSITOR_VERSION:raise ValueError('Current fixed light owner failed')
            light=owned_live_light(p,pid)
            key=(.5,-2**-.5,-.5) if live.get('viewLightRig')=='camera-key' else (0,-1,0)
            expected=[sum(key[j]*live['basis'][j*3+i] for j in range(3)) for i in range(3)]
            if max(abs(a-b) for a,b in zip(light['direction'],expected))>.025:raise ValueError('Sun no longer camera-relative')
            out['rows'].append(dict(name=name,hero=actor['hero'],modelId=actor['modelId'],image=str(path.relative_to(ROOT)),
                                    yaw=c['yaw'],pitch=c['pitch'],health=h,body=body,light=light))
            (folder/'manifest.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
            print(json.dumps(dict(scene=scene,hero=name,done=len(out['rows']))),flush=True)
        out['passed']=True
    finally:
        p.close();(folder/'manifest.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--pid',type=int,required=True);a.add_argument('--scene',choices=['kyoto-login','hollywood'],required=True);a.add_argument('--output',type=__import__('pathlib').Path,required=True);a.add_argument('--heroes',nargs='+');v=a.parse_args();main(v.pid,v.scene,v.output,v.heroes)
