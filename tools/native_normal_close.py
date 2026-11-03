"""Production normal close for the exact offline client, without forced exit.

Reuse the unchanged, accepted ABI verifier's mapped-interface, WM_CLOSE and
precise-console primitives. Keep the same kernel process object for both waits.
No gameplay callback, new native owner or global keyboard input is installed.
"""
from __future__ import annotations
from modpack.config import paths

import contextlib
import ctypes
from ctypes import wintypes
import hashlib
import importlib
import io
import json
from pathlib import Path
import psutil
import struct
import time

from observe_overwatch import ROOT, ResearchProcess, PATCHED_SHA256
from stop_passthrough import process_creation, read_report, restoration_complete, stop
from native_crash_evidence import wait_native_crash_reports
from provided_plugin_symbols import provided_plugin
from repair_provided_shutdown_abi import TARGET, CORRECTED, VTABLE, SLOT, ZERO

EXE = paths().get('owExecutable')
VERIFIER = ROOT / 'tools/verify_provided_shutdown_abi.py'
VERIFIER_SHA256 = '9c201db4bc25f206c554d12940af18af9c105e751b72609b0218f0e773fe8095'
OWNERS = (('native-emissions', {'emissions': True}),
          ('weapon-gate', {'weapon': True}), ('body-sync', {'body': True}),
          ('world-live', {}))
OWNER_FAMILIES = {'native-emissions':'owmc-native-emission-v',
                  'weapon-gate':'owmc-weapon-gate-v',
                  'body-sync':'owmc-guest-body-v',
                  'world-live':'owmc-live-passthrough-v'}


def mapped_callback_owners(pid):
    """A failed startup can end before three of the four owners were loaded."""
    from launch_passthrough_session import installed_modules
    modules=installed_modules(pid)
    result={prefix:{name:str(path) for name,path in modules.items()
                    if name.startswith(family)} for prefix,family in OWNER_FAMILIES.items()}
    if any(len(matches)>1 for matches in result.values()):
        raise ValueError('Multiple mapped callback owners in one family')
    return result


class NativeCloseError(RuntimeError):
    def __init__(self, result):
        self.result = result
        super().__init__(result.get('error', 'Normal native close failed'))


def capture_native_identity(pid):
    native = psutil.Process(pid)
    created = native.create_time()
    process = ResearchProcess(pid)
    try:
        identity = dict(pid=pid, creation=created,
                        creationFiletime=process_creation(process),
                        executable=str(process.path), sha256=PATCHED_SHA256)
    finally:
        process.close()
    validate_native_identity(identity)
    return identity


def validate_native_record(identity):
    """Check the saved identity even when its kernel process has disappeared."""
    path = Path(identity['executable']).resolve()
    if (type(identity['pid']) is not int or identity['pid'] <= 0
            or identity['creation'] <= 0 or identity['creationFiletime'] <= 0
            or path != EXE.resolve() or identity.get('sha256') != PATCHED_SHA256
            or hashlib.sha256(path.read_bytes()).hexdigest() != PATCHED_SHA256):
        raise ValueError('Normal close executable identity/hash differs')
    return path


def validate_native_identity(identity):
    """Refuse a stale PID before any restoration, close or console mutation."""
    path = validate_native_record(identity)
    native = psutil.Process(identity['pid'])
    if (native.create_time() != identity['creation'] or not native.is_running()
            or Path(native.exe()).resolve() != path):
        raise ValueError('Closing native identity changed')
    return native


def confirm_native_exited(identity):
    """Absence is allowed; an unreadable or reused PID is never absence."""
    validate_native_record(identity)
    try:
        native = psutil.Process(identity['pid'])
        if (native.create_time() != identity['creation']
                or Path(native.exe()).resolve() != Path(identity['executable']).resolve()):
            raise ValueError('Closing native identity changed; refusing exit shortcut')
        return not native.is_running()
    except psutil.NoSuchProcess:
        return True


class NativeExitWaiter:
    """Pin one process object; PID reuse cannot change the object being waited."""
    def __init__(self, identity):
        self.identity = identity
        self.handle = None
        kernel = self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.c_void_p] * 4
        kernel.GetProcessTimes.restype = wintypes.BOOL
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.WaitForSingleObject.restype = wintypes.DWORD
        kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel.GetExitCodeProcess.restype = wintypes.BOOL
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self.handle = kernel.OpenProcess(0x100000 | 0x1000, False, identity['pid'])
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            times = [ctypes.c_uint64() for _ in range(4)]
            if not kernel.GetProcessTimes(self.handle, *[ctypes.byref(t) for t in times]):
                raise ctypes.WinError(ctypes.get_last_error())
            if times[0].value != identity['creationFiletime']:
                raise ValueError('Normal close process FILETIME changed')
        except BaseException:
            self.close()
            raise

    def wait(self, seconds):
        value = self.kernel.WaitForSingleObject(self.handle, round(seconds * 1000))
        if value == 0x102:
            raise psutil.TimeoutExpired(seconds, pid=self.identity['pid'])
        if value != 0:
            raise ctypes.WinError(ctypes.get_last_error())
        code = wintypes.DWORD()
        if not self.kernel.GetExitCodeProcess(self.handle, ctypes.byref(code)):
            raise ctypes.WinError(ctypes.get_last_error())
        return code.value

    def close(self):
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None


def _verified_primitives():
    # Lazy import avoids verifier -> stop_session -> helper import recursion.
    # The verifier itself remains byte-for-byte equal to the accepted version.
    if hashlib.sha256(VERIFIER.read_bytes()).hexdigest() != VERIFIER_SHA256:
        raise ValueError('Accepted normal-close verifier identity differs')
    return importlib.import_module('verify_provided_shutdown_abi')


def _current_restoration(report, path, identity, prefix):
    if path.stat().st_mtime < identity['creation']:
        return False
    if 'creation' in report and report['creation'] != identity['creationFiletime']:
        return False
    return restoration_complete(report, identity['pid'], compositor=prefix == 'world-live')


def inspect_shutdown_system(process, *, observed=None):
    """Read current EA registry and cached singleton; never repair either one.

    A stale singleton is not evidence of destruction. Keep its raw pointer,
    type and owner separate from the system actually registered in current EA.
    """
    plugin, _, _ = provided_plugin(process)
    if hashlib.sha256(TARGET.read_bytes()).hexdigest() != CORRECTED:
        raise ValueError('Corrected plugin is not installed')

    def q(address):
        return struct.unpack('<Q', process.read(address, 8))[0]

    errors = {}
    def optional_q(label, address):
        try:
            return q(address)
        except (OSError, ValueError) as error:
            errors[label] = repr(error)
            return None

    admin = q(process.base + 0x17b7f90)
    cached = q(plugin + 0x2d0338)
    vtable = optional_q('singletonVtable', cached)
    owner = optional_q('singletonAdmin', cached + 8) if cached else None
    if observed is not None:
        # Preserve the requested raw roots even if the remaining registry is
        # already unavailable during teardown. This is diagnostic evidence,
        # never an incomplete proof accepted by shutdown_snapshot().
        observed.update(pluginBase=plugin, base=process.base, admin=admin,
                        cachedSingleton=cached, cachedSingletonVtable=vtable,
                        cachedSingletonAdmin=owner, rootPointersRead=True)
    header = process.read(admin + 0xd8, 16)
    items, count, capacity = struct.unpack('<Qii', header)
    if not 1 <= count <= capacity <= 512:
        raise ValueError('Current admin system array bounds')
    raw = process.read(items, count * 8)
    registered = []
    for address, in struct.iter_unpack('<Q', raw):
        if q(address) == plugin + VTABLE:
            registered.append(dict(instance=address, admin=q(address + 8)))
    slot = q(plugin + SLOT)
    zero = process.read(plugin + ZERO, 3)
    stable = (q(process.base + 0x17b7f90) == admin
              and q(plugin + 0x2d0338) == cached
              and q(plugin + SLOT) == slot and process.read(plugin + ZERO, 3) == zero
              and process.read(admin + 0xd8, 16) == header
              and process.read(items, count * 8) == raw
              and all(q(row['instance']) == plugin + VTABLE
                      and q(row['instance'] + 8) == row['admin'] for row in registered))
    if vtable is not None:
        stable = stable and optional_q('singletonVtableRecheck', cached) == vtable
    if owner is not None:
        stable = stable and optional_q('singletonAdminRecheck', cached + 8) == owner
    current = [row for row in registered if row['admin'] == admin]
    rebound = (stable and vtable == plugin + VTABLE and owner not in (None, 0, admin)
               and len(registered) == 1 and len(current) == 1
               and current[0]['instance'] != cached)
    classification = ('current-admin-replacement' if rebound else
                      'current-singleton' if stable and len(registered) == 1
                      and current and current[0]['instance'] == cached and owner == admin else
                      'singleton-null' if not cached else
                      'singleton-type-unreadable-or-changed' if vtable != plugin + VTABLE else
                      'singleton-admin-mismatch-unresolved')
    return dict(pluginBase=plugin, admin=admin, cachedSingleton=cached,
                cachedSingletonVtable=vtable, cachedSingletonAdmin=owner,
                expectedVtable=plugin + VTABLE, registeredSystems=registered,
                systemCount=count, slot=slot, expected=plugin + ZERO,
                zeroBytes=zero.hex(), mappedAbiValid=slot == plugin + ZERO and zero == b'\x33\xc0\xc3',
                diskSha256=CORRECTED, stable=bool(stable), classification=classification,
                readErrors=errors)


def shutdown_snapshot(process, primitives):
    """Retain the protected verifier; accept only a proved current replacement.

    No fallback for a missing/destructed/unknown singleton, incomplete registry,
    changed ABI, read failure or an admin changing during observation.
    """
    try:
        return primitives.snapshot(process)
    except ValueError as error:
        if str(error) != 'System singleton does not belong to current admin':
            raise
        state = inspect_shutdown_system(process)
        if (not state['stable'] or not state['mappedAbiValid'] or state['readErrors']
                or state['classification'] != 'current-admin-replacement'):
            raise ValueError('No proved current-admin replacement; normal close refused: ' +
                             json.dumps(state, sort_keys=True)) from error
        return dict(**state, instance=state['registeredSystems'][0]['instance'],
                    verificationRoute='current-admin-registry',
                    originalVerifierError=str(error))


def native_top_level_windows(pid):
    """Enumerate every owned top-level window, including hidden/zero-area ones."""
    user = ctypes.WinDLL('user32', use_last_error=True)
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user.GetWindowThreadProcessId.restype = wintypes.DWORD
    user.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user.GetClassNameW.restype = ctypes.c_int
    user.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
    user.EnumWindows.restype = wintypes.BOOL
    windows, errors = [], []

    @callback_type
    def visit(hwnd, _):
        # Never raise through a ctypes callback: Python would discard it and
        # an incomplete enumeration could look like "no render window".
        try:
            owner = wintypes.DWORD()
            if not user.GetWindowThreadProcessId(hwnd, ctypes.byref(owner)):
                errors.append('Top-level window owner unavailable')
                return False
            if owner.value == pid:
                name = ctypes.create_unicode_buffer(256)
                if not user.GetClassNameW(hwnd, name, len(name)):
                    errors.append('Native top-level window class unavailable')
                    return False
                windows.append(dict(hwnd=int(hwnd), className=name.value))
            return True
        except Exception as error:
            errors.append('Top-level window enumeration callback failed: ' + repr(error))
            return False

    complete = user.EnumWindows(visit, 0)
    if errors:
        raise RuntimeError('; '.join(errors))
    if not complete:
        raise ctypes.WinError(ctypes.get_last_error())
    return windows


def _try_self_destructed_pause(identity, primitives, out):
    """Prove terminal shutdown before touching a possibly destroyed EA.

    The hash-protected acknowledge primitive observes the exact console/PID,
    requires original exit0 + shutdown + pause text BEFORE sending Return,
    and rechecks creation. No owner restoration or WM_CLOSE is used here.
    """
    # Cheap, independent liveness check also avoids console/window inspection
    # after the identity's original process has already disappeared.
    try:
        native = psutil.Process(identity['pid'])
        if (native.create_time() != identity['creation']
                or Path(native.exe()).resolve() != Path(identity['executable']).resolve()):
            raise ValueError('Native identity changed before terminal pause inspection')
        if not native.is_running():
            return None
    except psutil.NoSuchProcess:
        return None
    windows = native_top_level_windows(identity['pid'])
    if any(window['className'] != 'ConsoleWindowClass' for window in windows):
        return None
    probe = out['selfDestructedPauseProbe'] = dict(windows=windows)
    reports = wait_native_crash_reports(identity['pid'], identity['creation'],
                                       Path(identity['executable']), seconds=1)
    probe['crashReports'] = reports
    if reports:
        raise RuntimeError('Matching crash report forbids self-destructed pause acknowledgement')
    validate_native_identity(identity)
    probe['windowsRecheck'] = native_top_level_windows(identity['pid'])
    if any(window['className'] != 'ConsoleWindowClass' for window in probe['windowsRecheck']):
        return None
    try:
        acknowledgement = primitives.acknowledge_shutdown_pause(identity['pid'], identity['creation'], 0)
    except ValueError as error:
        # The protected primitive sends no input when its observed text does
        # not prove the original shutdown pause. Preserve the normal path.
        if str(error) == 'No verified original shutdown pause; no input sent':
            probe['notPaused'] = str(error)
            return None
        raise
    text = acknowledgement.get('observedText', '')
    if (acknowledgement.get('acknowledged') is not True
            or acknowledgement.get('globalKeyboardInput') is not False
            or identity['pid'] not in acknowledgement.get('consolePids', [])
            or 'Process exit initiazed: 0' not in text or 'shutdown' not in text
            or not any(marker in text for marker in ('请按任意键', 'Press any key', 'press any key'))):
        raise ValueError('Protected terminal pause acknowledgement evidence is incomplete')
    return acknowledgement


def normal_close(identity, folder):
    """Finish a proved terminal pause, or strictly restore/close the live game.

    Any failure remains failed evidence and raises. There is deliberately no
    terminate/kill, no menu Exit shortcut and no retry with weaker restoration.
    """
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=False)
    out = {**identity, 'passed': False, 'normalClosePassed': False,
           'requestedNormalClose': True, 'forcedTermination': False,
           'restoration': {}, 'verifierSha256': VERIFIER_SHA256}
    process = waiter = None
    failure = None

    def save():
        (folder / 'result.json').write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8')

    try:
        validate_native_identity(identity)
        primitives = _verified_primitives()
        waiter = NativeExitWaiter(identity)
        acknowledgement = _try_self_destructed_pause(identity, primitives, out)
        if acknowledgement is not None:
            out.update(selfDestructedPaused=True, ownerRestorationSkipped=True,
                       requestedNormalClose=False, shutdownPause=acknowledgement)
            save()
            out['exitCode'] = waiter.wait(20)
        else:
            process = ResearchProcess(identity['pid'])
            if process_creation(process) != identity['creationFiletime']:
                raise ValueError('Native identity changed before restoration')
            out['mapped'] = shutdown_snapshot(process, primitives)
            inventory=mapped_callback_owners(identity['pid'])
            out['callbackOwnerInventory']=inventory
            save()
            for prefix, options in OWNERS:
                validate_native_identity(identity)
                if not inventory[prefix]:
                    out['restoration'][prefix]={'ownerNotMapped':True,
                        'reason':'No callback module of this family was mapped after supervisor stop'}
                    save()
                    continue
                path = ROOT / f"native-host/build/{prefix}-{identity['pid']}.json"
                # A missing/stale report cannot stand in for a restored owner.
                value = read_report(path)
                if not _current_restoration(value, path, identity, prefix):
                    with contextlib.redirect_stdout(io.StringIO()):
                        value = stop(identity['pid'], **options)
                if not _current_restoration(value, path, identity, prefix):
                    raise RuntimeError('Incomplete adapter restoration: ' + prefix)
                out['restoration'][prefix] = value
                save()
            validate_native_identity(identity)
            if mapped_callback_owners(identity['pid'])!=inventory:
                raise ValueError('Callback owner inventory changed during normal restoration')
            out['afterRestoration'] = shutdown_snapshot(process, primitives)
            # Use the accepted implementation, preserving original destructor flow.
            out['closeHwnd'] = primitives.close_window(identity['pid'])
            save()
            try:
                out['exitCode'] = waiter.wait(3)
            except psutil.TimeoutExpired:
                # 原版析构可能超过 3 s；等渲染窗口真正消失（最多 30 s）再确认退出暂停，否则会误报失败并留下半关闭进程。
                user = ctypes.WinDLL('user32')
                for _ in range(60):
                    if not user.IsWindow(out['closeHwnd']):
                        break
                    time.sleep(.5)
                validate_native_identity(identity)
                out['shutdownPause'] = primitives.acknowledge_shutdown_pause(
                    identity['pid'], identity['creation'], out['closeHwnd'])
                save()
                out['exitCode'] = waiter.wait(20)
    except Exception as caught:
        # It can exit between identity capture and OpenProcess/restoration, or
        # finish its destructor while the shutdown pause is being inspected.
        # Do not interpret AccessDenied, PID reuse or an arbitrary read failure
        # as exit. Recheck the saved path/hash/creation and actual absence.
        try:
            gone = isinstance(caught, (psutil.NoSuchProcess, OSError)) and confirm_native_exited(identity)
        except Exception as identity_error:
            gone = False
            out['exitVerificationError'] = repr(identity_error)
        if gone:
            out.update(alreadyExited=True, normalCloseSkipped=True,
                       exitObservedDuring='normal-close', exitCode=None,
                       exitReason=repr(caught),requestedNormalClose='closeHwnd' in out)
        else:
            failure = caught
            out['error'] = repr(caught)
    finally:
        if process is not None:
            process.close()
        if waiter is not None:
            waiter.close()
        # Exit0 can follow a caught native fault. Always classify matching
        # evidence, including failure/timeout paths, rather than trusting code0.
        try:
            out['crashReports'] = wait_native_crash_reports(
                identity['pid'], identity['creation'], Path(identity['executable']), seconds=2)
        except Exception as caught:
            out['crashEvidenceError'] = repr(caught)
            if failure is None and not out.get('alreadyExited'):
                failure = caught
                out['error'] = 'Native crash evidence unavailable: ' + repr(caught)
        if failure is None and not out.get('alreadyExited') and (out.get('crashReports') or out.get('exitCode') != 0):
            out['error'] = 'Normal close returned an error or a matching crash report'
            failure = RuntimeError(out['error'])
        out['nativeExitClassification'] = (
            'already-exited-evidence-unavailable' if out.get('alreadyExited') and out.get('crashEvidenceError') else
            'already-exited-crash-report' if out.get('alreadyExited') and out.get('crashReports') else
            'already-exited' if out.get('alreadyExited') else
            'crash-report' if out.get('crashReports') else
            'evidence-unavailable' if out.get('crashEvidenceError') else
            'native-self-destructed-paused' if failure is None and out.get('selfDestructedPaused') else
            'normal-close' if failure is None else 'normal-close-failed')
        if failure is None:
            out['passed'] = True
            out['normalClosePassed'] = not out.get('alreadyExited', False)
        save()
    if failure is not None:
        raise NativeCloseError(out) from failure
    return out
