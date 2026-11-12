"""Stop the current local passthrough test and verify native pointer restoration."""
import argparse,ctypes,json,time,os,struct,psutil,hashlib
from pathlib import Path
from ctypes import wintypes
from observe_overwatch import ROOT,ResearchProcess

BODY_RECOVERY_PINS = {
    39: '48325e7b6587af7527ddf8fd0d5822b4830c7d6b63970bcffb7c7f7d52c4ca82',
    40: '1ea18b895042efd506fedbd357263fba2aa40303f993bfec3d005e2366836299',
}

def read_report(path):
    # Windows can briefly deny opening a report while its atomic replace runs.
    # A transient read must not interrupt orderly callback restoration.
    for attempt in range(8):
        try:
            value=json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(value,dict):raise ValueError('Expected a native report object')
            return value
        except (OSError,ValueError):
            if attempt==7:raise
            time.sleep(.03)

def restoration_complete(report,pid,*,compositor=False):
    if report.get('pid')!=pid or report.get('restored') is not True or report.get('enabled') is not False:return False
    # The render owner clears active and publishes the vtable result before its
    # input/light/frame-limit releases finish. Do not accept that intermediate
    # snapshot and terminate the process while those releases are still running.
    version=report.get('probeVersion',0)
    if type(version) is not int:return False
    if compositor and version>=37:
        return (report.get('slotInputFilter') is False
                and all(report.get(key) is True for key in ('slotInputRestored','viewLightRestored','nativeFrameLimitRestored')))
    return True

def original_body_callbacks(process):
    """Read-only proof of the original movement system and its three callbacks."""
    def read(fmt,address):return struct.unpack(fmt,process.read(address,struct.calcsize(fmt)))
    admin,=read('<Q',process.base+0x17b7f90)
    items,count,capacity=read('<Qii',admin+0xf0)
    if not 1<=count<=capacity<=32:return False
    matches=0;expected=tuple(process.base+offset for offset in (0xca0960,0xca0800,0xca09c0))
    for index in range(count):
        component,=read('<Q',items+index*8)
        if not component:continue
        table,=read('<Q',component)
        if not table:continue
        if table==process.base+0x15c4e28:
            if read('<3Q',table)!=expected:return False
            matches+=1
        elif read('<3Q',table)[1:]==expected[1:]:
            # A second object still using the body's copied table is active,
            # even if an untouched original object also remains in the list.
            return False
    return matches==1

def emission_owner_version(pid):
    from launch_passthrough_session import installed_modules
    modules=installed_modules(pid)
    pins={11:'dee5bc83b02ebb1ff4dd1151fa1c945370ed5cfbaab42195f5b30d6455e2b231',12:'e196ba1bc0fd8d77a4227c8bac8d9f34e9bac5c786c7d7a3aaee106c425aca6a',13:'0bbcf58b6b38d03e8164a6fa3352e96cc03c66ef15e3e656ad991ae1aeb7cd70',14:'1519bff4e53103579920fc49db9d24de25f76a0952df3404b37eee1d6e5af80a',15:'502bf180e351d0e85d1c6b590dc6f7228a9e271c28efa7a6d89562139dbac701',16:'899033a800bdd0b772199c7a3bcc82c1beeb0db4bb7702d5e9ff40339e342da9'}
    loaded=[v for v in pins if f'owmc-native-emission-v{v}.dll' in modules]
    if len(loaded)!=1:return 0
    version=loaded[0];path=ROOT/f'native-host/build/owmc-native-emission-v{version}.dll'
    return version if modules.get(path.name)==path.resolve() and hashlib.sha256(path.read_bytes()).hexdigest()==pins[version] else 0

def emission_owner_verified(pid):return emission_owner_version(pid) in (11,12,13,14,15,16)

def process_creation(process):
    times=[ctypes.c_uint64() for _ in range(4)];kernel=process.kernel
    kernel.GetProcessTimes.argtypes=[wintypes.HANDLE]+[ctypes.c_void_p]*4
    kernel.GetProcessTimes.restype=wintypes.BOOL
    if not kernel.GetProcessTimes(process.handle,*[ctypes.byref(t) for t in times]):raise ctypes.WinError(ctypes.get_last_error())
    return times[0].value

def original_emission_callbacks(process):
    """All four calibrated emission11 entrypoints, with no native writes."""
    from prepare_native_emission import PREFIX,FACTORY_PREFIX
    if process.read(process.base+0xd35c20,len(PREFIX))!=PREFIX:return False
    if process.read(process.base+0xd354b0,len(FACTORY_PREFIX))!=FACTORY_PREFIX:return False
    return all(struct.unpack('<Q',process.read(process.base+0x15c8e30+offset,8))[0]==process.base+target
               for offset,target in ((0x110,0xf531f0),(0x158,0xf53270)))

def recover_weapon_terminal_report(process,pid,path):
    """Pinned production gate11: prove original slots before promoting its tmp.

    Entry/tick lifetime experiments are deliberately excluded. A terminal JSON
    claim alone never substitutes for actual original callback pointers.
    """
    try:
        from launch_passthrough_session import installed_modules
        modules=installed_modules(pid);name='owmc-weapon-gate-v11.dll'
        dll=ROOT/'native-host/build'/name
        owners=[n for n in modules if n.startswith('owmc-weapon-gate-v') and n.endswith('.dll')]
        if owners!=[name] or modules.get(name)!=dll.resolve():return None
        if hashlib.sha256(dll.read_bytes()).hexdigest()!='b53f738e2096ebb7043f8fffbb706a98de25e6e42c47be68365a544ef7a5ee51':return None
        request=ROOT/f'native-host/build/weapon-gate-request-{pid}.bin'
        data=request.read_bytes()
        if len(data)!=128 or request.stat().st_mtime<psutil.Process(pid).create_time():return None
        fields=struct.unpack('<8s4I13Q',data)
        if fields[:5]!=(b'OWGATE05',5,128,pid,0) or fields[5]!=process_creation(process):return None
        # Six optional pointers and the authority mask must all be zero.
        # Never infer retirement of a hook from an isolated lifetime experiment.
        if any(fields[11:]):return None
        def prove():
            admin=struct.unpack('<Q',process.read(process.base+0x17b7f90,8))[0]
            if admin!=fields[6] or request.read_bytes()!=data:return False
            for offset,target in ((0x110,0xd44b50),(0x120,0xd44d60),(0x270,0xd456c0)):
                if struct.unpack('<Q',process.read(process.base+0x15d2450+offset,8))[0]!=process.base+target:return False
            return request.read_bytes()==data
        return _recover_terminal_report(process,pid,path,11,prove,
            lambda value:value.get('skillEntryInstalled') is False and value.get('skillTickInstalled') is False)
    except (OSError,ValueError,psutil.Error,struct.error):return None


def _recover_terminal_report(process,pid,path,version,prove,identity=lambda value:True):
    """Recover an unchanged terminal tmp only after actual restoration is proved.

    Native MoveFileEx may lose a Windows sharing race on its final report. The
    worker then closes its stop event, leaving an old enabled main JSON. Never
    accept another owner/version, an earlier process's file, or JSON alone.
    """
    pending=path.with_suffix('.json.tmp')
    try:
        before=pending.stat()
        if not 0<before.st_size<=16384 or before.st_mtime<psutil.Process(pid).create_time():return None
        raw=pending.read_bytes();terminal=json.loads(raw)
        if not isinstance(terminal,dict) or any(type(terminal.get(k)) is not int for k in ('pid','probeVersion','failures')) or terminal.get('pid')!=pid or terminal.get('probeVersion')!=version or terminal.get('enabled') is not False or terminal.get('restored') is not True or terminal.get('failures')!=0 or not identity(terminal):return None
        for attempt in range(8):
            if not prove():return None
            after=pending.stat()
            if (after.st_mtime_ns,after.st_size)!=(before.st_mtime_ns,before.st_size) or pending.read_bytes()!=raw:return None
            try:os.replace(pending,path);return terminal
            except PermissionError:
                if attempt==7:raise
                time.sleep(.03)
    except (FileNotFoundError,ValueError,OSError,psutil.Error,struct.error):return None

def recover_body_terminal_report(process,pid,path):
    # New logic owner retains the same original three-slot callback table.
    # A loaded module, its exact build hash, a current terminal packet and the
    # actual original callback pointers are all required; JSON alone is not proof.
    try:
        from launch_passthrough_session import installed_modules
        modules=installed_modules(pid)
        pins={13:'35208fc277cedca3e3f6b85497ce9b3249e9fd6a8811bb03fa8760add99b861d',14:'7e4c57e491d557c71501000c4ea41407fe973ffb07a277399bb8825ef49323f3',15:'6631271a4e3247aa31f68b56a5d43c165502b9d196430ac40a74ab4cc5ed5cd4',16:'ddc6083e3db42286217292c39e48cb10ab663aa06b2e1bd62c5b53294805cffc',17:'e919c0406d66495468304dd8d8f22bb57d9fc6175b235af5ac7ad056fc471516',18:'dc8e7768b80a4b4dba7579f4db31639e7ecc7254449fdc8593dbefa015c87afe',19:'b54c94dae41563bc6a4df29c75a1c73367a9998bd98eebd56bb093e837b7c8d2',20:'6beb19ccf2f3672ddaac8e059688ab230261ca23308ab9404c414130752b2702',21:'89100f0b219f7f28fd346586bd372bb15abaea1cc8691432ca6e0b7c5af60dd2',22:'cbe392b3dd70607b9330c6cb06daeea8e3f4b82473a6adf3d6ae96f69f04ea68',23:'7d643cfb339448b43532e1d45346f7ee8931f31cc41e9293b8e8f856fac0ca82',24:'f31b3d6620f69a799417c360e00da8af6c34e8d763cd209d3053b76d5800c5a7',25:'941bf7a6232e9cb9dead9b8ef7c6a04c6ea52eb42786c372bd4742b32a2b25c4',26:'66e4e47e68b280a8cc2e699ff3cfd94e231531699cb3a7e1370184540e3156e9'}
        pins.update(BODY_RECOVERY_PINS)
        versions=[v for v in pins if f'owmc-guest-body-v{v}.dll' in modules]
        if len(versions)!=1:return _recover_terminal_report(process,pid,path,10,lambda:original_body_callbacks(process))
        version=versions[0];name=f'owmc-guest-body-v{version}.dll';dll=ROOT/'native-host/build'/name
        owners=[n for n in modules if n.startswith('owmc-guest-body-v') and n.endswith('.dll')]
        if owners==[name] and modules.get(name)==dll.resolve() and hashlib.sha256(dll.read_bytes()).hexdigest()==pins[version]:
            return _recover_terminal_report(process,pid,path,version,lambda:original_body_callbacks(process),
                                            lambda report: 'creation' not in report or report['creation']==process_creation(process))
    except (OSError,ValueError,psutil.Error):pass
    return _recover_terminal_report(process,pid,path,10,lambda:original_body_callbacks(process))

def recover_emission_terminal_report(process,pid,path):
    try:
        def identity(value):
            return (type(value.get('protocol')) is int and value['protocol']==3
                    and type(value.get('creation')) is int and value['creation']==process_creation(process)
                    and emission_owner_verified(pid))
        version=emission_owner_version(pid)
        if version not in (11,12,13,14,15,16):return None
        return _recover_terminal_report(process,pid,path,version,lambda:original_emission_callbacks(process),identity)
    except (OSError,ValueError,psutil.Error):return None

def original_compositor40_restored(process,base):
    """Read-only terminal proof for the exact hash-pinned compositor40 build.

    RVAs/layouts are from this build's COFF symbols and C++ members. Do not
    apply these to another binary. The caller checks its mapped path/hash.
    """
    def q(rva):return struct.unpack('<Q',process.read(base+rva,8))[0]
    # stop() sets finished only after restoring tables, hooks, WndProc, light
    # and frame limit and releasing the retained context/swap references.
    if process.read(base+0x1514ed,3)!=b'\x01\x01\x00':return False
    if q(0x151510) or q(0x151518):return False
    # Independently check every saved user32 prologue against actual memory.
    if process.read(base+0x151340+40,2)!=b'\x00\x01':return False
    start,end=struct.unpack('<2Q',process.read(base+0x151340,16))
    if end<start or (end-start)%24 or not 1<=(end-start)//24<=9:return False
    for at in range(start,end,24):
        target=struct.unpack('<Q',process.read(at,8))[0]
        if process.read(target,16)!=process.read(at+8,16):return False
    if q(0x144240) or process.read(base+0x144240+60,2)!=b'\x00\x01':return False
    if q(0x108020) or process.read(base+0x108020+16,2)!=b'\x00\x01':return False
    if process.read(process.base+0x179f130,4)!=process.read(base+0x108020+12,4):return False
    return True

def recover_compositor_terminal_report(process,pid,path):
    try:
        from launch_passthrough_session import installed_modules
        modules=installed_modules(pid);name='owmc-live-passthrough-v40.dll';dll=ROOT/'native-host/build'/name
        owners=[n for n in modules if n.startswith('owmc-live-passthrough-') and n.endswith('.dll')]
        if owners!=[name] or modules.get(name)!=dll.resolve() or hashlib.sha256(dll.read_bytes()).hexdigest()!='c3b2184bf4a4faae227b0d5ad316c14ec33ca6ff76da218f08849c7c421f6a1a':return None
        handles=(ctypes.c_void_p*512)();needed=wintypes.DWORD();kernel=process.kernel
        if not kernel.K32EnumProcessModulesEx(process.handle,handles,ctypes.sizeof(handles),ctypes.byref(needed),2) or needed.value>ctypes.sizeof(handles):return None
        kernel.K32GetModuleFileNameExW.argtypes=[wintypes.HANDLE,wintypes.HMODULE,wintypes.LPWSTR,wintypes.DWORD]
        kernel.K32GetModuleFileNameExW.restype=wintypes.DWORD
        base=None
        for handle in handles[:needed.value//ctypes.sizeof(ctypes.c_void_p)]:
            value=ctypes.create_unicode_buffer(32768)
            if kernel.K32GetModuleFileNameExW(process.handle,handle,value,len(value)) and Path(value.value).resolve()==dll.resolve():base=handle;break
        if not base:return None
        return _recover_terminal_report(process,pid,path,40,lambda:original_compositor40_restored(process,base),lambda terminal:restoration_complete(terminal,pid,compositor=True))
    except (OSError,ValueError,psutil.Error,struct.error):return None

class NoStopEvent(ValueError):
    pass


def stop(pid,body=False,weapon=False,emissions=False):
    if sum((body,weapon,emissions))>1:raise ValueError('Stop one independent callback owner at a time')
    process=ResearchProcess(pid);kernel=process.kernel
    kernel.OpenEventW.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.LPCWSTR];kernel.OpenEventW.restype=wintypes.HANDLE
    kernel.SetEvent.argtypes=[wintypes.HANDLE]
    event_name=f'Local\\OWMCEmissionStop_{pid}' if emissions else f'Local\\OWMCWeaponGateStop_{pid}' if weapon else f'Local\\OWMCBodyStop_{pid}' if body else f'Local\\OWMCLiveStop_{pid}'
    handle=None
    try:
        prefix='native-emissions' if emissions else 'weapon-gate' if weapon else 'body-sync' if body else 'world-live'
        path=ROOT/f'native-host/build/{prefix}-{pid}.json'
        def recover():
            if body:return recover_body_terminal_report(process,pid,path)
            if emissions:return recover_emission_terminal_report(process,pid,path)
            if weapon:return recover_weapon_terminal_report(process,pid,path)
            if not weapon:return recover_compositor_terminal_report(process,pid,path)
            return None
        for attempt in range(5):
            handle=kernel.OpenEventW(2,False,event_name)
            if handle:break
            open_error=ctypes.get_last_error()
            if open_error not in (0,2):raise ctypes.WinError(open_error)
            recovered=recover()
            if recovered is not None:print(json.dumps(recovered,indent=2));return recovered
            if attempt<4:time.sleep(.1)
        if not handle:
            raise NoStopEvent('No active local passthrough stop event')
        if not kernel.SetEvent(handle):raise ctypes.WinError(ctypes.get_last_error())
        created=psutil.Process(pid).create_time()
        deadline=time.monotonic()+20
        while time.monotonic()<deadline:
            try:
                report=read_report(path)
                if (path.stat().st_mtime>=created
                        and ('creation' not in report or report['creation']==process_creation(process))
                        and restoration_complete(report,pid,compositor=not (body or weapon or emissions))):
                    version=report.get('probeVersion',2 if body else 7)
                    try:
                        (path.parent/f'{prefix}-v{version}-{pid}.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
                    except OSError:
                        pass  # The current report already proves restoration.
                    print(json.dumps(report,indent=2));return report
            except (OSError,ValueError):
                pass  # A mapped owner can restore even before its first report exists.
            recovered=recover()
            if recovered is not None:print(json.dumps(recovered,indent=2));return recovered
            time.sleep(.1)
        raise TimeoutError('Stop requested; restoration still needs an active render/present. Do not reload another module.')
    finally:
        if handle:kernel.CloseHandle(handle)
        process.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pid',type=int,required=True);parser.add_argument('--body',action='store_true',help='Stop only the MC-to-native presentation motor callback');parser.add_argument('--weapon',action='store_true',help='Restore only the original Genji weapon callbacks');parser.add_argument('--emissions',action='store_true',help='Restore only the original projectile initializer hook');args=parser.parse_args();stop(args.pid,args.body,args.weapon,args.emissions)
