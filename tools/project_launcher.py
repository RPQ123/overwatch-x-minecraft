"""Desktop front end for the existing independent OW/MC session supervisor.

This module never injects modules, kills games, or owns a gameplay callback.
Actions run in a detached coordinator, so closing the UI cannot interrupt a
strict stop/restart or end the existing independent gameplay supervisor.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
import traceback
import uuid
from typing import Any

import psutil

from modpack.config import PackPaths, OW_RELATIVE, OW_SHA256
from startup_cover import (LOAD_SECONDS, START_ACTIONS, LoadingTicket, covered_timeline_path, loading_progress,
                           matching_timeline, presentation_receipt)

ROOT = Path(__file__).resolve().parents[1]
EXE_RELATIVE = Path(OW_RELATIVE)
TARGET_SHA256 = OW_SHA256
ACTIONS = ('start', 'stop', 'crash-stop', 'restart', 'show', 'diagnose', 'new-world', 'settings', 'toggle', 'reboot',
           'setup-check', 'setup-install', 'setup-verify')
PROFILE_DIRS = ('guest-passthrough-client', 'aoa3-connector-client')


def read_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise ValueError(f'Expected an object in {path.name}')
    return value


def write_object(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f'.{os.getpid()}.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for attempt in range(12):
        try:
            temporary.replace(path)
            return
        except PermissionError:
            if attempt == 11:
                raise
            time.sleep(.01)


class NamedMutex:
    """Windows lifetime mutex: one UI and one action coordinator per checkout."""
    def __init__(self, root: Path, purpose: str):
        digest = hashlib.sha256(str(root.resolve()).casefold().encode('utf-8')).hexdigest()[:20]
        self.name = f'Local\\OWMCProjectLauncher-{digest}-{purpose}'
        self.handle = None

    def acquire(self) -> bool:
        if os.name != 'nt':
            raise RuntimeError('This project launcher requires Windows.')
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p]
        kernel.CreateMutexW.restype = ctypes.c_void_p
        ctypes.set_last_error(0)
        handle = kernel.CreateMutexW(None, False, self.name)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        existed = ctypes.get_last_error() == 183
        self.handle = handle
        if existed:
            self.close()
            return False
        return True

    def close(self) -> None:
        if self.handle:
            kernel = ctypes.WinDLL('kernel32', use_last_error=True)
            kernel.CloseHandle.argtypes = [ctypes.c_void_p]
            kernel.CloseHandle(self.handle)
            self.handle = None


def detached_flags() -> int:
    # NO_WINDOW is ignored alongside DETACHED_PROCESS. A new process group with
    # redirected handles survives closing this UI without owning a console.
    return (subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP) if os.name == 'nt' else 0


def _script_processes(script: Path, python_paths: set[Path]) -> list[psutil.Process]:
    """Exact script + interpreter paths, never a name-only process match."""
    result = []
    for process in psutil.process_iter(['exe', 'cmdline']):
        try:
            executable = process.info.get('exe')
            if not executable or Path(executable).resolve() not in python_paths:
                continue
            arguments = process.info.get('cmdline') or []
            for item in arguments[1:]:
                if item.startswith('-'):
                    continue
                path = Path(item)
                if not path.is_absolute():
                    path = Path(process.cwd()) / path
                if path.resolve() == script.resolve():
                    result.append(process)
                    break
        except (psutil.Error, OSError, ValueError):
            continue
    return result


class SessionBackend:
    """Small process facade; tests replace every external action with fixtures."""
    def __init__(self, root: Path = ROOT):
        self.root = root.resolve()
        self.paths = PackPaths(self.root)
        self.python = self.paths.get('python')
        self.native_path = self.paths.get('owExecutable')
        self.logs = self.root / 'research/launcher'
        self.status_path = self.root / 'research/session-status.json'
        self.action_path = self.logs / 'action-status.json'

    def settings(self) -> dict:
        value = read_object(self.root / 'passthrough-settings.json')
        if value.get('schemaVersion') != 1:
            raise ValueError('设置格式不受支持；请保留文件并查看诊断。')
        return value

    def validate_start(self) -> None:
        from configure_passthrough import validate_flight_key
        validate_flight_key(self.settings().get('flightKey', 'F6'))
        self.paths=PackPaths(self.root)
        self.native_path=self.paths.get('owExecutable')
        blockers = self.paths.launch_blockers()
        if blockers:
            raise ValueError('；'.join(blockers))
        if self.paths.packaged:
            from modpack.first_run import status
            preparation = status(self.root)
            if not preparation['ready']:
                raise ValueError('；'.join(preparation['errors'] + preparation['launchBlockers']))
        for path in (self.python, self.root / 'tools/launch_passthrough_session.py',
                     self.root / 'tools/stop_passthrough_session.py'):
            if not path.is_file():
                raise FileNotFoundError(f'缺少 {path.name}；请检查首次运行页或运行 tools/setup_environment.ps1。')
        with self.native_path.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if digest != TARGET_SHA256:
            raise ValueError('离线 OW 文件 SHA256 不匹配；未启动任何游戏。')

    def supervisors(self) -> list[psutil.Process]:
        paths = {self.python.resolve(), Path(sys.executable).resolve(),
                 Path(getattr(sys, '_base_executable', sys.executable)).resolve()}
        return _script_processes(self.root / 'tools/launch_passthrough_session.py', paths)

    def spawn(self, command: list[str], log: Path) -> subprocess.Popen:
        log.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.root / 'data/tmp'
        temporary.mkdir(parents=True, exist_ok=True)
        environment = {**os.environ, 'PYTHONIOENCODING': 'utf-8', 'PYTHONDONTWRITEBYTECODE': '1',
                       'OWMC_NO_CONSOLE': '1', 'TEMP': str(temporary), 'TMP': str(temporary)}
        # Only the gameplay supervisor launches the native client and needs
        # its VC search directory. The UI/action coordinator do not load it.
        if str(self.root/'tools/launch_passthrough_session.py') in command:
            environment = self.paths.child_environment(environment)
        with log.open('ab', buffering=0) as stream:
            return subprocess.Popen(command, cwd=self.root, stdin=subprocess.DEVNULL,
                                    stdout=stream, stderr=subprocess.STDOUT,
                                    creationflags=detached_flags(), close_fds=True,
                                    env=environment)

    def checked_command(self, command: list[str], log: Path) -> dict:
        process = self.spawn(command, log)
        code = process.wait()
        if code:
            raise RuntimeError(f'现有流程返回 {code}；已停止后续步骤。日志：{log}')
        return {'exitCode': code, 'log': str(log)}

    def read_action(self) -> dict:
        try:
            return read_object(self.action_path)
        except (OSError, ValueError):
            return {}

    def action_active(self, action: dict) -> bool:
        """A saved running flag cannot keep a reopened UI locked forever."""
        if action.get('phase') != 'running':
            return False
        try:
            process = psutil.Process(int(action['pid']))
            if abs(process.create_time() - float(action['created'])) > .001 or not process.is_running():
                return False
            python_paths = {self.python.resolve(), Path(sys.executable).resolve(),
                            Path(getattr(sys, '_base_executable', sys.executable)).resolve()}
            if Path(process.exe()).resolve() not in python_paths:
                return False
            arguments = process.cmdline()
            scripts = ((self.root / 'tools/project_launcher.py', '--action'),
                       (self.root / 'tools/configure_passthrough.py', '--gui'))
            for script, flag in scripts:
                if flag not in arguments:
                    continue
                for argument in arguments[1:]:
                    if argument.startswith('-'):
                        continue
                    path = Path(argument)
                    if not path.is_absolute():
                        path = Path(process.cwd()) / path
                    if path.resolve() == script.resolve():
                        return True
            return False
        except (psutil.Error, KeyError, OSError, TypeError, ValueError):
            return False

    def start(self, log: Path, *, loading=None) -> dict:
        active = self.supervisors()
        if active:
            return {'result': 'existing-supervisor', 'supervisorPids': [p.pid for p in active],
                    'message': '已存在独立监督，继续查看现有会话；未新增模块所有者。'}
        self.validate_start()
        if loading:
            loading.checkpoint()
        process = self.spawn([str(self.python), '-u', str(self.root / 'tools/launch_passthrough_session.py')], log)
        if loading:
            self.loading_child = process
        return {'result': 'supervisor-started', 'supervisorPid': process.pid, 'log': str(log),
                'message': '后台启动请求已提交；选人/合成/战斗状态仍需分别确认。'}

    def start_covered(self, action, log, ticket) -> dict:
        """Own exactly this request until the UI acknowledges or cancels the handoff."""
        from startup_timeline import startup_request
        if action not in START_ACTIONS:
            raise ValueError('该操作不能使用启动加载画面。')
        ticket.checkpoint()
        running = self.running()
        if action == 'restart':
            self.stop(log)
        elif (running and action == 'reboot') or (not running and self.project_processes()):
            self.robust_stop(log)
        ticket.checkpoint()
        with startup_request(self.root, loading=ticket):
            result = self.start(log, loading=ticket)
        if result['result'] == 'existing-supervisor':
            return result
        process = self.loading_child
        try:
            while process.poll() is None:
                if ticket.state() == 'released':
                    return {**result, 'phase': 'hero-selection', 'coveredHandoff': True}
                ticket.checkpoint()
                time.sleep(.1)
            raise RuntimeError(f'启动监督进程已退出（{process.returncode}）。')
        except Exception:
            try:
                process.wait(timeout=90)
            except subprocess.TimeoutExpired as failure:
                raise RuntimeError('启动监督仍在处理取消请求，请查看本次日志。') from failure
            timeline = self.loading_timeline(ticket.request_id)
            started = any(event.get('name') in ('native_spawn_requested', 'mc_jvm_spawn_requested')
                          for event in timeline.get('events', ()))
            if started and not self.supervisors() and self.project_processes():
                self.robust_stop(log)
            raise

    def project_processes(self) -> list[psutil.Process]:
        """Exact native exe path or a JVM whose --gameDir is a project profile; never name-only."""
        native_path = self.native_path
        profiles = {self.paths.get('profile'), self.paths.get('aoaProfile')}
        found = []
        for process in psutil.process_iter(['exe', 'cmdline']):
            try:
                executable = process.info.get('exe')
                if not executable:
                    continue
                path = Path(executable).resolve()
                if path == native_path:
                    found.append(process)
                    continue
                arguments = process.info.get('cmdline') or []
                if path.name.lower() in ('java.exe', 'javaw.exe') and '--gameDir' in arguments:
                    index = arguments.index('--gameDir')
                    if index + 1 < len(arguments) and Path(arguments[index + 1]).resolve() in profiles:
                        found.append(process)
            except (psutil.Error, OSError, ValueError):
                continue
        return found

    def running(self) -> bool:
        """A live supervisor means the session is (being) owned; leftovers alone are not 'running'."""
        return bool(self.supervisors())

    def session_phase(self, since: float) -> str:
        try:
            status = read_object(self.status_path)
            native = self.native_identity(status)
            if native and native.create_time() > since:
                return str(status.get('phase', 'stale'))
        except (OSError, ValueError, psutil.Error):
            pass
        return 'stale'

    def robust_stop(self, log: Path, attempts: int = 3) -> dict:
        """Normal close; if it exits abnormally while project processes remain, close normally again."""
        last: Exception | None = None
        for attempt in range(attempts):
            try:
                result = self.stop(log, allow_window_close=True)
            except RuntimeError as failure:
                last = failure
                result = None
            if not self.supervisors() and not self.project_processes():
                return {**(result or {}), 'attempts': attempt + 1}
            time.sleep(3)
        raise RuntimeError(f'正常关闭 {attempts} 次后仍有游戏进程残留；未强制结束。{last or ""}')

    def wait_started(self, since: float, timeout: float = 240) -> str:
        """Until the original picker/gameplay is reached, or the supervisor dies."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            phase = self.session_phase(since)
            if phase in ('hero-selection', 'gameplay'):
                return phase
            if not self.supervisors():
                time.sleep(2)  # its final status write may lag the exit
                phase = self.session_phase(since)
                return phase if phase in ('hero-selection', 'gameplay') else 'supervisor-exited'
            time.sleep(.2)
        return 'timeout'

    def clean_start(self, log: Path, attempts: int = 2) -> dict:
        """One-click start: close leftovers normally, start, wait for the picker, retry once on failure."""
        from startup_timeline import startup_request
        outcome = 'not-started'
        for attempt in range(attempts):
            if not self.supervisors() and self.project_processes():
                self.robust_stop(log)
            since = time.time()
            with startup_request(self.root):
                result = self.start(log)
            if result.get('result') == 'existing-supervisor':
                return result
            outcome = self.wait_started(since)
            if outcome in ('hero-selection', 'gameplay'):
                return {**result, 'phase': outcome, 'attempts': attempt + 1}
            print(f'第 {attempt + 1} 次启动未到达选人界面（{outcome}）；正常清理后重试。', flush=True)
            if self.supervisors() or self.project_processes():
                self.robust_stop(log)
        raise RuntimeError(f'启动 {attempts} 次均未进入选人界面（{outcome}）；已正常清理。请查看日志。')

    def toggle(self, log: Path) -> dict:
        """Decided inside the action mutex, so double clicks cannot start and stop at once."""
        if self.running():
            return {'toggled': 'stopped', **self.robust_stop(log)}
        return {'toggled': 'started', **self.clean_start(log)}

    def reboot(self, log: Path) -> dict:
        if self.running() or self.project_processes():
            self.robust_stop(log)  # A failed restoration never falls through.
        return {'toggled': 'started', **self.clean_start(log)}

    def stop(self, log: Path, *, allow_window_close: bool = False) -> dict:
        # Only this established entrypoint can restore/terminate project owners.
        command = [str(self.python), '-u', str(self.root / 'tools/stop_passthrough_session.py')]
        if allow_window_close:
            command.append('--allow-window-close')
        return self.checked_command(command, log)

    def native_identity(self, status: dict) -> psutil.Process | None:
        try:
            process = psutil.Process(int(status['nativePid']))
            if Path(process.exe()).resolve() != self.native_path:
                return None
            # A status from a reused PID cannot authorize a different process.
            started = float(status.get('startedMs', 0)) / 1000
            if not started or process.create_time() > started + 1:
                return None
            return process if process.is_running() else None
        except (psutil.Error, KeyError, OSError, TypeError, ValueError):
            return None

    def show_windows(self) -> dict:
        status = read_object(self.status_path)
        native = self.native_identity(status)
        if native is None:
            raise ValueError('没有身份匹配的运行中 OW 会话；请先启动。')
        with self.native_path.open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != TARGET_SHA256:
                raise ValueError('离线 OW 文件 SHA256 不匹配；未操作窗口。')
        minecraft = (status.get('state') or {}).get('minecraft') or {}
        if not minecraft.get('sourcePid'):
            # Picker records deliberately omit gameplay state; read-only API
            # is used solely to identify the actual private Minecraft process.
            import urllib.request
            with urllib.request.urlopen('http://127.0.0.1:32133/health', timeout=2) as response:
                minecraft = json.load(response)
        if minecraft.get('mode') != 'full-world-frame-proof':
            raise ValueError('Minecraft 桥接身份不匹配；未操作窗口。')
        guest = psutil.Process(int(minecraft['sourcePid']))
        if str(self.paths.get('profile')) not in guest.cmdline():
            raise ValueError('Minecraft 不是本项目独立档案；未操作窗口。')
        from window_layout import arrange, windows_for_pid, user32
        # This action is an explicit user request. Restore both exact windows
        # before applying the existing no-topmost/no-resize arrangement.
        native_windows = windows_for_pid(native.pid, visible_only=False)
        guest_windows = windows_for_pid(guest.pid, visible_only=False)
        if not native_windows or not guest_windows:
            raise ValueError('身份已匹配，但游戏窗口尚未创建；稍后再试。')
        for window in (guest_windows[0], native_windows[0]):
            user32.ShowWindow(wintypes.HWND(window.handle), 9)
        return arrange(native.pid, guest.pid, 0, 0,
                       native_fullscreen=bool(self.settings().get('nativeFullscreen',False)))

    def recent_log(self, action: dict) -> list[str]:
        value = action.get('log')
        if not value:
            return []
        path = Path(value).resolve()
        if not path.is_relative_to(self.logs.resolve()):
            return []
        try:
            with path.open('rb') as stream:
                stream.seek(0, 2)
                stream.seek(max(0, stream.tell() - 16_384))
                return stream.read().decode('utf-8', errors='replace').splitlines()[-8:]
        except OSError:
            return []

    def loading_timeline(self, request_id: str) -> dict:
        try:
            path = covered_timeline_path(self.root, request_id)
            if path.stat().st_size < 256 * 1024:
                data = read_object(path)
                request = data.get('request') or {}
                if request.get('covered') is True and request.get('requestId') == request_id:
                    return data
        except (OSError, ValueError, TypeError):
            pass
        return {}

    def focus_loading_pair(self, status, receipt, *, foreground_only=False) -> bool:
        from window_layout import focus_render_pair, guest_window_owner
        native = self.native_identity(status)
        if native is None or native.create_time() != receipt['nativeCreated']:
            raise ValueError('原版渲染进程身份已变化。')
        guest = guest_window_owner(self.paths, receipt['guestPid'])
        if guest.create_time() != receipt['guestCreated']:
            raise ValueError('Minecraft 渲染进程身份已变化。')
        return focus_render_pair(native.pid, guest.pid, receipt['nativeHwnd'], receipt['guestHwnd'],
                                 foreground_only=foreground_only)

    def snapshot(self) -> dict:
        now = time.time()
        errors = []
        try:
            status = read_object(self.status_path)
        except (OSError, ValueError) as failure:
            status = {}
            errors.append(f'暂未取得会话状态：{failure}')
        try:
            settings = self.settings()
        except (OSError, ValueError) as failure:
            settings = {}
            errors.append(str(failure))
        native = self.native_identity(status)
        supervisors = self.supervisors()
        fresh = 0 <= now - float(status.get('heartbeatMs', 0) or 0) / 1000 < 5
        action = self.read_action()
        try:
            project = [p.pid for p in self.project_processes()]
        except Exception as failure:
            project = []
            errors.append(f'进程扫描失败：{failure}')
        try:
            resources=read_object(self.root / 'research/launcher/resource-status.json')
            resource_warnings=resources.get('warnings',[]) if resources.get('profile')==str(self.paths.get('profile')) else []
        except (OSError,ValueError):
            resource_warnings=[]
        return {'status': status, 'settings': settings, 'nativeAlive': native is not None,
                'supervisorPids': [p.pid for p in supervisors], 'fresh': fresh, 'projectPids': project,
                'action': action, 'actionActive': self.action_active(action),
                'recentLog': self.recent_log(action), 'errors': errors, 'resourceWarnings': resource_warnings,
                'loadingTimeline': self.loading_timeline(action.get('requestId', '')) if action.get('loading') else {}}


def execute_action(backend: SessionBackend, action: str, log: Path, world_name: str = '') -> dict:
    if action == 'setup-check':
        from modpack.first_run import environment
        return environment(backend.root)
    if action in ('setup-install', 'setup-verify'):
        if backend.supervisors() or backend.project_processes():
            raise ValueError('请先通过现有关闭流程保存并关闭游戏，再准备安装。未操作运行中的档案。')
        from modpack.install import install, verify_installation
        return install(backend.root) if action == 'setup-install' else verify_installation(backend.root)
    if action == 'start':
        return backend.start(log)
    if action == 'stop':
        return backend.stop(log)
    if action == 'crash-stop':
        return backend.stop(log, allow_window_close=True)
    if action == 'toggle':
        return backend.toggle(log)
    if action == 'reboot':
        return backend.reboot(log)
    if action == 'restart':
        backend.stop(log)  # A failed strict restoration never falls through.
        return backend.start(log)
    if action == 'show':
        return backend.show_windows()
    if action == 'diagnose':
        return backend.checked_command([str(backend.python), '-u',
                                        str(backend.root / 'tools/check_environment.py')], log)
    if action == 'new-world':
        from configure_passthrough import world_name as validate_name
        name = validate_name(world_name)
        return backend.checked_command([str(backend.python), '-u',
                                        str(backend.root / 'tools/configure_passthrough.py'),
                                        '--new-world', name], log)
    if action == 'settings':
        # Hold the same action coordinator mutex until the editor is CLOSED.
        # The hidden helper avoids this machine's console pythonw redirector.
        return backend.checked_command(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                                        '-WindowStyle', 'Hidden', '-File',
                                        str(backend.root / 'tools/open_project_launcher.ps1'),
                                        '-Settings', '-WaitForExit'], log)
    raise ValueError(f'Unknown action: {action}')


def run_action(backend: SessionBackend, action: str, log: Path, world_name: str = '', request_id: str = '',
               *, loading=False) -> int:
    mutex = NamedMutex(backend.root, 'action')
    if not mutex.acquire():
        print('已有启动/恢复操作进行中；未重复执行。', flush=True)
        return 2
    record = {'action': action, 'phase': 'running', 'pid': os.getpid(), 'requestId': request_id or uuid.uuid4().hex,
              'created': psutil.Process().create_time(), 'startedMs': round(time.time() * 1000),
              'log': str(log)}
    if loading:
        record['loading'] = True
    try:
        write_object(backend.action_path, record)
        if loading:
            result = backend.start_covered(action, log, LoadingTicket.open(backend.root, request_id))
        else:
            result = execute_action(backend, action, log, world_name)
        record.update(phase='succeeded', result=result, finishedMs=round(time.time() * 1000))
        return 0
    except Exception as failure:
        record.update(phase='failed', error=str(failure), finishedMs=round(time.time() * 1000))
        traceback.print_exc()
        return 1
    finally:
        try:
            write_object(backend.action_path, record)
        finally:
            mutex.close()


def action_completion_message(code: int, request_id: str, record: dict, log: Path) -> str:
    """Correlate this process exit with THIS request, never a cached old error."""
    location = f'本次日志：{log}'
    if record.get('requestId') != request_id:
        if code == 2:
            return '其他操作仍持有互斥，本次请求未执行。' + location
        return f'操作进程已退出（{code}），尚未取得本次匹配回执；不能据此确认完成。{location}'
    if code != 0 or record.get('phase') == 'failed':
        return f'本次操作失败：{record.get("error") or f"退出码 {code}"}。{location}'
    if record.get('phase') != 'succeeded':
        return f'操作进程已退出，但回执未完成；请查看本次日志。{location}'
    if record.get('action') == 'settings':
        return '设置窗口已关闭。保存过的设置在下次正常重启生效；关闭窗口本身不代表保存。'
    if record.get('action') == 'new-world':
        return '新世界名称已保存；下次正常重启时创建，当前运行世界未切换。'
    return '本次后台操作已结束。请查看当前阶段；启动请求不代表完整可玩验收。' + location


def describe_snapshot(snapshot: dict) -> tuple[str, str, str]:
    """Return presentation text, never infer gameplay acceptance from health."""
    status = snapshot.get('status') or {}
    if snapshot.get('supervisorPids') and not snapshot.get('nativeAlive'):
        return ('启动 / 恢复中', '独立监督仍在运行。上一次退出记录保留在诊断中；正在等待本次身份匹配的新状态。', 'warning')
    if status.get('nativeExitClassification') == 'crash-report' and not snapshot.get('nativeAlive'):
        return ('原生客户端曾异常退出', '本次身份匹配的崩溃报告已保留。退出码 0 也不代表正常。请查看诊断。', 'error')
    if status.get('stopped') and not snapshot.get('nativeAlive'):
        return ('会话已停止', '启动会重新使用现有独立监督与严格恢复流程。', 'neutral')
    if snapshot.get('nativeAlive') and snapshot.get('fresh'):
        if status.get('phase') == 'hero-selection':
            return ('等待选择英雄', '这是正常阶段。请在原生 OW 选人界面确认英雄；ready=false 不表示启动失败。', 'normal')
        if status.get('error'):
            return ('部分运行条件未就绪', str(status['error']), 'warning')
        if status.get('ready'):
            return ('运行信号已连接', '监督器报告当前绑定与帧传输就绪；实际画面、攻击和完整技能仍需游戏内验证。', 'normal')
        return ('等待当前英雄绑定', '原生进程存在；正在等待同一模型和世界的有效状态。', 'warning')
    if snapshot.get('supervisorPids'):
        return ('启动 / 恢复中', '独立监督仍在运行。尚无新鲜、身份匹配的完整会话状态；请查看启动日志。', 'warning')
    if snapshot.get('nativeAlive'):
        return ('进程仍在，监督状态已过期', '未自动重载模块。可查看日志或使用正常重启；不要反复加载所有者。', 'warning')
    if status.get('error'):
        return ('上次操作未完成', str(status['error']), 'error')
    return ('尚未启动', '选择世界与设置后启动，默认停留在原生动画选人界面。', 'neutral')


def load_catalog(path: Path) -> tuple[list[dict], str]:
    if not path.exists():
        return [], '地图库档案尚未生成。地图下载和战斗验收不会由此界面自动完成。'
    try:
        from pve_map_catalog import load_catalog as read_catalog
        value = read_catalog(path)
        maps = value['maps']
        if not all(isinstance(item, dict) and item.get('id') and item.get('title') for item in maps):
            raise ValueError('Malformed map entries')
        return maps, ''
    except (OSError, ValueError, TypeError, AttributeError) as failure:
        return [], f'地图库读取失败：{failure}'


def map_is_accepted(item: dict) -> bool:
    from pve_map_catalog import challenge_ready
    try:
        return challenge_ready(item)
    except (AttributeError, TypeError):
        return False


def show_launcher_window(window: Any) -> None:
    """Undo inherited SW_HIDE for this process's own Tk top-level only.

    The venv pythonw is a console redirector on this machine. The desktop
    entry hides its Python console; Windows can apply that startup show state
    to Tk as well. Two explicit ShowWindow calls consume that initial state
    and restore the UI without exposing the console or touching game windows.
    """
    window.update_idletasks()
    window.deiconify()
    if os.name != 'nt':
        window.lift()
        return
    user = ctypes.WinDLL('user32', use_last_error=True)
    user.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
    user.GetAncestor.restype = wintypes.HWND
    user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user.GetWindowThreadProcessId.restype = wintypes.DWORD
    user.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user.ShowWindow.restype = wintypes.BOOL
    user.SetForegroundWindow.argtypes = [wintypes.HWND]
    user.SetForegroundWindow.restype = wintypes.BOOL
    widget_handle = window.winfo_id()
    handle = user.GetAncestor(wintypes.HWND(widget_handle), 2) or widget_handle
    owner = wintypes.DWORD()
    user.GetWindowThreadProcessId(wintypes.HWND(handle), ctypes.byref(owner))
    if owner.value != os.getpid():
        raise RuntimeError('Launcher HWND does not belong to the current UI process.')
    user.ShowWindow(wintypes.HWND(handle), 5)  # SW_SHOW; initial STARTUPINFO may override it.
    user.ShowWindow(wintypes.HWND(handle), 9)  # SW_RESTORE; explicit subsequent call.
    user.SetForegroundWindow(wintypes.HWND(handle))


def prepare_launcher_input(window: Any) -> None:
    """Associate an IME only with editable fields, without a floating boot bar."""
    if os.name != 'nt':
        return
    try:
        user = ctypes.WinDLL('user32', use_last_error=True)
        imm = ctypes.WinDLL('imm32', use_last_error=True)
        user.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
        user.GetAncestor.restype = wintypes.HWND
        user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        imm.ImmAssociateContextEx.argtypes = [wintypes.HWND, wintypes.HANDLE, wintypes.DWORD]
        imm.ImmAssociateContextEx.restype = wintypes.BOOL
        widget_handle = window.winfo_id()
        if not isinstance(widget_handle, int):
            return
        handle = user.GetAncestor(widget_handle, 2) or widget_handle
        owner = wintypes.DWORD()
        user.GetWindowThreadProcessId(handle, ctypes.byref(owner))
        if owner.value != os.getpid():
            return
        imm.ImmAssociateContextEx(handle, None, 1)  # Own HWND/children only.
        def editing(event):
            if event.widget.winfo_class() in ('Entry', 'TEntry', 'Text'):
                imm.ImmAssociateContextEx(event.widget.winfo_id(), None, 0x10)  # IACE_DEFAULT
        window.bind_all('<FocusIn>', editing, add='+')
    except (OSError, ValueError, AttributeError):
        pass


class LauncherUI:
    """Compact Overwatch-style launcher with an in-window settings page. All game
    actions still run in the detached mutex-guarded coordinator."""

    WIDTH, HEIGHT = 860, 580
    C = dict(bg='#0b111d', panel='#121b2b', panel2='#172338', line='#243450', text='#f1f5fc', dim='#8798b3',
             faint='#4d5f7d', orange='#f99e1a', orange_hi='#ffb44a', cyan='#45c8ff', red='#ff4d5e',
             red_hi='#ff7480', green='#3fe08f', yellow='#ffcf4a', disabled='#1d2a40')
    HOTKEYS = (('F6', '飞行'), ('F7', '世界'), ('F8', '传送门'), ('F9', '召唤'), ('F10', 'BOSS'), ('F11', '技能恢复'))
    FONT = 'Microsoft YaHei UI'
    TECH = 'Bahnschrift SemiBold Condensed'

    def __init__(self, window: Any, backend: SessionBackend):
        import tkinter as tk
        self.window, self.backend = window, backend
        self.updates: queue.Queue = queue.Queue()
        self.startup_updates: queue.Queue = queue.Queue()
        self.startup_pending = True
        self.startup_result: dict | None = None
        self.startup_requested: tuple[str, str] | None = None
        self.auto_start_enabled = backend.paths.auto_start()
        self.auto_start_pending = self.auto_start_enabled
        self.closed = False
        self.polling = False
        self.pending: subprocess.Popen | None = None
        self.pending_request_id = ''
        self.pending_log: Path | None = None
        self.pending_action = ''
        self.loading = None
        self.loading_ticket = None
        self.loading_error = None
        self.loading_retry = None
        self.last_snapshot: dict = {}
        self.action_buttons: list[Any] = []
        self.phase = 0
        self.page = 'main'
        self.action_var = tk.StringVar(value='关闭启动器不会影响正在运行的游戏。')
        window.title('守望先锋 × 我的世界 — 启动器')
        window.geometry(f'{self.WIDTH}x{self.HEIGHT}')
        window.resizable(False, False)
        window.configure(background=self.C['bg'])
        try:
            window.iconbitmap(default=str(ROOT / 'assets/launcher/owmc.ico'))
        except Exception:
            pass
        self.canvas = tk.Canvas(window, width=self.WIDTH, height=self.HEIGHT, highlightthickness=0,
                                background=self.C['bg'])
        self.canvas.pack(fill='both', expand=True)
        self._draw_frame()
        self._draw_main()
        self.settings = _SettingsPage(self)
        self.first_run = _FirstRunPage(self)
        window.protocol('WM_DELETE_WINDOW', self.close)
        if not (backend.root / 'passthrough-settings.json').is_file():
            self.show_page('setup')
        threading.Thread(target=self._read_startup, daemon=True).start()
        self.tick()

    # ---------- drawing ----------
    def _draw_frame(self) -> None:
        c, C, W, H = self.canvas, self.C, self.WIDTH, self.HEIGHT
        for i in range(0, H, 3):
            k = i / H
            c.create_rectangle(0, i, W, i + 3, outline='',
                               fill='#%02x%02x%02x' % (int(11 + 6 * (1 - k)), int(17 + 9 * (1 - k)), int(29 + 18 * (1 - k))))
        c.create_polygon(W - 300, 0, W, 0, W, H, W - 520, H, fill='#0e1626', outline='')
        for x in range(W - 280, W + 200, 38):
            c.create_line(x, 0, x - 240, H, fill='#111c30')
        c.create_rectangle(0, 0, W, 4, fill=C['orange'], outline='')
        c.create_polygon(34, 30, 48, 30, 40, 74, 26, 74, fill=C['orange'], outline='')
        x = 60
        for word, color in (('OVERWATCH', C['text']), ('×', C['orange']), ('MINECRAFT', C['text'])):
            item = c.create_text(x, 44, text=word, anchor='w', fill=color, font=(self.TECH, 28))
            x = c.bbox(item)[2] + 10
        c.create_text(61, 70, text='守望先锋 × 我的世界', anchor='w', fill=C['dim'], font=(self.FONT, 9))
        self.page_tag = c.create_text(W - 40, 44, text='', anchor='e', fill=C['faint'], font=(self.TECH, 13))

    def _draw_main(self) -> None:
        c, C, W = self.canvas, self.C, self.WIDTH
        t = ('main',)
        # 状态卡：状态灯 + 标题 + 说明，底部一行是当前配置与光影开关。
        c.create_polygon(40, 104, W - 40, 104, W - 52, 214, 28, 214, fill=C['panel'], outline=C['line'], tags=t)
        c.create_rectangle(40, 104, 140, 107, fill=C['cyan'], outline='', tags=t)
        self.dot_ring = c.create_oval(58, 126, 86, 154, outline='', width=2, tags=t)
        self.dot = c.create_oval(65, 133, 79, 147, fill=C['dim'], outline='', tags=t)
        self.status_id = c.create_text(100, 140, text='正在读取状态…', anchor='w', fill=C['text'],
                                       font=(self.FONT, 19, 'bold'), tags=t)
        self.detail_id = c.create_text(62, 172, text='', anchor='w', fill=C['dim'], width=W - 150,
                                       font=(self.FONT, 10), tags=t)
        c.create_line(56, 186, W - 56, 186, fill=C['line'], tags=t)
        self.world_id = c.create_text(62, 200, text='', anchor='w', fill=C['cyan'], font=(self.FONT, 9), tags=t)
        # 光影快捷开关（MakeUp-UltraFast，开启用“低”档）；下次启动生效。
        self.shader_button = _SlantButton(self, W - 190, 190, 120, 20, '光影：关', self.toggle_shaders,
                                          font=(self.FONT, 9, 'bold'), tags=t)
        self.action_buttons.append(self.shader_button)
        cx = W // 2
        self.main_button = _SlantButton(self, cx - 190, 240, 380, 80, '开始游戏', self.toggle,
                                        font=(self.FONT, 22, 'bold'), primary=True, tags=t)
        self.action_buttons.append(self.main_button)
        self.bar = c.create_rectangle(cx - 190, 330, cx - 190, 333, fill=C['orange'], outline='', state='hidden', tags=t)
        bw, gap = 140, 16
        x = cx - (4 * bw + 3 * gap) // 2
        for label, callback, guarded in (('重启', lambda: self.dispatch('reboot'), True),
                                         ('设置', self.open_settings, True),
                                         ('显示窗口', lambda: self.dispatch('show'), True),
                                         ('日志', self.open_logs, False)):
            button = _SlantButton(self, x, 352, bw, 36, label, callback, font=(self.FONT, 10, 'bold'), tags=t)
            if guarded:
                self.action_buttons.append(button)
            x += bw + gap
        # 游戏内快捷键：等宽格子，一行排开。
        top = 420
        c.create_line(40, top, W - 40, top, fill=C['line'], tags=t)
        c.create_text(44, top + 18, text='游戏内快捷键', anchor='w', fill=C['faint'], font=(self.FONT, 9), tags=t)
        cell = (W - 80) / len(self.HOTKEYS)
        y = top + 56
        for index, (key, label) in enumerate(self.HOTKEYS):
            x0 = 40 + index * cell
            c.create_polygon(x0 + 10, y - 22, x0 + cell - 2, y - 22, x0 + cell - 10, y + 22, x0 + 2, y + 22,
                             fill=C['panel'], outline=C['line'], tags=t)
            c.create_text(x0 + cell / 2, y - 8, text=key, fill=C['orange'], font=('Bahnschrift SemiBold', 12), tags=t)
            c.create_text(x0 + cell / 2, y + 11, text=label, fill=C['text'], font=(self.FONT, 9), tags=t)
        self.message_id = c.create_text(W // 2, self.HEIGHT - 28, text='', fill=C['dim'], width=W - 100,
                                        font=(self.FONT, 9), tags=t)
        self.auto_start_button = _SlantButton(self, W // 2 - 100, 514, 200, 24, '', self.toggle_auto_start,
                                              font=(self.FONT, 9), tags=t)
        self.auto_start_button.set_label('打开即启动：' + ('开' if self.auto_start_enabled else '关'))
        self.auto_start_button.set_selected(self.auto_start_enabled)
        self.action_buttons.append(self.auto_start_button)

    def _render(self, title: str, detail: str, color: str, settings: dict) -> None:
        c, C = self.canvas, self.C
        status = self.last_snapshot.get('status') or {}
        warnings = (status.get('settings') or {}).get('displayWarnings') or []
        mode_warning = (status.get('nativeDisplayMode') or {}).get('warning')
        warning = (warnings[-1] if isinstance(warnings, list) and warnings else mode_warning)
        if self.last_snapshot.get('fresh') and isinstance(warning, str) and warning:
            detail += ' 显示适配：' + warning
        tone = {'normal': C['green'], 'warning': C['yellow'], 'error': C['red'], 'neutral': C['dim'],
                'busy': C['orange']}.get(color, C['dim'])
        c.itemconfigure(self.dot, fill=tone)
        c.itemconfigure(self.dot_ring, outline=tone if color in ('normal', 'busy') else '')
        c.itemconfigure(self.status_id, text=title)
        c.itemconfigure(self.detail_id, text=detail)
        if settings:
            c.itemconfigure(self.world_id, text=f'{settings.get("worldName", "?")}   ·   '
                                                f'{settings.get("width", "?")}×{settings.get("height", "?")}   ·   '
                                                f'视距 {settings.get("renderDistance", "?")}')
        c.itemconfigure(self.message_id, text=self.action_var.get())

    def show_page(self, page: str) -> None:
        self.page = page
        if page != 'main':
            self.auto_start_pending = False
        self.canvas.itemconfigure('main', state='normal' if page == 'main' else 'hidden')
        self.canvas.itemconfigure(self.bar, state='hidden')
        self.settings.show(page == 'settings')
        self.first_run.show(page == 'setup')
        self.canvas.itemconfigure(self.page_tag, text={'settings': 'SETTINGS', 'setup': 'FIRST RUN'}.get(page, ''))

    # ---------- state ----------
    def _supervised(self) -> bool:
        return bool(self.last_snapshot.get('supervisorPids'))

    def _leftovers(self) -> bool:
        s = self.last_snapshot
        return not self._supervised() and bool(s.get('projectPids') or s.get('nativeAlive'))

    def _busy(self) -> bool:
        local = self.pending is not None and self.pending.poll() is None
        return local or bool(self.last_snapshot.get('actionActive'))

    def _view(self) -> tuple[str, str, str]:
        if self._busy():
            action = self.pending_action or (self.last_snapshot.get('action') or {}).get('action', '')
            names = {'toggle': '处理中', 'start': '正在启动', 'reboot': '正在重启', 'restart': '正在重启',
                     'stop': '正在关闭', 'crash-stop': '正在关闭', 'settings': '设置窗口已打开', 'show': '正在显示窗口'}
            return (names.get(action, '处理中') + '…', '后台执行中，启动会一直等到选人界面出现。可以关闭启动器，不会中断。', 'busy')
        if self._leftovers():
            return ('上次会话未正常结束', '点击「重新启动」：先正常关闭残留进程，再启动新会话。', 'warning')
        if self.startup_pending and not self._supervised():
            return ('准备就绪检查中', '正在后台校验本地文件；点击开始后将自动继续。', 'neutral')
        if self.startup_result and not self.startup_result.get('ready') and not self._supervised():
            return ('启动准备失败', '；'.join(self.startup_result.get('errors', []))[:180], 'error')
        title, detail, color = describe_snapshot(self.last_snapshot)
        if not self._supervised() and title in ('尚未启动', '会话已停止', '上次操作未完成'):
            return ('未运行', '点击「开始游戏」，进入原版选人界面后选择英雄即可。', 'neutral')
        status = self.last_snapshot.get('status') or {}
        warnings = self.last_snapshot.get('resourceWarnings') or []
        resource_note = f' {len(warnings)} 项可选私有资源未启用（不影响启动），详情见日志。' if warnings else ''
        if self._supervised() and status.get('phase') == 'hero-selection':
            return ('请选择英雄', '原版选人界面已就绪。'+resource_note, 'normal')
        if self._supervised() and self.last_snapshot.get('fresh') and status.get('ready'):
            return ('游戏运行中', '运行信号已连接。「结束游戏」会正常保存世界并关闭。'+resource_note, 'normal')
        return title, detail, color

    # ---------- actions ----------
    def toggle(self) -> None:
        self.dispatch('reboot' if self._leftovers() else 'toggle')

    def dispatch(self, action: str, world_name: str = '') -> None:
        from tkinter import messagebox
        if self.pending is not None and self.pending.poll() is None:
            self.action_var.set('已有操作进行中；未重复执行。')
            return
        if self.last_snapshot.get('actionActive'):
            self.action_var.set('另一独立操作仍在运行；若已打开设置，请先保存或关闭该窗口。')
            return
        supervised = self._supervised()
        covered = action in START_ACTIONS and (not supervised or action in ('restart', 'reboot'))
        if covered and not self.open_loading(action):
            return
        if action in START_ACTIONS and not supervised:
            if getattr(self, 'startup_pending', False):
                self.startup_requested = (action, world_name)
                self.action_var.set('正在校验本地文件，通过后自动开始。')
                return
            preparation = getattr(self, 'startup_result', None)
            if preparation and not preparation.get('ready'):
                note = '；'.join(preparation.get('errors', []))
                self.first_run.set_note(note)
                self.show_page('setup')
                self.fail_loading(note)
                return
            blockers = self.backend.paths.launch_blockers()
            if blockers:
                note = '；'.join(blockers)
                self.first_run.set_note(note)
                self.show_page('setup')
                self.fail_loading(note)
                return
        self.auto_start_pending = False
        stamp = time.strftime('%Y%m%d-%H%M%S') + f'-{time.time_ns() % 1_000_000_000:09d}'
        log = self.backend.logs / f'{stamp}-{action}.log'
        request_id = uuid.uuid4().hex
        command = [str(self.backend.python), '-u', str(Path(__file__).resolve()),
                   '--action', action, '--log', str(log), '--request-id', request_id]
        if world_name:
            command.extend(('--world-name', world_name))
        try:
            if covered:
                self.loading_log = log
                self.loading_ticket = LoadingTicket.create(self.backend.root, request_id, self.loading_deadline_ns)
                command.append('--loading')
            self.pending = self.backend.spawn(command, log)
            self.pending_request_id = request_id
            self.pending_log = log
            self.pending_action = action
            self.action_var.set('已提交，后台执行中。')
            for button in self.action_buttons:
                button.set_enabled(False)
        except Exception as failure:
            if covered:
                self.fail_loading(str(failure))
            else:
                messagebox.showerror('无法提交操作', str(failure), parent=self.window)

    def open_loading(self, action):
        from launcher_loading_screen import LoadingScreen
        self.loading_action = action
        if self.loading:
            return True
        if self.loading_error:
            self.loading_error.destroy()
            self.loading_error = None
        self.loading_deadline_ns = time.perf_counter_ns() + LOAD_SECONDS * 10**9
        self.loading_step = '正在检查本地文件'
        self.loading_log = self.backend.logs/'loading-preflight.log'
        self.loading_focus_needed = False
        try:
            self.loading = LoadingScreen(self.window, self.backend.root/'assets/launcher/owmc.png',
                                         lambda: self.fail_loading('启动已取消。'), self.try_loading_focus)
        except Exception as failure:
            self.fail_loading(str(failure))
            return False
        return True

    def begin_auto_loading(self):
        if self.auto_start_pending and self.page == 'main':
            self.open_loading('start')

    def end_loading(self, decision=None):
        cover, ticket = self.loading, self.loading_ticket
        self.loading = self.loading_ticket = None
        try:
            if ticket and decision:
                try:
                    ticket.finish(decision)
                except (OSError, RuntimeError):
                    if decision == 'released':
                        try:
                            ticket.finish('cancelled')
                        except OSError:
                            pass
                    raise
        finally:
            if cover:
                cover.close()

    def fail_loading(self, detail):
        from launcher_loading_screen import show_loading_error
        self.auto_start_pending = False
        self.startup_requested = None
        try:
            self.end_loading('cancelled')
        except OSError as failure:
            detail += f' 取消回执写入失败（{failure}）。'
        if self.loading_log.name == 'loading-preflight.log':
            try:
                self.loading_log.parent.mkdir(parents=True, exist_ok=True)
                with self.loading_log.open('a', encoding='utf-8') as stream:
                    stream.write(f'{self.loading_step}  {detail}\n')
            except OSError:
                pass
        self.window.attributes('-topmost', False)
        self.action_var.set(detail[:180])
        if self.loading_error:
            self.loading_error.destroy()
        self.loading_error = show_loading_error(self.window, self.loading_step, detail, self.loading_log,
                                                self.retry_loading, self.close)

    def retry_loading(self):
        self.loading_error.destroy()
        self.loading_error = None
        self.loading_retry = self.loading_action

    def try_loading_focus(self):
        ticket = self.loading_ticket
        if not ticket or not self.loading or self.loading.fading:
            return
        receipt = presentation_receipt(self.last_snapshot, ticket.request_id, round(time.time()*1000))
        if receipt is None:
            return
        try:
            ticket.checkpoint()
            if not self.backend.focus_loading_pair(self.last_snapshot['status'], receipt):
                self.loading_focus_needed = True
                return
            self.loading.fade(lambda: self.finish_loading(ticket))
        except (OSError, ValueError, KeyError, RuntimeError, psutil.Error) as failure:
            self.fail_loading(str(failure))

    def finish_loading(self, ticket):
        if self.loading_ticket is not ticket:
            return
        receipt = presentation_receipt(self.last_snapshot, ticket.request_id, round(time.time()*1000))
        if not receipt:
            self.fail_loading('切换窗口时合成信号已失效。')
            return
        try:
            if not self.backend.focus_loading_pair(self.last_snapshot['status'], receipt, foreground_only=True):
                self.loading_focus_needed = True
                self.loading.restore_opacity()
                return
            self.end_loading('released')
        except (OSError, ValueError, KeyError, RuntimeError, psutil.Error) as failure:
            self.fail_loading(str(failure))

    def update_loading(self):
        if not self.loading:
            return
        if time.perf_counter_ns() >= self.loading_deadline_ns:
            self.fail_loading(f'启动等待超过 {LOAD_SECONDS} 秒。')
            return
        ticket = self.loading_ticket
        timeline = matching_timeline(self.last_snapshot, ticket.request_id) if ticket else {}
        done, total, self.loading_step = loading_progress(bool((self.startup_result or {}).get('ready')), timeline)
        if timeline.get('status') == 'failed':
            event = next((event for event in timeline.get('events', ()) if event.get('name') == 'startup_failed'), {})
            self.fail_loading(event.get('error') or '启动监督报告失败。')
            return
        if ticket and self.loading_step == '合成画面已连通' and not presentation_receipt(
                self.last_snapshot, ticket.request_id, round(time.time()*1000)):
            done -= 1
            self.loading_step = '正在等待新的合成帧'
        if not self.loading.fading:
            try:
                self.loading.update(done, total, self.loading_step, focus_required=self.loading_focus_needed)
            except (OSError, RuntimeError) as failure:
                self.fail_loading(str(failure))
                return
            self.try_loading_focus()

    def toggle_auto_start(self) -> None:
        if self._busy():
            return
        mutex = NamedMutex(self.backend.root, 'action')
        if not mutex.acquire():
            self.action_var.set('另一操作正在进行，稍后再保存启动选项。')
            return
        try:
            from modpack.config import write_json
            paths = PackPaths(self.backend.root)
            value = not self.auto_start_enabled
            write_json(paths.config_path, {**paths.config, 'schemaVersion': 1, 'autoStart': value})
            self.backend.paths = PackPaths(self.backend.root)
            from modpack.config import sha256
            self.first_run.config_sha = sha256(paths.config_path)
            self.auto_start_enabled = value
            # Enabling applies on the next opening, never unexpectedly while
            # the player is changing settings in this window.
            self.auto_start_pending = False
            self.auto_start_button.set_label('打开即启动：' + ('开' if value else '关'))
            self.auto_start_button.set_selected(value)
            self.action_var.set('启动选项已保存，下次打开启动器生效。')
        except (OSError, ValueError) as failure:
            self.action_var.set('启动选项保存失败：' + str(failure))
        finally:
            mutex.close()

    def toggle_shaders(self) -> None:
        if self._busy():
            self.action_var.set('后台操作进行中，稍后再切换光影。')
            return
        try:
            self.settings.load()
            target = 'off' if self.settings.values.get('shaders', 'off') != 'off' else 'low'
            ok, error = self.settings._invoke('--shaders', target)
        except Exception as failure:
            ok, error = False, str(failure)
        if ok:
            self.action_var.set('光影已' + ('开启（MakeUp 轻量，低档）' if target != 'off' else '关闭') + '，下次启动游戏生效。')
            self.last_snapshot = {**self.last_snapshot, 'settings': {**(self.last_snapshot.get('settings') or {}), 'shaders': target}}
        else:
            self.action_var.set('光影设置未保存：' + error)

    def open_settings(self) -> None:
        if self._busy():
            self.action_var.set('后台操作进行中，稍后再打开设置。')
            return
        try:
            self.settings.load()
        except FileNotFoundError:
            self.first_run.set_note('请先选择离线 OW 并保存首次运行配置。')
            self.show_page('setup')
            return
        self.show_page('settings')

    def open_file(self, path: Path) -> None:
        from tkinter import messagebox
        try:
            os.startfile(path)
        except OSError as failure:
            messagebox.showerror('无法打开', str(failure), parent=self.window)

    def open_logs(self) -> None:
        self.backend.logs.mkdir(parents=True, exist_ok=True)
        self.open_file(self.backend.logs)

    def _read_snapshot(self) -> None:
        try:
            self.updates.put(self.backend.snapshot())
        except Exception as failure:
            self.updates.put({'errors': [str(failure)]})

    def _read_startup(self) -> None:
        try:
            from modpack.first_run import startup_check
            self.startup_updates.put(startup_check(self.backend.root,layout_only=True))
        except Exception as failure:
            self.startup_updates.put(dict(ready=False, errors=['启动准备检查失败：' + str(failure)]))

    def refresh_startup(self) -> None:
        if self.startup_pending:
            return
        self.startup_pending = True
        threading.Thread(target=self._read_startup, daemon=True).start()

    def _accept_startup(self, result: dict) -> None:
        self.startup_pending = False
        self.startup_result = result
        checks = result.get('environment', {}).get('checks', [])
        self.first_run.environment_ok = not any(row.get('status') == 'error' for row in checks)
        if not result.get('ready'):
            self.auto_start_pending = False
            self.startup_requested = None
            note = '；'.join(result.get('errors', []))
            self.first_run.set_note(note)
            self.action_var.set(note[:180])
            if not self._supervised() and not self._busy():
                self.show_page('setup')
            if self.loading and not self.loading_ticket:
                self.fail_loading(note or '启动准备检查失败。')

    def _try_startup_action(self) -> None:
        if self.startup_pending or not self.startup_result or not self.startup_result.get('ready'):
            return
        # Wait for an exact process snapshot, not the initial empty UI state.
        if 'supervisorPids' not in self.last_snapshot:
            return
        if self._busy() or self._supervised():
            self.auto_start_pending = False
            self.startup_requested = None
            if self.loading and not self.loading_ticket:
                self.end_loading()
            return
        requested = self.startup_requested
        self.startup_requested = None
        automatic = self.auto_start_pending
        self.auto_start_pending = False
        if requested:
            self.dispatch(*requested)
        elif automatic and self.page == 'main' and not self._leftovers():
            self.dispatch('start')
        elif self.loading and not self.loading_ticket:
            self.end_loading()

    def tick(self) -> None:
        if self.closed:
            return
        try:
            try:
                self.last_snapshot = self.updates.get_nowait()
                self.polling = False
            except queue.Empty:
                pass
            try:
                self._accept_startup(self.startup_updates.get_nowait())
            except queue.Empty:
                pass
            if self.pending is not None and self.pending.poll() is not None:
                code = self.pending.returncode
                self.pending = None
                record = self.backend.read_action()
                self.action_var.set(friendly_completion(code, self.pending_request_id, record,
                                                        self.pending_log or self.backend.logs))
                if self.pending_action.startswith('setup-'):
                    self.first_run.completed(code, self.pending_request_id, record)
                if self.loading_ticket and self.loading_ticket.request_id == self.pending_request_id:
                    if (not code and record.get('requestId') == self.pending_request_id
                            and (record.get('result') or {}).get('result') == 'existing-supervisor'):
                        self.end_loading('cancelled')
                    else:
                        self.fail_loading(friendly_completion(code, self.pending_request_id, record,
                                                              self.pending_log or self.backend.logs))
                self.pending_action = ''
            if self.loading_retry and 'supervisorPids' in self.last_snapshot and not self._busy():
                action = 'reboot' if self._leftovers() or self._supervised() else self.loading_retry
                self.loading_retry = None
                self.refresh_startup()
                self.dispatch(action)
            self._try_startup_action()
            self.update_loading()
            busy = self._busy()
            for button in self.action_buttons:
                button.set_enabled(not busy)
            self.first_run.set_busy(busy)
            if busy:
                label = '请稍候…'
            elif self._supervised():
                label = '结束游戏'
            elif self._leftovers():
                label = '重新启动'
            else:
                label = '开始游戏'
            self.main_button.set_label(label)
            shaders = (self.last_snapshot.get('settings') or {}).get('shaders', 'off')
            self.shader_button.set_label('光影：' + ('开' if shaders != 'off' else '关'))
            self.shader_button.set_selected(shaders != 'off')
            self.main_button.set_danger(label == '结束游戏')
            if self.page == 'main':
                title, detail, color = self._view()
                self._render(title, detail, color, self.last_snapshot.get('settings') or {})
                self._animate(busy)
        except Exception as failure:
            traceback.print_exc()
            if self.loading:
                self.fail_loading(str(failure))
        if not self.polling:
            self.polling = True
            threading.Thread(target=self._read_snapshot, daemon=True).start()
        self.window.after(400, self.tick)

    def _animate(self, busy: bool) -> None:
        c, W = self.canvas, self.WIDTH
        if not busy:
            c.itemconfigure(self.bar, state='hidden')
            return
        self.phase = (self.phase + 1) % 24
        left = W // 2 - 190
        start = left + (self.phase / 24) * 380 - 70
        c.coords(self.bar, max(left, start), 330, min(left + 380, start + 140), 333)
        c.itemconfigure(self.bar, state='normal')

    def close(self) -> None:
        self.closed = True
        try:
            if getattr(self, 'loading', None):
                self.end_loading('cancelled')
        finally:
            self.window.destroy()


class _SlantButton:
    """Parallelogram canvas button in the Overwatch menu style."""

    def __init__(self, ui: Any, x: int, y: int, w: int, h: int, label: str, command, *,
                 font=('Microsoft YaHei UI', 11, 'bold'), primary: bool = False, tags=()):
        self.ui, self.command, self.primary = ui, command, primary
        self.enabled, self.hover, self.danger, self.selected = True, False, False, False
        c, k = ui.canvas, h * .27
        self.glow = c.create_polygon(x + k - 3, y - 3, x + w + k + 3, y - 3, x + w - k + 3, y + h + 3, x - k - 3, y + h + 3,
                                     outline='', fill='', tags=tags)
        self.shape = c.create_polygon(x + k, y, x + w + k, y, x + w - k, y + h, x - k, y + h, outline='', width=1, tags=tags)
        self.text = c.create_text(x + w / 2, y + h / 2, text=label, font=font, tags=tags)
        for item in (self.shape, self.text):
            c.tag_bind(item, '<Enter>', lambda _e: self._hover(True))
            c.tag_bind(item, '<Leave>', lambda _e: self._hover(False))
            c.tag_bind(item, '<Button-1>', lambda _e: self._click())
        self._paint()

    def _hover(self, value: bool) -> None:
        self.hover = value
        self.ui.canvas.configure(cursor='hand2' if value and self.enabled else '')
        self._paint()

    def _click(self) -> None:
        if self.enabled:
            self.command()

    def set_enabled(self, value: bool) -> None:
        if value != self.enabled:
            self.enabled = value
            self._paint()

    def set_label(self, label: str) -> None:
        self.ui.canvas.itemconfigure(self.text, text=label)

    def set_danger(self, value: bool) -> None:
        if value != self.danger:
            self.danger = value
            self._paint()

    def set_selected(self, value: bool) -> None:
        if value != self.selected:
            self.selected = value
            self._paint()

    def state(self, flags: list[str]) -> None:  # ttk-compatible shim
        self.set_enabled('disabled' not in flags)

    def _paint(self) -> None:
        C, c = self.ui.C, self.ui.canvas
        glow = ''
        if not self.enabled:
            fill, outline, ink = C['disabled'], '', '#5d6f8c'
        elif self.primary:
            base, hi = (C['red'], C['red_hi']) if self.danger else (C['orange'], C['orange_hi'])
            fill, outline, ink = (hi if self.hover else base), '', '#0b111d'
            glow = '#3a2a12' if not self.danger else '#3a1820'
        elif self.selected:
            fill, outline, ink = C['orange'], '', '#0b111d'
        else:
            fill = '#22385a' if self.hover else C['panel2']
            outline, ink = C['cyan'] if self.hover else C['line'], C['text']
        c.itemconfigure(self.glow, fill=glow if self.hover else '')
        c.itemconfigure(self.shape, fill=fill, outline=outline)
        c.itemconfigure(self.text, fill=ink)


class _FirstRunPage:
    """Preparation shares the existing canvas and action mutex; no game owner."""
    def __init__(self, ui: LauncherUI):
        import tkinter as tk
        from modpack.config import sha256
        self.ui = ui
        self.config_sha = sha256(ui.backend.paths.config_path) if ui.backend.paths.config_path.exists() else ''
        self.environment_ok = False
        c, C, W = ui.canvas, ui.C, ui.WIDTH
        tags = ('setup',)
        c.create_polygon(40, 100, W - 40, 100, W - 52, 510, 28, 510,
                         fill=C['panel'], outline=C['line'], tags=tags)
        c.create_rectangle(40, 100, 140, 103, fill=C['orange'], outline='', tags=tags)
        c.create_text(68, 128, text='启动排错 · 环境与文件准备', anchor='w', fill=C['text'],
                      font=(ui.FONT, 15, 'bold'), tags=tags)
        self.checks = c.create_text(68, 158, text='完整整合包会自动校验并开始游戏。文件缺失时，可在此检查或准备安装。',
                                    anchor='nw', fill=C['dim'], width=720, font=(ui.FONT, 10), tags=tags)
        c.create_text(68, 254, text='已有离线 OW 客户端（只接受指定 SHA256）', anchor='w', fill=C['dim'], font=(ui.FONT, 10), tags=tags)
        c.create_text(68, 332, text='新世界名称（首次合法启动时才会创建）', anchor='w', fill=C['dim'], font=(ui.FONT, 10), tags=tags)
        self.ow_var = tk.StringVar(value=str(ui.backend.native_path))
        self.world_var = tk.StringVar(value='Overwatch World')
        entry_style = dict(bg=C['panel2'], fg=C['text'], insertbackground=C['orange'],
                           relief='flat', font=(ui.FONT, 10), highlightthickness=1,
                           highlightbackground=C['line'], highlightcolor=C['orange'])
        self.ow_entry = tk.Entry(ui.window, textvariable=self.ow_var, **entry_style)
        self.world_entry = tk.Entry(ui.window, textvariable=self.world_var, **entry_style)
        self.buttons = []
        self.buttons.append(_SlantButton(ui, 714, 274, 72, 30, '选择…', self.browse, tags=tags, font=(ui.FONT, 10)))
        self.note = c.create_text(68, 406, text='请先检查提示的缺失文件；完整离线包无需下载或重新选择客户端。',
                                  anchor='nw', fill=C['yellow'], width=710, font=(ui.FONT, 10), tags=tags)
        actions = (('检查环境', lambda: ui.dispatch('setup-check')), ('保存配置', self.save),
                   ('下载 MC/Fabric', lambda: ui.dispatch('setup-install')),
                   ('校验安装', lambda: ui.dispatch('setup-verify')), ('返回', lambda: ui.show_page('main')))
        for index, (label, command) in enumerate(actions):
            self.buttons.append(_SlantButton(ui, 66 + 148 * index, 530, 132, 34, label, command,
                                             primary=index == 1, font=(ui.FONT, 10, 'bold'), tags=tags))
        self.show(False)

    def show(self, visible: bool) -> None:
        self.ui.canvas.itemconfigure('setup', state='normal' if visible else 'hidden')
        if visible:
            self.ow_entry.place(x=68, y=274, width=622, height=31)
            self.world_entry.place(x=68, y=352, width=500, height=31)
        else:
            self.ow_entry.place_forget()
            self.world_entry.place_forget()

    def set_note(self, value: str) -> None:
        self.ui.canvas.itemconfigure(self.note, text=value[:240])

    def set_busy(self, busy: bool) -> None:
        for button in self.buttons:
            button.set_enabled(not busy)
        self.ow_entry.configure(state='disabled' if busy else 'normal')
        self.world_entry.configure(state='disabled' if busy else 'normal')

    def browse(self) -> None:
        from tkinter import filedialog
        value = filedialog.askopenfilename(parent=self.ui.window, title='选择已持有的离线 OW 研究可执行文件',
                                           filetypes=[('离线客户端', '*.exe')])
        if value:
            self.ow_var.set(value)

    def save(self) -> None:
        if self.ui._busy():
            return
        if not self.environment_ok:
            self.set_note('请先点击“检查环境”，处理阻塞项后再保存配置。')
            return
        mutex = NamedMutex(self.ui.backend.root, 'action')
        if not mutex.acquire():
            self.set_note('另一操作正在进行，请稍后重新保存。')
            return
        try:
            from modpack.first_run import prepare
            from modpack.config import sha256
            from modpack.install import download_plan
            if self.ui.backend.supervisors() or self.ui.backend.project_processes():
                raise ValueError('请先通过现有关闭流程保存并关闭游戏，再保存首次运行配置。')
            result = prepare(self.ui.backend.root, Path(self.ow_var.get()), self.world_var.get(),
                             expected_config=self.config_sha)
            write_object(self.ui.backend.root / 'config/download-plan.json', download_plan())
            self.ui.backend.paths = PackPaths(self.ui.backend.root)
            self.ui.backend.native_path = self.ui.backend.paths.get('owExecutable')
            self.config_sha = sha256(self.ui.backend.paths.config_path)
            self.set_note(f'配置已保存。正在后台校验本地游戏文件。')
            self.ui.refresh_startup()
        except Exception as failure:
            self.set_note(str(failure))
        finally:
            mutex.close()

    def completed(self, code: int, request_id: str, record: dict) -> None:
        if record.get('requestId') != request_id:
            self.set_note('尚未取得本次匹配回执，请查看日志后重试。')
            return
        if code or record.get('phase') != 'succeeded':
            self.set_note(str(record.get('error') or '准备操作失败，请查看日志。'))
            return
        result = record.get('result') or {}
        if record.get('action') == 'setup-check':
            self.environment_ok = bool(result.get('ok'))
            rows = [f'{r["name"]}：{r["detail"]}' for r in result.get('checks', [])]
            # Full numeric details stay in action-status.json, avoiding a huge
            # UI log or truncated error that hides installation failures.
            self.ui.canvas.itemconfigure(self.checks, text='\n'.join(row[:56] for row in rows), font=(self.ui.FONT, 9))
            self.set_note('环境检查通过（显卡能力仍需实测）。请选择离线 OW 后保存配置。' if self.environment_ok
                          else '环境检查存在阻塞项，暂不安装。完整结果在日志文件夹的 action-status.json。')
        elif record.get('action') == 'setup-install':
            self.set_note('安装步骤结束，正在校验本地文件。')
            self.ui.refresh_startup()
        else:
            self.set_note(f'本地 SHA256 校验通过：{result.get("files", 0)} 个文件。')
            self.ui.refresh_startup()


class _SettingsPage:
    """In-window settings drawn on the same canvas; saving reuses the guarded configure CLI."""
    SHADERS = (('off', '关闭'), ('low', '轻量'), ('medium', '标准'))
    RESOLUTIONS = (('1080p', '1080p'), ('1440p', '1440p'))
    DISTANCES = tuple((str(v), str(v)) for v in (8, 12, 16, 20, 24, 32))
    QUALITY = (('low', '低'), ('medium', '中'))

    def __init__(self, ui: LauncherUI):
        self.ui = ui
        self.values: dict[str, str] = {}
        self.groups: dict[str, list[tuple[str, _SlantButton]]] = {}
        self.worlds: list[str] = []
        self.sha = ''
        self.raw: dict = {}
        c, C, W = ui.canvas, ui.C, ui.WIDTH
        t = ('settings',)
        c.create_polygon(40, 100, W - 40, 100, W - 52, 516, 28, 516, fill=C['panel'], outline=C['line'], tags=t)
        c.create_rectangle(40, 100, 140, 103, fill=C['orange'], outline='', tags=t)
        rows = (('world', '世界存档', 140), ('shaders', 'MC 光影', 222), ('resolution', '分辨率', 272),
                ('distance', '视距（区块）', 322), ('quality', '守望画质', 372), ('flight', '飞行键', 422))
        for _key, label, y in rows:
            c.create_text(70, y, text=label, anchor='w', fill=C['dim'], font=(ui.FONT, 10), tags=t)
        # world selector: < name >
        self.world_text = c.create_text(330, 140, text='', anchor='w', fill=C['text'],
                                        font=(ui.FONT, 12, 'bold'), tags=t)
        self.world_note = c.create_text(330, 164, text='', anchor='w', fill=C['faint'], font=(ui.FONT, 9), tags=t)
        _SlantButton(ui, 230, 126, 34, 28, '‹', lambda: self.step_world(-1), font=(ui.FONT, 13, 'bold'), tags=t)
        _SlantButton(ui, 276, 126, 34, 28, '›', lambda: self.step_world(1), font=(ui.FONT, 13, 'bold'), tags=t)
        _SlantButton(ui, 640, 178, 70, 26, '导入…', self.import_map, font=(ui.FONT, 9, 'bold'), tags=t)
        _SlantButton(ui, 722, 178, 80, 26, '新建世界', self.new_world, font=(ui.FONT, 9, 'bold'), tags=t)
        for key, options, y in (('shaders', self.SHADERS, 222), ('resolution', self.RESOLUTIONS, 272),
                                ('distance', self.DISTANCES, 322), ('quality', self.QUALITY, 372)):
            x, group = 230, []
            for value, label in options:
                width = 58 if key == 'distance' else 76
                button = _SlantButton(ui, x, y - 14, width, 28, label, lambda k=key, v=value: self.pick(k, v),
                                      font=(ui.FONT, 10, 'bold'), tags=t)
                group.append((value, button))
                x += width + 12
            self.groups[key] = group
        c.create_text(230, 422, text='F6（空格上升 · Ctrl 下降）', anchor='w', fill=C['text'], font=(ui.FONT, 10), tags=t)
        c.create_line(56, 452, W - 60, 452, fill=C['line'], tags=t)
        c.create_text(70, 472, text='设置在下次启动时生效；运行中的游戏不会被改动。', anchor='w', fill=C['faint'],
                      font=(ui.FONT, 9), tags=t)
        self.note = c.create_text(70, 494, text='', anchor='w', fill=C['yellow'], font=(ui.FONT, 9), width=W - 160, tags=t)
        _SlantButton(ui, 66, 530, 130, 36, '首次运行向导', lambda: ui.show_page('setup'), font=(ui.FONT, 10, 'bold'), tags=t)
        self.save_button = _SlantButton(ui, W - 330, 530, 130, 36, '保存', self.save, primary=True,
                                        font=(ui.FONT, 12, 'bold'), tags=t)
        _SlantButton(ui, W - 186, 530, 120, 36, '返回', lambda: ui.show_page('main'), font=(ui.FONT, 11, 'bold'), tags=t)
        self.show(False)

    def show(self, visible: bool) -> None:
        self.ui.canvas.itemconfigure('settings', state='normal' if visible else 'hidden')

    def load(self) -> None:
        import configure_passthrough as cp
        raw = cp.SETTINGS.read_bytes()
        self.sha = hashlib.sha256(raw).hexdigest()
        self.raw = json.loads(raw.decode('utf-8'))
        self.worlds = cp.available()
        name = self.raw.get('worldName', '')
        if name and name not in self.worlds:
            self.worlds.append(name)
        self.values = dict(world=name, shaders=str(self.raw.get('shaders', 'off')),
                           resolution='1440p' if self.raw.get('height') == 1440 else '1080p',
                           distance=str(self.raw.get('renderDistance', 16)),
                           quality=str(self.raw.get('nativeRenderProfile', 'medium')))
        if self.values['distance'] not in {v for v, _ in self.DISTANCES}:
            self.values['distance'] = '16'
        for key in self.groups:
            self.pick(key, self.values[key])
        self._world_label()
        self.ui.canvas.itemconfigure(self.note, text='')

    def _world_label(self) -> None:
        import configure_passthrough as cp
        name = self.values.get('world', '')
        note = '已有存档' if name and (cp.SAVES / name / 'level.dat').is_file() else '下次启动时新建'
        shown = name if len(name) <= 36 else name[:34] + '…'
        self.ui.canvas.itemconfigure(self.world_text, text=shown or '（未选择）')
        self.ui.canvas.itemconfigure(self.world_note, text=f'{note}  ·  共 {len(self.worlds)} 个存档')

    def step_world(self, delta: int) -> None:
        if not self.worlds:
            return
        current = self.values.get('world')
        index = self.worlds.index(current) if current in self.worlds else 0
        self.values['world'] = self.worlds[(index + delta) % len(self.worlds)]
        self._world_label()

    def pick(self, key: str, value: str) -> None:
        self.values[key] = value
        for option, button in self.groups.get(key, []):
            button.set_selected(option == value)

    def _invoke(self, *arguments: str) -> tuple[bool, str]:
        import configure_passthrough as cp
        result = subprocess.run([sys.executable, str(Path(cp.__file__).resolve()), *arguments,
                                 '--expected-settings-sha256', self.sha], capture_output=True, text=True,
                                encoding='utf-8', errors='replace', timeout=120,
                                env={**os.environ, 'PYTHONIOENCODING': 'utf-8', 'OWMC_NO_CONSOLE': '1'},
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        if result.returncode:
            lines = (result.stderr or result.stdout or '').strip().splitlines()
            return False, lines[-1] if lines else f'退出码 {result.returncode}'
        return True, ''

    def save(self) -> None:
        import configure_passthrough as cp
        name = self.values['world']
        new = (self.raw.get('createWorld') and name == self.raw.get('worldName')
               and not (cp.SAVES / name / 'level.dat').is_file())
        ok, error = self._invoke('--new-world' if new else '--world', name, '--flight-key', 'F6',
                                 '--shaders', self.values['shaders'], '--resolution', self.values['resolution'],
                                 '--render-distance', self.values['distance'], '--ow-quality', self.values['quality'])
        if ok:
            self.ui.action_var.set('设置已保存，下次启动生效。')
            self.ui.show_page('main')
        else:
            self.ui.canvas.itemconfigure(self.note, text='未保存：' + error)

    def import_map(self) -> None:
        from tkinter import filedialog
        source = filedialog.askdirectory(title='选择包含 level.dat 的 Java 版地图文件夹', parent=self.ui.window)
        if not source:
            return
        ok, error = self._invoke('--import-world', source)
        if ok:
            self.load()
            self.values['world'] = Path(source).name
            self._world_label()
            self.ui.canvas.itemconfigure(self.note, text='地图已导入；点「保存」使用它。')
        else:
            self.ui.canvas.itemconfigure(self.note, text='导入失败：' + error)

    def new_world(self) -> None:
        from tkinter import simpledialog
        import configure_passthrough as cp
        value = simpledialog.askstring('新建世界', '新世界名称（使用配置中的种子，下次启动时创建）：',
                                       initialvalue='Overwatch World ' + time.strftime('%Y%m%d-%H%M'), parent=self.ui.window)
        if not value:
            return
        try:
            cp.world_name(value)
        except ValueError as failure:
            self.ui.canvas.itemconfigure(self.note, text=str(failure))
            return
        ok, error = self._invoke('--new-world', value)
        if ok:
            self.load()
            self.ui.canvas.itemconfigure(self.note, text='已设为新世界；下次启动时创建。')
        else:
            self.ui.canvas.itemconfigure(self.note, text='未创建：' + error)


def friendly_completion(code: int, request_id: str, record: dict, log: Path) -> str:
    if record.get('requestId') == request_id and code == 0 and record.get('phase') == 'succeeded':
        action = record.get('action')
        result = record.get('result') if isinstance(record.get('result'), dict) else {}
        if action in ('stop', 'crash-stop') or (action == 'toggle' and result.get('toggled') == 'stopped'):
            return '游戏已正常关闭。'
        if action in ('toggle', 'start', 'reboot', 'restart'):
            return '游戏已启动，请在原版界面选择英雄。'
    if record.get('requestId') == request_id and record.get('phase') == 'failed':
        return '操作失败：' + str(record.get('error') or code)[:160] + '（日志文件夹里有完整记录）'
    return action_completion_message(code, request_id, record, log)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--action', choices=ACTIONS)
    parser.add_argument('--log', type=Path)
    parser.add_argument('--world-name', default='')
    parser.add_argument('--request-id', default='')
    parser.add_argument('--loading', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--snapshot', action='store_true', help='Read-only machine state; never launch a game')
    parser.add_argument('--setup-check', action='store_true', help='Read-only first-run environment check; no download/game')
    arguments = parser.parse_args()
    if arguments.setup_check:
        backend = SessionBackend(ROOT)
        from modpack.first_run import environment, status
        print(json.dumps({'environment': environment(backend.root), 'setup': status(backend.root)}, ensure_ascii=False, indent=2))
        return 0
    if arguments.snapshot:
        backend = SessionBackend(ROOT)
        print(json.dumps(backend.snapshot(), ensure_ascii=False, indent=2))
        return 0
    if arguments.action:
        backend = SessionBackend(ROOT)
        log = arguments.log or backend.logs / (time.strftime('%Y%m%d-%H%M%S') + '-' + arguments.action + '.log')
        return run_action(backend, arguments.action, log, arguments.world_name, arguments.request_id,
                          loading=arguments.loading)
    mutex = NamedMutex(ROOT, 'ui')
    from launcher_ui_owner import Owner, acquire_ui, notify_ready
    if not acquire_ui(ROOT, mutex, NamedMutex):
        return 0
    owner = None
    window = None
    ui = None
    try:
        owner = Owner(ROOT)
        backend = SessionBackend(ROOT)
        import tkinter as tk
        window = tk.Tk()
        window.withdraw()
        ui = LauncherUI(window, backend)
        prepare_launcher_input(window)
        if ui is not None:
            ui.begin_auto_loading()
        show_launcher_window(window)
        owner.watch(window, ui)
        window.after_idle(lambda: notify_ready(ROOT))
        try:
            # Float above a fullscreen game for a moment so a click never opens "nothing".
            if ui is not None and not ui.loading and not ui.loading_error:
                window.attributes('-topmost', True)
                window.after(1500, lambda: window.attributes('-topmost', False))
        except Exception:
            pass
        window.mainloop()
        return 0
    finally:
        if ui is not None:
            ui.closed = True
        if window is not None:
            try:
                window.destroy()
            except Exception:
                pass
        if owner is not None:
            owner.close()
        mutex.close()


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception:
        # pythonw has no console. Preserve startup failures in a discoverable
        # local file instead of silently disappearing after a desktop click.
        path = ROOT / 'research/launcher/ui-errors.log'
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('a', encoding='utf-8') as stream:
            traceback.print_exc(file=stream)
        raise SystemExit(1)
