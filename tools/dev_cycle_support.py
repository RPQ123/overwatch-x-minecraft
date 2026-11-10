"""Development-cycle crash/identity support. Importing this starts no process."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

import psutil
from minecraft_crash_evidence import detect, snapshot, PROFILES
from modpack.config import paths
from process_images import game_processes

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / '.venv/Scripts/python.exe'
NATIVE = ROOT / 'overwatch-2015/Overwatch Beta 0.8.0.24919/GameClientApp.patched.exe'


def project_processes():
    """Exact paths/--gameDir, including javaw; unrelated Java is not a blocker."""
    processes = game_processes(native=NATIVE, profiles=(ROOT/name for name in PROFILES), java=paths().get('java'))
    return [dict(pid=process.pid, created=process.create_time(), executable=process.exe()) for process in processes]


def check_crash(state, output):
    baseline = json.loads(Path(state).read_text(encoding='utf-8'))
    evidence = detect(baseline)
    if not evidence:
        return False
    Path(output).write_text(json.dumps(dict(minecraftCrashed=True, evidence=evidence,
                                          forcedTermination=False), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('检测到 Minecraft 客户端/JVM 崩溃，本轮失败；将正常关闭残余会话，禁止强杀。', flush=True)
    for row in evidence[:4]:
        print('崩溃证据：' + row['path'] + ('；' + row['description'] if row.get('description') else ''), flush=True)
    return True


def backup_profiles(logs):
    # Only a stopped profile is a consistent pre-test save backup. This stays
    # in ignored local evidence, never in source control or a system directory.
    if project_processes():
        raise RuntimeError('游戏仍在运行；未备份/改装档案，也未继续构建')
    destination = Path(logs) / 'profile-backups' / str(time.time_ns())
    destination.mkdir(parents=True, exist_ok=False)
    copied = []
    for name in PROFILES:
        profile = ROOT / name
        if profile.is_dir():
            # MC 自带的 backups/ 只是存档的历史副本（13G 且每局增长），原地保留，不重复复制，否则几局就占满磁盘。
            shutil.copytree(profile, destination / name,
                            ignore=lambda folder, names: ['backups'] if Path(folder) == profile else [])
            copied.append(name)
    # 只保留最近 8 份自动备份（每份约 1.6G），否则几十局测试就会占满磁盘。
    history = sorted((p for p in destination.parent.iterdir() if p.is_dir() and p.name.isdigit()), key=lambda p: int(p.name))
    for old in history[:-8]:
        shutil.rmtree(old, ignore_errors=True)
    receipt = dict(directory=str(destination.resolve()), profiles=copied, stoppedBeforeBackup=True)
    (Path(logs) / 'profile-backup.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print('游戏档案/存档已备份：' + str(destination), flush=True)
    return receipt


def normal_cleanup(logs):
    """Invoke strict native restoration and normal API/GLFW guest close."""
    logs = Path(logs)
    logs.mkdir(parents=True, exist_ok=True)
    stop_log = logs / 'stop.log'
    # No timeout command/kill fallback. Strict stop has its own bounded waits.
    result = subprocess.run([str(PYTHON), 'tools/project_launcher.py', '--action', 'crash-stop',
                             '--log', str(stop_log)], cwd=ROOT, capture_output=True, text=True)
    remaining = project_processes()
    receipt = dict(stopExitCode=result.returncode,
                   remaining=remaining, forcedTermination=False, log=str(stop_log))
    (logs / 'cleanup-result.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    if result.returncode or remaining:
        print(f'正常关闭未完成；保留进程 {[(p["pid"]) for p in remaining]}，未强杀。日志：{stop_log}', flush=True)
        return 1
    print('残余会话已正常关闭；保存结果见 research/normal-session-stop 与 cleanup-result.json。', flush=True)
    return 0


def run_test(arguments):
    if check_crash(arguments.state, arguments.crash_output):
        normal_cleanup(arguments.logs)
        return 4
    from launch_passthrough_session import native_pids, api, PROFILE
    from native_normal_close import capture_native_identity
    pids = native_pids()
    if len(pids) != 1:
        raise ValueError('需要唯一身份匹配的原版进程')
    native = capture_native_identity(pids[0])
    health = api('health')
    guest = psutil.Process(health['sourcePid'])
    args = guest.cmdline()
    index = args.index('--gameDir')
    if (health.get('mode') != 'full-world-frame-proof' or index + 1 >= len(args)
            or Path(args[index + 1]).resolve() != PROFILE.resolve()
            or Path(guest.exe()).name.lower() not in ('java.exe', 'javaw.exe')):
        raise ValueError('Minecraft 身份不匹配；未运行测试')
    command = [str(PYTHON), arguments.test, '--pid', str(native['pid']), '--created', repr(native['creation']),
               '--mc-pid', str(guest.pid), '--mc-created', repr(guest.create_time()),
               '--world', health['worldName'], '--guest-sha256',
               hashlib.sha256((PROFILE / 'mods/owmc-guest-0.1.0.jar').read_bytes()).hexdigest(),
               '--output', arguments.evidence]
    test_log = Path(arguments.logs) / 'test.log'
    with test_log.open('w', encoding='utf-8') as stream:
        process = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
        crashed = False
        while process.poll() is None:
            if check_crash(arguments.state, arguments.crash_output):
                crashed = True
                normal_cleanup(arguments.logs)
                try:
                    process.wait(20)  # tests normally end on their identity/API timeout
                except subprocess.TimeoutExpired:
                    print(f'测试辅助进程 {process.pid} 尚未退出；已记录，未强杀。', flush=True)
                break
            time.sleep(.5)
    if not crashed:
        crashed = check_crash(arguments.state, arguments.crash_output)
        if crashed:
            normal_cleanup(arguments.logs)
    if crashed:
        return 4
    if process.returncode:
        print(f'实测脚本失败（exit={process.returncode}）；日志：{test_log}', flush=True)
        return process.returncode or 1
    print('实测脚本退出码 0；报告：' + arguments.evidence, flush=True)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('backup', 'snapshot', 'check', 'alive', 'phase', 'cleanup', 'run'))
    parser.add_argument('--state', default='research/dev-cycle/crash-baseline.json')
    parser.add_argument('--crash-output', default='research/dev-cycle/minecraft-crash.json')
    parser.add_argument('--logs', default='research/dev-cycle')
    parser.add_argument('--since', type=float, default=0)
    parser.add_argument('--test')
    parser.add_argument('--evidence')
    args = parser.parse_args()
    if args.action == 'backup':
        backup_profiles(args.logs)
    elif args.action == 'snapshot':
        Path(args.state).parent.mkdir(parents=True, exist_ok=True)
        Path(args.state).write_text(json.dumps(snapshot(ROOT), indent=2) + '\n', encoding='utf-8')
    elif args.action == 'check':
        return 4 if check_crash(args.state, args.crash_output) else 0
    elif args.action == 'alive':
        print(len(project_processes()))
    elif args.action == 'cleanup':
        return normal_cleanup(args.logs)
    elif args.action == 'phase':
        from project_launcher import read_object, SessionBackend
        try:
            status = read_object(ROOT / 'research/session-status.json')
            native = SessionBackend().native_identity(status)
            phase = status.get('phase', 'stale') if native and native.create_time() > args.since else 'stale'
        except (OSError, ValueError, psutil.Error):
            phase = 'stale'
        print(phase)
    elif args.action == 'run':
        return run_test(args)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        print('开发循环失败：' + repr(error), file=sys.stderr)
        raise SystemExit(1)
