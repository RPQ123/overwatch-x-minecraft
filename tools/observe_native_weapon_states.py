"""Read original-plugin weapon state timestamps, without installing another hook.

The existing plugin logs native state/action entry. Its map stores only the last
change per node: this observer is diagnostic and cannot promise lossless attacks.
It never sends input, changes variables, executes native functions or applies MC
damage. Projectile emission and ammo semantics need independent confirmation.
"""
import argparse,json,struct,time
from observe_overwatch import ROOT,ResearchProcess
from inspect_native_scripts import ScriptReader
from provided_plugin_symbols import provided_plugin
from native_map_snapshot import snapshot_map
from native_weapon_binding import WeaponBindingReader

VOLLEY_HASH='860ee5fc' # CRC32(STUStatescriptStateWeaponVolley), observed native graph.

def changed_records(previous,current):
    if previous is None:return [] # Initial state is a baseline, never a new attack.
    return [record for key,record in current.items() if previous.get(key)!=record]

class WeaponStates(ScriptReader):
    def __init__(self,process):
        super().__init__(process)
        module,image,pdb=provided_plugin(process)
        self.logger=module+image.symbol_rva(pdb.exact('statescript_logger::s_scriptStates'))
        self.logger_entry=module+image.symbol_rva(pdb.exact('statescript_logger::StateEntry_orig'))
        self.graph_cache={}
        self.bindings=WeaponBindingReader(process)

    def sample_weapon(self,require_volley=True,all_scripts=False):
        admin=self.pointer(self.memory.base+0x17b7f90);local_id=self.unpack('<I',admin+0x220)[0]
        table=self.memory.read(self.pointer(admin+0x10),65536);controller=self.entity(table,local_id)
        reference=self.component(controller,0x20);model_id=self.unpack('<I',reference+0x94)[0];model=self.entity(table,model_id)
        inner=self.component(model,0x23)+0xc0
        scripts={};used_graphs=set()
        for instance, in struct.iter_unpack('<Q',self.vector(inner+0xf0,8)):
            if not instance:continue
            graph=self.pointer(instance+0x160);resource=self.unpack('<Q',instance+0x150)[0];identity=(instance,graph,resource);used_graphs.add(identity)
            if identity not in self.graph_cache:
                nodes=self.graph_nodes(graph);self.graph_cache[identity]={'script':f'{resource:016x}','volleyNodes':[n['index'] for n in nodes if n.get('hash')==VOLLEY_HASH],'nodeCount':len(self.stu_list(graph+0x50))}
                definition=self.graph_cache[identity];definition['ammoOutputs']={}
                if definition['volleyNodes']:
                    pointers=self.stu_list(graph+0x50)
                    for node in definition['volleyNodes']:
                        try:definition['ammoOutputs'][str(node)]=self.bindings.ammo_output(pointers[node])
                        except (OSError,ValueError) as error:definition['ammoOutputs'][str(node)]={'bindingIdentified':False,'error':str(error)}
            definition=self.graph_cache[identity]
            if definition['volleyNodes'] or all_scripts:scripts[instance]=definition
        self.graph_cache={key:value for key,value in self.graph_cache.items() if key in used_graphs}
        if not scripts and require_volley:raise ValueError('No original native WeaponVolley graph on the local model')
        if not self.unpack('<Q',self.logger_entry)[0]:raise ValueError('Provided original logger has no state-entry trampoline')
        result={};variables={}
        for instance,inner_map in snapshot_map(self.memory,self.logger,'Q'):
            if instance not in scripts:continue
            script=scripts[instance];variables[script['script']]=self.varbag(self.unpack('<Q',instance+0x98)[0])
            for node,value in snapshot_map(self.memory,inner_map,'i',4096):
                timestamp,finished=self.unpack('<qB',value)
                if not 0<=node<script['nodeCount'] or timestamp<0 or finished>1:raise ValueError('Native logger record bounds')
                key=f'{instance:x}:{node}'
                result[key]={'instanceAddress':instance,'script':script['script'],'node':node,'nativeTick':timestamp,'finished':bool(finished),'weaponVolleyNode':node in script['volleyNodes']}
        if self.pointer(self.memory.base+0x17b7f90)!=admin or self.unpack('<I',admin+0x220)[0]!=local_id:raise ValueError('Local world/controller changed during read')
        return {'localId':local_id,'modelId':model_id,'records':result,'observedVariables':variables,'weaponScripts':list(scripts.values())}

def run(pid,seconds,output):
    process=ResearchProcess(pid);previous=None;previous_variables=None
    rows=[];samples=failures=changes=0;started=time.monotonic();last_error=''
    try:
        observer=WeaponStates(process)
        while time.monotonic()-started<seconds:
            try:
                current=observer.sample_weapon();events=changed_records(previous,current['records']);baseline=previous is None
                samples+=1;changes+=len(events)
                if len(rows)<10000 and (baseline or events or previous_variables!=current['observedVariables']):
                    rows.append({'elapsed':time.monotonic()-started,'baseline':baseline,'changes':events,**current})
                previous=current['records'];previous_variables=current['observedVariables']
            except (OSError,ValueError) as error:failures+=1;last_error=str(error)
            time.sleep(.02)
    finally:process.close()
    report={'pid':pid,'readOnly':True,'newHooksInstalled':False,'nativeCalls':False,'inputSent':False,'samples':samples,'readFailures':failures,'lastError':last_error,'observedNodeChanges':changes,'projectileEmissionVerified':False,'ammoIdentified':False,'losslessAttackChannel':False,'rows':rows}
    output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({key:value for key,value in report.items() if key!='rows'},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pid',type=int,required=True);parser.add_argument('--seconds',type=int,default=30);parser.add_argument('--output',default='research/native-weapon-state-observation.json');args=parser.parse_args()
    output=(ROOT/args.output).resolve()
    if ROOT/'research' not in output.parents or not 1<=args.seconds<=300:parser.error('Private research output and 1..300 seconds required')
    run(args.pid,args.seconds,output)
