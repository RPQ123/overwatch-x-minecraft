"""Persistent one-entry offline passthrough startup, with per-process verification."""
import time as _startup_time
_PYTHON_ENTERED_NS=_startup_time.perf_counter_ns()
from modpack.config import paths
import argparse,ctypes,hashlib,json,os,socket,subprocess,sys,time,urllib.error,urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import psutil
from launch_passthrough_guest import prepare,PROFILE
from observe_overwatch import ROOT,ResearchProcess
from attach_hand_depth_probe import attach, NativeLoaderPending
from fill_native_health import fill
from prepare_survival_health import prepare as prepare_health
from hide_native_hero_prompt import hide
from prepare_native_ultimate import prepare as prepare_ultimate
from prepare_native_locomotion import prepare as prepare_locomotion
from prepare_hero_voice_ammo import prepare as prepare_voice_ammo
from prepare_native_emission import prepare as prepare_emission
from prepare_native_roll import prepare as prepare_roll
from prepare_native_blink import prepare as prepare_blink
from prepare_native_skills import prepare as prepare_skills
from prepare_native_meter import prepare as prepare_meter
from prepare_native_melee import prepare as prepare_melee
from prepare_native_sustain import prepare as prepare_sustain
from prepare_native_biotic import prepare as prepare_biotic
from prepare_native_pulse import prepare as prepare_pulse
from prepare_native_recall import prepare as prepare_recall
from prepare_native_wraith import prepare as prepare_wraith
from prepare_native_shadow import prepare as prepare_shadow
from prepare_native_grapple import prepare as prepare_grapple
from prepare_native_mei import prepare as prepare_mei
from prepare_native_junkrat import prepare as prepare_junkrat
from prepare_native_hanzo import prepare as prepare_hanzo
from prepare_native_torb import prepare as prepare_torb
import importlib as _importlib
HERO_PREPARES={}
for _path in sorted(Path(__file__).resolve().parent.glob('prepare_hero_*.py')):
    _module=_importlib.import_module(_path.stem)
    # Voice/tool helpers share this prefix but are not hero binding plugins.
    if isinstance(getattr(_module,'HERO',None),int) and callable(getattr(_module,'prepare',None)):
        HERO_PREPARES.setdefault(_module.HERO,[]).append(_module.prepare)
from native_picker_cursor import PickerCursorRepair
from native_display_mode import acquire_display,prepare_display,restore_display,configure_display
from display_console import start_console_guard,native_startupinfo,reveal_native_render,verified_owner
from native_armory_binding import prepare as prepare_armory,UnsupportedArmory
from window_layout import arrange as arrange_windows
from native_runtime_settings import apply_render_profile
from startup_render_budget import budget as startup_render_budget
from process_images import game_processes
from native_hover_response import apply as apply_hover_response
from native_mccree_profile import apply as apply_mccree_profile
from native_hero_profiles import HERO_IDS
from native_bootstrap_maps import DLL as BOOTSTRAP_DLL,VERSION as BOOTSTRAP_VERSION,MAPS,selected_map,read_loaded_map
from stop_passthrough import read_report
from native_compositor_version import VERSION as COMPOSITOR_VERSION,DLL as COMPOSITOR_DLL
from native_body_version import VERSION as BODY_VERSION,DLL as BODY_DLL
from native_weapon_gate_version import VERSION as GATE_VERSION,DLL as GATE_DLL
from native_emission_version import VERSION as EMISSION_VERSION,DLL as EMISSION_DLL
from native_binding_scope import GuestBindingScope,current_body
from native_crash_evidence import wait_native_crash_reports
from minecraft_crash_evidence import snapshot as minecraft_snapshot,detect as minecraft_crashes,MinecraftCrashError
from minecraft_save_evidence import capture as capture_save_evidence,inspect as inspect_save_evidence
from startup_timeline import StartupTimeline, GuestStartupLog, compositor_summary, guest_summary
from startup_cover import CompositionGate, FRAME_MAX_AGE_MS, LOAD_SECONDS, LoadingTicket, presentation_notice

EXE=paths().get('owExecutable')
BUILD=ROOT/'native-host/build'
STATUS=ROOT/'research/session-status.json'
MODULES={'world-live':COMPOSITOR_VERSION,'body-sync':BODY_VERSION,'weapon-gate':GATE_VERSION,'native-emissions':EMISSION_VERSION}
NATIVE_FILES={'world-live':COMPOSITOR_DLL,'body-sync':BODY_DLL,'weapon-gate':GATE_DLL,'native-emissions':EMISSION_DLL}
MODES={'world-live':'live_passthrough','body-sync':'body_sync','weapon-gate':'weapon_gate','native-emissions':'emissions'}
OBSERVERS=('body-sync','weapon-gate','native-emissions')
STARTUP_TIMELINE=None
WINDOW_REVEALS=set()

class CompositionProgress:
    """A live Present counter cannot hide a frozen last-composed image."""
    def __init__(self):self.identity=None;self.last=None;self.changed_at=0;self.mask_sample=None
    def observe(self,pid,presentation,now):
        identity=(pid,presentation.get('generation'));frame=presentation.get('lastMcFrame')
        if identity!=self.identity:self.identity=identity;self.last=None;self.mask_sample=None
        if frame!=self.last:self.last=frame;self.changed_at=now
        reasons=[]
        if now-self.changed_at>3:reasons.append('Composed Minecraft image has stopped advancing')
        sample=(now,presentation.get('blended',0),presentation.get('unmaskedFrames',0))
        if self.mask_sample and now-self.mask_sample[0]>=1:
            delta=sample[1]-self.mask_sample[1];missing=sample[2]-self.mask_sample[2]
            if delta>20 and missing>=delta:reasons.append('Native foreground mask is missing')
            self.mask_sample=sample
        elif self.mask_sample is None:self.mask_sample=sample
        return reasons

composition_progress=CompositionProgress()

class HeroBindingRefresh:
    """Refresh native movement and calibrated combat channels on each new model."""
    def __init__(self,settings=None):self.identity=None;self.filled_identity=None;self.settings=settings or {};self.health=None;self.warnings=[]
    def refresh(self,pid,body,force=False):
        if body.get('pid')!=pid or body.get('probeVersion')!=BODY_VERSION or not body.get('enabled') or body.get('failures'):
            raise ValueError('No healthy current native body for hero rebinding')
        # A body packet from the first tick after a Nether/End transfer is
        # rebased but not yet stable.  Never initialize health or native
        # ability owners during that hand-off; doing so can bind McCree to the
        # departed Genji model and leave a zero-health floating player.
        if not body.get('worldStable',True):
            raise ValueError('Waiting for stable guest dimension')
        identity=(pid,body.get('hero'),body.get('modelId'),body.get('worldId',1) or 1,
                  body.get('sourcePid',0),body.get('guestGeneration',0),body.get('hostGeneration',0))
        if identity[1] not in HERO_IDS or not identity[2] or not identity[3]:
            raise ValueError('Native hero is outside the verified beta roster')
        same=identity==self.identity
        if same and not force:return False
        # A dimension is a new transport/skill scope, not a new native pawn.
        # Requiring MC20 again here deadlocks an injured surviving hero before
        # its meter/ability bindings can be republished. Guest restart still
        # changes this identity and receives normal new-session initialization.
        pawn_identity=identity[:3]+identity[4:]
        if pawn_identity!=self.filled_identity:self.health=None
        self.warnings=[]
        process=ResearchProcess(pid)
        try:
            # These three use the generic factory channel as their PRIMARY.
            # Publishing it after field/melee/meter preparation loses actual
            # original shots during equip (observed76 factories42..45 while
            # combatReady=false). The native consumer still validates exact
            # current model/creation/typed definitions; MC scope stays guarded.
            early_armory=identity[1] in (0x02e0000000000002,0x02e0000000000003,0x02e000000000006e,0x02e0000000000040)
            if early_armory:prepare_armory(process,pid)
            # Publish E before the new locomotion identity is visible to MC.
            # Otherwise an immediate post-switch E can outrun its owner binding.
            if identity[1]==0x02e000000000006e:prepare_biotic(process,pid)
            if identity[1]==0x02e0000000000002:prepare_skills(process,pid);prepare_wraith(process,pid);prepare_shadow(process,pid)
            if identity[1]==0x02e0000000000003:prepare_pulse(process,pid);prepare_recall(process,pid)
            if identity[1]==0x02e000000000000a:prepare_grapple(process,pid)
            if identity[1]==0x02e00000000000dd:prepare_mei(process,pid)
            if identity[1]==0x02e0000000000065:prepare_junkrat(process,pid)
            if identity[1]==0x02e0000000000005:prepare_hanzo(process,pid)
            if identity[1]==0x02e0000000000006:prepare_torb(process,pid)
            # 新英雄：自动发现 tools/prepare_hero_*.py（模块常量 HERO + prepare(process,pid)），无需改本文件。
            for hero_prepare in HERO_PREPARES.get(identity[1],[]):hero_prepare(process,pid)
            record=prepare_locomotion(process,pid)
            if (pid,record['hero'],record['modelId'])!=identity[:3]:raise ValueError('Native hero changed during binding refresh')
            # Publish the actual primary before slower optional skill/armory
            # preparation, closing the old two-second first-shot loss window.
            if record['hero'] in (0x02e0000000000029,0x02e0000000000042,0x02e0000000000009,0x02e0000000000008):prepare_emission(process,pid,refresh=True)
            # Fill the new hero before the ability readers and HUD settle, so
            # a switch never presents the old 169 HP base pool for a frame.
            if self.settings.get('fillNativeHealth') and pawn_identity!=self.filled_identity:
                self.health=fill(process,pid);self.filled_identity=pawn_identity
            prepare_health(process,pid)
            if record['hero']==0x02e0000000000029:
                prepare_ultimate(process,pid)
            if record['hero']==0x02e0000000000042:
                prepare_roll(process,pid);apply_mccree_profile(process,pid)
            if record['hero']==0x02e0000000000003:prepare_blink(process,pid)
            if record['hero'] in (0x02e0000000000042,0x02e0000000000015,0x02e0000000000029,0x02e0000000000008,0x02e000000000006e,0x02e000000000000a,0x02e0000000000006):prepare_skills(process,pid)
            if record['hero']&0xffff in (2,3,5,6,8,9,10,0x15,0x29,0x40,0x42,0x65,0x6e,0xdd):prepare_melee(process,pid)
            if record['hero']==0x02e0000000000008:apply_hover_response(process,pid)
            if record['hero'] in (0x02e0000000000015,0x02e00000000000dd):prepare_sustain(process,pid)
            # Each beta hero owns the same typed charge/cost primitive IDs, but
            # values are read from the current native model. Genji keeps the
            # Dragonblade-specific controller to avoid two writers; all other
            # verified roster heroes use the generic meter adapter when their
            # local graph exposes both primitives.
            if record['hero'] in HERO_IDS and record['hero']!=0x02e0000000000029:
                prepare_meter(process,pid)
            if not early_armory and record['hero'] in (0x02e0000000000042,0x02e0000000000002,0x02e0000000000003,0x02e000000000006e,0x02e0000000000015,0x02e0000000000006,0x02e000000000000a,0x02e0000000000008,0x02e0000000000005,0x02e00000000000dd,0x02e0000000000040):
                try:prepare_armory(process,pid)
                except UnsupportedArmory as unavailable:
                    # Pharah's independently validated primary was bound above.
                    # Unsupported Barrage variants must not block supervision,
                    # menus or later hero switches. No native guard is relaxed.
                    if record['hero']!=0x02e0000000000008 or unavailable.hero!=record['hero'] or unavailable.model!=record['modelId']:raise
                    current=prepare_locomotion(process,pid)
                    if (current['hero'],current['modelId'])!=(record['hero'],record['modelId']):raise ValueError('Native hero changed during optional armory fallback')
                    self.warnings=[dict(channel='optional-armory',hero=unavailable.hero,modelId=unavailable.model,issues=unavailable.issues)]
            # integrator/voice: optional read-only binding never blocks main recovery.
            try:
                record['heroVoiceAmmo'] = prepare_voice_ammo(process, pid)
            except Exception as voice_error:
                record['heroVoiceAmmo'] = {'optional': True, 'error': str(voice_error)}
            if self.settings.get('hideHeroPrompt'):hide(process,pid)
        finally:process.close()
        if (pid,record['hero'],record['modelId'])!=identity[:3]:raise ValueError('Native hero changed during binding refresh')
        self.identity=identity
        return True
def module_snapshot(kernel,pid):
    # Windows may return ERROR_BAD_LENGTH while the new client loads DLLs.
    # Retry only that transient condition, with a finite bound; all other
    # failures still abort before any attachment or process mutation.
    from attach_host_probe import bind
    from ctypes import wintypes
    create=bind(kernel,'CreateToolhelp32Snapshot',wintypes.HANDLE,[wintypes.DWORD,wintypes.DWORD])
    for attempt in range(10):
        snapshot=create(0x18,pid)
        if snapshot!=ctypes.c_void_p(-1).value:return snapshot
        error=ctypes.get_last_error()
        if error!=24 or attempt==9:raise ctypes.WinError(error)
        time.sleep(.05)

def installed_modules(pid):
    # Inspect what is actually mapped, rather than trusting files left by an old PID.
    from attach_host_probe import ModuleEntry,bind
    from ctypes import wintypes
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    snapshot=module_snapshot(kernel,pid)
    first=bind(kernel,'Module32FirstW',wintypes.BOOL,[wintypes.HANDLE,ctypes.POINTER(ModuleEntry)])
    next_module=bind(kernel,'Module32NextW',wintypes.BOOL,[wintypes.HANDLE,ctypes.POINTER(ModuleEntry)])
    close=bind(kernel,'CloseHandle',wintypes.BOOL,[wintypes.HANDLE]);entry=ModuleEntry();entry.dwSize=ctypes.sizeof(entry);result={}
    try:
        ok=first(snapshot,ctypes.byref(entry))
        while ok:
            if len(result)>4096:raise RuntimeError('Module inventory bound exceeded')
            result[entry.szModule.lower()]=Path(entry.szExePath).resolve()
            ok=next_module(snapshot,ctypes.byref(entry))
        return result
    finally:close(snapshot)
def stage_ready(pid,prefix,created_ns):
    path=BUILD/f'{prefix}-{pid}.json'
    try:state=json.loads(path.read_text());modified=path.stat().st_mtime_ns
    except (OSError,ValueError):return False
    return isinstance(state,dict) and state.get('pid')==pid and state.get('probeVersion')==MODULES[prefix] and state.get('enabled') is True and not state.get('failures') and modified>=created_ns and time.time_ns()-modified<4_000_000_000

def ensure_bootstrap(pid,map_id=MAPS['hollywood']):
    if map_id not in MAPS.values():raise ValueError('Unverified native bootstrap map')
    name=BOOTSTRAP_DLL;loaded=installed_modules(pid)
    family=[n for n in loaded if n.startswith('owmc-session-bootstrap-')]
    if not family:
        # Windows can reuse a PID whose previous run left a successful report.
        attach(pid,bootstrap=True,bootstrap_map=map_id);return
    if family!=[name] or loaded[name]!=(BUILD/name).resolve():raise RuntimeError('A different native bootstrap is loaded; preserve the process')
    path=BUILD/f'session-bootstrap-{pid}.json';prior=read_report(path)
    if (path.stat().st_mtime_ns<int(psutil.Process(pid).create_time()*1e9) or prior.get('pid')!=pid
        or prior.get('probeVersion')!=BOOTSTRAP_VERSION or prior.get('mapId')!=map_id or prior.get('phase')!=3 or not prior.get('restored') or prior.get('failures')):
        raise RuntimeError('Current native startup is pending/failed; preserve the process for diagnosis')
def connect_stages(pid,prefixes=None,*,loading=None,observer_attempts=None):
    created_ns=int(psutil.Process(pid).create_time()*1e9)
    options={'loading':loading} if loading else {}
    for prefix,name in NATIVE_FILES.items():
        if prefixes is not None and prefix not in prefixes:continue
        if loading:loading.checkpoint()
        optional=observer_attempts is not None and prefix in OBSERVERS
        installed=installed_modules(pid)
        family=name.rsplit('-v',1)[0]+'-v'
        others=[n for n in installed if n.startswith(family) and n!=name]
        if others:raise RuntimeError('An earlier native build remains loaded: '+', '.join(others)+'. Restart this offline client before changing native builds.')
        if name in installed:
            if installed[name]!=(BUILD/name).resolve():
                raise RuntimeError('Loaded native stage is unhealthy; do not reload its hooks: '+prefix)
            if not stage_ready(pid,prefix,created_ns):
                if optional:return prefix  # The mapped owner can still publish its first report.
                raise RuntimeError('Loaded native stage is unhealthy; do not reload its hooks: '+prefix)
        elif optional:
            if prefix in observer_attempts:return prefix
            prerequisites=('world-live', *OBSERVERS[:OBSERVERS.index(prefix)])
            if not all(stage_ready(pid,key,created_ns) for key in prerequisites):return prefix
            try:
                attach(pid,**{MODES[prefix]:True},wait_for_report=False)
            except NativeLoaderPending:
                observer_attempts.add(prefix)
                return prefix  # Never race a remote load by requesting another owner.
            except (json.JSONDecodeError, urllib.error.URLError, TimeoutError):
                return prefix
            except FileNotFoundError as failure:
                if failure.filename is None or Path(failure.filename).name not in {
                    f'{key}-{pid}.json' for key in prerequisites
                }:raise
                return prefix
            except ValueError as failure:
                if str(failure) not in (
                    'Unexpected native hero flags/Volley nodes',
                    'No calibrated initial weapon gate profile for this hero',
                    'No calibrated weapon for current hero',
                    'No original native WeaponVolley graph on the local model',
                    'No actual current acknowledged guest world',
                    'Native hero changed while binding emissions',
                    'Local world/controller changed during read',
                ):
                    raise
                return prefix  # Read-only preflight can run again when the hero or world settles.
            observer_attempts.add(prefix)
            try:
                wait('Verifying optional owner '+prefix,lambda:stage_ready(pid,prefix,created_ns),.65,**options)
            except TimeoutError:
                return prefix
        else:
            # The original weapon graph briefly exposes transitional nodes and
            # flags during hero entry. This exact preflight error is read-only
            # and occurs before any DLL is loaded, so retry only this case.
            # Loader, identity, callback and module failures remain fatal.
            attempts=20 if prefix=='weapon-gate' else 1
            for attempt in range(attempts):
                if loading:loading.checkpoint()
                try:
                    arguments={MODES[prefix]:True}
                    if loading and prefix=='world-live':arguments['loading']=loading
                    attach(pid,**arguments);break
                except ValueError as failure:
                    if prefix!='weapon-gate' or 'Unexpected native hero flags/Volley nodes' not in str(failure) or attempt+1==attempts:
                        raise
                    time.sleep(.15)
            wait('Verifying '+prefix,lambda:stage_ready(pid,prefix,created_ns),10,**options)
def api(route,post=False,*,timeout=2):
    with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:32133/'+route,method='POST' if post else 'GET'),timeout=timeout) as response:return json.load(response)

def require_bridge_port():
    with socket.socket() as probe:
        probe.settimeout(.25)
        try:
            occupied = probe.connect_ex(('127.0.0.1', 32133)) == 0
        except TimeoutError:
            return  # A slow check is not proof that a listener exists.
    if occupied:
        raise RuntimeError('本地端口 32133 已被占用。请正常退出旧游戏或占用该端口的程序，再重试。')


def finish_guest_after_native_exit(recovery,record,*,output=None):
    """Persist automatic shutdown provenance instead of swallowing API errors.

    Called only AFTER the existing supervisor observes its native process exit.
    It cannot request native exit and never attaches an owner or forces MC out.
    """
    path=Path(output) if output is not None else ROOT/'research/native-session-exit'/f'{time.time_ns()}-{record.get("nativePid")}.json'
    path.parent.mkdir(parents=True,exist_ok=True)
    process=recovery.identity
    receipt={key:record.get(key) for key in ('nativePid','nativeCreation','nativeExitObservedMs','nativeExitCode','nativeExitClassification','nativeCrashEvidence')}
    receipt.update(nativeCloseRequested=False,source='supervisor-observed-native-exit',
                   nativeExitTrigger='unknown-not-instrumented',worldSaved=None,
                   worldSaveStatus='not-requested-no-live-guest',minecraftShutdownRequested=False,
                   minecraftKeptRunning=None,forcedTermination=False)
    def save():
        path.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    save()
    try:
        receipt['minecraftKeptRunning']=process.is_running()
        if receipt['minecraftKeptRunning']:
            args=process.cmdline();index=args.index('--gameDir')
            health=api('health')
            if (process.pid!=recovery.guest['sourcePid'] or health.get('sourcePid')!=process.pid
                    or health.get('mode')!='full-world-frame-proof'
                    or Path(process.exe()).name.lower() not in ('java.exe','javaw.exe')
                    or index+1>=len(args) or Path(args[index+1]).resolve()!=PROFILE.resolve()
                    or not process.is_running()):
                raise ValueError('Automatic Minecraft shutdown identity changed; preserved')
            receipt['minecraftIdentity']=dict(pid=process.pid,creation=process.create_time(),executable=process.exe(),
                                               profile=str(PROFILE.resolve()),worldName=health.get('worldName'))
            baseline=capture_save_evidence(PROFILE,health.get('worldName'))
            receipt.update(minecraftShutdownRequested=True,minecraftCloseMethod='verified-HTTP-shutdown',worldSaveStatus='normal-api-shutdown-requested')
            save()
            receipt['minecraftShutdownResponse']=api('shutdown',True)
            if isinstance(receipt['minecraftShutdownResponse'],dict) and receipt['minecraftShutdownResponse'].get('accepted') is False:
                raise ValueError('Automatic Minecraft shutdown request was refused')
            receipt['minecraftExitCode']=process.wait(45)
            receipt['minecraftKeptRunning']=False
            receipt['minecraftSaveEvidence']=evidence=inspect_save_evidence(baseline)
            if receipt['minecraftExitCode']!=0 or evidence['saveErrors']:
                receipt.update(worldSaved=False,worldSaveStatus='failed-exit-or-save-log')
            else:
                receipt.update(worldSaved=True,minecraftSaveLogVerified=evidence['complete'],
                               worldSaveStatus='saved-log-confirmed' if evidence['complete'] else 'normal-api-exit0-log-unconfirmed')
    except Exception as error:
        receipt.update(minecraftSaveError=repr(error),worldSaveStatus='unconfirmed-auto-shutdown-error')
        try:receipt['minecraftKeptRunning']=process.is_running()
        except psutil.Error as identity_error:
            receipt.update(minecraftKeptRunning=None,minecraftIdentityError=repr(identity_error))
    finally:
        save()
        record.update(nativeExitReceipt=str(path),worldSaved=receipt['worldSaved'],worldSaveStatus=receipt['worldSaveStatus'],
                      minecraftKeptRunning=receipt['minecraftKeptRunning'],stopped=receipt['minecraftKeptRunning'] is False,ready=False)
    return receipt


def wait(label,fn,seconds=60,*,interval=.05,loading=None):
    print(label,flush=True);deadline=time.monotonic()+seconds;last='not ready'
    while time.monotonic()<deadline:
        if loading:loading.checkpoint()
        try:
            result=fn()
            if result:return result
        except (OSError,ValueError,KeyError,StopIteration) as failure:last=str(failure)
        remaining=deadline-time.monotonic()
        if remaining>0:time.sleep(min(interval,remaining))
    raise TimeoutError(label+': '+last)
def native_pids():
    found=[process.pid for process in game_processes(native=EXE)]
    if len(found)>1:raise RuntimeError('本整合包有多个原版 OW 在运行。请逐个正常退出，再重新启动。')
    return found
def native_ready(pid):
    p=ResearchProcess(pid)
    try:
        from observe_native_weapon_states import WeaponStates
        return WeaponStates(p).sample_weapon(require_volley=False)
    finally:p.close()
def guest_ready(*,timeout=2):
    h=api('health',timeout=timeout);p=h.get('player')
    return h if not h['failed'] and h['published']>2 and p and p['alive'] else None

def first_person_ready(pid):
    """A valid spawned hero is not proof that the native picker was confirmed."""
    from stability_selection import native_view_state
    return native_view_state(pid)['viewMode']==1

class GuestRecovery:
    """The same bounded, creation-aware guest owner serves picker and gameplay."""
    def __init__(self,guest):
        self.guest=guest;self.identity=psutil.Process(guest['sourcePid']);self.retries=0
        self.crash_baseline=minecraft_snapshot(ROOT,[PROFILE])
    def alive(self):return self.identity.is_running()
    def recover(self,record):
        if self.alive():return False
        evidence=minecraft_crashes(self.crash_baseline)
        if evidence:
            record.update(ready=False,phase='minecraft-crashed',minecraftCrashEvidence=evidence,
                          error='Minecraft 客户端崩溃；保留报告并正常关闭残余会话，未自动重启')
            write_status(record)
            raise MinecraftCrashError(evidence)
        if self.retries>=3:raise RuntimeError('Minecraft stopped repeatedly; startup log retained')
        self.retries+=1
        guest=launch_guest(bool(record['settings']['showMinecraft']))
        self.guest=guest;self.identity=psutil.Process(guest['sourcePid'])
        record['settings']={**record['settings'],'worldName':guest['worldName']}
        # prepare() can copy a new guest JAR only after the old process exits.
        guest_jar=PROFILE/'mods/owmc-guest-0.1.0.jar'
        record['loadedFiles']['guest\\build\\libs\\owmc-guest-0.1.0.jar']=hashlib.sha256(guest_jar.read_bytes()).hexdigest()
        record['guestRecovery']={'restarts':self.retries,'sourcePid':guest['sourcePid']}
        return True

def wait_for_selection(pid,settings,recovery,record,*,advance_observers=None):
    native_identity=psutil.Process(pid)
    cursor=PickerCursorRepair(pid,MODULES['world-live'])
    while native_identity.is_running():
        if advance_observers:advance_observers()
        try:cursor.poll();record['pickerCursorReleases']=cursor.released
        except OSError:pass
        if not recovery.alive():
            record.update(ready=False,phase='hero-selection',error='Minecraft process stopped',heartbeatMs=round(time.time()*1000))
            write_status(record)
            recovery.recover(record)
            record.pop('error',None)
        settings=record['settings']
        try:
            if settings.get('fillNativeHealth'):
                process=ResearchProcess(pid)
                try:
                    record['heroHealth']=fill(process,pid)
                finally:process.close()
            if first_person_ready(pid):return
        except (OSError,ValueError):pass
        record.update(ready=False,phase='hero-selection',heartbeatMs=round(time.time()*1000));record.pop('error',None)
        write_status(record)
        time.sleep(.1)
    raise RuntimeError('Original client exited during hero selection')
def launch_guest(visible,timeline=None,*,display_settings=None,loading=None,isolation=None):
    if loading:loading.checkpoint()
    command=prepare(visible=False,timeline=timeline)
    if display_settings is None:
        display_settings=json.loads((ROOT/'passthrough-settings.json').read_text(encoding='utf-8'))
        configure_display(display_settings)
    for flag,key in (('--width','width'),('--height','height')):
        if flag in command:command[command.index(flag)+1]=str(display_settings[key])
        else:command.extend([flag,str(display_settings[key])])
    # Replace prepare()'s defaults rather than leaving contradictory JVM flags.
    command[:]=[value for value in command if not value.startswith(('-Dowmc.startHidden=','-Dowmc.allowWindowShow='))]
    if loading:
        # prepare() keeps pauseOnLostFocus=false and fullscreen=false. The
        # progress window does not cover either renderer. Keep GLFW visible.
        command[:]=[value for value in command if not value.startswith('-Dowmc.backgroundExport=')]
        command[1:1]=['-Dowmc.startHidden=false','-Dowmc.backgroundExport=false']
    else:
        command[1:1]=['-Dowmc.startHidden=true','-Dowmc.allowWindowShow='+str(bool(visible)).lower()]
    (PROFILE/'logs').mkdir(exist_ok=True)
    if timeline:timeline.mark('mc_jvm_spawn_requested')
    with (PROFILE/'logs/launch.log').open('w',encoding='utf-8') as log:
        if loading:loading.checkpoint()
        spawn_options={'startupinfo':native_startupinfo(covered=True)} if loading else {}
        spawn = subprocess.Popen
        if isolation:
            spawn = isolation.spawn
            spawn_options['role'] = 'mc'
        process=spawn(command,cwd=PROFILE,stdout=log,stderr=subprocess.STDOUT,
                      creationflags=subprocess.CREATE_NO_WINDOW,**spawn_options)
    if timeline:timeline.mark('mc_jvm_spawned',pid=process.pid,creation=psutil.Process(process.pid).create_time())
    startup_log=GuestStartupLog(PROFILE/'logs/launch.log',timeline)
    def ready():
        startup_log.poll()
        if loading and process.poll() is not None:
            raise RuntimeError(f'Minecraft 在世界就绪前已退出（0x{process.returncode & 0xffffffff:08X}）。')
        guest=guest_ready(timeout=.25)
        if loading and guest and guest.get('sourcePid')!=process.pid:
            raise RuntimeError('Minecraft 就绪信号来自另一进程。')
        return guest
    guest=wait('Waiting for the real saved Minecraft world',ready,240 if loading else 90,interval=.1,loading=loading)
    startup_log.poll()
    if timeline:timeline.mark('mc_world_ready',pid=guest['sourcePid'],published=guest['published'],guest=guest_summary(guest))
    return guest

def arrange_visible_windows(pid,guest,settings,*,reveal=True):
    if not settings.get('showMinecraft',False):return None
    try:
        result=arrange_windows(pid,int(guest['sourcePid']),
                               int(settings.get('minecraftWindowWidth',960)),
                               int(settings.get('minecraftWindowHeight',540)),
                               native_fullscreen=bool(settings.get('nativeFullscreen',False)),
                               show_minecraft=False)
        if not reveal:return result
        identity=(int(guest['sourcePid']),psutil.Process(int(guest['sourcePid'])).create_time())
        if identity not in WINDOW_REVEALS:
            created_ns=int(psutil.Process(pid).create_time()*1e9)
            if stage_ready(pid,'world-live',created_ns):
                presentation=read_report(BUILD/f'world-live-{pid}.json')
                generation=guest.get('generation')
                composed_generation=presentation.get('lastMcGeneration')
                if (presentation.get('blended',0)>0 and presentation.get('lastMcFrame',0)>0
                        and type(generation) is int and generation!=0 and type(composed_generation) is int
                        and (composed_generation&0xffffffffffffffff)==(generation&0xffffffffffffffff)):
                    response=api('window/show',post=True,timeout=.25)
                    if response.get('accepted'):WINDOW_REVEALS.add(identity)
        return result
    except (OSError,RuntimeError,ValueError,KeyError):
        # GLFW can publish health before its top-level window exists. Retry in
        # the supervision loop without mutating either process.
        return None
def health(pid,binding_body=None):
    created_ns=int(psutil.Process(pid).create_time()*1e9)
    native={}
    for prefix in MODULES:
        if not stage_ready(pid,prefix,created_ns):
            raise ValueError('Native stage is missing, stale or unhealthy: '+prefix)
        native[prefix]=json.loads((BUILD/f'{prefix}-{pid}.json').read_text())
    h=api('health');combat=api('combat')
    if not native['native-emissions'].get('combatReady'):raise ValueError('Current hero has no ready native combat binding; presentation and movement remain active')
    expected=binding_body or native['body-sync']
    if any(native['native-emissions'].get(k)!=expected.get(k) for k in ('hero','modelId')):raise ValueError('Combat acknowledgement belongs to a departed hero')
    reasons=runtime_problems(h,combat,native['world-live'],expected.get('hero'))
    reasons+=binding_problems(combat,native['world-live'],expected)
    reasons+=composition_progress.observe(pid,native['world-live'],time.monotonic())
    if reasons:raise ValueError('; '.join(reasons))
    return {'minecraft':h,'combat':combat,'native':native,'performance':api('performance')}

def binding_problems(combat,lighting,expected):
    reasons=[]
    def differs(actual,keys):
        def value(record,key):
            v=record.get(key)
            # Java serializes an unsigned wire world/session ID as signed long.
            return v&0xffffffffffffffff if key in ('worldId','hostGeneration','guestGeneration') and type(v) is int else v
        return any(value(actual,k)!=value(expected,k) for k in keys)
    movement=combat.get('locomotion') or {}
    if differs(movement,('hero','modelId','worldId')):reasons.append('Locomotion acknowledgement belongs to a departed hero/world')
    if lighting.get('fixedViewLight') and (not lighting.get('viewLightOwned') or lighting.get('viewLightHero')!=expected.get('hero') or lighting.get('viewLightModelId')!=expected.get('modelId') or lighting.get('viewLightWorldId')!=expected.get('worldId') or lighting.get('viewLightVerifiedEpoch')!=lighting.get('viewLightEpoch')):reasons.append('Current hero/world light scope is not acknowledged')
    if expected.get('hero')==0x02e0000000000029:
        dash=combat.get('dashBinding') or {}
        if not dash.get('ready') or differs(dash,('modelId','worldId','hostGeneration')):reasons.append('Current Genji skill scope is not acknowledged')
    if expected.get('hero')==0x02e0000000000042:
        roll=combat.get('roll') or {}
        if not roll.get('ready') or roll.get('modelId')!=expected.get('modelId'):reasons.append('Current McCree roll binding is not acknowledged')
    if expected.get('hero') in HERO_IDS and expected.get('hero')!=0x02e0000000000029:
        meter=combat.get('nativeCharge') or {}
        if not meter.get('ready') or meter.get('hero')!=expected.get('hero'):reasons.append('Current native meter is not acknowledged')
        if differs(meter,('modelId','worldId','hostGeneration')):reasons.append('Native meter acknowledgement belongs to a departed hero/world')
        if expected.get('hero') in (0x02e0000000000002,0x02e0000000000008,0x02e000000000006e,0x02e000000000000a,0x02e0000000000006) and not meter.get('skillsReady'):reasons.append('Current native skills are not acknowledged')
    return reasons

def runtime_problems(guest,combat,presentation,hero=None):
    """Channel readiness only; no claim that attacks or visual acceptance passed."""
    reasons=[]
    player=guest.get('player') or {}
    if guest.get('failed') or guest.get('published',0)<=2 or not player.get('alive'):
        reasons.append('Minecraft world is not ready: '+str(guest.get('error') or 'no live player/frames'))
    if not guest.get('hostPoseConnected') or guest.get('hostPoseFlags')!=1:
        reasons.append('Minecraft has no original native camera')
    generation=presentation.get('generation',0)
    if not generation or guest.get('hostGeneration')!=generation:
        reasons.append('Minecraft camera belongs to a different native session')
    if (presentation.get('blended',0)<=0 or presentation.get('colorUploads',0)<=0
            or presentation.get('lastMcFrame',0)<=0 or presentation.get('lastMcGeneration',0)<=0):
        reasons.append('No Minecraft image has been composited: '
                       f"blended={presentation.get('blended',0)}, "
                       f"uploads={presentation.get('colorUploads',0)}, "
                       f"held={presentation.get('heldFrames',0)}")
    if presentation.get('viewMode')!=1:
        reasons.append('Original hero selection has not entered first person')
    locomotion=combat.get('locomotion') or {}
    if not locomotion.get('ready') or locomotion.get('error'):
        reasons.append('Native hero locomotion is not ready: '+str(locomotion.get('error','no native speed binding')))
    channels=[('projectile',combat.get('feedError'))]
    # Dash and Dragonblade readers are Genji-only. Their deliberate
    # "native hero changed" state must not make McCree/Winston in another
    # Minecraft dimension look unplayable after a hero switch.
    if hero in (None,0x02e0000000000029):
        channels.extend((('dash',combat.get('dashError')),
                         ('ultimate',(combat.get('ultimate') or {}).get('error'))))
    for label,error in channels:
        if error:reasons.append(label+': '+str(error))
    return reasons
def write_status(value):
    if STARTUP_TIMELINE:value['startup']=STARTUP_TIMELINE.summary()
    STATUS.parent.mkdir(exist_ok=True);temp=STATUS.with_suffix('.tmp');temp.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    # Windows readers can momentarily omit FILE_SHARE_DELETE. Telemetry must
    # not terminate the independent gameplay supervisor on that sharing race.
    for attempt in range(12):
        try:temp.replace(STATUS);return True
        except PermissionError:
            if attempt<11:time.sleep(.005)
    return False
def launch_native(settings,map_id,timeline=None,*,guest=None,loading=None,isolation=None):
    # Always read live identities here, after any guest wait, never a cached PID.
    pids=native_pids();pid=pids[0] if pids else None
    if loading and pid:raise RuntimeError('覆盖式启动检测到已有 OW 进程，请先正常关闭。')
    if not pid:
        if loading:loading.checkpoint()
        # A prior supervisor may have exited before restoring its durable lease.
        # Recovery is allowed only before any new native process exists.
        restore_display()
        # Renderer/UI dimensions are cached at creation. A post-creation mode
        # switch can leave a visible but unclickable picker or held composition.
        try:prepare_display(settings)
        except (OSError,ValueError) as failure:
            restore_display()  # A change already made must be restored first.
            settings['nativeFullscreen']=False
            print(f'显示模式不可用，已使用原桌面的窗口模式：{failure}',flush=True)
        # The original game is the user's play/hero-selection window.
        if timeline:timeline.mark('native_spawn_requested')
        # The independent console guard only operates on verified console HWNDs.
        try:
            if loading:loading.checkpoint()
            spawn_options=dict(startupinfo=native_startupinfo(covered=bool(loading)))
            spawn = subprocess.Popen
            if isolation:
                spawn = isolation.spawn
                spawn_options['role'] = 'ow'
            child=spawn([str(EXE)],cwd=EXE.parent,creationflags=subprocess.CREATE_NO_WINDOW,**spawn_options)
            pid=child.pid
        except OSError:
            restore_display()
            raise
        try:start_console_guard(pid)
        except (OSError,ValueError,psutil.Error) as failure:
            print('控制台隐藏辅助程序未启动：'+str(failure),flush=True)
        if timeline:timeline.mark('native_spawned',pid=pid,creation=psutil.Process(pid).create_time())
        native_identity=verified_owner(pid,psutil.Process(pid).create_time())
        native_created=native_identity.create_time()
        def ready_visible():
            if loading and not native_identity.is_running():
                raise RuntimeError(f'OW 在场景就绪前已退出（0x{(child.poll() or 0) & 0xffffffff:08X}）。')
            try:visible=reveal_native_render(pid,native_created,native=native_identity)
            except OSError:
                visible=False  # The original can finish loading while its window is being created.
            if visible and loading and timeline:timeline.mark('loading_native_window_visible')
            return cold_ready(pid,timeline)
        wait('Waiting for the supplied original client/plugin',ready_visible,180 if loading else 150,loading=loading)
    if timeline:timeline.mark('native_client_ready',pid=pid)
    try:startup_render_budget.start(pid,settings,timeline)
    except (OSError, ValueError, RuntimeError) as failure:
        print(f'启动限帧不可用，已继续启动：{failure}',flush=True)
    try:display_mode=acquire_display(pid,settings)
    except (OSError,ValueError) as failure:
        display_mode=dict(managed=False,warning='暂未取得窗口显示模式。')
        print(f'未能读取游戏显示模式，已继续启动：{failure}',flush=True)
    if settings.get('displayWarnings'):display_mode['warning']=settings['displayWarnings'][-1]
    if guest is not None and not loading:arrange_visible_windows(pid,guest,settings,reveal=False)
    if timeline:timeline.mark('native_bootstrap_started')
    if loading:loading.checkpoint()
    ensure_bootstrap(pid,map_id)
    if timeline:timeline.mark('native_bootstrap_finished')
    map_process=ResearchProcess(pid)
    try:
        if read_loaded_map(map_process)!={'state':8,'mapId':map_id}:raise RuntimeError('Actual native backing scene differs from configured nativeMap; cold restart required')
    finally:map_process.close()
    try:has_hero=bool(native_ready(pid))
    except (OSError,ValueError,KeyError,StopIteration):has_hero=False
    if not has_hero:
        if loading:loading.checkpoint()
        if timeline:timeline.mark('native_hero_spawn_started')
        attach(pid,local_hero=True)
    if timeline:timeline.mark('native_hero_spawn_complete',alreadySpawned=has_hero)
    if timeline:timeline.mark('native_weapon_graph_wait_started')
    wait('Waiting for the original Genji model and weapon graph',lambda:native_ready(pid),60 if loading else 45,loading=loading)
    if timeline:timeline.mark('native_weapon_graph_ready')
    return pid,display_mode


def _launch_pair(settings,map_id,guest=None,timeline=None,*,loading=None,isolation=None):
    """Only cold, independent loading can overlap; attachment waits for both."""
    options={'loading':loading} if loading else {}
    if isolation:options['isolation']=isolation
    def verify_world(value):
        if value.get('worldName')!=settings.get('worldName','Overwatch Survival World'):
            raise RuntimeError('Minecraft has a different world/configuration loaded. Stop the game from the launcher, then start again.')
    if guest:
        verify_world(guest)  # Never mutate native state for a wrong existing save.
        if timeline:timeline.mark('mc_world_ready',pid=guest['sourcePid'],adopted=True)
        pid,display_mode=launch_native(settings,map_id,timeline,guest=guest,**options)
    elif settings.get('startupParallel',True):
        # No persistent worker/watcher. The single worker ends on the existing
        # bounded guest-ready wait, including on native failure. Shared hooks
        # are still installed only below, after the future and world check.
        with ThreadPoolExecutor(max_workers=1,thread_name_prefix='owmc-startup') as executor:
            pending=executor.submit(launch_guest,bool(settings['showMinecraft']),timeline=timeline,display_settings=settings,**options)
            pid,display_mode=launch_native(settings,map_id,timeline,**options)
            guest=pending.result()
        verify_world(guest)
    else:
        guest=launch_guest(bool(settings['showMinecraft']),timeline=timeline,display_settings=settings,**options)
        verify_world(guest)
        pid,display_mode=launch_native(settings,map_id,timeline,guest=guest,**options)
    return guest,pid,display_mode

def launch_pair(settings,map_id,guest=None,timeline=None,*,loading=None,isolation=None):
    try:return _launch_pair(settings,map_id,guest,timeline,loading=loading,isolation=isolation)
    finally:
        try:startup_render_budget.restore()
        except (OSError, ValueError, RuntimeError) as failure:
            print(f'启动限帧未能恢复：{failure}',flush=True)


def await_loading_handoff(pid, guest, loading, record, timeline):
    from window_layout import guest_window_owner, render_pair
    native = psutil.Process(pid)
    minecraft = psutil.Process(guest['sourcePid'])
    native_created = native.create_time()
    guest_created = minecraft.create_time()

    def pair():
        if guest_window_owner(paths(), minecraft.pid).create_time() != guest_created:
            raise ValueError('Minecraft 窗口身份已变化。')
        return render_pair(pid, minecraft.pid)

    arranged_ms = round(time.time()*1000)
    gate = CompositionGate()
    last_receipt = None
    fallback = False
    last_report = {}
    last_guest = guest_summary(guest)
    presentation_deadline = time.monotonic() + 15

    def receipt(ow, mc, evidence):
        return dict(evidence, requestId=loading.request_id, supervisorPid=os.getpid(),
                    nativePid=pid, nativeCreated=native_created, nativeHwnd=ow.handle,
                    guestPid=minecraft.pid, guestCreated=guest_created, guestHwnd=mc.handle)

    def publish(value):
        record.update(phase='hero-selection', heartbeatMs=round(time.time()*1000))
        if value:record['startupPresentation']=value
        else:record.pop('startupPresentation',None)
        write_status(record)

    def advance():
        nonlocal last_receipt,fallback,last_report,last_guest
        if loading.state() == 'released':
            if last_receipt is None and not fallback:
                raise RuntimeError('当前请求没有合成回执。')
            return True
        loading.checkpoint()
        if not native.is_running() or not minecraft.is_running():
            raise RuntimeError('交接前游戏进程已退出。请查看本次日志。')
        if fallback:return None
        if time.monotonic() >= presentation_deadline:
            try:
                ow,mc=pair()
                last_receipt=receipt(ow,mc,dict(observedMs=round(time.time()*1000),frameVerified=False))
            except (OSError, ValueError, psutil.Error):
                last_receipt=None  # Leave unverified windows untouched.
            fallback=True
            notice=presentation_notice(last_report,last_guest)
            record['startupPresentationNotice']=notice
            publish(last_receipt)
            timeline.mark('loading_presentation_skipped',report=last_report,guest=last_guest,notice=notice)
            print(notice,flush=True)
            return None
        try:
            ow,mc=pair()
            report=read_report(BUILD/f'world-live-{pid}.json')
            sample=api('health', timeout=.25)
        except (OSError, ValueError, psutil.Error):
            gate.previous=None
            return None
        last_report=compositor_summary(report)
        last_guest=guest_summary(sample)
        now = round(time.time() * 1000)
        evidence = gate.observe(sample, report, pid, minecraft.pid, now)
        if (report.get('probeVersion') != COMPOSITOR_VERSION
                or not stage_ready(pid, 'world-live', int(native_created*1e9))
                or (report.get('sampleWallMs') or 0) < arranged_ms
                or sample.get('worldName') != guest.get('worldName')):
            evidence = None
            gate.previous = None
        if evidence:
            last_receipt=receipt(ow,mc,dict(evidence,frameVerified=True))
            timeline.mark('loading_presentation_ready',report=last_report,guest=last_guest)
            publish(last_receipt)
        elif last_receipt and (now-last_receipt['observedMs'] > FRAME_MAX_AGE_MS or gate.previous is None):
            last_receipt = None
            record.pop('startupPresentation', None)
            record.update(phase='starting', heartbeatMs=now)
            write_status(record)

    wait('Waiting for advancing native composition and launcher handoff', advance, LOAD_SECONDS, interval=.1)
    WINDOW_REVEALS.add((minecraft.pid, guest_created))
    record.pop('startupPresentation', None)
    timeline.mark('loading_handoff')


def initialize_session(settings,timeline,loading,*,isolation=None,observer_attempts=None):
    from configure_passthrough import validate_flight_key
    # Validate before any files, guest launch or native attachment. F7..F11
    # already own portals/mobs/charge and cannot double as flight.
    flight=validate_flight_key(settings.get('flightKey','F6'))
    map_id=selected_map(settings)
    cap=int(settings['hostFps'])
    if not 30<=cap<=240:raise ValueError('Host FPS must be 30..240')
    if loading:loading.checkpoint()
    # Resolve a stale stopped lease before reading the desktop. Both independent
    # cold loaders then receive the same in-memory source/display configuration.
    existing_native = native_pids()
    if loading and existing_native:raise RuntimeError('覆盖式启动需要全新会话，请先正常关闭已有 OW。')
    if not existing_native:restore_display()
    configure_display(settings)
    if timeline:
        timeline.document['strategy']='parallel' if settings.get('startupParallel',True) else 'serial'
        write_status(dict(ready=False,phase='starting',settings=settings,heartbeatMs=round(time.time()*1000)))
    (BUILD/'presentation-fps.txt').write_text(str(cap),encoding='ascii')
    (BUILD/'flight-key.txt').write_text(str(0x70+int(flight[1:])-1),encoding='ascii')
    files=[ROOT/'guest/build/libs/owmc-guest-0.1.0.jar']+[BUILD/name for name in (BOOTSTRAP_DLL,'owmc-local-hero-spawn-v1.dll',COMPOSITOR_DLL,BODY_DLL,GATE_DLL,EMISSION_DLL)]
    from render_optimization import verify as verify_renderer
    renderer=verify_renderer()
    if renderer is not None:files.append(renderer)
    manifest={paths().store_path(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    try:guest=guest_ready(timeout=.25)
    except (OSError,ValueError,KeyError):guest=None
    cold_guest=guest is None
    options={'loading':loading} if loading else {}
    if isolation:options['isolation']=isolation
    if loading and guest:
        raise RuntimeError('覆盖式启动需要全新会话，请先正常关闭已有 Minecraft。')
    if cold_guest:require_bridge_port()
    guest,pid,display_mode=launch_pair(settings,map_id,guest,timeline,**options)
    manifest['guest\\build\\libs\\owmc-guest-0.1.0.jar']=hashlib.sha256((PROFILE/'mods/owmc-guest-0.1.0.jar').read_bytes()).hexdigest()
    if loading:
        try:
            from window_layout import guest_window_owner
            minecraft=guest_window_owner(paths(),guest['sourcePid'])
            arrange_windows(pid,minecraft.pid,covered=True,native_fullscreen=bool(settings.get('nativeFullscreen',False)),
                            show_minecraft=bool(settings.get('showMinecraft',True)))
            if timeline:timeline.mark('loading_windows_arranged')
        except (OSError, ValueError, RuntimeError, psutil.Error) as failure:
            print(f'暂未自动排列窗口，已继续启动：{failure}',flush=True)
    elif cold_guest and settings.get('startupParallel',True):arrange_visible_windows(pid,guest,settings,reveal=False)
    if timeline:timeline.mark('compositor_attach_started')
    stage_options={'loading':loading} if loading else {}
    connect_stages(pid,{'world-live'},**stage_options)
    if timeline:
        try:presentation=read_report(BUILD/f'world-live-{pid}.json')
        except (OSError,ValueError):presentation={}
        timeline.mark('compositor_ready',report=compositor_summary(presentation),guest=guest_summary(guest))
    # The bootstrap's original Genji is initialized behind the animated picker.
    # Install the shared native weapon observers there, before the user can
    # confirm an uncalibrated initial hero. Body coupling still waits for the
    # actual gameplay selection, preserving the original picker animation.
    pending=connect_stages(pid,OBSERVERS,observer_attempts=observer_attempts,**stage_options)
    if pending:
        print(f'原生同步 {pending} 尚在初始化，继续交接游戏窗口。',flush=True)
    if timeline:
        timeline.mark('native_observers_checked')
        timeline.mark('native_observers_pending' if pending else 'native_observers_ready',waitingFor=pending)
    if not loading:arrange_visible_windows(pid,guest,settings)
    if settings.get('hideHeroPrompt'):
        try:
            process=ResearchProcess(pid)
            try:hide(process,pid)
            finally:process.close()
        except (OSError, ValueError, RuntimeError) as failure:
            print(f'原版英雄提示保持原样：{failure}',flush=True)
    record={'ready':False,'phase':'hero-selection','nativePid':pid,'startedMs':round(time.time()*1000),
            'settings':settings,'loadedFiles':manifest,'state':None,'heroHealth':None,
            'nativeDisplayMode':display_mode,'nativeObserversPending':pending}
    if loading:await_loading_handoff(pid,guest,loading,record,timeline)
    return record,guest,pid,files


def run(settings,timeline=None,*,loading=None):
    observer_attempts=set()
    if loading:
        from startup_isolation import StartupIsolation
        loading.checkpoint()
        with StartupIsolation(paths(), loading) as isolation:
            record,guest,pid,files=initialize_session(settings,timeline,loading,isolation=isolation,observer_attempts=observer_attempts)
        timeline.mark('loading_isolation_restored',pendingRecovery=isolation.pending)
    else:
        record,guest,pid,files=initialize_session(settings,timeline,loading,observer_attempts=observer_attempts)
    print('Original animated hero selection over Minecraft; confirm a supported hero to enter gameplay.',flush=True)
    if timeline:timeline.finish('hero-selection',pid=pid)
    recovery=GuestRecovery(guest)
    next_observers=0

    def advance_observers():
        nonlocal next_observers
        previous=record['nativeObserversPending']
        if not previous or time.monotonic()<next_observers:return
        next_observers=time.monotonic()+.5
        pending=connect_stages(pid,OBSERVERS,observer_attempts=observer_attempts)
        record['nativeObserversPending']=pending
        if pending!=previous:
            print(f'原生同步等待 {pending}。' if pending else '原生同步组件已就绪。',flush=True)
            if timeline and not pending:timeline.mark('native_observers_ready')

    wait_for_selection(pid,settings,recovery,record,advance_observers=advance_observers)
    settings=record['settings']
    arrange_visible_windows(pid,recovery.guest,settings)
    try:
        quality_process=ResearchProcess(pid)
        try:quality=apply_render_profile(quality_process,pid,settings.get('nativeRenderProfile','medium'))
        finally:quality_process.close()
    except (OSError,ValueError,RuntimeError) as failure:
        print(f'OW 画质保持原样：{failure}',flush=True)
        quality=dict(profile='unchanged',applied={})
    print('Applied Overwatch video profile: '+quality['profile'],flush=True)
    bindings=HeroBindingRefresh(settings)
    manifest={paths().store_path(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    manifest['guest\\build\\libs\\owmc-guest-0.1.0.jar']=record['loadedFiles']['guest\\build\\libs\\owmc-guest-0.1.0.jar']
    # A player may choose/change heroes while binding. Keep the verified hooks
    # supervised and retry current-owner binding; a missing Genji-only channel
    # on another hero must not terminate startup or prevent later hero switches.
    record.update(nativeRenderProfile=quality['profile'],nativeRenderValues=quality['applied'],
                  loadedFiles=manifest,state=None);write_status(record)
    print('Native adapters connected. Supervising current hero bindings and composition.',flush=True)
    native_identity=psutil.Process(pid)
    native_exit_observer=ResearchProcess(pid)
    native_created=native_identity.create_time()
    scope_reader=GuestBindingScope();next_repair=0;repair_requested=False;next_status=0;failed_binding=None;retry_binding=0
    cursor=PickerCursorRepair(pid,MODULES['world-live'])
    while native_identity.is_running():
        try:
            advance_observers()
            try:cursor.poll();record['pickerCursorReleases']=cursor.released
            except OSError:pass
            if not recovery.alive():raise ValueError('Minecraft process stopped')
            # Even if a Genji-only combat channel is currently unavailable, a
            # confirmed new native model gets its own original movement data.
            arrange_visible_windows(pid,recovery.guest,record['settings'])
            body=read_report(BUILD/f'body-sync-{pid}.json')
            emission=read_report(BUILD/f'native-emissions-{pid}.json')
            body=current_body(body,emission,scope_reader.read(pid),pid)
            key=tuple(body.get(k) for k in ('hero','modelId','sourcePid','guestGeneration','hostGeneration','worldId'))
            if key==failed_binding and time.monotonic()<retry_binding:
                time.sleep(.05);continue
            force=(not emission.get('combatReady') or repair_requested) and time.monotonic()>=next_repair
            try:changed=bindings.refresh(pid,body,force=force);failed_binding=None
            except (OSError,ValueError,KeyError,StopIteration):
                failed_binding=key;retry_binding=time.monotonic()+.25;raise
            if force:next_repair=time.monotonic()+.5
            # Binding discovery stays at50ms; large diagnostic/HTTP snapshots
            # need only4Hz. Do not serialize hundreds of history rows20Hz.
            if not changed and time.monotonic()<next_status:
                time.sleep(.05);continue
            next_status=time.monotonic()+.25
            record['heroHealth']=bindings.health
            record['warnings']=bindings.warnings
            record['hero']={'id':body['hero'],'modelId':body['modelId'],'worldId':body.get('worldId',1),
                            'worldStable':body.get('worldStable',True)}
            state=health(pid,body);repair_requested=False;record.update(ready=bool(state),phase='gameplay',state=state,heartbeatMs=round(time.time()*1000));record.pop('error',None)
            if state:record.pop('startupPresentationNotice',None)
            write_status(record)
        except (OSError,ValueError,KeyError,StopIteration) as failure:
            repair_requested='light scope' not in str(failure)
            if 'Original hero selection has not entered first person' in str(failure):
                record.update(ready=False,phase='hero-selection',heartbeatMs=round(time.time()*1000));record.pop('error',None)
            else:
                notice=record.get('startupPresentationNotice') or str(failure)
                if record.get('nativeObserversPending') and notice==str(failure):
                    notice='OW 已运行，MC 身体或武器同步仍在初始化。请保留本次启动日志。'
                record.update(ready=False,error=notice,heartbeatMs=round(time.time()*1000))
            write_status(record)
            if not recovery.alive():recovery.recover(record)
        time.sleep(.05)
    scope_reader.close()
    record.update(nativeCreation=native_created,nativeExitObservedMs=round(time.time()*1000))
    try:
        code=ctypes.c_ulong();kernel=native_exit_observer.kernel
        kernel.GetExitCodeProcess.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_ulong)]
        if kernel.GetExitCodeProcess(native_exit_observer.handle,ctypes.byref(code)):record['nativeExitCode']=code.value
    finally:native_exit_observer.close()
    # The original exception handler can return0 after a real crash. Preserve
    # its local report; never submit it or infer a healthy exit from the code.
    record['nativeExitClassification']='process-exit-unclassified'
    try:
        crash=wait_native_crash_reports(pid,native_created,EXE)
        if crash:
            record['nativeCrashEvidence']=crash
            record['nativeExitClassification']='crash-report'
            record['error']='Native client produced a matching crash report'
    except OSError as failure:record['nativeCrashInspectionError']=str(failure)
    try:record['desktopRestoration']=restore_display()
    except (OSError,ValueError,RuntimeError) as failure:record['desktopRestorationError']=str(failure)
    finish_guest_after_native_exit(recovery,record)
    write_status(record)
def cold_ready(pid,timeline=None):
    from provided_plugin_symbols import provided_plugin
    from observe_overwatch import PoseReader
    p=ResearchProcess(pid)
    try:
        provided_plugin(p)
        if timeline:timeline.mark('native_plugin_ready',pid=pid)
        r=PoseReader(p);admin=r.pointer(p.base+0x17b7f90)
        return bool(admin and r.pointer(p.base+0x181e3e0))
    finally:p.close()
_IMPORTS_READY_NS=time.perf_counter_ns()
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    settings=json.loads((ROOT/'passthrough-settings.json').read_text(encoding='utf-8'))
    if settings.get('schemaVersion')!=1:raise SystemExit('Unsupported settings version')
    if args.check:print(json.dumps({'settings':settings,'entry':'ow x mc 启动器.exe','modules':MODULES}));raise SystemExit(0)
    kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.CreateMutexW.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_wchar_p];kernel.CreateMutexW.restype=ctypes.c_void_p
    mutex=kernel.CreateMutexW(None,False,'Local\\OWMCPassthroughSessionLauncher')
    if not mutex:raise ctypes.WinError(ctypes.get_last_error())
    if ctypes.get_last_error()==183:print('The session launcher is already running.');raise SystemExit(0)
    STARTUP_TIMELINE=StartupTimeline(ROOT,settings,_PYTHON_ENTERED_NS,_IMPORTS_READY_NS)
    try:
        request=STARTUP_TIMELINE.document['request']
        loading=LoadingTicket.open(ROOT,request['requestId']) if request.get('covered') is True else None
        run(settings,STARTUP_TIMELINE,loading=loading)
    except Exception as failure:
        STARTUP_TIMELINE.finish('failed',error=str(failure))
        failure_record={'ready':False,'error':str(failure),'heartbeatMs':round(time.time()*1000)}
        if isinstance(failure,MinecraftCrashError):
            failure_record.update(phase='minecraft-crashed',minecraftCrashEvidence=failure.evidence)
        # If launch failed before any native client existed, roll back only our
        # durable display lease. Live/partial native owners still require the
        # normal Stop route, never an early display reset or forced termination.
        try:
            if not native_pids():failure_record['desktopRestoration']=restore_display()
        except (OSError,ValueError,RuntimeError) as recovery_failure:
            failure_record['desktopRestorationError']=str(recovery_failure)
        write_status(failure_record)
        raise
    finally:kernel.CloseHandle.argtypes=[ctypes.c_void_p];kernel.CloseHandle(mutex)
