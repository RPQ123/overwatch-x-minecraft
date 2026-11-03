"""Prepare current-owner weapon variants from native metadata, never from keys."""
import ctypes,json,math,struct,time
from observe_overwatch import ROOT
from observe_native_weapon_states import WeaponStates
from native_hero_profiles import camera_definition

HEROES={0x29:'Genji',0x42:'McCree',8:'Pharah',2:'Reaper',0x6e:'Soldier76',3:'Tracer',
        0x15:'Bastion',5:'Hanzo',0x65:'Junkrat',0xdd:'Mei',6:'Torbjorn',10:'Widowmaker'}
HEADER=struct.Struct('<8sIIII8QII')
SPEC=struct.Struct('<12Q4I6fIf')

class UnsupportedArmory(ValueError):
    """Only measured unsupported variants, distinct from invalid/stale owners."""
    def __init__(self,hero,model,issues):
        self.hero=hero;self.model=model;self.issues=issues
        super().__init__('Native weapon extensions require separate calibration: '+json.dumps(issues))
class ArmoryBindingPending(ValueError):
    """Retry discovery; never cache a partial primary-only skill binding."""
# Only primary factories actually calibrated and exercised in this client.
# Similar-looking Volley nodes can be ultimates, status projectiles or melee;
# their parameters do not establish the missing skill/world behavior.
PRIMARY_RESOURCES={0x42:{0x040000000000037d},2:{0x040000000000004a},3:{0x0400000000000018},8:{0x0400000000000052,0x040000000000010f},0x15:{0x0400000000000205,0x0400000000000207,0x04000000000003ce},
                   5:{0x0400000000000144,0x040000000000020b,0x0400000000000149,0x040000000000020d},0xdd:{0x040000000000108b,0x04000000000008be},
                   6:{0x0400000000000157,0x04000000000002d0},10:{0x040000000000004c,0x0400000000000107,0x040000000000004b,0x0400000000000108},0x6e:{0x04000000000003d4,0x040000000000072c}}

def hanzo_sonic_profile(r,hero,script,index,node,resource,gravity,damage):
    """Current typed Sonic-only gate; never borrow ordinary/Scatter factories.

    Actual current strong/weak factories are independently captured in sprint
    research. c3's10-second/10-range variables are calibrated here; the MC sphere
    and fixed impact anchor remain an explicitly separate server policy.
    """
    if (hero,script,index)!=(0x02e0000000000005,0x05800000000000b9,20):
        raise ValueError('Sonic original owner/Volley differs')
    if resource not in (0x0400000000000149,0x040000000000020d) or abs(gravity-9.800000190734863)>1e-6:
        raise ValueError('Sonic original resource/gravity differs')
    b=r.bindings
    from inspect_native_control_skills import ref,literal
    for key,expected in ((0x5257be73,5),(0x308e35d5,100)):
        if literal(b,ref(b,node,key,0x860ee5fc,0xbfd9aadd))!=expected:
            raise ValueError('Sonic original lifetime/range differs')
    if damage.get('resourcePath')!=['0d800000000001dc']:
        raise ValueError('Sonic original contextual damage differs')
    spawn=ref(b,node,0x3307a07b,0x860ee5fc,0x0dda5afc)
    entity=ref(b,spawn,0x40877716,0x0dda5afc,0xbfd9aadd)
    if b.metadata(entity)[1]!=0xe53c2921 or b.unpack('<Q',entity+24)[0]!=0x040000000000014a:
        raise ValueError('Sonic original impact prefab differs')
    if not getattr(r,'_sonic_child_verified',False):
        from provided_plugin_symbols import provided_plugin
        from native_map_snapshot import lookup_map
        base,image,pdb=provided_plugin(r.memory)
        at=base+image.symbol_rva(pdb.exact('stu_resources::_constructed_stus'))
        try:
            entry=lookup_map(r.memory,at,0x05800000000000c3,'Q',20000)
        except (OSError,ValueError) as error:
            raise ArmoryBindingPending('Sonic resource tree changed; retry current owner') from error
        graph=r.pointer(entry) if entry else 0
        if not graph:raise ArmoryBindingPending('Current original Sonic child not loaded yet')
        nodes=r.stu_list(graph+0x50)
        if len(nodes)!=27:raise ValueError('Sonic child graph differs')
        for index,path in ((12,'0d800000000000d7'),(13,'0d800000000001a6')):
            target=ref(b,nodes[index],0xec9f34a6,0x4698e4b6,0xf8cc195d)
            value=ref(b,nodes[index],0x5180e750,0x4698e4b6,0xbfd9aadd)
            if b.dynamic_path(target)!=[path] or literal(b,value)!=10:
                raise ValueError('Sonic child duration/range variables differ')
        wait=ref(b,nodes[9],0xdb0e39db,0x65f158da,0xbfd9aadd)
        bound=ref(b,nodes[11],0x9976e589,0x498b421a,0xbfd9aadd)
        angle=ref(b,nodes[11],0x9d812041,0x498b421a,0xbfd9aadd)
        if b.dynamic_path(wait)!=['0d800000000000d7'] or b.dynamic_path(bound)!=['0d800000000001a6'] or literal(b,angle)!=360:
            raise ValueError('Sonic original Wait/TrackTargets binding differs')
        r._sonic_child_verified=True

def config_resources(b,obj,depth=0,seen=None):
    seen=set() if seen is None else seen
    if not obj or obj in seen or depth>8:return []
    seen=seen|{obj};info,kind,size=b.metadata(obj)
    if kind==0xe53c2921:
        rid=b.unpack('<Q',obj+24)[0]
        return [(rid,obj+24)] if rid>>48==0x0400 else []
    out=[];parents=set()
    while info and info not in parents and len(parents)<32:
        parents.add(info);parent,args=b.unpack('<QQ',info+0x20);count=b.unpack('<i',info+0x54)[0]
        if not 0<=count<=512:raise ValueError('Config field bound')
        for i in range(count):
            key,offset,constraint=b.unpack('<IiQ',args+i*0xa0+8)
            if not 8<=offset<=size-8 or offset%8 or not constraint:continue
            try:identity=b.constraint_identity(constraint)
            except ValueError:continue
            category,declared=identity>>32,identity&0xffffffff
            if category==2 and declared in (0xbfd9aadd,0xf8cc195d):
                ptr=b.unpack('<Q',obj+offset)[0]
                if ptr:out+=config_resources(b,ptr,depth+1,seen)
            if category==3 and declared==0xbfd9aadd:
                storage,flag=b.unpack('<QQ',obj+offset)
                if not storage or flag not in (1,2):continue
                a,c=b.unpack('<QQ',storage);items,n=(a,c) if flag==1 else (c,a)
                if not 0<=n<=64:raise ValueError('Config variant bound')
                for ptr, in struct.iter_unpack('<Q',b.memory.read(items,n*8) if n else b''):
                    if ptr:out+=config_resources(b,ptr,depth+1,seen)
        info=parent
    return list(dict.fromkeys(out))

def primitive(r,bag,rid):
    found=[value for bucket in range(16) for key,value in struct.iter_unpack('<QQ',r.vector(bag+0xa0+bucket*0x30,16)) if key==rid]
    if len(found)!=1 or r.pointer(found[0])!=r.memory.base+0x1608248:raise ValueError('Numeric source is not unique/typed')
    raw,_,kind=r.unpack('<QII',found[0]+0xa0)
    if kind not in (2,3):raise ValueError('Damage primitive is not numeric')
    value=struct.unpack('<i' if kind==2 else '<f',struct.pack('<I',raw&0xffffffff))[0]
    if not math.isfinite(value) or not 0<=value<=10000:raise ValueError('Damage primitive bounds')
    bucket=next(bucket for bucket in range(16) if any(key==rid and pointer==found[0] for key,pointer in struct.iter_unpack('<QQ',r.vector(bag+0xa0+bucket*0x30,16))))
    return found[0],value,bucket

def projectile_resources(r,node):
    b=r.bindings;ref=b.pointer(b.field(node,0xf7329268)[1]);out=[]
    storage,flag=b.unpack('<QQ',ref+8)
    if storage:
        if flag not in (1,2):raise ValueError('Projectile asset list storage')
        a,c=b.unpack('<QQ',storage);items,n=(a,c) if flag==1 else (c,a)
        if not 0<=n<=64:raise ValueError('Projectile asset count')
        for index in range(n):
            _,resource=b.unpack('<QQ',items+index*16)
            if resource>>48==0x0400:out.append((resource,items+index*16+8,True,ref))
    config=b.unpack('<Q',ref+24)[0]
    if config:out.extend((resource,address,False,ref) for resource,address in config_resources(b,config))
    unique={}
    for item in out:unique.setdefault(item[0],item)
    return list(unique.values())

def projectile_gravity(r,node,barrage=False):
    b=r.bindings;kind,address,category,declared=b.field(node,0xb5d34136) # m_projectileMotions
    if (kind,category,declared)!=(0x860ee5fc,3,0x7f06bc91):raise ValueError('Native projectile motion declaration differs')
    motions=r.stu_list(address)
    if not motions:return 0.
    if barrage and len(motions)==2:
        keys=(0x70453da1,0xf1222348,0x78efb503,0x8b7ba07a,0x7ad99ab1,0x9cb93550,0x565a39d4,0xc629293e,0x45a2fcc6,0xd5d1ec2c,0x7d0091de,0x688b452c)
        for i,m in enumerate(motions):
            if b.metadata(m)[1:]!=(0x855ce717,104):raise ValueError('Barrage Wave type changed')
            expected=(0,.2,1 if i==0 else 0,.5,0,1,.1,1,.2,1.5,10,360)
            for j,(key,value) in enumerate(zip(keys,expected)):
                k,at,cat,typ=b.field(m,key)
                if (k,at,cat,typ)!=(0x855ce717,m+8+j*8,2,0xbfd9aadd):raise ValueError('Barrage Wave field changed')
                obj=b.unpack('<Q',at)[0]
                if not obj:
                    if value!=0:raise ValueError('Missing Barrage Wave literal')
                    continue
                t=b.metadata(obj)[1]
                if t not in (0x7b13a0d4,0x3ae7427e):raise ValueError('Barrage Wave nonliteral')
                actual=b.unpack('<f' if t==0x7b13a0d4 else '<i',obj+16)[0]
                if abs(actual-value)>1e-7:raise ValueError('Barrage Wave calibration changed')
        return 0.
    if len(motions)!=1 or b.metadata(motions[0])[1]!=0xc2b6ce4b:raise ValueError('Projectile motion requires separate calibration')
    # CRC32 names match STUStatescriptWeaponProjectileMotionGravity/m_gravity.
    kind,address,category,declared=b.field(motions[0],0x005269ee)
    if (kind,category,declared)!=(0xc2b6ce4b,2,0xbfd9aadd):raise ValueError('Native gravity declaration differs')
    value=b.pointer(address)
    typ=b.metadata(value)[1]
    if typ not in (0x7b13a0d4,0x3ae7427e):raise ValueError('Native projectile gravity is not a literal number')
    gravity=b.unpack('<f' if typ==0x7b13a0d4 else '<i',value+16)[0]
    if not math.isfinite(gravity) or not 0<=gravity<=30:raise ValueError('Native projectile gravity bounds')
    return gravity

def bastion_tank_profile(r,hero,script,index,graph,node,bag,damage,gravity):
    """Exact beta03ce declarations; actual factory callbacks remain the source.

    This binds the two damage rings only. The four-slot knockback declaration
    is recorded in private evidence; its integration/self impulse is unproved.
    """
    b=r.bindings
    if (hero,script,index)!=(0x02e0000000000015,0x058000000000024f,25) or b.metadata(node)[1]!=0x860ee5fc:
        raise ValueError('Tank cannon native source differs')
    nodes=r.stu_list(graph+0x50);states=r.stu_list(graph+0x60)
    if len(nodes)!=29 or len(states)!=22 or nodes[25]!=node or states[19]!=node:
        raise ValueError('Tank cannon original graph membership differs')
    def ref(obj,key,owner):
        kind,at,category,declared=b.field(obj,key)
        if (kind,category,declared)!=(owner,2,0xbfd9aadd):raise ValueError('Tank scalar declaration differs')
        return b.pointer(at)
    def typed(obj,kind,expected):
        if b.metadata(obj)[1]!=kind:raise ValueError('Tank scalar type differs')
        actual=b.literal_int(obj) if kind==0x3ae7427e else b.unpack('<f',obj+16)[0]
        if actual!=expected:raise ValueError('Tank scalar calibration differs')
    speed=ref(node,0xac2f916a,0x860ee5fc)
    if b.metadata(speed)[1]!=0xf8cc195d or b.dynamic_path(speed)!=['0d800000000018e0']:
        raise ValueError('Tank original speed source differs')
    speed_storage,speed_flag=b.unpack('<QQ',speed+0x10)
    if not speed_storage or speed_flag not in (1,2):raise ValueError('Tank original speed path storage differs')
    speed_object,speed_value,_=primitive(r,bag,0x0d800000000018e0)
    if speed_value!=60 or r.unpack('<I',speed_object+0xac)[0]!=2:
        raise ValueError('Tank original speed value differs')
    typed(ref(node,0x5257be73,0x860ee5fc),0x3ae7427e,5)
    typed(ref(node,0x308e35d5,0x860ee5fc),0x7b13a0d4,100.)
    typed(ref(node,0x472bec0c,0x860ee5fc),0x3ae7427e,1)
    typed(ref(node,0x120fd2f8,0x860ee5fc),0x3ae7427e,1)
    if damage.get('configType')!='STUConfigVarInt' or damage.get('value')!=50:
        raise ValueError('Tank original direct damage differs')
    typed(damage['valueAddress'],0x3ae7427e,50)
    kind,at,category,declared=b.field(node,0xb5d34136)
    if (kind,category,declared)!=(0x860ee5fc,3,0x7f06bc91) or r.stu_list(at) or gravity!=0:
        raise ValueError('Tank original empty motion differs')
    blast=b.explosion_profile(node)
    outer_scale=struct.unpack('<f',struct.pack('<f',.3))[0]
    if (blast['splash'],blast['inner'],blast['outer'],blast['outerScale'])!=(140,1,4,outer_scale):
        raise ValueError('Tank original blast calibration differs')
    explosion=blast['explosion']
    if b.metadata(explosion)[1]!=0x66bd247b:raise ValueError('Tank original blast type differs')
    kind,at,category,declared=b.field(explosion,0xee107893)
    if (kind,category,declared)!=(0x66bd247b,5,0xf91c284f):raise ValueError('Tank original blast ring declaration differs')
    storage,flag=b.unpack('<QQ',at)
    if not storage or flag not in (1,2):raise ValueError('Tank original blast ring storage differs')
    a,c=b.unpack('<QQ',storage);items,count=(a,c) if flag==1 else(c,a)
    if not items or count!=2:raise ValueError('Tank original blast ring count differs')
    rings=b.unpack('<4Q',items)
    for obj,typ,value in zip(rings,(0x3ae7427e,0x3ae7427e,0x3ae7427e,0x7b13a0d4),(1,1,4,outer_scale)):
        typed(obj,typ,value)
    kind,at,category,declared=b.field(explosion,0x89174668)
    if (kind,category,declared)!=(0x66bd247b,2,0x06a06f4e):raise ValueError('Tank original blast health source differs')
    health=b.pointer(at)
    if b.metadata(health)[1]!=0x06a06f4e:raise ValueError('Tank original blast health type differs')
    typed(ref(health,0xc43222bc,0x06a06f4e),0x3ae7427e,140)
    return blast


def prepare(process,pid):
    r=WeaponStates(process);s=r.sample_weapon(require_volley=False);b=r.bindings
    admin=r.pointer(process.base+0x17b7f90);table=process.read(r.pointer(admin+0x10),65536)
    controller=r.entity(table,s['localId']);model=r.entity(table,s['modelId']);hero=r.unpack('<Q',r.component(controller,0x3f)+0x98)[0]
    if hero&0xffff not in HEROES:raise ValueError('Hero is outside Assault/Defense scope')
    entity_bag=r.pointer(r.component(model,0x23)+0xc0+0x2e0)
    eye=camera_definition(b,model)['eyeHeight'];specs=[];issues=[]
    for (instance,graph,script),definition in r.graph_cache.items():
        nodes=r.stu_list(graph+0x50);bag=r.pointer(instance+0x98)
        for index in definition['volleyNodes']:
            node=nodes[index]
            try:
                variants=projectile_resources(r,node)
                if not variants:raise ValueError('No declared literal projectile variants')
                if (hero&0xffff) in PRIMARY_RESOURCES:
                    variants=[v for v in variants if v[0] in PRIMARY_RESOURCES[hero&0xffff]]
                    if not variants:raise ValueError('Secondary/skill factory requires separate native calibration')
                flash=hero&0xffff==0x42
                concussive=hero&0xffff==8 and script==0x058000000000007b and index==3
                impact=b.pointer(b.field(node,0x5b97fa06 if flash or concussive else 0x3d131607)[1]);health=b.pointer(b.field(impact,0x89174668)[1]);damage_config=b.pointer(b.field(health,0xc43222bc)[1])
                if flash:
                    if index!=7 or script!=0x05800000000001e9 or b.dynamic_path(damage_config)!=['0d800000000001dc']:raise ValueError('Flashbang native source differs')
                    damage=dict(resourcePath=b.dynamic_path(damage_config),configType='STUConfigVarDynamic')
                elif concussive:
                    from inspect_native_control_skills import inspect
                    proof=inspect(process)
                    if proof['modelId']!=s['modelId'] or proof['configurationPolicy']['profile']!='beta':raise ValueError('Concussive Blast owner/calibration differs')
                    if b.metadata(damage_config)[1]!=0x3ae7427e or b.literal_int(damage_config)!=1:raise ValueError('Concussive Blast native receipt amount differs')
                    damage=dict(configType='STUConfigVarInt',value=1,valueAddress=damage_config)
                else:damage=b.impact_damage(node)
                amount=0;kind=0;obj=0;value=0;vtable=0;rid=0
                if damage.get('configType')=='STUConfigVarPureProduct':
                    amount=0;obj=damage['expressionAddress'];vtable=r.pointer(obj);value=damage['implementation'];rid=damage['implementationVtable'];kind=7
                elif 'resourcePath' in damage:
                    path=[int(v,16) for v in damage['resourcePath']]
                    source=bag if len(path)==1 else entity_bag if len(path)==2 and path[0]==0x0d80000000000004 else 0
                    if not source:raise ValueError('Damage dynamic path requires unsupported scope')
                    try:
                        obj,amount,bucket=primitive(r,source,path[-1]);value=obj+0xa0;vtable=r.pointer(obj);kind=3|(bucket<<8)|(0x10000 if source==entity_bag else 0);rid=path[-1]
                    except ValueError:
                        if len(path)!=1 or path[0] not in (0x0d800000000001dc,0x0d80000000000e33):raise
                        obj=damage_config;vtable=r.pointer(obj);value=r.pointer(obj+8);rid=r.pointer(value);kind=6;amount=0
                        if rid!=process.base+0x16067a8 or r.pointer(rid+0xd0)!=process.base+0xf5c120 or process.read(process.base+0xf5c120,26)!=bytes.fromhex('4883ec284d8bd04885d2750732c04883c428c3488b8a98000000'):
                            raise ValueError('Native contextual damage getter differs')
                else:
                    amount=damage['value'];obj=damage.get('expressionAddress',damage['valueAddress']);vtable=r.pointer(obj)
                    kind={'STUConfigVarInt':1,'STUConfigVarFloat':2,'STUConfigVarFloatLiteralExpression':4,'STUConfigVarFloatEqualBranchExpression':5}[damage['configType']]
                    value=damage['valueAddress'] if kind in (4,5) else obj+16
                definitions=r.stu_list(graph+0x60);state_index=definitions.index(node)
                instance_id=r.unpack('<h',instance+0x18)[0]
                if state_index>255:raise ValueError('Native Volley token state bound')
                volley_key=((instance_id*8&0xffff)<<16)|(state_index<<8)
                for resource,address,array_resource,ref in variants:
                    # Do not enable guessed physics/status effects. Those require
                    # their own original config binding and real-client oracle.
                    suffix=hero&0xffff;effect=0;gravity=projectile_gravity(r,node,barrage=suffix==8 and script==0x058000000000002b and index==2 and resource==0x0400000000000052);splash=0.;radius=0.;bounces=0;fuse=0.;terrain=0.
                    blast=None
                    if flash:
                        from inspect_native_control_skills import inline,literal
                        rings=inline(b,impact,0xee107893,0x66bd247b,0xf91c284f,16)
                        if len(rings)!=1 or tuple(literal(b,v) for v in rings[0])!=(3,1) or gravity!=20 or amount!=25:raise ValueError('Flashbang blast calibration differs')
                        effect=2;radius=3.
                    if concussive:
                        if variants[0][0]!=0x040000000000010f or gravity!=0 or amount!=1:raise ValueError('Concussive Blast native flight differs')
                        effect=3;radius=8.
                    if (suffix==0x6e and resource==0x040000000000072c) or (suffix==8 and resource==0x0400000000000052):
                        blast=b.explosion_profile(node);effect=1;splash=blast['splash'];radius=blast['outer']
                    if resource==0x04000000000003ce:
                        blast=bastion_tank_profile(r,hero,script,index,graph,node,bag,damage,gravity)
                        effect=1;splash=blast['splash'];radius=blast['outer']
                    if resource in (0x0400000000000149,0x040000000000020d):
                        hanzo_sonic_profile(r,hero,script,index,node,resource,gravity,damage)
                    if suffix==0x65:
                        raise ValueError('Weapon physics/status calibration is pending; no approximate adapter admitted')
                    specs.append(dict(resource=resource,resourceAddress=address,script=instance,graph=graph,bag=bag,node=index,definition=node,
                        amountObject=obj,amountValue=value,amountVtable=vtable,amountKind=kind|(0x20000 if array_resource else 0),damage=amount,eyeHeight=eye,volleyKey=volley_key,
                        effect=effect,gravity=gravity,splash=splash,radius=radius,bounces=bounces,fuse=fuse,terrain=terrain,
                        resourceGuard=b.pointer(ref) if array_resource else b.pointer(address-24),damageConfig=damage_config,damageRid=rid,source=damage,blast=blast))
            except (OSError,ValueError,KeyError) as error:
                if isinstance(error,ArmoryBindingPending):raise
                issues.append(dict(script=f'{script:016x}',node=index,error=str(error)))
    if not specs:
        known={'Projectile motion requires separate calibration','Secondary/skill factory requires separate native calibration'}
        if issues and all(v['error'] in known for v in issues):
            if r.unpack('<I',admin+0x220)[0]!=s['localId'] or r.unpack('<I',r.component(controller,0x20)+0x94)[0]!=s['modelId']:
                raise ValueError('Hero changed while checking unsupported armory')
            raise UnsupportedArmory(hero,s['modelId'],issues)
        raise ValueError('No typed native weapon variants: '+json.dumps(issues))
    # Same resource may be emitted by several native states. Only merge when
    # its actual damage source agrees; ambiguous variants remain unavailable.
    grouped={}
    for spec in specs:grouped.setdefault((spec['resource'],spec['volleyKey']),[]).append(spec)
    unique=[]
    for resource,group in grouped.items():
        if len({(v['damage'],v['amountKind'],v['amountValue'] if (v['amountKind']&255)==3 else 0) for v in group})>1:
            issues.append(dict(resource=f'{resource[0]:016x}',error='Ambiguous damage variants'));continue
        unique.append(group[0])
    if not unique or len(unique)>64:raise ValueError('No bounded unambiguous weapon profiles')
    times=[ctypes.create_string_buffer(8) for _ in range(4)]
    process.kernel.GetProcessTimes.argtypes=[ctypes.c_void_p,*([ctypes.c_void_p]*4)]
    if not process.kernel.GetProcessTimes(process.handle,*times):raise ctypes.WinError(ctypes.get_last_error())
    creation=struct.unpack('<Q',times[0].raw)[0]
    live=json.loads((ROOT/f'native-host/build/world-live-{pid}.json').read_text())
    data=bytearray(HEADER.pack(b'OWARM002',2,HEADER.size+len(unique)*SPEC.size,pid,0,creation,admin,s['localId'],s['modelId'],model,hero,live['generation'],0,len(unique),0))
    for v in unique:
        data+=SPEC.pack(v['resource'],v['resourceAddress'],v['script'],v['graph'],v['bag'],v['definition'],v['amountObject'],v['amountValue'],v['amountVtable'],v['resourceGuard'],v['damageConfig'],v['damageRid'],
                        v['node'],v['amountKind'],v['effect'],v['bounces'],v['eyeHeight'],v['gravity'],v['splash'],v['radius'],v['fuse'],v['terrain'],v['volleyKey'],0)
    if r.unpack('<I',admin+0x220)[0]!=s['localId'] or r.unpack('<I',model+0x94)[0]!=s['modelId']:raise ValueError('Hero changed while preparing armory')
    path=ROOT/f'native-host/build/native-armory-request-{pid}.bin';tmp=path.with_suffix('.tmp');tmp.write_bytes(data);tmp.replace(path)
    result=dict(version=2,pid=pid,hero=hero,modelId=s['modelId'],specs=unique,issues=issues,headerBytes=HEADER.size,specBytes=SPEC.size,readOnly=True)
    diag=path.with_suffix('.json');temp=diag.with_suffix('.tmp');temp.write_text(json.dumps(result,indent=2)+'\n');temp.replace(diag)
    return result
