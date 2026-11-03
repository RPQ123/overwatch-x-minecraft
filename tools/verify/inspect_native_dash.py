"""Read declared original Genji dash parameters; no native calls or writes."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json
from observe_overwatch import ROOT,ResearchProcess
from observe_native_weapon_states import WeaponStates
from stu_hash_names import HashNames

def inspect(process):
    r=WeaponStates(process);r.sample_weapon()
    names=HashNames(ROOT/'research/owlib-prehash-reference/KnownFields.csv');types=HashNames(ROOT/'research/owlib-prehash-reference/KnownTypes.csv')
    instance,graph,_=next(key for key in r.graph_cache if key[2]==0x05800000000001db)
    def fields(obj):
        info,kind,size=r.bindings.metadata(obj);out=[];seen=set()
        while info:
            if info in seen or len(seen)>32:raise ValueError('metadata cycle')
            seen.add(info);parent,args=r.unpack('<QQ',info+0x20);count=r.unpack('<i',info+0x54)[0]
            if not 0<=count<=512:raise ValueError('metadata count')
            for i in range(count):
                key,off,constraint=r.unpack('<IiQ',args+i*0xa0+8)
                if not 8<=off<=size-8:continue
                try:category=r.bindings.constraint_identity(constraint)>>32
                except (OSError,ValueError):continue
                row={'hash':f'{key:08x}','name':names.get(key),'offset':off,'category':category,'raw':process.read(obj+off,8).hex()}
                if category==2:
                    try:
                        child=r.pointer(obj+off);ci,ck,cs=r.bindings.metadata(child);row['childType']=types.get(ck) or f'{ck:08x}'
                        if row['childType']=='STUConfigVarDynamic':row['path']=r.bindings.dynamic_path(child)
                        elif cs<=32:row['valueRaw']=process.read(child,min(cs,32)).hex()
                    except (OSError,ValueError):pass
                out.append(row)
            info=parent
        return out
    nodes=r.stu_list(graph+0x50)
    return {'pid':process.memory_pid if hasattr(process,'memory_pid') else None,'readOnly':True,'nodes':{str(i):fields(nodes[i]) for i in [5,6,10,26,54]},'variables':r.varbag(r.pointer(instance+0x98))}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pid',type=int,required=True);args=parser.parse_args();p=ResearchProcess(args.pid)
    try:
        result=inspect(p);(ROOT/f'research/native-dash-parameters-{args.pid}.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        for node,rows in result['nodes'].items():
            for row in rows:
                if row.get('childType') and any(t in (row.get('name') or '').lower() for t in ['speed','distance','damage','duration','time','amount','movement']):print(node,row)
        print('variables',result['variables'])
    finally:p.close()
