"""Bounded, read-only MC/JVM crash detection relative to a cycle snapshot."""
from __future__ import annotations

import time
from pathlib import Path
from modpack.config import PackPaths

PROFILES = ('guest-passthrough-client', 'aoa3-connector-client')
MARKERS = ('Reported exception thrown!', 'Minecraft has crashed!',
           'Crash report saved to:',
           'A fatal error has been detected by the Java Runtime Environment')


class MinecraftCrashError(RuntimeError):
    def __init__(self, evidence):
        self.evidence = evidence
        super().__init__('Minecraft 客户端崩溃；请正常关闭残余会话。报告：' +
                         ', '.join(row['path'] for row in evidence))


def _signature(path):
    stat = path.stat()
    return [stat.st_mtime_ns, stat.st_size, stat.st_ino]


def _reports(root, profiles):
    paths = set(root.glob('hs_err_pid*.log'))
    for profile in profiles:
        paths.update(profile.glob('hs_err_pid*.log'))
        paths.update((profile / 'crash-reports').glob('crash-*-client.txt'))
    return sorted(paths)


def snapshot(root, profiles=None):
    root = Path(root).resolve()
    configured=PackPaths(root)
    profiles = [Path(p).resolve() for p in profiles] if profiles is not None else [configured.get(key) for key in ('profile','aoaProfile')]
    files = {}
    for path in _reports(root, profiles) + [p / 'logs/latest.log' for p in profiles]:
        try:
            files[str(path)] = _signature(path)
        except FileNotFoundError:
            pass
    return dict(started=time.time(), root=str(root), profiles=list(map(str, profiles)), files=files)


def detect(baseline):
    root = Path(baseline['root'])
    profiles = list(map(Path, baseline['profiles']))
    found = []
    for path in _reports(root, profiles):
        try:
            signature = _signature(path)
            if signature == baseline['files'].get(str(path)):
                continue
            with path.open('rb') as stream:
                excerpt = stream.read(8192).decode('utf-8', errors='replace')
        except FileNotFoundError:
            continue
        description = next((line.strip() for line in excerpt.splitlines()
                            if line.startswith('Description:') or 'Exception:' in line), '')
        found.append(dict(path=str(path), kind='jvm-crash' if path.name.startswith('hs_err_') else 'mc-client-crash',
                          signature=signature, description=description[:500]))
    for profile in profiles:
        path = profile / 'logs/latest.log'
        try:
            current = _signature(path)
            old = baseline['files'].get(str(path))
            if current == old:
                continue
            # A rotated/truncated log is a new stream; an appended log is read
            # only after the baseline offset, never from an old crash marker.
            offset = old[1] if old and old[2] == current[2] and current[1] >= old[1] else 0
            with path.open('rb') as stream:
                stream.seek(max(offset, current[1] - 262144))
                tail = stream.read(262144).decode('utf-8', errors='replace')
            marker = next((marker for marker in MARKERS if marker in tail), None)
            if marker:
                found.append(dict(path=str(path), kind='mc-crash-log', marker=marker, signature=current))
        except FileNotFoundError:
            continue
    return found
