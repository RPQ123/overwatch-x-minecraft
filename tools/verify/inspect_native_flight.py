"""Bounded, read-only Pharah movement graph calibration from the guarded client."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,re,zlib,os
from pathlib import Path
from observe_overwatch import ROOT,ResearchProcess
from observe_native_weapon_states import WeaponStates
from inspect_native_impact import describe

def dictionaries():
    types={};fields={}
    source=Path(os.environ.get('OWMC_OWLIB_SOURCE',str(ROOT/'tools/OWLib-source')))
    types_directory=source/'TankLib/STU/Types'
    if not types_directory.is_dir():
        raise FileNotFoundError('Set OWMC_OWLIB_SOURCE to a local OWLib source tree')
    for path in types_directory.glob('*.cs'):
        source=path.read_text(encoding='utf-8-sig')
        for name in re.findall(r'public (?:abstract )?class (\w+)',source):types[f'{zlib.crc32(name.lower().encode()):08x}']=name
        for key,name in re.findall(r'\[STUField\(0x([0-9A-Fa-f]+)[^\n]*\n\s*public \S+ (\w+)',source):fields[key.lower().zfill(8)]=name
    return types,fields

def annotate(obj,types,fields):
    if isinstance(obj,dict):
        if 'type' in obj:obj['typeName']=types.get(obj['type'])
        if 'hash' in obj:obj['name']=fields.get(obj['hash'])
        for value in list(obj.values()):annotate(value,types,fields)
    elif isinstance(obj,list):
        for value in obj:annotate(value,types,fields)

def inspect(pid):
    p=ResearchProcess(pid)
    try:
        r=WeaponStates(p);sample=r.sample_weapon(require_volley=False,all_scripts=True);out=[]
        for (instance,graph,resource),definition in r.graph_cache.items():
            if resource not in (0x0580000000000025,0x0580000000000027):continue
            nodes=r.stu_list(graph+0x50)
            out.append(dict(resource=f'{resource:016x}',instance=instance,graph=graph,variables=sample['observedVariables'].get(f'{resource:016x}'),nodes=[dict(index=i,definition=describe(r.bindings,node)) for i,node in enumerate(nodes)]))
        types,fields=dictionaries();annotate(out,types,fields)
        path=ROOT/f'research/native-flight-fields-{pid}.json';path.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n');print(path)
    finally:p.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--pid',required=True,type=int);inspect(parser.parse_args().pid)
