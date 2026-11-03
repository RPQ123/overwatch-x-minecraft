"""Three-frame depth observation in the exact supplied offline OW build, never replay."""
from pathlib import Path
import argparse
import ctypes
from ctypes import wintypes
import json
import struct
import time
from observe_overwatch import ROOT, ResearchProcess, PoseReader
from attach_host_probe import ModuleEntry, bind
from native_bootstrap_maps import DLL as BOOTSTRAP_DLL,VERSION as BOOTSTRAP_VERSION
from stop_passthrough import read_report
from native_compositor_version import VERSION as COMPOSITOR_VERSION,DLL as COMPOSITOR_DLL
from native_body_version import VERSION as BODY_VERSION,DLL as BODY_DLL
from native_weapon_gate_version import VERSION as GATE_VERSION,DLL as GATE_DLL
from native_emission_version import VERSION as EMISSION_VERSION,DLL as EMISSION_DLL

DLL = ROOT / 'native-host/build/owmc-hand-depth-probe.dll'

def verify_native_hero_before_composition(process):
    # An imported MC frame alone must never conceal a missing native hero.
    from provided_plugin_symbols import provided_plugin
    from observe_native_weapon_states import WeaponStates
    base,image,pdb=provided_plugin(process)
    demo=base+image.symbol_rva(pdb.exact('?isDemo@globals@@3_NA'))
    if process.read(demo,1)!=b'\x01':raise ValueError('Enable the original offline Demo before attaching the compositor')
    sample=WeaponStates(process).sample_weapon()
    if [s['script'] for s in sample['weaponScripts']]!=['0580000000000304']:raise ValueError('Create and enter the calibrated original Genji before composition')

def verify_original_body_table(process):
    reader=PoseReader(process);base=process.base;admin=reader.pointer(base+0x17b7f90)
    items,count,capacity=struct.unpack('<Qii',process.read(admin+0xf0,16))
    if not 0<count<=capacity<=32:raise ValueError('Original movement-system list changed')
    matches=[]
    for address, in struct.iter_unpack('<Q',process.read(items,count*8)):
        if address and reader.pointer(address)==base+0x15c4e28:matches.append(address)
    if len(matches)!=1 or struct.unpack('<3Q',process.read(base+0x15c4e28,24))!=tuple(base+rva for rva in (0xca0960,0xca0800,0xca09c0)):raise ValueError('Previous body callback is not the original restored movement table')

def attach(pid, world_blend=False,pose_observer=False,live_passthrough=False,local_hero=False,empty_scene=False,body_sync=False,weapon_gate=False,emissions=False,bootstrap=False,selection_depth=False,bootstrap_map=0x08000000000002af):
    if empty_scene and not local_hero:raise ValueError('Empty-scene permission only applies to the fixed original hero probe')
    if sum((world_blend,pose_observer,live_passthrough,local_hero,body_sync,weapon_gate,emissions,bootstrap,selection_depth))>1:raise ValueError('Choose one fixed probe mode')
    dll = ROOT/'native-host/build/owmc-selection-depth-v1.dll' if selection_depth else ROOT/'native-host/build'/EMISSION_DLL if emissions else ROOT/'native-host/build'/GATE_DLL if weapon_gate else ROOT/'native-host/build'/BODY_DLL if body_sync else ROOT/'native-host/build/owmc-local-hero-spawn-v1.dll' if local_hero else ROOT/'native-host/build'/COMPOSITOR_DLL if live_passthrough else ROOT/'native-host/build/owmc-pose-observer-v1.dll' if pose_observer else ROOT/'native-host/build/owmc-world-blend-probe.dll' if world_blend else DLL
    if bootstrap:dll=ROOT/'native-host/build'/BOOTSTRAP_DLL
    if not dll.is_file():
        raise FileNotFoundError('Build/test the selected local three-frame probe first')
    if world_blend or live_passthrough:
        import sys
        sys.path.insert(0, str(ROOT/'bridge'))
        from world_frames import MCFrames
        frames = MCFrames()
        try:
            if frames.latest() is None:raise ValueError('No complete fresh Minecraft source')
        finally:
            frames.close()
    verified = ResearchProcess(pid)  # Exact local exe path and full SHA-256 guard.
    if live_passthrough:
        try:verify_native_hero_before_composition(verified)
        except Exception:verified.close();raise
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    close = bind(kernel, 'CloseHandle', wintypes.BOOL, [wintypes.HANDLE])
    snapshot_fn = bind(kernel, 'CreateToolhelp32Snapshot', wintypes.HANDLE, [wintypes.DWORD, wintypes.DWORD])
    first = bind(kernel, 'Module32FirstW', wintypes.BOOL, [wintypes.HANDLE, ctypes.POINTER(ModuleEntry)])
    next_module = bind(kernel, 'Module32NextW', wintypes.BOOL, [wintypes.HANDLE, ctypes.POINTER(ModuleEntry)])
    get_module = bind(kernel, 'GetModuleHandleW', wintypes.HMODULE, [wintypes.LPCWSTR])
    get_address = bind(kernel, 'GetProcAddress', ctypes.c_void_p, [wintypes.HMODULE, ctypes.c_char_p])
    get_owner = bind(kernel, 'GetModuleHandleExW', wintypes.BOOL, [wintypes.DWORD, ctypes.c_void_p, ctypes.POINTER(wintypes.HMODULE)])
    module_name = bind(kernel, 'GetModuleFileNameW', wintypes.DWORD, [wintypes.HMODULE, wintypes.LPWSTR, wintypes.DWORD])
    allocate = bind(kernel, 'VirtualAllocEx', ctypes.c_void_p, [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_size_t, wintypes.DWORD, wintypes.DWORD])
    write = bind(kernel, 'WriteProcessMemory', wintypes.BOOL, [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)])
    create_thread = bind(kernel, 'CreateRemoteThread', wintypes.HANDLE, [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)])
    wait = bind(kernel, 'WaitForSingleObject', wintypes.DWORD, [wintypes.HANDLE, wintypes.DWORD])
    free = bind(kernel, 'VirtualFreeEx', wintypes.BOOL, [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_size_t, wintypes.DWORD])
    open_process = bind(kernel, 'OpenProcess', wintypes.HANDLE, [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD])
    get_times = bind(kernel, 'GetProcessTimes', wintypes.BOOL, [wintypes.HANDLE]+[ctypes.POINTER(wintypes.FILETIME)]*4)
    snapshot = None;process = None;remote = None;thread = None;loader_finished = False
    started_ns = time.time_ns()
    try:
        loader = get_address(get_module('kernel32.dll'), b'LoadLibraryW');owner = wintypes.HMODULE()
        if not loader or not get_owner(6, loader, ctypes.byref(owner)):
            raise ctypes.WinError(ctypes.get_last_error())
        owner_path = ctypes.create_unicode_buffer(32768)
        if not module_name(owner, owner_path, len(owner_path)):
            raise ctypes.WinError(ctypes.get_last_error())
        snapshot = snapshot_fn(0x8 | 0x10, pid)
        if snapshot == ctypes.c_void_p(-1).value:
            snapshot = None
            raise ctypes.WinError(ctypes.get_last_error())
        times=[wintypes.FILETIME() for _ in range(4)]
        if not get_times(verified.handle,*[ctypes.byref(t) for t in times]):raise ctypes.WinError(ctypes.get_last_error())
        created_ns=(((times[0].dwHighDateTime<<32)|times[0].dwLowDateTime)-116444736000000000)*100
        entry = ModuleEntry();entry.dwSize = ctypes.sizeof(entry);success = first(snapshot, ctypes.byref(entry));prior_ranges=[]
        remote_owner = None;module_count = 0;active_emission_owners=set()
        while success:
            module_count += 1
            if module_count > 4096:
                raise ValueError('Module enumeration bound exceeded')
            name = entry.szModule.lower()
            if bootstrap and name.startswith('owmc-session-bootstrap-'):raise ValueError('A native bootstrap is already loaded; cold restart rather than overlay startup owners')
            if name.startswith(('owmc-', 'owhero-')):
                if emissions:
                    current={COMPOSITOR_DLL:('world-live',COMPOSITOR_VERSION),BODY_DLL:('body-sync',BODY_VERSION),GATE_DLL:('weapon-gate',GATE_VERSION)}
                    old={'owmc-native-emission-v1.dll':'native-emissions-v1','owmc-native-emission-v2.dll':'native-emissions-v2','owmc-guest-body-v1.dll':'body-sync-v1','owmc-guest-body-v2.dll':'body-sync-v2','owmc-guest-body-v3.dll':'body-sync-v3','owmc-guest-body-v4.dll':'body-sync-v4','owmc-live-passthrough-v7.dll':'world-live-v7','owmc-live-passthrough-v8.dll':'world-live-v8'}
                    old['owmc-session-bootstrap-v9.dll']='session-bootstrap'
                    old[BOOTSTRAP_DLL]='session-bootstrap'
                    old['owmc-local-hero-spawn-v1.dll']='local-hero'
                    # The bounded depth observer has already restored D3D before
                    # the current compositor was attached. It owns no combat hook.
                    old['owmc-hand-depth-probe.dll']='hand-depth'
                    if name in current:
                        prefix,version=current[name];owner_path_report=dll.parent/f'{prefix}-{pid}.json'
                    elif name in old:owner_path_report=dll.parent/f'{old[name]}-{pid}.json'
                    elif name in tuple(f'owmc-weapon-gate-v{v}.dll' for v in range(1,5)):owner_path_report=ROOT/f'research/{name.removeprefix("owmc-").removesuffix(".dll")}-{pid}.json'
                    else:raise ValueError('This emission observer or an unsupported native module is already loaded')
                    owner_report=json.loads(owner_path_report.read_text())
                    if Path(entry.szExePath).resolve()!=dll.parent/name or owner_report.get('pid')!=pid or owner_path_report.stat().st_mtime_ns<created_ns:raise ValueError('Native callback owner provenance differs')
                    if name in current:
                        if not owner_report.get('enabled') or owner_report.get('failures') or owner_report.get('probeVersion')!=version or time.time_ns()-owner_path_report.stat().st_mtime_ns>4_000_000_000:raise ValueError('Current native callback owner is not live and healthy')
                        active_emission_owners.add(name)
                    elif owner_report.get('enabled') or not owner_report.get('restored') or owner_report.get('failures')!=0:raise ValueError('Retired native callback owner was not restored cleanly')
                    success=next_module(snapshot,ctypes.byref(entry));continue
                if (body_sync or live_passthrough) and name in ('owmc-weapon-gate-v1.dll','owmc-weapon-gate-v2.dll','owmc-weapon-gate-v3.dll','owmc-weapon-gate-v4.dll'):
                    gate_path=dll.parent/f'weapon-gate-{pid}.json';gate=json.loads(gate_path.read_text())
                    if Path(entry.szExePath).resolve()!=dll.parent/name or gate_path.stat().st_mtime_ns<created_ns or gate.get('pid')!=pid or not gate.get('restored') or gate.get('enabled'):raise ValueError('Original weapon callbacks have not been restored')
                    from prepare_weapon_gate import request_data
                    request_data(verified,pid,((times[0].dwHighDateTime<<32)|times[0].dwLowDateTime))
                    success=next_module(snapshot,ctypes.byref(entry));continue
                if (body_sync or live_passthrough) and name in ('owmc-guest-body-v3.dll','owmc-guest-body-v4.dll'):
                    version=int(name.removesuffix('.dll').rsplit('v',1)[1])
                    prior_path=dll.parent/f'body-sync-{pid}.json';prior=json.loads(prior_path.read_text())
                    if prior.get('probeVersion')!=version:prior_path=dll.parent/f'body-sync-v{version}-{pid}.json';prior=json.loads(prior_path.read_text())
                    if Path(entry.szExePath).resolve()!=dll.parent/name or prior_path.stat().st_mtime_ns<created_ns or prior.get('pid')!=pid or prior.get('probeVersion')!=version or not prior.get('restored') or prior.get('enabled'):raise ValueError('Earlier body adapter has not restored its callback')
                    verify_original_body_table(verified)
                    (dll.parent/f'body-sync-v{version}-{pid}.json').write_text(json.dumps(prior,indent=2)+'\n',encoding='utf-8')
                    success=next_module(snapshot,ctypes.byref(entry));continue
                if weapon_gate and name in ('owmc-weapon-gate-v1.dll','owmc-weapon-gate-v2.dll','owmc-weapon-gate-v3.dll','owmc-weapon-gate-v4.dll'):
                    prior_path=ROOT/f'research/{name.removeprefix('owmc-').removesuffix('.dll')}-{pid}.json';prior=json.loads(prior_path.read_text())
                    if Path(entry.szExePath).resolve()!=dll.parent/name or prior_path.stat().st_mtime_ns<created_ns or prior.get('pid')!=pid or not prior.get('restored') or prior.get('enabled'):raise ValueError('Earlier weapon gate was not restored')
                    from prepare_weapon_gate import request_data
                    request_data(verified,pid,((times[0].dwHighDateTime<<32)|times[0].dwLowDateTime))
                    success=next_module(snapshot,ctypes.byref(entry));continue
                if (body_sync or weapon_gate) and name==COMPOSITOR_DLL:
                    # Body adapter owns only the local movement vtable. The
                    # already-running verified compositor retains D3D/WndProc.
                    live=json.loads((dll.parent/f'world-live-{pid}.json').read_text())
                    if Path(entry.szExePath).resolve()!=dll.parent/COMPOSITOR_DLL or live.get('pid')!=pid or live.get('probeVersion')!=COMPOSITOR_VERSION or not live.get('enabled') or live.get('failures')!=0 or (dll.parent/f'world-live-{pid}.json').stat().st_mtime_ns<created_ns:raise ValueError('No current healthy original compositor for body sync')
                    success=next_module(snapshot,ctypes.byref(entry));continue
                if weapon_gate and name in ('owmc-guest-body-v3.dll','owmc-guest-body-v4.dll',BODY_DLL):
                    version=int(name.removesuffix('.dll').rsplit('v',1)[1])
                    body_path=dll.parent/f'body-sync-{pid}.json'
                    if json.loads(body_path.read_text()).get('probeVersion')!=version:body_path=dll.parent/f'body-sync-v{version}-{pid}.json'
                    body=json.loads(body_path.read_text())
                    if Path(entry.szExePath).resolve()!=dll.parent/name or body.get('pid')!=pid or body.get('probeVersion')!=version or body_path.stat().st_mtime_ns<created_ns:raise ValueError('No current original body adapter record')
                    # Weapon tables and the movement-system table are separate.
                    # A stopped body adapter is allowed only after restoration.
                    if not body.get('enabled') and not body.get('restored'):raise ValueError('Body callback was not restored')
                    if body.get('enabled') and body.get('failures'):raise ValueError('Active body adapter failed')
                    success=next_module(snapshot,ctypes.byref(entry));continue
                allowed={'owmc-guest-body-v1.dll':'body-sync-v1','owmc-guest-body-v2.dll':'body-sync-v2','owmc-live-passthrough-v7.dll':'world-live-v7','owmc-live-passthrough-v8.dll':'world-live-v8','owmc-world-blend-probe.dll':'hand-depth','owmc-hand-depth-probe.dll':'hand-depth','owmc-pose-observer-v1.dll':'host-pose','owmc-live-passthrough-v1.dll':'world-live','owmc-live-passthrough-v2.dll':'world-live','owmc-live-passthrough-v5.dll':'world-live','owmc-live-passthrough-v6.dll':'world-live','owmc-local-hero-spawn-v1.dll':'local-hero'}
                allowed['owmc-session-bootstrap-v9.dll']='session-bootstrap'
                allowed[BOOTSTRAP_DLL]='session-bootstrap'
                if not any((world_blend,pose_observer,live_passthrough,local_hero,body_sync,weapon_gate,emissions,bootstrap)):
                    # A bounded, read-only frame diagnostic may follow a fully
                    # restored session. It must never layer over active owners.
                    retired={'owmc-live-passthrough-v30.dll':('world-live',30),
                             'owmc-live-passthrough-v31.dll':('world-live',31),
                             'owmc-live-passthrough-v32.dll':('world-live',32),
                             'owmc-live-passthrough-v33.dll':('world-live',33),
                             'owmc-live-passthrough-v34.dll':('world-live',34),
                             'owmc-live-passthrough-v35.dll':('world-live',35),
                             'owmc-live-passthrough-v36.dll':('world-live',36),
                             'owmc-live-passthrough-v37.dll':('world-live',37),
                             'owmc-live-passthrough-v38.dll':('world-live',38),
                             BODY_DLL:('body-sync',BODY_VERSION),
                             GATE_DLL:('weapon-gate',GATE_VERSION),
                             'owmc-native-emission-v8.dll':('native-emissions',8),
                             'owmc-native-emission-v9.dll':('native-emissions',9),
                             'owmc-native-emission-v10.dll':('native-emissions',10),
                             'owmc-native-emission-v15.dll':('native-emissions',15),
                             EMISSION_DLL:('native-emissions',EMISSION_VERSION)}
                    if name in retired:
                        prefix,version=retired[name]
                        prior=json.loads((dll.parent/f'{prefix}-{pid}.json').read_text())
                        if Path(entry.szExePath).resolve()!=dll.parent/name or prior.get('probeVersion')!=version:
                            raise ValueError('Restored diagnostic owner identity differs')
                        allowed[name]=prefix
                if Path(entry.szExePath).resolve()==dll.resolve() or name not in allowed:raise ValueError('This or an unsupported previous lab probe is loaded; do not reload it')
                old_report=dll.parent/f'{allowed[name]}-{pid}.json'
                if not old_report.is_file() or old_report.stat().st_mtime_ns<created_ns:raise ValueError('No current-process restoration record for old bounded probe')
                prior=json.loads(old_report.read_text())
                if prior.get('pid')!=pid or prior.get('restored') is not True or prior.get('failures')!=0 or prior.get('enabled',False):raise ValueError('Previous probe is active, failed or not restored')
                prior_ranges.append((entry.modBaseAddr,entry.modBaseAddr+entry.modBaseSize))
            if name == Path(owner_path.value).name.lower():
                if Path(entry.szExePath).resolve() != Path(owner_path.value).resolve():
                    raise ValueError('Different loader module path')
                remote_owner = entry.modBaseAddr
            success = next_module(snapshot, ctypes.byref(entry))
        if remote_owner is None:
            raise ValueError('Remote loader owner was not found')
        if emissions and active_emission_owners!={COMPOSITOR_DLL,BODY_DLL,GATE_DLL}:raise ValueError('Current verified compositor, body and native weapon owners are required')
        if prior_ranges:
            reader=PoseReader(verified);engine=reader.pointer(verified.base+0x181e3e0);a=reader.pointer(engine+0x900);b=reader.pointer(a+0x2e0);c=reader.pointer(b);swap=reader.pointer(c+8)
            callback=reader.pointer(reader.pointer(swap)+8*8)
            if any(lo<=callback<hi for lo,hi in prior_ranges):raise ValueError('A previous lab Present callback is still active')
        if bootstrap:
            from prepare_session_bootstrap import prepare
            prepare(verified,pid,((times[0].dwHighDateTime<<32)|times[0].dwLowDateTime),bootstrap_map)
        if local_hero:
            from prepare_local_hero import prepare
            prepare(verified,pid,((times[0].dwHighDateTime<<32)|times[0].dwLowDateTime),empty_scene)
        if weapon_gate:
            from prepare_weapon_gate import prepare
            prepare(verified,pid,((times[0].dwHighDateTime<<32)|times[0].dwLowDateTime))
        if emissions:
            from prepare_native_emission import prepare
            prepare(verified,pid,((times[0].dwHighDateTime<<32)|times[0].dwLowDateTime))
        if body_sync:
            from observe_native_weapon_states import WeaponStates
            reader=WeaponStates(verified);sample=reader.sample_weapon(require_volley=False)
            admin=reader.pointer(verified.base+0x17b7f90);table=verified.read(reader.pointer(admin+0x10),65536)
            controller=reader.entity(table,sample['localId']);reference=reader.component(controller,0x20)
            hero=reader.unpack('<Q',reader.component(controller,0x3f)+0x98)[0]
            model=reader.entity(table,sample['modelId'])
            from native_hero_profiles import HERO_IDS,camera_definition
            if hero not in HERO_IDS:raise ValueError('Body adapter requires a verified beta hero')
            camera_definition(reader.bindings,model)
            if reader.unpack('<I',reference+0x94)[0]!=sample['modelId'] or any(reader.pointer(reader.component(model,kind)+8)!=model for kind in (0x12,0x15)):
                raise ValueError('Body owner changed before attachment')
        remote_loader = remote_owner + loader - owner.value
        # Keep the verified handle open until the second handle is acquired: no PID reuse gap.
        process = open_process(0x100000 | 0x400 | 0x10 | 0x20 | 0x8 | 0x2, False, pid)
        if not process:
            raise ctypes.WinError(ctypes.get_last_error())
        if wait(process, 0) != 0x102:
            raise ValueError('Research process is exited or cannot be waited on')
        path = ctypes.create_unicode_buffer(str(dll.resolve()));copied = ctypes.c_size_t()
        remote = allocate(process, None, ctypes.sizeof(path), 0x3000, 0x04)
        if not remote or not write(process, remote, path, ctypes.sizeof(path), ctypes.byref(copied)) or copied.value != ctypes.sizeof(path):
            raise ctypes.WinError(ctypes.get_last_error())
        thread = create_thread(process, None, 0, remote_loader, remote, 0, None)
        if not thread:
            raise ctypes.WinError(ctypes.get_last_error())
        if wait(thread, 15000) != 0:
            raise TimeoutError('Native loader pending; do not load a second probe')
        loader_finished = True
    finally:
        if remote and (loader_finished or not thread):
            free(process, remote, 0, 0x8000)
        if thread:close(thread)
        if process:close(process)
        if snapshot:close(snapshot)
        verified.close()
    report = dll.parent / (f'native-emissions-{pid}.json' if emissions else f'weapon-gate-{pid}.json' if weapon_gate else f'body-sync-{pid}.json' if body_sync else f'local-hero-{pid}.json' if local_hero else f'world-live-{pid}.json' if live_passthrough else f'host-pose-{pid}.json' if pose_observer else f'hand-depth-{pid}.json')
    if bootstrap:report=dll.parent/f'session-bootstrap-{pid}.json'
    for _ in range(900 if bootstrap else 100):
        if report.is_file() and report.stat().st_mtime_ns >= started_ns:
            try:
                result = read_report(report)
            except json.JSONDecodeError:
                time.sleep(.1);continue
            if bootstrap:
                if result.get('probeVersion')!=BOOTSTRAP_VERSION or result.get('pid')!=pid or result.get('mapId')!=bootstrap_map:raise RuntimeError('Native startup report identity/map differs')
                if result.get('failures'):raise RuntimeError(f'Native startup failed: {result}')
                if result.get('enabled'):time.sleep(.1);continue
                if result.get('phase')!=3 or not result.get('restored'):raise RuntimeError(f'Native startup incomplete: {result}')
                print(json.dumps(result,indent=2));return result
            if weapon_gate or emissions:
                if result.get('pid')!=pid or result.get('failures') or not result.get('enabled') or (emissions and result.get('probeVersion')!=EMISSION_VERSION):raise RuntimeError(f'Original {"emission observer" if emissions else "weapon gate"} did not remain active: {result}')
                print(json.dumps(result,indent=2));return result
            if pose_observer or live_passthrough or body_sync:
                if result['failures']:raise RuntimeError(f'World-camera observer failed: {result}')
                if not result.get('writes' if body_sync else 'poses') and not (body_sync and result.get('menuHeldTicks')):time.sleep(.1);continue
                print(json.dumps(result,indent=2));return result
            if not result['restored'] or result['failures']:
                raise RuntimeError(f'Observation failed: {result}')
            if local_hero and (not result.get('called') or result.get('status')!='original-spawn-completed'):
                raise RuntimeError(f'Original spawn did not complete; never repeat automatically: {result}')
            if world_blend and not result.get('worldBlended'):
                raise RuntimeError(f'No bounded world blend was captured: {result}')
            print(json.dumps(result, indent=2));return result
        time.sleep(.1)
    raise TimeoutError('No completed observation; do not reload. Three-frame stop needs active presents.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid', type=int, required=True)
    parser.add_argument('--world-blend', action='store_true', help='One fused frame within a three-frame auto-restoring probe; no pose/input/motor coupling')
    parser.add_argument('--pose-observer',action='store_true',help='Read-only world-camera publisher, stop event and 120-second ceiling')
    parser.add_argument('--live-passthrough',action='store_true',help='GPU world compositor with original camera and MC movement intent; eight-hour test ceiling, no native combat changes')
    parser.add_argument('--local-hero',action='store_true',help='One original provided-plugin local Genji Spawn, only in a stable world without a local controller')
    parser.add_argument('--empty-scene',action='store_true',help='Allow original hero probe in the explicitly recorded cold zero-map scene experiment')
    parser.add_argument('--body-sync',action='store_true',help='Original Genji presentation motor follows the live MC result; separate movement callback, eight-hour ceiling')
    parser.add_argument('--weapon-gate',action='store_true',help='Scoped original Genji Volley gate experiment; no synthesized damage')
    parser.add_argument('--emissions',action='store_true',help='Original initialized projectile journal with MC acknowledgement; eight-hour lab ceiling')
    parser.add_argument('--bootstrap',action='store_true',help='Cold original Demo/data-pack/empty stage startup on the original UI owner')
    args = parser.parse_args();attach(args.pid, args.world_blend,args.pose_observer,args.live_passthrough,args.local_hero,args.empty_scene,args.body_sync,args.weapon_gate,args.emissions,args.bootstrap)
