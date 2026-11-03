"""Read the original HealthPool amounts; never execute a config evaluator."""
import math,struct,zlib
from observe_native_weapon_states import WeaponStates
from native_hero_profiles import HERO_IDS

HEALTH_GRAPH=0x0580000000000033
SUPPORTED_HEROES=HERO_IDS
POOL_LAYOUT=((1,0,0x0d800000000000c7,0x98),(7,1,0x0d800000000006c8,0x1d8),(3,2,0x0d800000000000dd,0x318))

def health_plan(parts,amounts):
    """Only initialize the base slot; preserve native metadata and extra pools."""
    if len(parts)!=3 or len(amounts)!=3 or not 0<sum(amounts)<=10000:
        raise ValueError('Native health pool count/total')
    result=[]
    for raw,amount in zip(parts,amounts):
        if len(raw)!=320 or not math.isfinite(amount) or not 0<=amount<=10000:
            raise ValueError('Native health pool bounds')
        enabled,maximum,current=struct.unpack_from('<Iff',raw)
        if enabled not in (0,1) or not all(math.isfinite(v) for v in (maximum,current)) or not 0<=current<=maximum<=10000:
            raise ValueError('Native health part differs')
        if not enabled and (maximum or current):raise ValueError('Inactive native health part has values')
        if any(struct.unpack_from('<I',raw,i*20)[0] for i in range(1,16)):
            raise ValueError('Preserve additional native health pools')
        if not amount:
            if enabled or maximum or current:raise ValueError('Preserve unexpected native health pool')
            result.append(raw[:12])
        else:result.append(struct.pack('<Iff',1,amount,amount))
    return result

def inspect_health(process):
    r=WeaponStates(process);s=r.sample_weapon(require_volley=False)
    admin=r.pointer(process.base+0x17b7f90);table=process.read(r.pointer(admin+0x10),65536)
    controller=r.entity(table,s['localId']);reference=r.component(controller,0x20)
    model=r.entity(table,s['modelId']);info=r.component(controller,0x3f);hero=r.unpack('<Q',info+0x98)[0]
    if hero not in SUPPORTED_HEROES:raise ValueError('Uncalibrated native health hero')
    found=[key for key in r.graph_cache if key[2]==HEALTH_GRAPH]
    if len(found)!=1:raise ValueError('Expected one original health-pool script')
    instance,graph,_=found[0];nodes=r.stu_list(graph+0x50);bag=r.pointer(instance+0x98)
    def data(at,stride):
        storage,flag=r.unpack('<QQ',at)
        if not storage or flag not in (1,2):raise ValueError('Missing/invalid health expression list')
        a,b=r.unpack('<QQ',storage);items,count=(a,b) if flag==1 else (b,a)
        if not 0<=count<=256 or (count and not items):raise ValueError('Health expression list bounds')
        return process.read(items,count*stride) if count else b''
    variables={}
    for bucket in range(16):
        for rid,value in struct.iter_unpack('<QQ',r.vector(bag+0xa0+bucket*0x30,16)):
            if rid in variables:raise ValueError('Duplicate health variable')
            variables[rid]=value
    pools=[]
    for node_index,pool_kind,rid,offset in POOL_LAYOUT:
        node=nodes[node_index]
        kind,address,category,declared=r.bindings.field(node,0xc43222bc)
        if kind!=zlib.crc32(b'stustatescriptstatehealthpool') or category!=2 or declared!=0xbfd9aadd:
            raise ValueError('Original HealthPool amount declaration changed')
        if r.unpack('<I',node+0x148)[0]!=pool_kind:raise ValueError('Original health-pool kind changed')
        expr=r.pointer(address)
        if r.bindings.metadata(expr)[1]!=0xec502a81 or data(expr+0x20,1)!=bytes((31,0,0)):
            raise ValueError('Health amount is not a single original dynamic-variable expression')
        dynamic=data(expr+0x30,8)
        if len(dynamic)!=8 or r.bindings.dynamic_path(struct.unpack('<Q',dynamic)[0])!=[f'{rid:016x}']:
            raise ValueError('Original HealthPool amount path changed')
        numeric=variables.get(rid,0)
        if not numeric or r.pointer(numeric)!=process.base+0x1608248:raise ValueError('Native health variable type changed')
        raw=process.read(numeric+0xa0,16);value_type=struct.unpack_from('<I',raw,12)[0]
        if value_type not in (2,3):raise ValueError('Native health amount is not numeric')
        amount=struct.unpack_from('<i' if value_type==2 else '<f',raw)[0]
        if not math.isfinite(amount) or not 0<=amount<=10000:raise ValueError('Native health amount bounds')
        pools.append({'kind':pool_kind,'offset':offset,'amount':amount,'variable':numeric,'variableType':value_type,'amountRaw':raw})
    health=r.component(model,0x28)
    if r.pointer(health)!=process.base+0x15c5aa0:raise ValueError('Native health component type changed')
    def verify(check_values=True):
        if r.pointer(process.base+0x17b7f90)!=admin or r.unpack('<I',admin+0x220)[0]!=s['localId'] or r.unpack('<I',reference+0x94)[0]!=s['modelId'] or r.unpack('<I',model+0x94)[0]!=s['modelId'] or r.pointer(health+8)!=model or r.unpack('<Q',info+0x98)[0]!=hero or r.pointer(instance+0x98)!=bag or r.unpack('<Q',instance+0x150)[0]!=HEALTH_GRAPH or r.pointer(instance+0x160)!=graph or r.pointer(health)!=process.base+0x15c5aa0:
            raise ValueError('Native health owner changed')
        if r.pointer(r.pointer(r.pointer(instance+0x10)+0x450)+8)!=model:
            raise ValueError('Native health script belongs to another model')
        for pool in pools if check_values else ():
            if r.pointer(pool['variable'])!=process.base+0x1608248 or process.read(pool['variable']+0xa0,16)!=pool['amountRaw']:
                raise ValueError('Original health configuration changed')
    verify()
    return r,{'hero':hero,'modelId':s['modelId'],'health':health,'pools':pools},verify
