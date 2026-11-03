"""Actual original input, native physics transport, and reversible MC collision lab."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,subprocess,time
from calibrate_hero_roster import api,drive
from verify_genji_elimination_reset import post
from observe_overwatch import ROOT

def sample(seconds,rows,phase):
    start=time.monotonic()
    while time.monotonic()-start<seconds:
        h=api('health');c=api('combat');rows.append(dict(phase=phase,t=time.time(),player=h['player'],flight=c.get('flight')));time.sleep(.04)

def action(commands,seconds,rows,phase):
    p=subprocess.Popen(['um','win','drive','--proc','GameClientApp.patched.exe','focus',*commands],stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=ROOT)
    sample(seconds,rows,phase);out,err=p.communicate(timeout=6)
    if p.returncode or b'-> fail' in out:raise ValueError((out+err).decode(errors='replace'))

def main(pid,ceiling,output_path=None):
    result={'pid':pid,'ceiling':ceiling,'rows':[]};rows=result['rows'];rec=None
    try:
        post('flight-ceiling' if ceiling else 'flight-open');time.sleep(.6);fixture=api('combat');result['fixture']=fixture
        if fixture.get('testError') or 'flightFloorY' not in fixture:raise ValueError('Flight lab failed: '+str(fixture.get('testError')))
        if not api('health')['player']['flying']:raise ValueError('Test setup must start in creative flight')
        drive('focus','key 0x75','sleep 500');sample(.5,rows,'ground')
        prefix=(ROOT/output_path).with_suffix('') if output_path else ROOT/('research/pharah-flight-ceiling' if ceiling else 'research/pharah-flight-open')
        rec=subprocess.Popen(['um','win','record','--pid',str(pid),'--exe','GameClientApp.patched.exe','--out',str(prefix),'--seconds','12','--fps','30'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=ROOT)
        action(['key 0x10','sleep 1400'],2.4,rows,'jet')
        action(['hold 0x20 1500'],2.6,rows,'hover')
        sample(2,rows,'release')
        result['maxY']=max(v['player']['feetY'] for v in rows);result['minY']=min(v['player']['feetY'] for v in rows)
        result['upward']=max(v['player']['velocityY'] for v in rows);result['downward']=min(v['player']['velocityY'] for v in rows)
        result['nativeReadySamples']=sum(bool(v.get('flight',{}).get('ready')) for v in rows)
        origin=rows[0]['player'];result['horizontalDrift']=max(((v['player']['x']-origin['x'])**2+(v['player']['z']-origin['z'])**2)**.5 for v in rows)
        result['passed']=result['maxY']>fixture['flightFloorY']+1 and result['upward']>0 and result['downward']<0 and result['nativeReadySamples']>20
        result['passed'] &= result['horizontalDrift']<.1
        if ceiling:result['passed'] &= result['maxY']+1.8<=fixture['flightRoofY']+.002 and any(v.get('flight',{}).get('blockedAxes',0)&2 for v in rows if v['phase']=='jet')
        print(json.dumps({k:v for k,v in result.items() if k not in ('rows','fixture')},indent=2))
    finally:
        if rec:out,err=rec.communicate(timeout=20);result['recordingExit']=rec.returncode
        if not api('health')['player']['flying']:drive('focus','key 0x75','sleep 150')
        post('cleanup');time.sleep(.2);result['cleaned']=api('combat').get('wallBlocks')==0
        (ROOT/output_path if output_path else ROOT/('research/pharah-flight-ceiling-result.json' if ceiling else 'research/pharah-flight-open-result.json')).write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--pid',type=int,required=True);parser.add_argument('--ceiling',action='store_true');parser.add_argument('--out');args=parser.parse_args();main(args.pid,args.ceiling,args.out)
