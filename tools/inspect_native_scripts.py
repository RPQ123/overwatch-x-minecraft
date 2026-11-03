"""Bounded read-only script/variable inventory of the supplied offline client.

Layouts come from the user's local Prometheus source. Unknown values remain
unidentified; a matching integer is never claimed to be ammo or an attack.
"""
import argparse,json,struct
from observe_overwatch import ROOT,ResearchProcess,PoseReader
from stu_hash_names import HashNames

class ScriptReader(PoseReader):
    def stu_type(self,address):
        # Decode only the simple LEA-RAX/RET getter; never execute native code.
        vt=self.pointer(address);getter=self.pointer(vt+0x28);code=self.memory.read(getter,16)
        if code[:3]!=b'\x48\x8d\x05' or code[7]!=0xc3:return {'vtableRva':f'{vt-self.memory.base:x}'}
        info=getter+7+struct.unpack_from('<i',code,3)[0]
        name=self.unpack('<Q',info)[0];raw=self.memory.read(name,192).split(b'\0',1)[0]
        return {'name':raw.decode('ascii',errors='replace'),'hash':f'{self.unpack("<I",info+0x50)[0]:08x}'}

    def stu_list(self,address):
        list_ptr,flag=self.unpack('<QQ',address)
        if not list_ptr:return []
        a,b=self.unpack('<QQ',list_ptr);items,count=(a,b) if flag==1 else (b,a)
        if count>4096:raise ValueError('Graph node bound')
        return [p for p, in struct.iter_unpack('<Q',self.memory.read(items,count*8) if count else b'')]

    def graph_nodes(self,graph):
        # STUStatescriptGraph.m_nodes follows its 8-byte base + 0x48 STUGraph.
        nodes=[]
        for index,pointer in enumerate(self.stu_list(graph+0x50)):
            if not pointer:continue
            item={'index':index,**self.stu_type(pointer)}
            item.update(clientOnly=self.unpack('<B',pointer+0x75)[0],serverOnly=self.unpack('<B',pointer+0x76)[0])
            nodes.append(item)
        return nodes

    def vector(self,address,stride,limit=512):
        items,count,capacity=self.unpack('<Qii',address)
        if not 0<=count<=capacity<=limit:raise ValueError('Untrusted script list bounds')
        if count and not items:raise ValueError('Missing script list data')
        return self.memory.read(items,count*stride) if count else b''

    def varbag(self,address,depth=0,seen=None):
        seen=set() if seen is None else seen
        if not address or address in seen or depth>4:return []
        seen.add(address);result=[]
        if self.unpack('<Q',address)[0]-self.memory.base!=0x1607a90:return []
        # Sixteen 0x30-byte buckets, including an embedded first entry.
        for bucket in range(16):
            start=address+0xa0+bucket*0x30;items,count,capacity=self.unpack('<Qii',start)
            if not 0<=count<=capacity<=512:raise ValueError('Varbag bucket bounds')
            if not count:continue
            # Prometheus UI iterates arr_ptr; embedded storage may be that pointer.
            if not items:raise ValueError('Missing varbag entries')
            for rid,pointer in struct.iter_unpack('<QQ',self.memory.read(items,count*16)):
                if not pointer:continue
                kind=self.unpack('<Q',pointer)[0]-self.memory.base
                item={'rid':f'{rid:016x}','kindRva':f'{kind:x}'}
                if kind==0x1608248:
                    raw,_,value_type=self.unpack('<QII',pointer+0xa0)
                    item.update(type=value_type,raw=f'{raw:016x}')
                    if value_type==2:item['value']=struct.unpack('<i',struct.pack('<I',raw&0xffffffff))[0]
                    elif value_type==3:
                        value=struct.unpack('<f',struct.pack('<I',raw&0xffffffff))[0]
                        item['value']=value if abs(value)<1e30 else None
                    elif value_type==1:item['value']=bool(raw)
                elif kind==0x1607a90:item['children']=self.varbag(pointer,depth+1,seen)
                result.append(item)
                if len(result)>2048:raise ValueError('Varbag total bound')
        return result

    def sample(self):
        admin=self.pointer(self.memory.base+0x17b7f90);local_id=self.unpack('<I',admin+0x220)[0]
        table=self.memory.read(self.pointer(admin+0x10),65536)
        controller=self.entity(table,local_id);ref=self.component(controller,0x20);model_id=self.unpack('<I',ref+0x94)[0]
        model=self.entity(table,model_id);entities=[]
        for label,owner in [('controller',controller),('model',model)]:
            data={'label':label,'entityId':self.unpack('<I',owner+0x94)[0]}
            components=self.vector(owner+0x50,8,256)
            data['componentIds']=[self.unpack('<B',p+0x10)[0] for p, in struct.iter_unpack('<Q',components) if p and self.unpack('<Q',p+8)[0]==owner]
            try:comp=self.component(owner,0x23)
            except ValueError:entities.append(data);continue
            inner=comp+0xc0;scripts=[]
            for pointer, in struct.iter_unpack('<Q',self.vector(inner+0xf0,8)):
                if not pointer:continue
                script={'instance':self.unpack('<h',pointer+0x18)[0],'resourceId':f'{self.unpack("<Q",pointer+0x150)[0]:016x}',
                        'executionFlags':self.unpack('<I',pointer+0x258)[0]}
                try:
                    graph=self.unpack('<Q',pointer+0x160)[0];script['nodes']=self.graph_nodes(graph)
                    definitions=self.stu_list(graph+0x60);states=[]
                    for state, in struct.iter_unpack('<Q',self.vector(pointer+0xa0,8,4096)):
                        if not state:continue
                        index=self.unpack('<i',state+0x70)[0]
                        if not 0<=index<len(definitions):raise ValueError('Runtime state outside definitions')
                        definition=definitions[index]
                        if not definition:continue
                        states.append({'index':index,'flags':self.unpack('<I',state+0x40)[0],'clientOnly':self.unpack('<B',definition+0x75)[0],'serverOnly':self.unpack('<B',definition+0x76)[0]})
                    script['runtimeStates']=states;script['definedStates']=len(definitions)
                except (OSError,ValueError) as error:script['nodeError']=str(error)
                bag=self.unpack('<Q',pointer+0x98)[0]
                try:script['variables']=self.varbag(bag)
                except (OSError,ValueError) as error:script['variableError']=str(error)
                scripts.append(script)
            data['scripts']=scripts;data['tick']=self.unpack('<Q',inner+0x2d0)[0]
            try:data['entityVariables']=self.varbag(self.unpack('<Q',inner+0x2e0)[0])
            except (OSError,ValueError) as error:data['variableError']=str(error)
            entities.append(data)
        if self.pointer(self.memory.base+0x17b7f90)!=admin:raise ValueError('World changed')
        return {'pid':self.memory_pid,'memoryWrites':False,'nativeCalls':False,'ammoIdentified':False,'attackIdentified':False,'entities':entities}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);mode=parser.add_mutually_exclusive_group(required=True);mode.add_argument('--pid',type=int);mode.add_argument('--annotate',type=str,help='Annotate a recorded private snapshot without opening any process');parser.add_argument('--type-names',help='Optional lowercase CRC32-verified community KnownTypes.csv');parser.add_argument('--output',default='research/native-script-inventory.json');args=parser.parse_args()
    out=(ROOT/args.output).resolve()
    if ROOT/'research' not in out.parents:raise ValueError('Private inventory must stay in research')
    if args.annotate:
        source=(ROOT/args.annotate).resolve()
        if ROOT/'research' not in source.parents or source==out:raise ValueError('Annotate must preserve the original private snapshot')
        result=HashNames(args.type_names).annotate(json.loads(source.read_text(encoding='utf-8')))
        out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
        print(json.dumps({'path':str(out),**result['typeNameResolution']}));raise SystemExit(0)
    names=HashNames(args.type_names);process=ResearchProcess(args.pid)
    try:
        reader=ScriptReader(process);reader.memory_pid=args.pid;result=names.annotate(reader.sample())
        out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
        print(json.dumps({'path':str(out),'entities':[{ 'label':e['label'],'components':e['componentIds'],'scripts':len(e.get('scripts',[])),'variables':len(e.get('entityVariables',[])),'variableError':e.get('variableError')} for e in result['entities']]}))
    finally:process.close()
