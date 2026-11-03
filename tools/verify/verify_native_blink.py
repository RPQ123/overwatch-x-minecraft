"""Real Tracer inputs, native charges and reversible MC collision/replay checks."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,math,subprocess,time
from observe_overwatch import ROOT,ResearchProcess
from observe_native_weapon_states import WeaponStates
from calibrate_hero_actions import select
from calibrate_hero_roster import api,drive
from verify_genji_elimination_reset import post

def main(pid, folder=None):
    folder = folder or ROOT/"research/tracer-blink-live-latest"
    folder.mkdir(parents=True, exist_ok=False)
    result=dict(pid=pid,rows=[]);p=None;rec=None;command=None
    try:
        select(pid,'Tracer');post('flight-open');time.sleep(.6)
        fixture=api('combat');result['fixture']=fixture
        if fixture.get('testError') or 'flightFloorY' not in fixture:raise ValueError('Fixture failed')
        if not api('health')['player']['flying']:raise ValueError('Creative fixture flight unavailable')
        yaw=api('combat')['yaw'];turn=(180-yaw+180)%360-180
        drive('focus',f'rel {round(turn/.1)} 0','sleep 150','key 0x75','sleep 500')
        deadline=time.monotonic()+6
        while not api('combat').get('blink',{}).get('ready'):
            if time.monotonic()>deadline:raise ValueError('Native Blink channel unavailable')
            time.sleep(.1)
        result['before']=api('health')['player'];result['yaw']=api('combat')['yaw']
        p=ResearchProcess(pid);r=WeaponStates(p);s=r.sample_weapon(False,True)
        script=next(k[0] for k in r.graph_cache if k[2]==0x0580000000000024);bag=r.pointer(script+0x98)
        initial=api('combat')['blink'];result['baseline']=initial
        rec=subprocess.Popen(['um','win','record','--pid',str(pid),'--exe','GameClientApp.patched.exe','--out',str(folder/'blink'),'--seconds','10','--fps','30'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        # One input process keeps the first three original presses inside a
        # single recharge interval. Third/fifth blink face the actual lab wall.
        commands=['focus','sleep 250','key 0x10','sleep 280','rel 1800 0','sleep 100','key 0x10','sleep 280','rel -900 0','sleep 100','key 0x10','sleep 280','key 0x10','sleep 3500','key 0x10','sleep 600']
        start=time.monotonic();command=subprocess.Popen(['um','win','drive','--proc','GameClientApp.patched.exe',*commands],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        while command.poll() is None or time.monotonic()-start<6:
            if time.monotonic()-start>12:raise RuntimeError('Input deadline')
            h=api('health');c=api('combat');variables=r.varbag(bag)
            charges=next(v['value'] for v in variables if v['rid']=='0d8000000000000b')
            result['rows'].append(dict(t=time.monotonic()-start,player=h['player'],blink=c.get('blink'),charges=charges,yaw=c['yaw']))
            time.sleep(.025)
        out,err=command.communicate(timeout=1);result['input']=out.decode(errors='replace');result['inputExit']=command.returncode
        if command.returncode or b'-> fail' in out:raise RuntimeError((out+err).decode(errors='replace'))
        rows=result['rows'];edges=[];previous=initial['starts'];last=result['before']
        for row in rows:
            value=row.get('blink') or {}
            if value.get('starts',previous)>previous:
                player=row['player'];edges.append(dict(t=row['t'],starts=value['starts'],charges=row['charges'],requested=value.get('requestedDistance'),actual=value.get('actualDistance'),position=[player['x'],player['feetY'],player['z']]))
                previous=value['starts'];last=player
        result['events']=edges
        result['chargeEdges']=[dict(t=row['t'],charges=row['charges']) for i,row in enumerate(rows) if i==0 or row['charges']!=rows[i-1]['charges']]
        result['wallMaximumX']=math.floor(result['before']['x'])+8-.3
        result['final']=api('combat')['blink'];result['after']=api('health')['player']
        result['passed']=len(edges)==4 and all(7.3<v['requested']<7.7 for v in edges) and 7.3<edges[0]['actual']<7.7 and 7.3<edges[1]['actual']<7.7
        result['passed'] &= len(edges)>=4 and edges[2]['actual']<edges[2]['requested']-.05 and edges[3]['actual']<.1
        result['passed'] &= result['after']['x']<=result['wallMaximumX']+.002 and result['after']['alive'] and not result['after']['flying']
        result['passed'] &= [v['charges'] for v in result['chargeEdges']][:4]==[3.,2.,1.,0.]
        print(json.dumps({k:v for k,v in result.items() if k not in ('rows','fixture','input')},indent=2))
        drive('focus');subprocess.run(['um','win','shot','--exe','GameClientApp.patched.exe',str(folder/'blink.png'),'--scale','.33'],cwd=ROOT,capture_output=True,check=True)
    except Exception as error:
        result['error']=str(error);result['passed']=False;print(json.dumps(dict(error=str(error),passed=False)))
    finally:
        if command and command.poll() is None:command.kill()
        if p:p.close()
        if rec:rec.communicate(timeout=20);result['recordingExit']=rec.returncode
        if not api('health')['player']['flying']:drive('focus','key 0x75','sleep 150')
        post('cleanup');time.sleep(.2);result['cleaned']=api('combat').get('wallBlocks')==0
        (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--pid',required=True,type=int);a.add_argument('--output',type=__import__('pathlib').Path);args=a.parse_args();main(args.pid,args.output)
