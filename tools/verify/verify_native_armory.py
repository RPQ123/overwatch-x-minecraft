"""Real native primary shots, MC cover/damage/replay, with no synthetic attacks."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,time,subprocess
from calibrate_hero_actions import select
from calibrate_hero_roster import api,drive,report
from verify_genji_elimination_reset import post
from observe_overwatch import ROOT

def main(pid,heroes,mode='primary'):
    path=ROOT/('research/armory-real-primary-result.json' if mode=='primary' else 'research/armory-real-modes-result.json')
    try:results=json.loads(path.read_text())
    except (OSError,ValueError):results=[]
    post('flight-open');time.sleep(.5)
    if api('combat').get('testError'):raise ValueError('No loaded empty air volume for weapon verification')
    post('cleanup');time.sleep(.15)
    for name in heroes:
        result={'hero':name,'pid':pid,'mode':mode}
        try:
            result['selection']=select(pid,name)['modelId'];deadline=time.monotonic()+10
            while True:
                native=report(ROOT/f'native-host/build/native-emissions-{pid}.json');c=api('combat')
                if native.get('combatReady') and native.get('armoryVariants',0)>0 and not c.get('feedError'):break
                if time.monotonic()>deadline:raise ValueError('No calibrated current armory: '+str(native.get('combatReady')))
                time.sleep(.2)
            # The original equip animation can outlive camera/body readiness.
            # Do not score its intentional firing lock as missing ammunition.
            time.sleep(1.5)
            if mode=='sentry':drive('focus','key 0x10','sleep 1500')
            if mode=='scoped':drive('focus','mdown 1280 720 right','sleep 1400')
            if not api('health')['player']['flying']:drive('focus','key 0x75','sleep 100')
            post('start');time.sleep(.2);result['fixture']=api('combat')
            if result['fixture'].get('testError') or result['fixture'].get('targetHealth')!=20:raise ValueError('Target corridor unavailable')
            button=' right' if mode=='alternate' else ''
            fire=['mdown 1280 720 right','sleep 150','mup right','sleep 700'] if mode=='helix' else ['mdown 1280 720'+button,'sleep 1000' if name=='Hanzo' else 'sleep 200','mup'+button,'sleep 450']
            post('wall');time.sleep(.15);drive('focus',*fire);result['covered']=api('combat')
            if mode=='helix':time.sleep(9) # Allow the original native cooldown; no timer/ability writes.
            post('open');time.sleep(.15);drive('focus',*fire);result['open']=api('combat')
            post('replay');time.sleep(.2);result['replay']=api('combat');native=report(ROOT/f'native-host/build/native-emissions-{pid}.json')
            result['native']=dict(combatReady=native.get('combatReady'),armoryVariants=native.get('armoryVariants'),armoryAccepted=native.get('armoryAccepted'))
            result['passed']=result['covered'].get('targetHealth')==20 and result['covered'].get('blockHits',0)>0 and result['open'].get('targetHealth',20)<20 and result['open'].get('targetHealth')==result['replay'].get('targetHealth') and result['open'].get('rejected')==0
            subprocess.run(['um','win','shot','--exe','GameClientApp.patched.exe',str(ROOT/f'research/armory-{name}-{mode}-{pid}.png'),'--scale','.33'],cwd=ROOT,capture_output=True,check=True)
        except (OSError,ValueError,KeyError) as error:result['error']=str(error);result['passed']=False
        finally:
            if mode=='scoped':drive('focus','mup right')
            post('cleanup');results=[v for v in results if (v.get('hero'),v.get('mode','primary'))!=(name,mode)];results.append(result);path.write_text(json.dumps(results,indent=2)+'\n')
            suffix='' if mode=='primary' else '-'+mode
            (ROOT/f'research/armory-{name}{suffix}-{pid}-result.json').write_text(json.dumps(result,indent=2)+'\n')
            print(json.dumps({k:result[k] for k in ('hero','passed','error','native') if k in result}),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--pid',required=True,type=int);parser.add_argument('--heroes',nargs='+',required=True);parser.add_argument('--mode',choices=['primary','alternate','scoped','sentry','helix'],default='primary');args=parser.parse_args();main(args.pid,args.heroes,args.mode)
