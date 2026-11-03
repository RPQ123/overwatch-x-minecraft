"""Read-only control-skill calibration for the exact offline research client.

This is NOT an attack source and never publishes a production binding. A Volley
logger snapshot can overwrite an earlier Begin; neither it nor a button press
proves lossless projectiles, a stun duration, knockback integration or MC effects.
Unknown server semantics are deliberately left unknown.
"""
import argparse,json,math
from observe_overwatch import ROOT,ResearchProcess
from observe_native_weapon_states import WeaponStates
from native_armory_binding import primitive,projectile_resources

PROFILES={
    0x02e0000000000042:dict(name='McCree',script=0x05800000000001e9,node=7,resource=0x040000000000037d),
    0x02e0000000000008:dict(name='Pharah',script=0x058000000000007b,node=3,resource=0x040000000000010f),
}

def calibrated_policy(hero,actual,knockback):
    """Recognize exact measured profiles, including the deployed E override.

    This labels observed configuration only; it never proves MC effects or who
    applied a value. Keep beta receipt damage/flight separate from modern policy.
    """
    if hero==0x02e0000000000042:
        if actual[:7]!=(30,5,7,20,3,1,25) or len(actual)!=8 or actual[7] not in (10,12) or knockback!=[]:
            raise ValueError('Current control-skill calibration differs; do not substitute defaults')
        return dict(profile='beta' if actual[7]==10 else 'beta-with-requested-modern-cooldown',baselineCooldown=10,
                    observedCooldown=actual[7],gameplayReference='docs/NATIVE-MCCREE.md')
    if hero==0x02e0000000000008 and actual==(60,5,100,0,8,1,1,12) and knockback==[[8,1,1,1]]:
        return dict(profile='beta',baselineCooldown=12,observedCooldown=12,gameplayReference='docs/HERO-SKILLS.md')
    raise ValueError('Current control-skill calibration differs; do not substitute defaults')

def literal(b,obj):
    kind=b.metadata(obj)[1]
    if kind==0x3ae7427e:value=b.literal_int(obj)
    elif kind==0x7b13a0d4:value=b.unpack('<f',obj+16)[0]
    elif kind==0xec502a81:value=b.literal_float_expression(obj)['value']
    else:raise ValueError('Control-skill value is not a measured literal')
    if not math.isfinite(value) or not 0<=value<=10000:raise ValueError('Control-skill literal bounds')
    return value

def ref(b,obj,key,owner,target):
    kind,at,category,declared=b.field(obj,key)
    if (kind,category,declared)!=(owner,2,target):raise ValueError('Control-skill field declaration changed')
    value=b.pointer(at)
    if target!=0xbfd9aadd and b.metadata(value)[1]!=target:raise ValueError('Control-skill object type changed')
    return value

def inline(b,obj,key,owner,element_type,stride,maximum=16):
    kind,at,category,declared=b.field(obj,key)
    if (kind,category,declared)!=(owner,5,element_type):raise ValueError('Control-skill inline declaration changed')
    storage,flag=b.unpack('<QQ',at)
    if not storage or flag not in (1,2):raise ValueError('Control-skill inline storage')
    a,c=b.unpack('<QQ',storage);items,count=(a,c) if flag==1 else(c,a)
    if not 0<=count<=maximum or count and not items:raise ValueError('Control-skill inline bounds')
    return [b.unpack('<'+'Q'*(stride//8),items+i*stride) for i in range(count)]

def inspect(process):
    r=WeaponStates(process);sample=r.sample_weapon(False,True);b=r.bindings
    admin=r.pointer(process.base+0x17b7f90);table=process.read(r.pointer(admin+16),65536)
    controller=r.entity(table,sample['localId']);reference=r.component(controller,0x20)
    info=r.component(controller,0x3f);hero=r.unpack('<Q',info+0x98)[0]
    if hero not in PROFILES:raise ValueError('Select McCree or Pharah for this measured calibration')
    model=r.entity(table,sample['modelId']);profile=PROFILES[hero]
    matches=[key for key in r.graph_cache if key[2]==profile['script']]
    if len(matches)!=1:raise ValueError('Control-skill graph is not unique on the current model')
    script,graph,_=matches[0];nodes=r.stu_list(graph+0x50);node=nodes[profile['node']]
    if b.metadata(node)[1]!=0x860ee5fc:raise ValueError('Control-skill Volley definition differs')
    variants=projectile_resources(r,node)
    if len(variants)!=1 or variants[0][0]!=profile['resource']:raise ValueError('Control-skill projectile resource differs')
    bag=r.pointer(script+0x98)
    def value(key):return literal(b,ref(b,node,key,0x860ee5fc,0xbfd9aadd))
    speed=value(0xac2f916a);lifetime=value(0x5257be73);range_=value(0x308e35d5)
    motion_kind,motions_at,category,declared=b.field(node,0xb5d34136)
    if (motion_kind,category,declared)!=(0x860ee5fc,3,0x7f06bc91):raise ValueError('Control-skill motion declaration differs')
    motions=r.stu_list(motions_at)
    if len(motions)>1:raise ValueError('Compound control-skill motion is uncalibrated')
    gravity=0 if not motions else literal(b,ref(b,motions[0],0x005269ee,0xc2b6ce4b,0xbfd9aadd))
    explosion=ref(b,node,0x5b97fa06,0x860ee5fc,0x66bd247b)
    rings=inline(b,explosion,0xee107893,0x66bd247b,0xf91c284f,16)
    if len(rings)!=1:raise ValueError('Expected the measured single control-skill blast ring')
    radius,scale=map(lambda obj:literal(b,obj),rings[0])
    health=ref(b,explosion,0x89174668,0x66bd247b,0x06a06f4e)
    amount=ref(b,health,0xc43222bc,0x06a06f4e,0xbfd9aadd)
    if b.metadata(amount)[1]==0xf8cc195d:
        path=b.dynamic_path(amount)
        if path!=['0d800000000001dc']:raise ValueError('Control-skill amount context is uncalibrated')
        _,amount_value,_=primitive(r,bag,int(path[0],16))
    else:amount_value=literal(b,amount)
    knockback=inline(b,health,0x59daadc5,0x06a06f4e,0x903c0ba5,32)
    # Inline slots are real native values. Their names/physics must not be
    # invented from the familiar numbers 8/1/1/1,20 or5.
    knockback_values=[[literal(b,v) for v in row] for row in knockback]
    tags=inline(b,health,0x74de05aa,0x06a06f4e,0x4d3ec3cf,8)
    identifiers=[]
    for (tag,) in tags:
        if b.metadata(tag)[1]!=0x6324dd9f: # CRC32(STUConfigVarIdentifier)
            raise ValueError('Control-skill tag is not a typed identifier')
        rid=r.unpack('<Q',tag+24)[0]
        if rid>>48!=0x0d80:raise ValueError('Control-skill identifier resource type')
        identifiers.append(f'{rid:016x}')
    _,cooldown,_=primitive(r,bag,0x0d800000000001d8)
    actual=(speed,lifetime,range_,gravity,radius,scale,amount_value,cooldown)
    policy=calibrated_policy(hero,actual,knockback_values)
    current_table=process.read(r.pointer(admin+16),65536)
    if r.pointer(process.base+0x17b7f90)!=admin or r.unpack('<I',admin+0x220)[0]!=sample['localId'] or r.entity(current_table,sample['localId'])!=controller or r.entity(current_table,sample['modelId'])!=model or r.component(controller,0x20)!=reference or r.component(controller,0x3f)!=info or r.unpack('<I',reference+0x94)[0]!=sample['modelId'] or r.unpack('<Q',info+0x98)[0]!=hero or r.pointer(script+0x160)!=graph or r.pointer(script+0x98)!=bag or r.unpack('<Q',script+0x150)[0]!=profile['script'] or r.pointer(r.pointer(r.pointer(script+0x10)+0x450)+8)!=model:
        raise ValueError('Control-skill owner changed during calibration')
    rows=[v for v in sample['records'].values() if v['instanceAddress']==script and v['node']==profile['node']]
    return dict(version=2,hero=profile['name'],heroId=f'{hero:016x}',modelId=sample['modelId'],
        script=f'{profile["script"]:016x}',volleyNode=profile['node'],projectile=f'{profile["resource"]:016x}',
        speed=speed,lifetime=lifetime,range=range_,gravity=gravity,blastRadius=radius,blastScale=scale,
        healthModifierAmount=amount_value,cooldown=cooldown,knockbackInlineSlots=knockback_values,identifiers=identifiers,
        configurationPolicy=policy,volleySnapshot=rows,stunSeconds=None,knockbackIntegrationVerified=False,
        mcSkillImplemented=None,mcEffectsVerifiedByThisInspection=False,
        readOnly=True,newHooksInstalled=False,nativeCalls=False,losslessProjectileChannel=False)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pid',type=int,required=True);parser.add_argument('--output',required=True);args=parser.parse_args()
    path=(ROOT/args.output).resolve()
    if ROOT/'research' not in path.parents or path.suffix!='.json':parser.error('Output must be a private research JSON file')
    p=ResearchProcess(args.pid)
    try:result=inspect(p)
    finally:p.close()
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result))

if __name__=='__main__':main()
