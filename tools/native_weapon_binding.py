"""Read native Volley ammo and impact-damage bindings through declared reflection.

Offsets come from the supplied plugin's STUInfo/ArgumentInfo/ConfigVarDynamic
layouts. No config evaluator or native getter is executed. Only measured constant
or metadata-backed constraint getters and LEA/RET metadata getters are decoded.
"""
import struct
from observe_overwatch import PoseReader

VOLLEY=0x860ee5fc
DYNAMIC=0xf8cc195d
OUT_AMMO=0x39d89271

def constant_return(code):
    if len(code)>=11 and code[:2]==b'\x48\xb8' and code[10]==0xc3:return struct.unpack_from('<Q',code,2)[0]
    if len(code)>=6 and code[0]==0xb8 and code[5]==0xc3:return struct.unpack_from('<I',code,1)[0]
    raise ValueError('Constraint getter is not a measured constant return')

class WeaponBindingReader(PoseReader):
    def constraint_identity(self,constraint):
        getter=self.pointer(self.pointer(constraint)+0x30);code=self.memory.read(getter,32)
        # Native primitive constraints return their declared primitive hash.
        if code[:4]==bytes.fromhex('8b4128c3'):
            return self.unpack('<I',constraint+0x28)[0]
        # Beta 0.8.0.24919: mov rax,[rcx+28h]; mov rcx,category;
        # mov eax,[rax+50h]; or rax,rcx; ret. Decode reads, never execute it.
        if code[:6]==bytes.fromhex('488b412848b9') and code[14:21]==bytes.fromhex('8b4050480bc1c3'):
            category=self.unpack('<Q',getter+6)[0]
            if category&0xffffffff or category>>32 not in range(14):raise ValueError('Uncalibrated constraint category')
            info=self.pointer(constraint+0x28);size=self.unpack('<i',info+0x5c)[0]
            if not 8<=size<=65536:raise ValueError('Constraint metadata size bounds')
            return category|self.unpack('<I',info+0x50)[0]
        return constant_return(code)

    def metadata(self,instance):
        getter=self.pointer(self.pointer(instance)+0x28);code=self.memory.read(getter,16)
        if code[:3]!=b'\x48\x8d\x05' or code[7]!=0xc3:raise ValueError('Unsupported STU metadata getter')
        info=getter+7+struct.unpack_from('<i',code,3)[0]
        kind=self.unpack('<I',info+0x50)[0];size=self.unpack('<i',info+0x5c)[0]
        if not 8<=size<=65536:raise ValueError('STU instance size bounds')
        return info,kind,size

    def field(self,instance,wanted):
        info,kind,size=self.metadata(instance);visited=set()
        while info:
            if info in visited or len(visited)>=32:raise ValueError('STU inheritance cycle')
            visited.add(info);parent,arguments=self.unpack('<QQ',info+0x20);count=self.unpack('<i',info+0x54)[0]
            if not 0<=count<=512:raise ValueError('STU argument count bounds')
            for index in range(count):
                key,offset,constraint=self.unpack('<IiQ',arguments+index*0xa0+8)
                if key!=wanted:continue
                if not 8<=offset<=size-8 or offset%8 or not constraint:raise ValueError('STU field offset/constraint bounds')
                identity=self.constraint_identity(constraint)
                return kind,instance+offset,identity>>32,identity&0xffffffff
            info=parent
        raise ValueError('Declared ammo output is absent from this native type')

    def dynamic_path(self,dynamic):
        _,actual_type,size=self.metadata(dynamic)
        if actual_type!=DYNAMIC or size<0x20:raise ValueError('Value is not a calibrated ConfigVarDynamic')
        storage,flag=self.unpack('<QQ',dynamic+0x10)
        if not storage:raise ValueError('Dynamic config path is absent')
        first,second=self.unpack('<QQ',storage);items,count=(first,second) if flag==1 else (second,first)
        if not 1<=count<=32 or not items:raise ValueError('Dynamic config path bounds')
        path=[rid for _,rid in struct.iter_unpack('<QQ',self.memory.read(items,count*16))]
        if not all(path):raise ValueError('Dynamic config path has an empty resource identifier')
        return [f'{rid:016x}' for rid in path]

    def ammo_output(self,volley):
        kind,address,category,declared_type=self.field(volley,OUT_AMMO)
        if kind!=VOLLEY or category!=2 or declared_type!=DYNAMIC:raise ValueError('Not a declared native Volley -> dynamic ammo output')
        path=self.dynamic_path(self.pointer(address))
        return {'bindingIdentified':True,'fieldHash':f'{OUT_AMMO:08x}','declaredField':'m_out_Ammo','configTypeHash':f'{DYNAMIC:08x}',
                'resourcePath':path,'nativeCalls':False,'ammoBehaviorVerified':False}

    def impact_damage(self,volley):
        # Measured beta metadata, each link also checked against its declared
        # field/type. No hard-coded object offsets or config evaluator calls.
        obj=volley
        for owner,key,declared,actual in ((VOLLEY,0x3d131607,0x4ef1dd7e,0x4ef1dd7e),
                (0x4ef1dd7e,0x89174668,0x06a06f4e,0x06a06f4e),
                (0x06a06f4e,0xc43222bc,0xbfd9aadd,None)):
            kind,address,category,target=self.field(obj,key)
            if kind!=owner or category!=2 or target!=declared:raise ValueError('Uncalibrated native projectile impact damage link')
            obj=self.pointer(address)
            if actual is not None and self.metadata(obj)[1]!=actual:raise ValueError('Native impact damage object type differs')
        result={'bindingIdentified':True,'fieldChain':['projectileImpact','m_modifyHealth','m_amount'],
                'unit':'overwatch-hp','nativeCalls':False,'hitBehaviorVerified':False}
        kind=self.metadata(obj)[1]
        if kind==DYNAMIC:result['resourcePath']=self.dynamic_path(obj)
        elif kind==0x3ae7427e:
            result.update(configType='STUConfigVarInt',value=self.literal_int(obj),valueAddress=obj)
        elif kind==0xec502a81:
            try:result.update(self.literal_float_expression(obj))
            except ValueError:result.update(self.equal_branch_float_expression(obj))
        elif kind==0xcc3a08f4:
            result.update(self.pure_product_expression(obj))
        elif kind==0x7b13a0d4:
            owner,address,category,primitive=self.field(obj,0x5180e750)
            if (owner,category,primitive)!=(kind,0,0x8fa75a30):raise ValueError('Literal float declaration differs')
            result.update(configType='STUConfigVarFloat',value=self.unpack('<f',address)[0],valueAddress=obj)
        else:raise ValueError('Native impact amount is not a calibrated dynamic or integer config')
        return result

    def literal_float_expression(self,obj):
        # Measured beta expression: opcode70 loads a float constant; opcode0
        # returns it. Reject operators/dynamics rather than guessing evaluation.
        if self.metadata(obj)[1]!=0xec502a81:raise ValueError('Not the measured float expression type')
        def array(at,stride):
            storage,flag=self.unpack('<QQ',at)
            if not storage or flag not in (1,2):raise ValueError('Expression list representation')
            a,b=self.unpack('<QQ',storage);items,count=(a,b) if flag==1 else (b,a)
            if not 0<=count<=256 or (count and not items):raise ValueError('Expression list bounds')
            return items,self.memory.read(items,count*stride) if count else b''
        _,code=array(obj+0x20,1);items,constants=array(obj+0x40,4)
        if len(code)!=3 or code[0]!=70 or code[2]!=0 or code[1]>=len(constants)//4:
            raise ValueError('Impact expression is not a single float literal')
        import math
        value=struct.unpack_from('<f',constants,code[1]*4)[0]
        if not math.isfinite(value) or not 0<=value<=10000:raise ValueError('Impact float bounds')
        return {'configType':'STUConfigVarFloatLiteralExpression','value':value,
                'valueAddress':items+code[1]*4,'expressionAddress':obj}

    def literal_int(self,obj):
        kind,address,category,primitive=self.field(obj,0x5180e750) # m_value
        if kind!=0x3ae7427e or category!=0 or primitive!=0x954a3bab:
            raise ValueError('Not a declared STUConfigVarInt -> s32 m_value')
        return self.unpack('<i',address)[0]

    def equal_branch_float_expression(self,obj):
        """Original Soldier conditional whose two exits load the same constant.

        Never evaluate its condition, emulate unknown operators, or substitute
        a weapon-stat default. Both complete original branches must agree.
        """
        if self.metadata(obj)[1]!=0xec502a81:raise ValueError('Not a float expression')
        def array(at,stride):
            storage,flag=self.unpack('<QQ',at)
            if not storage or flag not in (1,2):raise ValueError('Expression storage')
            a,b=self.unpack('<QQ',storage);items,count=(a,b) if flag==1 else (b,a)
            if not 0<count<=256 or not items:raise ValueError('Expression bounds')
            return items,self.memory.read(items,count*stride)
        _,code=array(obj+0x20,1);items,constants=array(obj+0x40,4)
        if len(code)!=11 or (code[0],code[2],code[3],code[4],code[6],code[7],code[8],code[10])!=(31,4,6,70,1,4,70,0):
            raise ValueError('Impact expression is not the calibrated equal-exit conditional')
        if max(code[5],code[9])>=len(constants)//4:raise ValueError('Expression constant index bounds')
        first=constants[code[5]*4:code[5]*4+4];second=constants[code[9]*4:code[9]*4+4]
        import math
        value=struct.unpack('<f',first)[0]
        if first!=second or not math.isfinite(value) or not 0<=value<=10000:raise ValueError('Conditional exits differ or are invalid')
        return dict(configType='STUConfigVarFloatEqualBranchExpression',value=value,valueAddress=items+code[5]*4,expressionAddress=obj,code=list(code))

    def pure_product_expression(self,obj):
        """Read the measured native constant-times-context-variable expression.

        The original getter must evaluate its contextual operand on the original
        factory thread. It is not necessarily stored in the persistent varbag.
        """
        if self.metadata(obj)[1]!=0xcc3a08f4:raise ValueError('Not the original scalar expression')
        def array(at,stride):
            storage,flag=self.unpack('<QQ',at)
            if not storage or flag not in (1,2):raise ValueError('Product storage')
            a,b=self.unpack('<QQ',storage);items,count=(a,b) if flag==1 else (b,a)
            if not 0<count<=256:raise ValueError('Product bounds')
            return items,self.memory.read(items,count*stride)
        _,code=array(obj+0x20,1);_,constants=array(obj+0x40,4);_,variables=array(obj+0x30,8)
        if len(code)!=6 or code[0]!=70 or code[2]!=31 or code[4:]!=bytes((102,0)) or code[1]>=len(constants)//4 or code[3]>=len(variables)//8:
            raise ValueError('Not the calibrated pure scalar product')
        value=struct.unpack_from('<f',constants,code[1]*4)[0]
        import math
        if not math.isfinite(value) or not 0<value<=10000:raise ValueError('Product constant bounds')
        variable=struct.unpack_from('<Q',variables,code[3]*8)[0];path=self.dynamic_path(variable)
        if len(path)!=1:raise ValueError('Product context path differs')
        impl=self.pointer(obj+8);vt=self.pointer(impl)
        if vt!=self.memory.base+0x160ae38 or self.pointer(vt+0xd0)!=self.memory.base+0xf6adc0:raise ValueError('Original pure-product evaluator differs')
        return dict(configType='STUConfigVarPureProduct',expressionAddress=obj,implementation=impl,implementationVtable=vt,constant=value,contextPath=path,code=list(code))

    def explosion_profile(self,volley):
        """Declared two-ring native blast with literal damage/radii/scales."""
        import math
        def ref(obj,key,owner,target):
            kind,address,category,declared=self.field(obj,key)
            if (kind,category,declared)!=(owner,2,target):raise ValueError('Blast declared field differs')
            return self.pointer(address)
        explosion=ref(volley,0x5b97fa06,VOLLEY,0x66bd247b)
        if self.metadata(explosion)[1]!=0x66bd247b:raise ValueError('Blast type differs')
        health=ref(explosion,0x89174668,0x66bd247b,0x06a06f4e)
        amount=ref(health,0xc43222bc,0x06a06f4e,0xbfd9aadd)
        def literal(obj):
            kind=self.metadata(obj)[1]
            if kind==0x3ae7427e:value=self.literal_int(obj)
            elif kind==0x7b13a0d4:value=self.unpack('<f',obj+16)[0]
            elif kind==0xec502a81:value=self.literal_float_expression(obj)['value']
            else:raise ValueError('Nonliteral blast value requires native evaluation')
            if not math.isfinite(value):raise ValueError('Nonfinite blast value')
            return value
        kind,address,category,declared=self.field(explosion,0xee107893)
        if (kind,category,declared)!=(0x66bd247b,5,0xf91c284f):raise ValueError('Blast ring declaration differs')
        storage,flag=self.unpack('<QQ',address)
        if not storage or flag not in (1,2):raise ValueError('Blast ring storage')
        a,b=self.unpack('<QQ',storage);items,count=(a,b) if flag==1 else (b,a)
        if count!=2:raise ValueError('Only measured two-ring blasts admitted')
        inner,scale,outer,falloff=self.unpack('<4Q',items)
        splash,lo,hi,first,last=map(literal,(amount,inner,outer,scale,falloff))
        if not 0<splash<=1000 or not 0<=lo<hi<=10 or first!=1 or not 0<=last<=1:raise ValueError('Blast ring bounds')
        return dict(splash=splash,inner=lo,outer=hi,outerScale=last,explosion=explosion)

    def pharah_rocket(self,volley):
        """Measured beta primary: direct40, splash80, two declared falloff rings."""
        def ref(obj,key,owner,target):
            kind,address,category,declared=self.field(obj,key)
            if (kind,category,declared)!=(owner,2,target):raise ValueError('Rocket declared field differs')
            return self.pointer(address)
        direct=self.impact_damage(volley)
        explosion=ref(volley,0x5b97fa06,VOLLEY,0x66bd247b)
        health=ref(explosion,0x89174668,0x66bd247b,0x06a06f4e)
        splash=ref(health,0xc43222bc,0x06a06f4e,0xbfd9aadd)
        if self.metadata(explosion)[1]!=0x66bd247b or direct.get('value')!=40 or self.literal_int(splash)!=80:
            raise ValueError('Rocket direct/splash calibration differs')
        kind,address,category,declared=self.field(explosion,0xee107893)
        if (kind,category,declared)!=(0x66bd247b,5,0xf91c284f):raise ValueError('Rocket ring declaration differs')
        storage,flag=self.unpack('<QQ',address)
        if flag not in (1,2):raise ValueError('Rocket ring storage')
        a,b=self.unpack('<QQ',storage);items,count=(a,b) if flag==1 else (b,a)
        if count!=2:raise ValueError('Rocket ring count differs')
        inner,scale,outer,falloff=self.unpack('<4Q',items)
        def literal_float(obj):
            if self.metadata(obj)[1]!=0x7b13a0d4:raise ValueError('Rocket ring is not a literal float')
            return self.unpack('<f',obj+16)[0]
        if (literal_float(inner),self.literal_int(scale),literal_float(outer),literal_float(falloff))!=(.5,1,2.5,.125):
            raise ValueError('Rocket ring calibration differs')
        return dict(direct=direct['valueAddress'],splash=splash,rings=items,inner=inner,outer=outer,falloff=falloff,volley=volley)
