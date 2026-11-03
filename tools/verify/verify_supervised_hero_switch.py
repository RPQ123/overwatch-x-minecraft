"""Real hero transitions must update the persistent supervisor, including optional failures."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,time
from calibrate_hero_actions import select
from calibrate_hero_roster import api,drive,report
from observe_overwatch import ROOT

def wait(predicate,seconds=18):
    end=time.monotonic()+seconds
    while True:
        value=report(ROOT/'research/session-status.json')
        if predicate(value):return value
        if time.monotonic()>end:raise ValueError('Supervisor did not settle: '+json.dumps({k:value.get(k) for k in ('nativePid','hero','phase','ready','error','warnings')}))
        time.sleep(.2)

def main(pid):
    d={'pid':pid,'passed':False,'rows':[]}
    try:
        for name in ('Pharah','McCree','Genji','Pharah'):
            actor=select(pid,name)
            status=wait(lambda s:s.get('nativePid')==pid and s.get('ready') and s.get('phase')=='gameplay' and not s.get('error') and s.get('hero',{}).get('id')==actor['hero'] and s.get('hero',{}).get('modelId')==actor['modelId'])
            h=api('health');body=report(ROOT/f'native-host/build/body-sync-{pid}.json')
            if h['player']['health']!=20 or not h['player']['alive'] or not body['worldStable'] or body['failures']:raise ValueError('Real player/body is not healthy after '+name)
            if name!='Pharah' and status.get('warnings'):raise ValueError('Optional warning leaked across heroes')
            d['rows'].append({'hero':name,'status':status,'health':h,'body':body})
        drive('focus','key 0x48','sleep 500')
        d['picker']=wait(lambda s:s.get('nativePid')==pid and s.get('phase')=='hero-selection' and not s.get('ready') and not s.get('error'))
        d['passed']=True
    except Exception as error:d['error']=str(error)
    path=ROOT/f'research/supervised-hero-switch-{pid}.json';path.write_text(json.dumps(d,indent=2)+'\n')
    print(json.dumps({'path':str(path),'passed':d['passed'],'error':d.get('error'),'rows':[{'hero':r['hero'],'warnings':len(r['status'].get('warnings',[]))} for r in d['rows']]},indent=2))
    return d['passed']

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pid',type=int,required=True)
    raise SystemExit(0 if main(parser.parse_args().pid) else 1)
