"""Prefer the primary desktop mode; lease explicit changes and restore on exit.

Only a hash-verified original offline process can acquire this primary-display
lease. No hook, renderer change, process kill or frame-time resolution polling.
The durable receipt lets normal Stop restore after the supervisor has exited.
"""
from __future__ import annotations
from modpack.config import paths
import ctypes
from ctypes import wintypes as w
import hashlib
import json
import os
from pathlib import Path
import re
import time
import psutil
from observe_overwatch import ROOT, ResearchProcess, PATCHED_SHA256

EXE=paths().get('owExecutable')
LEASE=paths().get('displayLease')
CURRENT=0xffffffff
REGISTERED=0xfffffffe
TEST=2
REGISTRY=1
NO_RESET=0x10000000


class DisplayModeRefused(RuntimeError):
    """A driver refused TEST/apply, distinct from an identity/ownership failure."""


class DisplayModeUnavailable(ValueError):
    """A requested mode cannot be read/enumerated on this display."""


def stored_executable():
    """Package-owned identities survive moving the whole package directory."""
    executable=EXE.resolve();root=ROOT.resolve()
    return executable.relative_to(root).as_posix() if executable.is_relative_to(root) else str(executable)


def receipt_executable_matches(value):
    path=Path(value)
    if not path.is_absolute():
        return '..' not in path.parts and (ROOT/path).resolve()==EXE.resolve()
    if path.resolve()==EXE.resolve():return True
    # Migrate an old absolute receipt only for the same guarded package member.
    # External client paths cannot be adopted by matching a filename.
    if not EXE.resolve().is_relative_to(ROOT.resolve()):return False
    relative=EXE.resolve().relative_to(ROOT.resolve()).parts
    if tuple(p.casefold() for p in path.parts[-len(relative):])!=tuple(p.casefold() for p in relative):return False
    return hashlib.sha256(EXE.read_bytes()).hexdigest()==PATCHED_SHA256


def same_owner(left,right):
    if not receipt_executable_matches(left.get('executable','')) or not receipt_executable_matches(right.get('executable','')):
        return False
    return {k:v for k,v in left.items() if k!='executable'}=={k:v for k,v in right.items() if k!='executable'}


def source_size(width,height):
    """The desktop may be 4K/ultrawide; the unchanged frame wire is <=2560x1440."""
    if width<320 or height<180:raise DisplayModeUnavailable('Invalid primary display size')
    scale=min(1,2560/width,1440/height)
    return [max(320,int(width*scale)//2*2),max(180,int(height*scale)//2*2)]


def display_warning(settings,message):
    warnings=settings.setdefault('displayWarnings',[])
    if message not in warnings:
        warnings.append(message);print(message,flush=True)


def configure_display(settings,backend=None):
    """Read once before both cold loaders; never switch the desktop to match MC.

    Automatic mode is intentionally native even for unusual desktop sizes: the
    actual original renderer supplies its own target size. Source frame scaling
    is independent and does not change the native swapchain or the frame wire.
    This only changes the in-memory session copy, never the player's settings.
    """
    automatic=settings.get('nativeDisplayAuto',True)
    source_automatic=settings.get('sourceResolutionAuto',automatic)
    try:
        current=(backend or WinDisplay()).read(CURRENT)
        if current is None or current.hz<1 or current.bits<1:
            raise DisplayModeUnavailable('Primary display is unavailable')
        desktop=signature(current)
        source=source_size(*desktop[:2]) if source_automatic else source_size(int(settings['width']),int(settings['height']))
        target=desktop if automatic else [int(settings['width']),int(settings['height']),
                                         int(settings.get('nativeRefreshHz',current.hz)),current.bits]
        settings.update(width=source[0],height=source[1],nativeDisplayWidth=target[0],nativeDisplayHeight=target[1])
        if automatic:settings['nativeDisplayTemporary']=True
        plan=dict(automatic=bool(automatic),sourceAutomatic=bool(source_automatic),desktop=desktop,target=target,sourceSize=source,
                  modeChangeRequired=target!=desktop)
    except (OSError,ValueError) as error:
        source=source_size(int(settings.get('width',1920)),int(settings.get('height',1080)))
        settings.update(width=source[0],height=source[1],nativeFullscreen=False)
        message='无法读取主显示器配置，已保留当前桌面并跳过显示模式切换。'
        display_warning(settings,message)
        plan=dict(automatic=bool(automatic),sourceSize=source,modeChangeRequired=False,warning=message,error=str(error))
    settings['displayConfiguration']=plan
    return plan


def requested_size(settings):
    return (int(settings.get('nativeDisplayWidth',settings['width'])),
            int(settings.get('nativeDisplayHeight',settings['height'])))


class Mode(ctypes.Structure):
    _fields_=[('device',w.WCHAR*32),('spec',w.WORD),('driver',w.WORD),
              ('size',w.WORD),('extra',w.WORD),('fields',w.DWORD),
              ('display',w.DWORD*4),('color',w.SHORT),('duplex',w.SHORT),
              ('yres',w.SHORT),('tt',w.SHORT),('collate',w.SHORT),
              ('form',w.WCHAR*32),('dpi',w.WORD),('bits',w.DWORD),
              ('width',w.DWORD),('height',w.DWORD),('flags',w.DWORD),
              ('hz',w.DWORD),('tail',w.DWORD*8)]


class DisplayDevice(ctypes.Structure):
    _fields_=[('size',w.DWORD),('name',w.WCHAR*32),('description',w.WCHAR*128),
              ('flags',w.DWORD),('deviceId',w.WCHAR*128),('deviceKey',w.WCHAR*128)]


def signature(mode):
    if mode is None:raise ValueError('Display mode unavailable during a bounded transition')
    return [mode.width,mode.height,mode.hz,mode.bits]


def same_registered(actual,expected):
    """Registry copy: this machine's driver stores 2560x1440@200 but reads back @60, so
    the registry entry is compared by size/bits only; the live desktop stays exact."""
    return actual[0]==expected[0] and actual[1]==expected[1] and actual[3]==expected[3]


def restoration_readback(display,expected,registry_unavailable=False):
    """Observe a temporarily unavailable driver read, never replay a mode change.

    A real mismatching mode is still an immediate refusal. A new native process
    is also a refusal, even during this bounded observation-only transition.
    """
    deadline=time.monotonic()+6;retries=0
    while True:
        if any_native_running():raise ValueError('Native started during desktop restoration readback')
        actual={name:display.read(index) for name,index in (('current',CURRENT),('registered',REGISTERED))}
        if any_native_running():raise ValueError('Native started during desktop restoration readback')
        for name,mode in actual.items():
            if mode is not None and (signature(mode)!=signature(expected[name]) if name=='current' else not same_registered(signature(mode),signature(expected[name]))):
                raise RuntimeError('Original desktop restoration readback differs')
        if all(mode is not None for mode in actual.values()):return retries
        # Driver without a registry copy (see acquire): the backup registry mode was the live
        # desktop itself, so a matching current mode is the complete restoration evidence.
        if registry_unavailable and actual['current'] is not None and actual['registered'] is None:return retries
        if time.monotonic()>=deadline:raise ValueError('Display mode unavailable during bounded restoration readback')
        retries+=1;time.sleep(.05)


class WinDisplay:
    def __init__(self):
        if ctypes.sizeof(Mode)!=220:raise ValueError('Unsupported DEVMODE layout')
        self.user=ctypes.WinDLL('user32',use_last_error=True)
        self.user.EnumDisplaySettingsW.argtypes=[w.LPCWSTR,w.DWORD,ctypes.POINTER(Mode)]
        self.user.EnumDisplaySettingsW.restype=w.BOOL
        self.user.EnumDisplayDevicesW.argtypes=[w.LPCWSTR,w.DWORD,ctypes.POINTER(DisplayDevice),w.DWORD]
        self.user.EnumDisplayDevicesW.restype=w.BOOL
        self.user.ChangeDisplaySettingsExW.argtypes=[w.LPCWSTR,ctypes.POINTER(Mode),w.HWND,w.DWORD,ctypes.c_void_p]
        self.user.ChangeDisplaySettingsExW.restype=w.LONG
        self.device=None
        for index in range(64):
            device=DisplayDevice();device.size=ctypes.sizeof(device)
            if not self.user.EnumDisplayDevicesW(None,index,ctypes.byref(device),0):break
            if device.flags&1 and device.flags&4:self.device=device.name;break
        if not self.device:raise DisplayModeUnavailable('Cannot identify the primary display')

    def read(self,index):
        deadline=time.monotonic()+2
        while True:
            if index in (CURRENT,REGISTERED):
                # Microsoft's API caches nonzero-index queries until index0
                # refreshes them. Refresh after a real mode switch rather than
                # accepting an old registry snapshot or retrying the mutation.
                refresh=Mode();refresh.size=ctypes.sizeof(refresh)
                self.user.EnumDisplaySettingsW(getattr(self,'device',None),0,ctypes.byref(refresh))
            mode=Mode();mode.size=ctypes.sizeof(mode)
            if self.user.EnumDisplaySettingsW(getattr(self,'device',None),index,ctypes.byref(mode)):return mode
            # Actual original-desktop restoration briefly made CURRENT return
            # false after a successful ChangeDisplaySettings. Observe again;
            # never replay the mode change or retry enumeration's end marker.
            if index not in (CURRENT,REGISTERED) or time.monotonic()>=deadline:return None
            time.sleep(.025)

    def change(self,mode,flags):
        code=self.user.ChangeDisplaySettingsExW(self.device,ctypes.byref(mode),None,flags,None)
        if code!=0:raise DisplayModeRefused(f'Display mode change refused: {code}, flags={flags}')


def verified_native(pid):
    process=psutil.Process(pid);created=process.create_time()
    memory=ResearchProcess(pid)
    try:
        if memory.path.resolve()!=EXE:raise ValueError('Display owner is not the offline client')
    finally:memory.close()
    # The calibrated route uses the primary display only. Never silently change
    # another screen when the original window was moved to a secondary monitor.
    from window_layout import windows_for_pid,MonitorInfo,_window_class,user32
    windows=[item for item in windows_for_pid(pid)
             if item.title.casefold().startswith('overwatch')
             and _window_class(item.handle).casefold()=='tankwindowclass']
    if len(windows)!=1:raise ValueError('Expected one original render window for display mode')
    user32.MonitorFromWindow.argtypes=[w.HWND,w.DWORD];user32.MonitorFromWindow.restype=w.HANDLE
    user32.GetMonitorInfoW.argtypes=[w.HANDLE,ctypes.POINTER(MonitorInfo)]
    info=MonitorInfo();info.size=ctypes.sizeof(info)
    monitor=user32.MonitorFromWindow(w.HWND(windows[0].handle),2)
    if not monitor or not user32.GetMonitorInfoW(monitor,ctypes.byref(info)) or not info.flags&1:
        raise ValueError('Calibrated fullscreen mode requires the primary display')
    if not process.is_running() or process.create_time()!=created:raise ValueError('Native identity changed')
    return dict(pid=pid,created=created,executable=stored_executable())


def any_native_running():
    from process_images import game_images, native_image
    # A name alone can prevent a desktop mode change, never authorize one.
    return any(native_image(name, EXE) for _, name in game_images())


def verified_launch():
    if any_native_running():raise ValueError('检测到守望先锋仍在运行，请先正常退出后再开始游戏。')
    if hashlib.sha256(EXE.read_bytes()).hexdigest()!=PATCHED_SHA256:
        raise ValueError('Offline executable SHA256 differs before display preparation')
    return dict(kind='launch-reservation',pid=os.getpid(),created=psutil.Process().create_time(),executable=stored_executable())


class DisplayLease:
    def __init__(self,path=LEASE,backend=None):
        self.path=Path(path);self.backend=backend

    def display(self):
        if self.backend is None:self.backend=WinDisplay()
        return self.backend

    def load(self):
        return json.loads(self.path.read_text(encoding='utf-8')) if self.path.exists() else None

    def save(self,record):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        temporary=self.path.with_suffix('.tmp')
        temporary.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
        temporary.replace(self.path)

    def acquire(self,pid,settings):
        if not settings.get('nativeFullscreen'):return dict(managed=False,changed=False)
        size=requested_size(settings)
        if not 320<=size[0]<=16384 or not 180<=size[1]<=16384:
            raise DisplayModeUnavailable('Unsupported native fullscreen size')
        verify=verified_launch if pid is None else lambda:verified_native(pid)
        identity=verify();display=self.display()
        previous=self.load()
        if previous and previous['state']!='restored':
            if not same_owner(previous['identity'],identity) or previous['target'][:2]!=list(size):
                raise ValueError('Another display lease needs normal shutdown/recovery first')
            if signature(display.read(CURRENT))!=previous['target'] or (not previous.get('temporary') and signature(display.read(REGISTERED))!=previous['target']):
                raise ValueError('Display changed during this session; not overriding user changes')
            return dict(managed=True,changed=False,receipt=str(self.path))
        current=display.read(CURRENT)
        # The live desktop is authoritative. A different registry mode is not a
        # reason to flash/reset a desktop which already has the requested size.
        refresh=settings.get('nativeRefreshHz') if not settings.get('nativeDisplayAuto',True) else None
        if current is not None and (current.width,current.height)==size and (refresh is None or current.hz==refresh):
            return dict(managed=False,changed=False,mode=signature(current),registeredNotNeeded=True)
        registered=display.read(REGISTERED)
        # Same driver case for a size change: the live desktop is the user's normal
        # mode (user-approved 2026-10-24), so it is also the registry copy to restore.
        registry_unavailable=current is not None and registered is None
        if registry_unavailable:registered=current
        if current is None or registered is None:raise ValueError('Cannot read original desktop mode')
        # This machine's display driver actually returns dmSize188, the legacy
        # public prefix through dmDisplayFrequency, with no private bytes.
        # Every requested field fits that prefix; retain the exact returned
        # size, and refuse truncated fields or unsupported private data.
        if any(m.size not in (Mode.hz.offset+4,ctypes.sizeof(Mode)) or m.extra for m in (current,registered)):
            raise ValueError('Desktop mode needs unsupported driver-private data')
        target_signature=[*size,int(refresh or current.hz),current.bits]
        if signature(current)==signature(registered)==target_signature:
            return dict(managed=False,changed=False,mode=target_signature)
        # Live desktop already is the requested mode; this driver's registry copy differs only in refresh.
        if signature(current)==target_signature and same_registered(signature(registered),target_signature):
            return dict(managed=False,changed=False,mode=target_signature,registryRefreshDiffers=True)
        if pid is not None:
            raise ValueError('Normal restart required: fullscreen mode must precede native renderer startup')
        candidates=[]
        for index in range(512):
            mode=display.read(index)
            if mode is None:break
            if (mode.width,mode.height)==size and mode.bits==current.bits and mode.hz>0:candidates.append(mode)
        if not candidates:raise DisplayModeUnavailable('Requested fullscreen mode/refresh is not enumerated')
        target=min(candidates,key=lambda m:(abs(m.hz-target_signature[2]),m.hz>target_signature[2]))
        if target.size not in (Mode.hz.offset+4,ctypes.sizeof(Mode)) or target.extra:
            raise DisplayModeUnavailable('Requested display mode needs driver-private data')
        target_signature=signature(target)
        target.fields=0x40000|0x80000|0x100000|0x400000
        display.change(target,TEST)
        if verify()!=identity:raise ValueError('Display owner changed before mode switch')
        folder=self.path.parent/('display-backup-'+str(time.time_ns()))
        folder.mkdir(parents=True,exist_ok=False)
        backups={}
        for name,mode in (('current',current),('registered',registered)):
            data=bytes(mode);file=folder/(name+'.bin');file.write_bytes(data)
            backups[name]=dict(path=file.relative_to(self.path.parent).as_posix(),sha256=hashlib.sha256(data).hexdigest(),mode=signature(mode))
        record=dict(schema=2,state='preparing',identity={**identity,'executable':stored_executable()},target=target_signature,backups=backups)
        if registry_unavailable:record['registryUnavailable']=True
        self.save(record)  # Persist original desktop before any actual mutation.
        temporary=bool(settings.get('nativeDisplayTemporary'))
        if temporary:record['temporary']=True;self.save(record)
        # Temporary (dynamic) switch leaves the registry untouched; a reboot also restores the desktop.
        display.change(target,0 if temporary else REGISTRY)
        if signature(display.read(CURRENT))!=target_signature or (not temporary and signature(display.read(REGISTERED))!=target_signature):
            raise DisplayModeRefused('Fullscreen display readback differs; normal stop must restore the receipt')
        record['state']='active';self.save(record)
        return dict(managed=True,changed=True,mode=target_signature,receipt=str(self.path),backup=str(folder))

    def bind(self,pid,settings):
        if not settings.get('nativeFullscreen'):return dict(managed=False,changed=False)
        record=self.load()
        if not record or record['state']=='restored':return self.acquire(pid,settings)
        identity=verified_native(pid)
        if record['identity'].get('kind')=='launch-reservation':
            expected=dict(kind='launch-reservation',pid=os.getpid(),created=psutil.Process().create_time(),executable=stored_executable())
            if not same_owner(record['identity'],expected):raise ValueError('Display reservation belongs to another launcher')
            target=[*requested_size(settings),*record['target'][2:]]
            display=self.display()
            if record['target']!=target or signature(display.read(CURRENT))!=target or (not record.get('temporary') and signature(display.read(REGISTERED))!=target):
                raise ValueError('Prepared fullscreen mode changed during native startup')
            record['identity']=identity;self.save(record)
        elif not same_owner(record['identity'],identity):
            raise ValueError('Display lease belongs to another native process')
        display=self.display()
        if signature(display.read(CURRENT))!=record['target'] or (not record.get('temporary') and signature(display.read(REGISTERED))!=record['target']):
            raise ValueError('Display changed during the native session; normal restart required')
        return dict(managed=True,changed=False,mode=record['target'],receipt=str(self.path))

    def backup_path(self,value,name):
        base=self.path.parent.resolve();path=Path(value)
        if not path.is_absolute():
            if '..' in path.parts:raise ValueError('Display backup is outside its private root')
            path=(base/path).resolve()
        elif not path.resolve().is_relative_to(base):
            # Legacy schema-1 absolute paths may move with a package. Only the
            # exact generated directory/file pair can be remapped, then its
            # full binary checksum is still required below.
            if not re.fullmatch(r'display-backup-\d+',path.parent.name) or path.name!=name+'.bin':
                raise ValueError('Display backup is outside its private root')
            path=(base/path.parent.name/path.name).resolve()
        if not path.is_relative_to(base):raise ValueError('Display backup is outside its private root')
        return path

    def restore(self):
        record=self.load()
        if not record or record['state']=='restored':return dict(managed=False,restored=True)
        if record.get('schema') not in (1,2) or not receipt_executable_matches(record['identity']['executable']):
            raise ValueError('Unknown display receipt identity')
        if any_native_running():raise ValueError('Refusing desktop restoration while a native client is still running')
        display=self.display();modes={}
        if set(record['backups'])!={'current','registered'}:raise ValueError('Incomplete original display backups')
        for name,item in record['backups'].items():
            path=self.backup_path(item['path'],name)
            data=path.read_bytes()
            if len(data)!=ctypes.sizeof(Mode) or hashlib.sha256(data).hexdigest()!=item['sha256']:
                raise ValueError('Original display backup checksum differs')
            mode=Mode.from_buffer_copy(data)
            if signature(mode)!=item['mode']:raise ValueError('Original display backup metadata differs')
            modes[name]=mode
        current=display.read(CURRENT)
        original=signature(modes['current'])
        # After a resolution lease, an already-original desktop size with a
        # different refresh belongs to the user/driver, not to our target. Keep
        # it (including driver readback aliases); refresh-only leases stay exact.
        original_size=(current is not None and record['target'][:2]!=original[:2]
                       and same_registered(signature(current),original))
        if current is not None and (signature(current)==original or original_size):
            # Windows/the user may already have restored the desktop after a
            # reboot or a failed launch. Retire a stale active/preparing receipt
            # without rewriting the registry or blocking the next launch.
            if any_native_running():raise ValueError('Native started during desktop restoration readback')
            preserved_refresh=signature(current)[2]!=original[2]
            record.update(state='restored',restoredAt=time.time(),alreadyOriginal=True,preservedRefresh=preserved_refresh)
            self.save(record)
            return dict(managed=True,restored=True,alreadyOriginal=True,preservedRefresh=preserved_refresh,
                        current=signature(current),receipt=str(self.path))
        allowed=[record['target'],*(signature(m) for m in modes.values())]
        unavailable=bool(record.get('registryUnavailable') or record.get('temporary'))
        before={name:signature(display.read(index)) for name,index in (('current',CURRENT),('registered',REGISTERED))
                if not(unavailable and name=='registered')}
        if unavailable:before['registered']=before['current']
        if before['current'] not in allowed or not any(same_registered(before['registered'],m) for m in allowed):
            raise ValueError('Desktop changed outside the lease; preserving the new user display mode')
        # Only rewrite what differs. A registry copy that already has the right size/bits is
        # left alone: this driver refuses (-2) re-registering 2560x1440@200 and stores @60.
        need_registry=not record.get('temporary') and not same_registered(before['registered'],signature(modes['registered']))
        need_current=before['current']!=signature(modes['current'])
        if need_registry or need_current:
            if any_native_running():raise ValueError('Native started before desktop restoration')
            if need_registry:display.change(modes['registered'],REGISTRY|NO_RESET)
            if any_native_running():raise ValueError('Native started during desktop restoration')
            display.change(modes['current'],0)
        retries=restoration_readback(display,modes,unavailable)
        record.update(state='restored',restoredAt=time.time(),restorationReadbackRetries=retries);self.save(record)
        return dict(managed=True,restored=True,before=before,
                    current=signature(modes['current']),registered=signature(modes['registered']),receipt=str(self.path),readbackRetries=retries)


def prepare_display(settings):
    lease=DisplayLease()
    try:return lease.acquire(None,settings)
    except (DisplayModeRefused,DisplayModeUnavailable) as failure:
        # A failed TEST never mutated anything. A failed apply/readback may
        # already own a receipt: restore it before choosing a desktop fallback.
        record=lease.load()
        if record and record['state']!='restored':lease.restore()
        current=lease.display().read(CURRENT)
        message='系统拒绝了请求的显示模式，已保留桌面原生分辨率继续启动。'
        if current is not None:
            settings.update(nativeDisplayWidth=current.width,nativeDisplayHeight=current.height)
            settings.pop('nativeRefreshHz',None)
            plan=settings.setdefault('displayConfiguration',{})
            plan.update(target=signature(current),modeChangeRequired=False,fallback=True)
            result=dict(managed=False,changed=False,mode=signature(current),fallback='desktop-native')
        else:
            settings['nativeFullscreen']=False
            message='系统拒绝了请求的显示模式，已保留当前桌面并使用游戏窗口继续启动。'
            result=dict(managed=False,changed=False,fallback='unchanged-desktop')
        display_warning(settings,message)
        return dict(result,warning=message,error=str(failure))


def acquire_display(pid,settings):return DisplayLease().bind(pid,settings)
def restore_display():return DisplayLease().restore()
