"""Read-only preparation for the exact native projectile-factory observer."""
from modpack.config import paths
import ctypes,hashlib,json,struct,time,urllib.request
from observe_overwatch import ROOT
from observe_native_weapon_states import WeaponStates
from native_emission_version import VERSION as EMISSION_VERSION,DLL as EMISSION_DLL

PREFIX=bytes.fromhex('48895c2408488954241055565741544155415641574883ec')
FACTORY_PREFIX=bytes.fromhex('4055565741544155488dac24f0cfffff')
MINHOOK_SHA256='894e5a3655d0ed6963e8c048227eabf6a84aad862184cb2148502ff13b74e1d7'

def prepare(process,pid,creation=None,refresh=False):
    if creation is None:
        times=[ctypes.create_string_buffer(8) for _ in range(4)]
        process.kernel.GetProcessTimes.argtypes=[ctypes.c_void_p,*([ctypes.c_void_p]*4)]
        if not process.kernel.GetProcessTimes(process.handle,*times):raise ctypes.WinError(ctypes.get_last_error())
        creation=struct.unpack('<Q',times[0].raw)[0]
    if refresh:
        from launch_passthrough_session import installed_modules
        name=EMISSION_DLL;path=ROOT/f'native-host/build/native-emissions-{pid}.json';report=json.loads(path.read_text())
        if (installed_modules(pid).get(name)!=(ROOT/'native-host/build'/name).resolve() or report.get('pid')!=pid
            or report.get('creation')!=creation or report.get('probeVersion')!=EMISSION_VERSION or not report.get('enabled')
            or report.get('failures') or time.time_ns()-path.stat().st_mtime_ns>4_000_000_000):
            raise ValueError(f'No current healthy emission{EMISSION_VERSION} owner for binding refresh')
    else:
        if process.read(process.base+0xd35c20,len(PREFIX))!=PREFIX:raise ValueError('Native projectile initializer differs or is already hooked')
        if process.read(process.base+0xd354b0,len(FACTORY_PREFIX))!=FACTORY_PREFIX:raise ValueError('Native pellet factory differs or is already hooked')
        for offset,target in ((0x110,0xf531f0),(0x158,0xf53270)):
            if struct.unpack('<Q',process.read(process.base+0x15c8e30+offset,8))[0]!=process.base+target:raise ValueError('Native ChaseVar callbacks differ or are already observed')
    library=paths().get('owExecutable').parent/'minhook.x64.dll'
    if hashlib.sha256(library.read_bytes()).hexdigest()!=MINHOOK_SHA256:raise ValueError('Provided hook library differs')
    reader=WeaponStates(process);sample=reader.sample_weapon()
    admin=reader.pointer(process.base+0x17b7f90);table=process.read(reader.pointer(admin+0x10),65536)
    controller=reader.entity(table,sample['localId']);hero=reader.unpack('<Q',reader.component(controller,0x3f)+0x98)[0]
    if hero not in (0x02e0000000000029,0x02e0000000000042,0x02e0000000000009,0x02e0000000000008):raise ValueError('No calibrated weapon for current hero')
    script_resource={0x29:0x304,0x42:0x1d2,9:0xfe,8:0x23}[hero&0xffff]|0x0580000000000000
    secondary=0;extra=(0,0,0,0)
    admin=reader.pointer(process.base+0x17b7f90);model=reader.entity(process.read(reader.pointer(admin+0x10),65536),sample['modelId'])
    if reader.pointer(model+0x28)!=admin:raise ValueError('Original native model/admin mismatch')
    live=json.loads((ROOT/f'native-host/build/world-live-{pid}.json').read_text())
    with urllib.request.urlopen('http://127.0.0.1:32133/health',timeout=2) as response:guest=json.load(response)
    if not guest.get('hostPoseConnected') or guest.get('hostGeneration')!=live.get('generation') or not guest.get('player',{}).get('alive'):raise ValueError('No actual current acknowledged guest world')
    matches=[]
    for (instance,graph,resource),definition in reader.graph_cache.items():
        if resource!=script_resource:continue
        nodes=reader.stu_list(graph+0x50)
        if hero==0x02e0000000000008:
            if definition['volleyNodes']!=[10]:raise ValueError('Original Pharah Volley changed')
            rocket=reader.bindings.pharah_rocket(nodes[10])
            if reader.pointer(rocket['direct'])!=process.base+0x1565f40 or reader.pointer(rocket['splash'])!=process.base+0x1565f40:
                raise ValueError('Rocket integer vtable differs')
            if any(reader.pointer(rocket[k])!=process.base+0x1558ba8 for k in ('inner','outer','falloff')):raise ValueError('Rocket float vtable differs')
            secondary=rocket['splash'];extra=(rocket['inner'],rocket['volley'],rocket['outer'],rocket['falloff'])
            matches.append((instance,reader.pointer(instance+0x98),rocket['direct'],rocket['rings'],0));continue
        if hero==0x02e0000000000009:
            from observe_native_beam import BeamReader
            beam=BeamReader(process)
            if beam.instance!=instance or beam.model!=model:raise ValueError('Native beam model changed')
            secondary=beam.rate;extra=(beam.ammo,beam.radius,beam.angle,beam.period)
            matches.append((instance,beam.bag,beam.damage,0,0));continue
        if hero==0x02e0000000000042:
            bindings=[reader.bindings.impact_damage(nodes[i]) for i in (33,38)]
            if any(b.get('configType')!='STUConfigVarInt' or b.get('value')!=70 for b in bindings):raise ValueError('Original McCree base damage differs')
            if any(reader.pointer(b['valueAddress'])!=process.base+0x1565f40 for b in bindings):raise ValueError('Original integer config vtable differs')
            secondary=bindings[1]['valueAddress'];matches.append((instance,reader.pointer(instance+0x98),bindings[0]['valueAddress'],0,0));continue
        bindings=[reader.bindings.impact_damage(nodes[i]) for i in (6,31)]
        if any(b['resourcePath']!=['0d800000000001dc'] for b in bindings):raise ValueError('Original Genji impact damage path changed')
        bag=reader.pointer(instance+0x98)
        for bucket in range(16):
            entries=reader.vector(bag+0xa0+bucket*0x30,16)
            for rid,value in struct.iter_unpack('<QQ',entries):
                if rid==0x0d800000000001dc:
                    if reader.pointer(value)!=process.base+0x1608248 or reader.unpack('<I',value+0xac)[0] not in (2,3):raise ValueError('Original impact damage variable is not numeric')
                    matches.append((instance,bag,value,rid,bucket))
    if len(matches)!=1:raise ValueError('Exactly one original local weapon damage binding is required')
    instance,bag,value,rid,bucket=matches[0]
    projectile={0x29:0x04000000000007ca,0x42:0x04000000000002a7,9:0x05800000000000fe,8:0x0400000000000033}[hero&0xffff]
    data=struct.pack('<8sIIII11QII6Q',b'OWEMIT01',4,168,pid,0,creation,admin,sample['localId'],sample['modelId'],model,live['generation'],projectile,instance,bag,value,rid,bucket,0,hero,secondary,*extra)
    if len(data)!=168:raise AssertionError('Native emission request layout')
    if reader.unpack('<I',admin+0x220)[0]!=sample['localId'] or reader.unpack('<I',model+0x94)[0]!=sample['modelId'] or reader.pointer(reader.pointer(reader.pointer(instance+0x10)+0x450)+8)!=model:
        raise ValueError('Native hero changed while binding emissions')
    path=ROOT/f'native-host/build/native-emissions-request-{pid}.bin';temp=path.with_suffix('.tmp');temp.write_bytes(data);temp.replace(path);return path
