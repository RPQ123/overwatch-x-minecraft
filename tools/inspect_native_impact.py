"""Read bounded declared native Volley fields for offline calibration only."""
import argparse,json,struct
from observe_overwatch import ROOT,ResearchProcess
from observe_native_weapon_states import WeaponStates

def describe(r,obj,depth=0,seen=None):
    seen=set() if seen is None else seen
    if obj in seen:return {'cycle':hex(obj)}
    seen=seen|{obj};info,kind,size=r.metadata(obj)
    out={'address':obj,'type':f'{kind:08x}','size':size,'fields':[]}
    if kind==0x3ae7427e:out['literal']=r.literal_int(obj)
    if kind==0xf8cc195d:out['path']=r.dynamic_path(obj)
    if kind==0x7b13a0d4:out['literal']=r.unpack('<f',obj+16)[0]
    if kind==0xec502a81:
        try:out['literal']=r.literal_float_expression(obj)
        except ValueError as e:out['expressionError']=str(e)
    visited=set()
    while info and info not in visited and len(visited)<32:
        visited.add(info);parent,args=r.unpack('<QQ',info+0x20);count=r.unpack('<i',info+0x54)[0]
        if not 0<=count<=512:raise ValueError('argument bounds')
        for i in range(count):
            key,offset,constraint=r.unpack('<IiQ',args+i*0xa0+8)
            if not 8<=offset<size or not constraint:continue
            f={'hash':f'{key:08x}','offset':offset}
            try:
                identity=r.constraint_identity(constraint);category,declared=identity>>32,identity&0xffffffff
                f.update(category=category,declared=f'{declared:08x}')
                if category==2 and offset<=size-8:
                    ptr=r.unpack('<Q',obj+offset)[0];f['pointer']=ptr
                    if ptr and depth<3:f['object']=describe(r,ptr,depth+1,seen)
                elif category==0 and offset<=size-4:
                    f['raw']=r.memory.read(obj+offset,min(8,size-offset)).hex()
                    if declared==0x8fa75a30:f['float']=r.unpack('<f',obj+offset)[0]
                    elif declared==0x954a3bab:f['int']=r.unpack('<i',obj+offset)[0]
            except (OSError,ValueError) as e:f['error']=str(e)
            out['fields'].append(f)
        info=parent
    return out

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pid',type=int,required=True);args=parser.parse_args()
    p=ResearchProcess(args.pid)
    try:
        r=WeaponStates(p);sample=r.sample_weapon(require_volley=False);out=[]
        for (instance,graph,resource),definition in r.graph_cache.items():
            nodes=r.stu_list(graph+0x50)
            for index in definition['volleyNodes']:
                out.append({'script':f'{resource:016x}','instance':instance,'node':index,'definition':describe(r.bindings,nodes[index])})
        path=ROOT/f'research/impact-fields-{args.pid}.json';path.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n');print(path)
    finally:p.close()

if __name__=='__main__':main()
