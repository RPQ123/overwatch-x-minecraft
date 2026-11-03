"""Unaccepted private Wraith experiment; not part of the stable launch/acceptance suite."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,struct,time
from observe_overwatch import ROOT,ResearchProcess
from observe_native_weapon_states import WeaponStates
from calibrate_hero_actions import select
from calibrate_hero_roster import api,drive,report
from verify_genji_elimination_reset import post
from verify_native_motor import action

def snapshot(r):
    s=r.sample_weapon(False,True);script,graph,_=next(k for k in r.graph_cache if k[2]==0x0580000000000020);nodes=r.stu_list(graph+0x50);defs=r.stu_list(graph+0x60)
    def implementation(node):
        index=defs.index(nodes[node]);matches=[v for v, in struct.iter_unpack('<Q',r.vector(script+0xa0,8)) if v and r.unpack('<i',v+0x70)[0]==index]
        if len(matches)!=1:raise ValueError('Original state membership differs')
        return matches[0],index
    cooldown,_=implementation(19)
    if r.pointer(cooldown)!=r.memory.base+0x15d7c98:raise ValueError('Original cooldown implementation differs')
    rows={v['node']:v for v in s['records'].values() if v['script']=='0580000000000020'}
    return dict(model=s['modelId'],script=script,graph=graph,nodes=nodes,implementation=implementation,rows=rows,cooldown=r.unpack('<f',cooldown+0x150)[0])
def wait(r,node,active,seconds=5):
    start=time.monotonic()
    while True:
        s=snapshot(r);v=s['rows'].get(node)
        if v and (not v['finished'])==active:return s
        if time.monotonic()-start>seconds:raise ValueError('Native phase did not become '+str((node,active)))
        time.sleep(.025)
def view(s):return {k:v for k,v in s.items() if k not in ('nodes','implementation')}
def main(pid):
    d=dict(pid=pid,passed=False);path=ROOT/f'native-host/build/native-lifetime-lab-request-{pid}.bin';old=path.read_bytes() if path.exists() else None;payload=None;p=None
    try:
        body=report(ROOT/f'native-host/build/body-sync-{pid}.json')
        if not body.get('nativeLifetimeLab'):raise ValueError('Private lab unavailable')
        select(pid,'Genji');drive('focus','rel 0 -600','click 1280 720','sleep 1000','rel 0 600');select(pid,'Reaper');time.sleep(1)
        post('flight-open');time.sleep(.3)
        if api('combat').get('testError'):raise ValueError('Safe floor unavailable')
        drive('focus','key 0x75','sleep 350');d['walk']=action(['hold 0x57 400','sleep 150']);post('start');time.sleep(.2)
        if api('combat').get('testError'):raise ValueError('Temporary target unavailable')
        p=ResearchProcess(pid);r=WeaponStates(p);drive('focus','key 0x10','sleep 80');s=wait(r,2,True);state,index=s['implementation'](2);body=report(ROOT/f'native-host/build/body-sync-{pid}.json');native=report(ROOT/f'native-host/build/native-emissions-{pid}.json');thread=report(ROOT/f'native-host/build/weapon-gate-{pid}.json')['callbackThread'];seq=time.time_ns()
        payload=struct.pack('<8sII14Q4I',b'OWLIFE01',1,pid,native['creation'],seq,round(time.time()*1000),native['hostGeneration'],body['worldId'],r.pointer(p.base+0x17b7f90),s['model'],0x02e0000000000002,s['script'],s['graph'],s['nodes'][2],state,r.logger,s['rows'][2]['nativeTick'],2,index,thread,0)
        tmp=path.with_suffix('.tmp');tmp.write_bytes(payload);tmp.replace(path);d['begin']=view(wait(r,1,True));d['combatBefore']=api('combat')
        d['wraith']=action(['key 0x57 down','mdown 1280 720','sleep 300','mup','sleep 100','key 0x57 up','sleep 100']);d['combatDuring']=api('combat');d['end']=view(wait(r,1,False));time.sleep(.3)
        d['normal']=action(['hold 0x57 400','sleep 100']);drive('focus','click 1280 720','sleep 350');d['combatAfter']=api('combat');d['beforeRepeat']=view(snapshot(r));drive('focus','key 0x10','sleep 300');d['repeat']=view(snapshot(r));d['body']=report(ROOT/f'native-host/build/body-sync-{pid}.json')
        d['passed']=d['walk']['peakOriginalSpeed']>5 and d['wraith']['peakOriginalSpeed']>d['walk']['peakOriginalSpeed']*1.05 and abs(d['normal']['peakOriginalSpeed']-d['walk']['peakOriginalSpeed'])<.05
        d['passed'] &= d['combatBefore']['targetHealth']==20 and d['combatDuring']['targetHealth']==20 and d['combatAfter']['targetHealth']<20
        d['passed'] &= d['beforeRepeat']['cooldown']>0 and d['repeat']['rows'][2]['nativeTick']==d['beforeRepeat']['rows'][2]['nativeTick'] and d['body']['nativeLifetimeCalls']==body['nativeLifetimeCalls']+1 and not d['body']['failures']
    except Exception as e:d['error']=str(e)
    finally:
        if p:p.close()
        if payload is not None and path.exists() and path.read_bytes()==payload:
            if old is None:path.unlink()
            else:path.write_bytes(old)
        try:
            drive('focus','mup','key 0x57 up','key 0x10 up')
            if not api('health')['player']['flying']:drive('focus','key 0x75')
            post('cleanup');d['cleaned']=api('combat').get('wallBlocks')==0
        except Exception as e:d['cleanupError']=str(e);d['passed']=False
        try:post('cleanup')
        except Exception as e:d['fixtureCleanupError']=str(e);d['passed']=False
        out=ROOT/f'research/reaper-lifetime-motor-{pid}-{time.time_ns()}.json';out.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(path=str(out),**{k:d[k] for k in ('passed','error','cleaned','cleanupError') if k in d})))
    return d['passed']
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pid',required=True,type=int);a=p.parse_args();raise SystemExit(0 if main(a.pid) else 1)
