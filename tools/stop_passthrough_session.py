"""Normally close this project's original client and save its private MC world."""
import argparse,hashlib,json,os,time,psutil
from pathlib import Path
from modpack.config import paths
from observe_overwatch import ROOT
from launch_passthrough_session import native_pids,api,write_status,PROFILE
from native_normal_close import capture_native_identity,normal_close,NativeCloseError,EXE,PATCHED_SHA256
from native_display_mode import restore_display
from minecraft_save_evidence import capture as capture_save_evidence,inspect as inspect_save_evidence

def stop_supervisor():
    """Stop only this project's exact supervisor; caller manages native owners."""
    target=(ROOT/'tools/launch_passthrough_session.py').resolve()
    for proc in psutil.process_iter(['exe','cmdline']):
        try:
            info=dict(proc.info or {});executable=info.get('exe')
            if not executable or not Path(executable).name.lower()=='python.exe':continue
            args=info.get('cmdline') or []
            matched=any((Path(a) if Path(a).is_absolute() else Path(proc.cwd())/a).resolve()==target for a in args[1:] if not a.startswith('-'))
            if not matched:continue
            # Stop the real Python child first; its venv redirector exits with it.
            interpreter=paths().get('python')
            if (Path(executable).resolve()==interpreter
                    and (interpreter.parent.parent/'pyvenv.cfg').is_file()):continue
            proc.terminate();proc.wait(5)
        except (psutil.NoSuchProcess,psutil.AccessDenied,OSError):continue

def _profile_arguments(arguments):
    """Exact --gameDir argument, never a substring in an unrelated JVM flag."""
    try:
        index=arguments.index('--gameDir')
        return Path(arguments[index+1]).resolve()==PROFILE.resolve()
    except (ValueError,IndexError,OSError):return False


def _project_guest_processes():
    result=[]
    for process in psutil.process_iter(['name','exe','cmdline']):
        try:
            info=dict(process.info or {})
            executable=info.get('exe')
            name=info.get('name') or (Path(executable).name if executable else '')
            if (name.lower() in ('java.exe','javaw.exe')
                    and (not info.get('exe') or info.get('cmdline') is None)):
                raise RuntimeError('Minecraft JVM identity is unreadable; cannot prove absence')
            if (executable and Path(executable).name.lower() in ('java.exe','javaw.exe')
                    and _profile_arguments(info.get('cmdline') or [])):
                result.append(process)
        except (psutil.Error,OSError):continue
    return result


def _guest_identity():
    try:
        health=api('health')
        if (health.get('mode')!='full-world-frame-proof'
                or type(health.get('sourcePid')) is not int or health['sourcePid']<=0):
            raise ValueError('Guest process identity differs')
        guest=psutil.Process(health['sourcePid'])
        if (Path(guest.exe()).name.lower() not in ('java.exe','javaw.exe')
                or not _profile_arguments(guest.cmdline())):
            raise ValueError('Guest process identity differs')
        return dict(process=guest,pid=guest.pid,creation=guest.create_time(),executable=guest.exe(),
                    worldName=health.get('worldName'))
    except (OSError,psutil.NoSuchProcess):
        # A living project JVM with unavailable HTTP is not proof it is absent.
        # Preserve it and refuse a restart which could create another guest.
        if _project_guest_processes():
            raise RuntimeError('Project Minecraft is alive but its identity API is unavailable; preserved')
        return None


def _validate_guest(identity):
    guest=identity['process']
    if not guest.is_running():raise psutil.NoSuchProcess(identity['pid'])
    if (guest.create_time()!=identity['creation']
            or guest.exe()!=identity['executable'] or not _profile_arguments(guest.cmdline())):
        raise ValueError('Guest process identity changed before save')
    health=api('health')
    if health.get('sourcePid')!=identity['pid'] or health.get('mode')!='full-world-frame-proof':
        raise ValueError('Guest process identity changed before save')
    return guest


def _guest_window_identity():
    """Opt-in crash cleanup: match the exact private JVM without trusting HTTP."""
    candidates=_project_guest_processes()
    if not candidates:return None
    if len(candidates)!=1:raise ValueError('Multiple private Minecraft JVMs; preserved')
    guest=candidates[0]
    return dict(process=guest,pid=guest.pid,creation=guest.create_time(),
                executable=guest.exe(),windowCloseOnly=True)


def _close_guest_window(identity):
    import ctypes
    from ctypes import wintypes
    from window_layout import windows_for_pid,_window_class,user32
    guest=identity['process']
    def verify():
        if (not guest.is_running() or guest.create_time()!=identity['creation']
                or guest.exe()!=identity['executable'] or not _profile_arguments(guest.cmdline())):
            raise ValueError('Guest process identity changed before WM_CLOSE')
    verify()
    windows=[w for w in windows_for_pid(guest.pid,visible_only=False) if _window_class(w.handle)=='GLFW30']
    if len(windows)!=1:raise RuntimeError('No unique Minecraft GLFW window; preserved without force')
    verify();owner=wintypes.DWORD();hwnd=wintypes.HWND(windows[0].handle)
    user32.GetWindowThreadProcessId(hwnd,ctypes.byref(owner))
    if owner.value!=guest.pid:raise ValueError('Minecraft window owner changed')
    user32.PostMessageW.argtypes=[wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM]
    user32.PostMessageW.restype=wintypes.BOOL
    if not user32.PostMessageW(hwnd,0x0010,0,0):raise ctypes.WinError(ctypes.get_last_error())
    return guest.wait(45)


def stop_session(keep_minecraft=False,*,output_root=None,allow_window_close=False):
    # All identities are captured before changing the supervisor or either game.
    identities=[];vanished=[]
    for pid in native_pids():
        try:identities.append(capture_native_identity(pid))
        except (psutil.NoSuchProcess,OSError):
            # native_pids already matched the exact executable path. Capture
            # may race its exit, but a recycled/unreadable PID is not a skip.
            if hashlib.sha256(EXE.read_bytes()).hexdigest()!=PATCHED_SHA256:
                raise ValueError('Native executable hash changed during exit')
            if psutil.pid_exists(pid) or native_pids():
                raise ValueError('Native identity changed during capture; preserved')
            vanished.append(dict(pid=pid,executable=str(EXE),sha256=PATCHED_SHA256,
                                 alreadyExited=True,identitySource='exact-path enumeration; PID absence rechecked'))
    try:guest=_guest_identity()
    except RuntimeError:
        if not allow_window_close:raise
        guest=_guest_window_identity()
    folder=Path(output_root) if output_root is not None else ROOT/'research/normal-session-stop'/f'{time.time_ns()}-{os.getpid()}'
    folder.mkdir(parents=True,exist_ok=False)
    record=dict(ready=False,stopped=False,phase='stopping',normalCloseEvidence=str(folder),
                nativeClosePassed=False,worldSaved=None,minecraftKeptRunning=bool(guest),
                forcedNativeTermination=False,nativeNormalClose=[],nativeExitedBeforeCapture=vanished,
                nativeAbsentAtStop=not identities and not vanished,minecraftAbsentAtStop=guest is None,
                minecraftShutdownRequested=False,worldSaveStatus='not-requested-no-live-guest' if guest is None else
                    'kept-running' if keep_minecraft else 'pending',
                nativeStopAction='normal-close' if identities else 'none-already-absent')
    def save():
        (folder/'session-result.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
        write_status(record)
    save()
    save_baseline=None
    if guest:
        record['minecraftIdentity']={key:guest.get(key) for key in ('pid','creation','executable','worldName')}
        record['minecraftIdentity']['profile']=str(PROFILE.resolve())
        if not keep_minecraft:save_baseline=capture_save_evidence(PROFILE,guest.get('worldName'))
        save()
    try:
        stop_supervisor()
        for identity in identities:
            result=normal_close(identity,folder/f"native-{identity['pid']}")
            record['nativeNormalClose'].append(result)
            record.update(nativeExitCode=result['exitCode'],
                          nativeExitClassification=result['nativeExitClassification'],
                          nativeCrashEvidence=result['crashReports'])
            save()
        record['nativeClosePassed']=bool(record['nativeNormalClose']) and all(r.get('normalClosePassed',False) for r in record['nativeNormalClose']) and not vanished
        record['nativeCloseSkipped']=bool(vanished or record['nativeAbsentAtStop'] or any(r.get('alreadyExited') for r in record['nativeNormalClose']))
        record['nativeExitVerified']=True
        # Never restore while any owner/native process remains alive. This also
        # works after stop_supervisor has ended the original lease holder.
        record['desktopRestoration']=restore_display()
        if guest and not keep_minecraft:
            try:
                window_close=guest.get('windowCloseOnly',False)
                if window_close:
                    record['minecraftCloseMethod']='verified-GLFW-WM_CLOSE'
                    record['minecraftShutdownRequested']=True
                    record['worldSaveStatus']='normal-window-close-requested'
                    save()
                    record['minecraftExitCode']=_close_guest_window(guest)
                else:
                    process=_validate_guest(guest)
                    record.update(minecraftCloseMethod='verified-HTTP-shutdown',minecraftShutdownRequested=True,
                                  worldSaveStatus='normal-api-shutdown-requested')
                    save()
                    try:
                        record['minecraftShutdownResponse']=api('shutdown',True)
                        if isinstance(record['minecraftShutdownResponse'],dict) and record['minecraftShutdownResponse'].get('accepted') is False:
                            raise ValueError('Minecraft shutdown request was refused')
                        record['minecraftExitCode']=process.wait(45)
                    except OSError as error:
                        record['minecraftShutdownRequestError']=repr(error)
                        if not allow_window_close:raise
                        if not process.is_running():raise psutil.NoSuchProcess(guest['pid']) from error
                        window_close=True
                        record.update(minecraftCloseMethod='verified-GLFW-after-HTTP-error',
                                      worldSaveStatus='normal-window-close-requested')
                        save()
                        record['minecraftExitCode']=_close_guest_window(guest)
                record['minecraftKeptRunning']=False
                if record['minecraftExitCode']!=0:
                    record.update(worldSaved=False,worldSaveStatus='failed-nonzero-exit')
                    raise RuntimeError('Minecraft save/exit returned a nonzero code')
                evidence=inspect_save_evidence(save_baseline)
                record['minecraftSaveEvidence']=evidence
                if evidence['saveErrors']:
                    record.update(worldSaved=False,worldSaveStatus='failed-save-log-error')
                    raise RuntimeError('Minecraft reported world save errors; save not confirmed')
                # HTTP requests vanilla scheduleStop and waits for normal JVM
                # exit. Keep this established success contract, but separately
                # record whether actual appended save-completion logs prove it.
                verified=evidence['complete']
                record.update(worldSaved=True if verified or not window_close else None,minecraftKeptRunning=False,
                              minecraftSaveUnconfirmed=window_close and not verified,
                              minecraftSaveLogVerified=verified,
                              worldSaveStatus='saved-log-confirmed' if verified else
                                'unconfirmed-normal-window-exit' if window_close else 'normal-api-exit0-log-unconfirmed')
            except psutil.NoSuchProcess:
                # The exact captured psutil object, not another PID occupant.
                if guest['process'].is_running():raise
                evidence=inspect_save_evidence(save_baseline)
                record.update(minecraftAlreadyExited=True,minecraftKeptRunning=False,minecraftSaveEvidence=evidence,
                              worldSaved=True if evidence['complete'] else None,
                              worldSaveStatus='saved-log-confirmed' if evidence['complete'] else 'unconfirmed-already-exited')
        record.update(stopped=True,phase='stopped')
        save()
    except Exception as failure:
        if isinstance(failure,NativeCloseError):
            result=failure.result
            record['nativeNormalClose'].append(result)
            record.update(nativeExitCode=result.get('exitCode'),
                          nativeExitClassification=result.get('nativeExitClassification','normal-close-failed'),
                          nativeCrashEvidence=result.get('crashReports',[]))
        if record['worldSaveStatus'] in ('pending','normal-api-shutdown-requested','normal-window-close-requested'):
            record['worldSaveStatus']='unconfirmed-shutdown-failed' if record['minecraftShutdownRequested'] else 'not-requested-stop-failed'
        if record['minecraftShutdownRequested']:record['minecraftSaveError']=repr(failure)
        record.update(stopped=False,phase='stop-failed',error=repr(failure))
        save()
        raise
    print('Project processes stopped/preserved as requested; worldSaved='+('unknown' if record['worldSaved'] is None else str(record['worldSaved']))+
          '; worldSaveStatus='+record['worldSaveStatus']+
          '; nativeAlreadyExited='+str(bool(vanished or record['nativeAbsentAtStop'] or any(r.get('alreadyExited') for r in record['nativeNormalClose']))))
    return record

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--keep-minecraft',action='store_true',help='Restore/stop native owners and supervisor while preserving the verified guest for controlled A/B tests')
    parser.add_argument('--allow-window-close',action='store_true',help='Crash cleanup only: if HTTP is unavailable, normally close the exact private GLFW window; never force exit or claim a save')
    args=parser.parse_args()
    stop_session(args.keep_minecraft,allow_window_close=args.allow_window_close)
