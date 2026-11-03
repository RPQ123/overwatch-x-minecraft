"""Read loaded original projectile prefab components through their asset entries."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,struct
from observe_overwatch import ROOT,ResearchProcess
from observe_native_weapon_states import WeaponStates
from calibrate_hero_actions import select,names
from inspect_native_impact import describe
from native_armory_binding import config_resources

def resources(r,node):
    ref=r.pointer(r.bindings.field(node,0xf7329268)[1]);out=[]
    storage,flag=r.unpack('<QQ',ref+8)
    if storage:
        if flag not in (1,2):raise ValueError('Projectile asset list storage')
        a,b=r.unpack('<QQ',storage);items,n=(a,b) if flag==1 else (b,a)
        if not 0<=n<=64:raise ValueError('Projectile asset count')
        for j in range(n):
            _,rid=r.unpack('<QQ',items+j*16)
            if rid>>48==0x0400:out.append((rid,items+j*16+8,True,ref))
    config=r.unpack('<Q',ref+24)[0]
    if config:out.extend((rid,at,False,ref) for rid,at in config_resources(r.bindings,config))
    return list({(rid,at):(rid,at,array,ref) for rid,at,array,ref in out}.values())

def inspect(pid,heroes):
    result=[];known=names()
    for hero in heroes:
        select(pid,hero);p=ResearchProcess(pid);r=WeaponStates(p);r.sample_weapon(False,True);records=[];seen=set()
        try:
            for (script,graph,rid),meta in r.graph_cache.items():
                nodes=r.stu_list(graph+0x50)
                for index in meta['volleyNodes']:
                    try:variants=resources(r,nodes[index])
                    except (OSError,ValueError):continue
                    for resource,address,array,ref in variants:
                        if resource in seen:continue
                        seen.add(resource);record=dict(resource=hex(resource),script=hex(rid),node=index,array=array,components=[]);records.append(record)
                        try:
                            entry=r.pointer(address-8)&~63;definition=r.pointer(entry)
                            if r.bindings.metadata(definition)[1]!=0xec23fffd:raise ValueError('Not an original entity definition')
                            storage,flag=r.unpack('<QQ',definition+0x28)
                            if flag!=2:raise ValueError('Prefab component map differs')
                            buckets,ends,items=r.unpack('<i4xQQ',storage)
                            if not 0<buckets<=256:raise ValueError('Prefab component bucket bound')
                            n=r.unpack('<i',ends+4*(buckets-1))[0]
                            if not 0<n<=256:raise ValueError('Prefab component count')
                            for kind,obj in struct.iter_unpack('<I4xQ',p.read(items,n*16)):
                                record['components'].append(dict(kind=hex(kind),name=known.get(f'{kind:08x}'),definition=describe(r.bindings,obj)))
                            print(hero,hex(resource),[(c['kind'],c['name']) for c in record['components']],flush=True)
                        except (OSError,ValueError) as e:record['error']=str(e)
            result.append(dict(hero=hero,records=records))
            (ROOT/'research/native-projectile-prefabs-20261019.json').write_text(json.dumps(result,indent=2)+'\n')
        finally:p.close()

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--pid',type=int,required=True);a.add_argument('--heroes',nargs='+',required=True);args=a.parse_args();inspect(args.pid,args.heroes)
