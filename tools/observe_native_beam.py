"""Read-only Winston beam calibration and native ammo/state observations.

The original ChaseVar's stored value is an interpolation baseline, not the live
ammo value. Read its declared output in the original variable bag instead.
This polling tool is evidence gathering, not a lossless attack/damage bridge.
"""
import argparse,json,struct,time
from observe_overwatch import ROOT,ResearchProcess
from observe_native_weapon_states import WeaponStates
from native_map_snapshot import snapshot_map

HERO=0x02e0000000000009
SCRIPT=0x05800000000000fe

class BeamReader(WeaponStates):
    def __init__(self,process):
        super().__init__(process)
        sample=self.sample_weapon()
        self.admin=self.pointer(process.base+0x17b7f90)
        self.local_id=sample['localId'];self.model_id=sample['modelId']
        table=process.read(self.pointer(self.admin+0x10),65536)
        self.controller=self.entity(table,self.local_id);self.model=self.entity(table,self.model_id)
        if self.unpack('<Q',self.component(self.controller,0x3f)+0x98)[0]!=HERO:
            raise ValueError('Original local hero is not Winston')
        matches=[key for key in self.graph_cache if key[2]==SCRIPT]
        if len(matches)!=1:raise ValueError('Expected one original Winston weapon script')
        self.instance,self.graph,_=matches[0];nodes=self.stu_list(self.graph+0x50)
        self.bag=self.pointer(self.instance+0x98)
        self.clock_address=self.pointer(self.instance+0x10)+0x2d0
        b=self.bindings
        def config(node,key):return self.pointer(b.field(nodes[node],key)[1])
        def variable(config_object,expected):
            path=b.dynamic_path(config_object)
            if path!=[expected]:raise ValueError('Original Winston dynamic path differs')
            matches=[]
            for bucket in range(16):
                for rid,value in struct.iter_unpack('<QQ',self.vector(self.bag+0xa0+bucket*0x30,16)):
                    if rid==int(expected,16):matches.append(value)
            if len(matches)!=1:raise ValueError('Original Winston variable binding differs')
            return matches[0]
        for index,kind in ((30,'498b421a'),(34,'970ec198'),(44,'619d9e95')):
            if self.stu_type(nodes[index]).get('hash')!=kind:raise ValueError('Original Winston node type differs')
        self.ammo=variable(config(34,0xec9f34a6),'0d80000000000035')
        self.radius=variable(config(30,0x71ef3ca4),'0d80000000000670')
        self.angle=variable(config(30,0x9d812041),'0d800000000000f3')
        modify=config(44,0x89174668)
        self.damage=self.pointer(b.field(modify,0xc43222bc)[1])
        self.rate=config(34,0x41430518);self.period=config(44,0xd525b22b)
        targets=b.dynamic_path(config(30,0xc86ea723))
        if targets!=b.dynamic_path(config(44,0xebda16f6)) or targets!=['0d800000000001d4']:
            raise ValueError('Original beam tracking and damage target paths differ')
        self.calibration=self.parameters()
        self.identity()

    def number(self,address):
        if self.pointer(address)!=self.memory.base+0x1608248:raise ValueError('Original numeric variable vtable differs')
        raw,_,kind=self.unpack('<QII',address+0xa0)
        if kind==2:return struct.unpack('<i',struct.pack('<I',raw&0xffffffff))[0]
        if kind==3:return struct.unpack('<f',struct.pack('<I',raw&0xffffffff))[0]
        raise ValueError('Original variable is not numeric')

    def parameters(self):
        b=self.bindings
        result={'damageAmount':b.literal_int(self.damage),'ammoRate':b.literal_int(self.rate),
                'damagePeriod':b.literal_int(self.period),'radius':self.number(self.radius),'angle':self.number(self.angle)}
        if result!={'damageAmount':60,'ammoRate':20,'damagePeriod':1,'radius':8,'angle':40}:
            raise ValueError('Original Winston calibration changed')
        return result

    def identity(self):
        if (self.pointer(self.memory.base+0x17b7f90)!=self.admin
            or self.unpack('<I',self.admin+0x220)[0]!=self.local_id
            or self.unpack('<I',self.controller+0x94)[0]!=self.local_id
            or self.unpack('<I',self.model+0x94)[0]!=self.model_id
            or self.unpack('<I',self.component(self.controller,0x20)+0x94)[0]!=self.model_id
            or self.unpack('<Q',self.component(self.controller,0x3f)+0x98)[0]!=HERO
            or self.pointer(self.pointer(self.pointer(self.instance+0x10)+0x450)+8)!=self.model
            or self.unpack('<Q',self.instance+0x150)[0]!=SCRIPT
            or self.pointer(self.instance+0x98)!=self.bag):
            raise ValueError('Native Winston owner/script changed')

    def sample_beam(self):
        self.identity();clock=self.unpack('<Q',self.clock_address)[0];ammo=self.number(self.ammo)
        if not 0<=ammo<=100:raise ValueError('Native ammo bounds')
        state=None
        for instance,inner in snapshot_map(self.memory,self.logger,'Q'):
            if instance!=self.instance:continue
            for node,value in snapshot_map(self.memory,inner,'i',4096):
                if node!=34:continue
                stamp,finished=self.unpack('<qB',value)
                if stamp<0 or stamp>clock or finished>1:raise ValueError('Native beam state bounds')
                state={'nativeTick':stamp,'finished':bool(finished)}
        self.identity()
        return {'modelId':self.model_id,'clock':clock,'ammo':ammo,'state':state}

def run(pid,seconds,output):
    process=ResearchProcess(pid);rows=[];last=None;failures=[];start=time.monotonic()
    try:
        reader=BeamReader(process)
        while time.monotonic()-start<seconds:
            try:
                current=reader.sample_beam()
                if current!=last:
                    rows.append({'wallMs':round(time.time()*1000),'baseline':last is None,**current})
                    last=current
            except (OSError,ValueError) as error:
                if len(failures)<32:failures.append(str(error))
            time.sleep(.01)
        report={'pid':pid,'readOnly':True,'memoryWrites':False,'nativeCalls':False,
                'losslessAttackChannel':False,'mcDamageSent':False,
                'calibration':reader.calibration,'rows':rows,'errors':failures}
        output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
        print(json.dumps({k:v for k,v in report.items() if k!='rows'}))
    finally:process.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pid',type=int,required=True)
    parser.add_argument('--seconds',type=int,default=20);parser.add_argument('--output',default='research/native-winston-beam.json')
    args=parser.parse_args();output=(ROOT/args.output).resolve()
    if not 1<=args.seconds<=60 or ROOT/'research' not in output.parents:parser.error('1..60 seconds and private research output required')
    run(args.pid,args.seconds,output)
