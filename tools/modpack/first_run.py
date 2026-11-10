"""Read-only prerequisites and atomic first-run configuration. Never launch games."""
from __future__ import annotations

import json
import os
from pathlib import Path
import platform
import shutil
import struct
import subprocess
import sys

import psutil

from .config import PackPaths, OW_SHA256, local_path, manifest_files, read_json, resolved_within, sha256, verify_files, write_json

DEFAULT_SETTINGS = dict(
    schemaVersion=1, width=1920, height=1080, captureFps=165, hostFps=165,
    renderDistance=12, showMinecraft=True, minecraftWindowWidth=0,
    minecraftWindowHeight=0, fullBright=False, fillNativeHealth=True,
    hideHeroPrompt=True, flightKey='F6', villagePortals=False,
    worldName='Overwatch World', worldSeed=20261014, shaders='off',
    dayNightCycle=True, performanceGraphics=True, createWorld=True,
    nativeRenderProfile='low', twilightTrial=False, nativeMap='hollywood',
    nativeFullscreen=True, nativeDisplayTemporary=True,
)


def environment(root: Path, *, gpu: bool = True) -> dict:
    """These are preparation recommendations, not a D3D/FPS acceptance test."""
    rows = []
    def add(name, status, detail):
        rows.append(dict(name=name, status=status, detail=detail))
    windows = os.name == 'nt'
    build = sys.getwindowsversion().build if windows else 0
    add('系统', 'ok' if windows and build >= 19041 and struct.calcsize('P') == 8 else 'error',
        f'{platform.system()} {platform.release()} / {platform.machine()} / build {build}；需要 64 位 Windows 10 2004 或更新版本')
    memory = psutil.virtual_memory().total / 1024**3
    add('内存', 'ok' if memory >= 16 else 'warning',
        f'{memory:.1f} GiB；建议至少 16 GiB。内存较少时可先关闭其他大型程序。')
    free = shutil.disk_usage(root).free / 1024**3
    add('磁盘', 'ok' if free >= 15 else 'error',
        f'整合包所在卷可用 {free:.1f} GiB；准备 MC 至少预留 15 GiB，OW 与存档另计')
    try:
        import tkinter  # noqa: F401
        tk_ready = True
    except ImportError:
        tk_ready = False
    add('Python', 'ok' if sys.version_info >= (3, 13) and tk_ready else 'error',
        f'{platform.python_version()}；需要 Python 3.13+ 和 Tk')
    if gpu and windows:
        try:
            result = subprocess.run(
                ['powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
                 '[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; '
                 'Get-CimInstance Win32_VideoController | Select-Object Name,DriverVersion | ConvertTo-Json -Compress'],
                capture_output=True, text=True, encoding='utf-8-sig', timeout=12,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), check=True)
            cards = json.loads(result.stdout)
            if isinstance(cards, dict):
                cards = [cards]
            detail = '；'.join(f'{c["Name"]} / {c["DriverVersion"]}' for c in cards)
            add('显卡', 'warning', detail + '；需 D3D11/OpenGL 支持，型号枚举不代表渲染验收')
        except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError):
            add('显卡', 'warning', '未能读取显卡信息；请检查驱动。未进行游戏或渲染测试。')
    else:
        add('显卡', 'warning', '未枚举显卡；安装前请检查 D3D11/OpenGL 驱动。')
    return dict(ok=not any(r['status'] == 'error' for r in rows), checks=rows)


def verify_ow(path: Path) -> dict:
    if not path.is_file():
        raise ValueError('找不到离线 OW 可执行文件，请选择已有研究客户端；整合包不提供下载。')
    digest = sha256(path)
    if digest != OW_SHA256:
        raise ValueError('OW 文件 SHA256 不匹配，仅支持已验证的离线研究版本；未复制或启动该文件。')
    return dict(sha256=digest, bytes=path.stat().st_size)


def prepare(root: Path, ow: Path, world: str, *, expected_config: str | None = None) -> dict:
    from configure_passthrough import world_name
    name = world_name(world)
    paths = PackPaths(root)
    try:
        verified = verify_ow(ow)  # No writes before identity validation.
    except ValueError:
        if ow.is_file():raise  # Never silently replace an explicitly selected wrong hash.
        from .client import choose
        # UI work stays outside LauncherUI: only the existing interactive save
        # call may request a picker; CLI checks/tests never create a Tk root.
        import tkinter as tk
        found=choose(root,current=ow,allow_picker=getattr(tk,'_default_root',None) is not None)
        if found is None:raise
        ow=found;verified=verify_ow(ow)
    if expected_config is not None:
        current = sha256(paths.config_path) if paths.config_path.exists() else ''
        if current != expected_config:
            raise ValueError('配置已被其他窗口更新，请重新检查后保存。')
    settings_path = local_path(paths.root, 'passthrough-settings.json')
    settings = read_json(settings_path) if settings_path.exists() else {**DEFAULT_SETTINGS, 'worldName': name}
    if settings.get('schemaVersion') != 1:
        raise ValueError('现有游戏设置格式不受支持，未覆盖。')
    # Existing profiles/settings are never replaced by the wizard. The settings
    # page remains the guarded place to change an existing world's selection.
    value = {'autoStart': False, **paths.config, 'schemaVersion': 1,
             'paths': {**paths.overrides, 'owExecutable': paths.store_path(ow)}}
    write_json(paths.config_path, value)
    if not settings_path.exists():
        with settings_path.open('x', encoding='utf-8') as stream:
            stream.write(json.dumps(settings, ensure_ascii=False, indent=2) + '\n')
    from .install import verify_installation
    try:
        installation = verify_installation(root, require_complete=True)
    except (OSError, ValueError):
        installation = {}
    receipt = dict(schemaVersion=1, configured=True, ow=verified,
                   worldName=settings['worldName'], worldCreated=False,
                   minecraftInstalled=bool(installation.get('installationVerified')), gameLaunched=False,
                   launchBlockers=PackPaths(root).launch_blockers())
    write_json(local_path(paths.root, 'config/setup-state.json'), receipt)
    return receipt


def status(root: Path) -> dict:
    """Fresh, read-only offline readiness; no saved boolean can bypass SHA checks."""
    paths = PackPaths(root)
    root = paths.root
    errors = []
    inventory = None
    if paths.packaged:
        try:
            inventory = manifest_files(root)
        except (OSError, ValueError) as error:
            errors.append(str(error))
    try:
        ow = verify_ow(paths.get('owExecutable'))
    except (OSError, ValueError) as error:
        ow = None
        errors.append(str(error))
    for key, label in (('python', 'Python'), ('java', 'Java 21')):
        if not paths.get(key).is_file():
            errors.append(f'缺少 {label} 运行时：{paths.get(key)}')
    settings = local_path(paths.root, 'passthrough-settings.json')
    try:
        if not settings.is_file():
            raise ValueError('缺少游戏设置 passthrough-settings.json，请重新解压完整包或在排错页保存配置。')
        if read_json(settings).get('schemaVersion') != 1:
            raise ValueError('游戏设置格式不受支持，请保留文件后重新检查。')
    except (OSError, ValueError) as error:
        errors.append(str(error))
    from .install import _required_minecraft_files, verify_installation
    try:
        lock_path = local_path(paths.root, 'config/installation-sha256.json')
        if not paths.packaged and not lock_path.is_file():
            # The established developer checkout predates pack inventories.
            # Preserve its launch route without inventing SHA verification.
            required = _required_minecraft_files(paths.get('minecraft'))
            installation = dict(files=len(required), minecraftInstalled=True,
                                installationVerified=False, source='development-layout')
        else:
            installation = verify_installation(root, require_complete=True, _inventory=inventory)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        installation = {}
        errors.append('MC/Fabric 检查失败：' + str(error))
    verified_runtime_files = 0
    native_runtime = None
    if paths.packaged:
        try:
            inventory = manifest_files(root) if inventory is None else inventory
            prefixes = (paths.get('python').parent, paths.get('java').parent.parent,
                        root / 'tools', root / 'native-host/build', root / 'guest/build/libs',
                        paths.get('profile') / 'mods')
            prefix_text = tuple(os.path.normcase(str(prefix)) + os.sep for prefix in prefixes)
            ffmpeg_text = os.path.normcase(str(root / 'tools/ffmpeg')) + os.sep
            rows = {path: row for path, row in inventory.items()
                    if os.path.normcase(str(path)).startswith(prefix_text)
                    and not os.path.normcase(str(path)).startswith(ffmpeg_text)}
            # Minimal packs can be repaired through the explicit installer.
            # Its profile copies inherit the pinned hashes of shipped inputs,
            # without rewriting the immutable factory manifest or trusting a
            # mutable "installed" boolean.
            if installation.get('source') == 'config/installation-sha256.json':
                sources = [root / 'guest/build/libs/owmc-guest-0.1.0.jar']
                sources += [path for path in inventory if path.parent == paths.get('minecraft') / 'mods'
                            and path.match('fabric-api-*.jar')]
                for source in sources:
                    destination = paths.get('profile') / 'mods' / source.name
                    if source in inventory and destination not in rows:
                        rows[destination] = {**inventory[source],
                                             'path': paths.store_path(destination)}
            required = [paths.get('python'), paths.get('java'),
                        root / 'guest/build/libs/owmc-guest-0.1.0.jar',
                        root / 'tools/launch_passthrough_session.py', root / 'tools/stop_passthrough_session.py',
                        root / 'tools/configure_passthrough.py',
                        paths.get('profile') / 'mods/owmc-guest-0.1.0.jar']
            for stem in ('live-passthrough', 'guest-body', 'weapon-gate', 'native-emission',
                         'session-bootstrap', 'local-hero-spawn'):
                candidates = [path for path in rows if path.parent == root / 'native-host/build'
                              and path.match(f'owmc-{stem}-v*.dll')]
                if not candidates:
                    raise ValueError(f'缺少原生模块清单：owmc-{stem}，请重新解压完整包。')
            profile_mods = paths.get('profile') / 'mods'
            api = [path for path in rows if path.parent == profile_mods
                   and path.match('fabric-api-*.jar')]
            if not api:
                raise ValueError('缺少游戏档案中的 Fabric API，请重新解压完整包。')
            for path in required:
                if resolved_within(path,paths.root) and path not in inventory and path not in rows:
                    raise ValueError(f'必需文件未列入 SHA256 清单：{path.relative_to(paths.root).as_posix()}')
            verified_runtime_files = verify_files(rows)
            native_runtime = paths.native_runtime(_inventory=inventory)
        except (OSError, ValueError) as error:
            errors.append(str(error))
    blockers = paths.launch_blockers()
    return dict(packaged=paths.packaged, configured=paths.config_path.is_file(), ow=ow,
                minecraftLockPresent=local_path(paths.root, 'config/installation-sha256.json').is_file(),
                launchBlockers=blockers, errors=errors, gameLaunched=False,
                installationVerified=bool(installation.get('installationVerified')),
                minecraftInstalled=bool(installation.get('minecraftInstalled')),
                minecraftFiles=installation.get('files', 0), installationSource=installation.get('source'),
                nativeRuntime=native_runtime,
                runtimeFiles=verified_runtime_files, ready=not errors and not blockers)


def startup_check(root: Path, *, layout_only: bool = False) -> dict:
    """Background recommendations stay silent unless a required check fails."""
    paths = PackPaths(root)
    if layout_only and paths.packaged:
        # The UI only submits a request. Its independent action coordinator
        # still runs status() with every SHA check before spawning either game.
        # Avoid doing that entire scan twice on a player's first double-click.
        required = [root/'manifest.json', paths.get('python'), paths.get('java'),
                    paths.get('owExecutable'), root/'passthrough-settings.json',
                    root/'guest/build/libs/owmc-guest-0.1.0.jar']
        errors = [f'缺少必需文件：{path.name}' for path in required if not path.is_file()]
        setup = dict(errors=errors,launchBlockers=paths.launch_blockers(),
                     ready=not errors,integrityVerified=False,
                     integrityCheck='action-coordinator-before-game-spawn')
    else:
        setup = status(root)
    prerequisites = environment(root, gpu=False)
    # The 15 GiB recommendation is for downloading a new installation. It must
    # not send an already complete offline pack back through the installer.
    environment_errors = [row['detail'] for row in prerequisites['checks']
                          if row['status'] == 'error' and row['name'] != '磁盘']
    errors = setup['errors'] + setup['launchBlockers'] + environment_errors
    return dict(ready=not errors, errors=errors, setup=setup, environment=prerequisites,
                gameLaunched=False)
