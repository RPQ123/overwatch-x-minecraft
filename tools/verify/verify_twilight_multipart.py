"""Real mod/server part fixture, separate from native firing acceptance."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,time,urllib.request
from calibrate_hero_roster import api,drive,report
from launch_passthrough_session import first_person_ready
from observe_overwatch import ROOT,ResearchProcess

def post(kind):
    request=urllib.request.Request('http://127.0.0.1:32133/world/twilight/probe-'+kind,method='POST')
    with urllib.request.urlopen(request,timeout=3) as response:return json.load(response)

def main(pid):
    process=ResearchProcess(pid);process.close()
    result={'pid':pid,'kind':'real-mod-server-fixture-not-native-fire','passed':False,'probes':[]};flightChanged=False
    try:
        world=api('world');result['before']=world
        if not world.get('enabled') or world.get('dimension')!='twilightforest:twilight_forest' or not first_person_ready(pid):raise ValueError('Enter the separate Twilight trial in the actual native first-person window')
        if not api('health')['player']['flying']:
            drive('focus','key 0x75','sleep 300');flightChanged=True
        if not api('health')['player']['flying']:raise ValueError('Creative flight was not enabled')
        # Empty air above the canopy; do not clear any forest terrain for the lab.
        drive('focus','hold 0x20 4000','sleep 500')
        for kind in ('naga','hydra'):
            post(kind);deadline=time.monotonic()+6
            while True:
                current=api('world');probe=current.get('multipartProbe') or {}
                if current.get('error'):raise ValueError(current['error'])
                if probe.get('type')=='twilightforest:'+kind and not probe.get('pending',True):break
                if time.monotonic()>deadline:raise ValueError('Multipart fixture completion deadline')
                time.sleep(.1)
            result['probes'].append(current)
            if not probe.get('passed') or not probe.get('explosionSemanticsPassed') or current.get('probeActive') or current.get('mobGriefing')!=world.get('mobGriefing'):raise ValueError('Actual part damage/source semantics/cleanup/rule restoration failed')
        result['passed']=True
    except Exception as error:result['error']=str(error)
    finally:
        if flightChanged:
            try:drive('focus','key 0x20 up','key 0x75','sleep 3500')
            except Exception as error:result['cleanupError']=str(error);result['passed']=False
        try:result['finalHealth']=api('health');result['finalWorld']=api('world')
        except Exception as error:result['finalError']=str(error);result['passed']=False
        path=ROOT/f'research/twilight-multipart-{pid}.json';path.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({'path':str(path),'passed':result['passed'],'error':result.get('error'),'probes':[v.get('multipartProbe') for v in result['probes']]},indent=2))
    return result['passed']

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pid',required=True,type=int)
    raise SystemExit(0 if main(parser.parse_args().pid) else 1)
