"""Private original StartStopState notification experiment; never enabled in normal launch."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,struct,time
from observe_overwatch import ROOT,ResearchProcess
from observe_native_weapon_states import WeaponStates,changed_records
from calibrate_hero_actions import select
from calibrate_hero_roster import drive,report,api
from provided_plugin_symbols import provided_plugin

def main(pid):
    path=ROOT/f'native-host/build/native-lifetime-lab-request-{pid}.bin';old=path.read_bytes() if path.exists() else None;payload=None
    result=dict(pid=pid,privateExperiment=True,passed=False)
    try:
        body=report(ROOT/f'native-host/build/body-sync-{pid}.json')
        if not body.get('nativeLifetimeLab') or not body.get('enabled') or body.get('failures'):raise ValueError('Private lifetime lab is not enabled/healthy')
        select(pid,'Genji');drive('focus','rel 0 -600','click 1280 720','sleep 1200','rel 0 600');time.sleep(.3)
        thread=report(ROOT/f'native-host/build/weapon-gate-{pid}.json')['callbackThread']
        if not thread:raise ValueError('Original callback owner thread is not established')
        result['model']=select(pid,'Reaper')['modelId'];time.sleep(.8)
        p=ResearchProcess(pid)
        try:
            module,image,pdb=provided_plugin(p);rva,prefix=image.function_prefix(pdb.exact('?StartStopState@StatescriptInstance@@QEAAXH_N@Z'))
            if rva!=0x7acd0 or p.read(module+rva,32)!=prefix:raise ValueError('Original lifetime helper code differs')
            r=WeaponStates(p);drive('focus','key 0x10','sleep 100');s=r.sample_weapon(False,True)
            row=next(v for v in s['records'].values() if v['script']=='0580000000000020' and v['node']==2 and not v['finished']);script=row['instanceAddress'];graph=r.pointer(script+0x160);definition=r.stu_list(graph+0x50)[2];stateIndex=r.stu_list(graph+0x60).index(definition)
            state=next(v for v, in struct.iter_unpack('<Q',r.vector(script+0xa0,8)) if v and r.unpack('<i',v+0x70)[0]==stateIndex)
            native=report(ROOT/f'native-host/build/native-emissions-{pid}.json');body=report(ROOT/f'native-host/build/body-sync-{pid}.json');seq=time.time_ns()
            payload=struct.pack('<8sII14Q4I',b'OWLIFE01',1,pid,native['creation'],seq,round(time.time()*1000),native['hostGeneration'],body['worldId'],r.pointer(p.base+0x17b7f90),s['modelId'],0x02e0000000000002,script,graph,definition,state,r.logger,row['nativeTick'],2,stateIndex,thread,0)
            if len(payload)!=144:raise AssertionError('Lifetime lab wire size')
            result['before']=dict(node=row,stateFlags=r.unpack('<I',state+0x40)[0],body=body,player=api('health')['player']);temp=path.with_suffix('.tmp');temp.write_bytes(payload);temp.replace(path)
            previous=s['records'];start=time.monotonic();changes=[];errors=[]
            while time.monotonic()-start<5.2:
                try:
                    snap=r.sample_weapon(False,True);events=[v for v in changed_records(previous,snap['records']) if v['script']=='0580000000000020'];previous=snap['records']
                    if events:changes.append(dict(elapsed=time.monotonic()-start,changes=events))
                except (OSError,ValueError) as e:errors.append(str(e))
                time.sleep(.025)
            result.update(changes=changes,errors=errors,body=report(ROOT/f'native-host/build/body-sync-{pid}.json'),player=api('health')['player'],combat=api('combat'))
            events=[v for t in changes for v in t['changes']];result['physicalBegan']=any(v['node']==5 and not v['finished'] for v in events);result['physicalEnded']=any(v['node']==5 and v['finished'] for v in events)
            result['passed']=result['physicalBegan'] and result['physicalEnded'] and not errors and result['body']['nativeLifetimeCalls']==body['nativeLifetimeCalls']+1 and result['body']['nativeLifetimeSequence']==seq and not result['body']['failures']
        finally:p.close()
    except Exception as e:result['error']=str(e)
    finally:
        if payload is not None and path.exists() and path.read_bytes()==payload:
            if old is None:path.unlink()
            else:path.write_bytes(old)
        out=ROOT/f'research/reaper-lifetime-{pid}-{time.time_ns()}.json';out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(path=str(out),**{k:result[k] for k in ('passed','physicalBegan','physicalEnded','error') if k in result})))
    return result['passed']
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pid',type=int,required=True);a=p.parse_args();raise SystemExit(0 if main(a.pid) else 1)
