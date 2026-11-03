"""Actual native skill overlap probes, preserve the failing native pawn intact.

Only disposable MC fixtures and explicit lab Q charge grants are used. Native
states, ammo, entity variables, factories and actual MC damage are independent
observations. A failed case stops the sequence before another hero is selected.
"""
import argparse,json,subprocess,time,struct
from pathlib import Path
from calibrate_hero_actions import select
from calibrate_hero_roster import api,drive,report
from verify_genji_elimination_reset import post
from verify_native_light_angles import point
from observe_overwatch import ROOT,ResearchProcess
from observe_native_weapon_states import WeaponStates
from native_charge import grant_for_test

CASES=[('recall',['key 0x45']),('pulse-recall',['key 0x51','sleep 60','key 0x45']),
       ('pulse-melee',['key 0x51','sleep 60','key 0x56']),('pulse-reload',['key 0x51','sleep 60','key 0x52']),
       ('pulse-blink',['key 0x51','sleep 60','key 0x10']),('recall-reload',['key 0x45','sleep 60','key 0x52']),
       ('recall-melee',['key 0x45','sleep 60','key 0x56']),('recall-pulse',['key 0x45','sleep 60','key 0x51'])]

def capture(pid,detail=False):
    p=ResearchProcess(pid)
    try:
        r=WeaponStates(p);s=r.sample_weapon(False,True);a=r.pointer(p.base+0x17b7f90);table=p.read(r.pointer(a+16),65536);model=r.entity(table,s['modelId']);bag=r.pointer(r.component(model,0x23)+0xc0+0x2e0)
        entity=r.varbag(bag);out=dict(modelId=s['modelId'],states=s,entityVariables=entity)
        if detail:
            out['graphs']=[dict(instance=k[0],graph=k[1],script=f'{k[2]:016x}',nodes=r.graph_nodes(k[1])) for k in r.graph_cache]
        return out
    finally:p.close()

def main(pid,folder,cycles):
    folder.mkdir(parents=True,exist_ok=False);out=dict(pid=pid,passed=False,explicitLabQGrants=True,rows=[])
    def save():(folder/'result.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
    try:
        assert api('health')['worldName'].startswith('Overwatch Twilight Switch ')
        for cycle in range(cycles):
            for label,commands in CASES:
                select(pid,'Genji');select(pid,'Tracer');point(180,0);post('flight-open');time.sleep(.25)
                # History builds from actual server samples. Fixture flight
                # prevents cleanup of the temporary lane from causing a fall.
                time.sleep(3.2);p=ResearchProcess(pid)
                try:grant=grant_for_test(p,pid) if 'pulse' in label else None
                finally:p.close()
                row=dict(cycle=cycle,case=label,grant=grant,before=capture(pid),combatBefore=api('combat'));out['rows'].append(row);save()
                drive('focus',*commands,'sleep 3200');row['afterSkill']=capture(pid);row['combatAfterSkill']=api('combat');point(180,0);post('melee');time.sleep(.2)
                row['beforeFire']=report(ROOT/f'native-host/build/native-emissions-{pid}.json');drive('focus','mdown 1280 720','sleep 180','mup','sleep 450');row['combatAfterFire']=api('combat');row['afterFire']=capture(pid)
                row['afterEmission']=report(ROOT/f'native-host/build/native-emissions-{pid}.json');row['passed']=row['combatAfterFire'].get('targetHealth',20)<20
                if not row['passed']:
                    row['failureSnapshot']=capture(pid,True);subprocess.run(['um','win','shot','--exe','GameClientApp.patched.exe',str(folder/f'failed-{cycle}-{label}.png'),'--scale','.33'],cwd=ROOT,capture_output=True,check=True);save();raise AssertionError('Original primary failed after '+label)
                post('cleanup');save();print(json.dumps(dict(cycle=cycle,case=label,passed=True,health=row['combatAfterFire']['targetHealth'])),flush=True)
        out['passed']=True
    except Exception as e:out['error']=repr(e)
    finally:
        try:drive('mup');post('cleanup');out['cleaned']=True
        except Exception as e:out['cleanupError']=repr(e)
        save();print(json.dumps({k:out.get(k) for k in ('passed','error','cleaned')}),flush=True)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--pid',type=int,required=True);a.add_argument('--output',type=Path,required=True);a.add_argument('--cycles',type=int,default=2);v=a.parse_args();main(v.pid,v.output,v.cycles)
