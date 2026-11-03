"""Read original Genji ability state entries; never treats a key as a hit."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,struct,time
from observe_overwatch import ROOT,ResearchProcess
from observe_native_weapon_states import WeaponStates
from native_map_snapshot import snapshot_map
from observe_native_combat import CombatReader

def sample(reader):
    weapon=reader.sample_weapon()
    found=[key for key in reader.graph_cache if key[2]==0x05800000000001db]
    if len(found)!=1:raise ValueError('Expected one original Genji MoveTo/TrackTargets ability graph')
    instance,graph,resource=found[0]
    records=[]
    for address,inner in snapshot_map(reader.memory,reader.logger,'Q'):
        if address!=instance:continue
        for node,value in snapshot_map(reader.memory,inner,'i',4096):
            tick,finished=reader.unpack('<qB',value)
            if not 0<=node<58 or tick<0 or finished>1:raise ValueError('Ability logger bounds')
            records.append({'node':node,'nativeTick':tick,'finished':bool(finished)})
    return {'localId':weapon['localId'],'modelId':weapon['modelId'],'resource':f'{resource:016x}',
            'flags':reader.unpack('<I',instance+0x258)[0],'entries':sorted(records,key=lambda x:x['node']),
            'variables':reader.varbag(reader.pointer(instance+0x98))}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pid',type=int,required=True);parser.add_argument('--seconds',type=int,default=40);args=parser.parse_args()
    if not 1<=args.seconds<=120:parser.error('1..120 seconds')
    process=ResearchProcess(args.pid);reader=WeaponStates(process);commands=CombatReader(process)
    rows=[];prior=None;errors=[];started=time.monotonic();out=ROOT/f'research/native-ability-{args.pid}.json'
    try:
        while time.monotonic()-started<args.seconds:
            try:
                current=sample(reader);signature=json.dumps(current,sort_keys=True)
                if signature!=prior:
                    current['buttons']=commands.sample()['currentButtons'];rows.append({'wallMs':round(time.time()*1000),'elapsed':time.monotonic()-started,**current});prior=signature
                    temp=out.with_suffix('.tmp');temp.write_text(json.dumps({'pid':args.pid,'readOnly':True,'rows':rows,'errors':errors},indent=2)+'\n',encoding='utf-8');temp.replace(out)
            except (OSError,ValueError) as error:
                if len(errors)<30:errors.append(str(error))
            time.sleep(.02)
    finally:process.close()
    print(json.dumps({'path':str(out),'changes':len(rows),'errors':errors}))
