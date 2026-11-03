"""Observe original Tank factory ownership; never synthesize an attack.

Uses the existing single emission owner and an explicit diagnostic meter grant.
The result remains a diagnostic, separate from cannon damage acceptance.
"""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import time

import psutil

from observe_overwatch import ROOT, ResearchProcess
from observe_native_weapon_states import WeaponStates
from calibrate_hero_actions import select, record_action, names
from calibrate_hero_roster import api, report, drive
from native_charge import grant_for_test
from verify_genji_elimination_reset import post
from verify_native_light_angles import point


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True)+'\n', encoding='utf-8')


def backup(folder):
    files = [ROOT/'passthrough-settings.json', ROOT/'guest-passthrough-client/options.txt']
    files += list((ROOT/'guest-passthrough-client/config').glob('*'))
    files += list((ROOT/'guest-passthrough-client/mods').glob('owmcguest*.jar'))
    world = api('health')['worldName']
    files += [ROOT/'guest-passthrough-client/saves'/world/'level.dat']
    rows=[]
    for file in files:
        if not file.is_file():
            continue
        target=folder/'backup'/file.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file, target)
        rows.append(dict(path=str(file), backup=str(target), sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
    save(folder/'backup.json', rows)


def current_scripts(reader):
    sample=reader.sample_weapon(require_volley=False, all_scripts=True)
    rows=[]
    for (instance, graph, resource), definition in reader.graph_cache.items():
        rows.append(dict(instance=instance, graph=graph, resource=resource,
                         flags=reader.unpack('<I',instance+0x258)[0], **definition))
    return dict(sample=sample, scripts=rows)


def run(pid, folder):
    folder.mkdir(parents=True,exist_ok=True)
    result=dict(pid=pid, created=psutil.Process(pid).create_time(), passed=False,
                explicitLabGrant=True, inputAttackSynthesis=False, newHooks=False,
                cannonDamageAccepted=False)
    process=ResearchProcess(pid)
    try:
        health=api('health')
        if not health['worldName'].startswith('Overwatch Twilight Switch '):
            raise ValueError('Use the isolated mod-pinned Switch lab')
        result['backup']=backup(folder)
        result['hero']=select(pid,'Bastion')
        point(180,0)
        post('flight-open');time.sleep(.3)
        post('start');time.sleep(.2)
        reader=WeaponStates(process)
        result['initial']=current_scripts(reader)
        result['gateBefore']=report(ROOT/f'native-host/build/weapon-gate-{pid}.json')
        result['emissionBefore']=report(ROOT/f'native-host/build/native-emissions-{pid}.json')
        result['combatBefore']=api('combat')
        result['grant']=grant_for_test(process,pid)
        result['action']=record_action(pid,reader,'tank-primary',
            ['key 0x51','sleep 1900','mdown 1280 720','sleep 650','mup','sleep 700'],names())
        result['after']=current_scripts(reader)
        result['gateAfter']=report(ROOT/f'native-host/build/weapon-gate-{pid}.json')
        result['emissionAfter']=report(ROOT/f'native-host/build/native-emissions-{pid}.json')
        result['combatAfter']=api('combat')
        resource=0x04000000000003ce
        result['tankFactories']=[r for r in result['action']['factoryObservations'] if r.get('resource')==resource]
        result['factoryCallsDelta']=result['emissionAfter'].get('factoryCalls',0)-result['emissionBefore'].get('factoryCalls',0)
        result['gateFilteredDelta']=result['gateAfter'].get('filtered',0)-result['gateBefore'].get('filtered',0)
        result['passed']=bool(result['tankFactories'])
        subprocess.run(['um','win','shot','--exe','GameClientApp.patched.exe',str(folder/'tank.png'),'--scale','.33'],cwd=ROOT,capture_output=True,check=True,timeout=15)
    except Exception as error:
        result['error']=str(error)
    finally:
        process.close()
        try:
            drive('mup')
            select(pid,'Genji')
            post('cleanup')
            time.sleep(.25)
            result['cleaned']=not api('combat').get('targetHealth') and api('combat').get('wallBlocks',0)==0
        except Exception as error:
            result['cleanupError']=str(error)
        save(folder/'result.json',result)
        print(json.dumps({k:result.get(k) for k in ('pid','passed','error','factoryCallsDelta','gateFilteredDelta','cleaned','cleanupError')}),flush=True)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid',required=True,type=int)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    folder=(ROOT/args.output).resolve()
    if ROOT/'research' not in folder.parents:
        parser.error('Use private research output')
    raise SystemExit(0 if run(args.pid,folder)['passed'] else 1)
