"""All paths introduced by the pack are relative to its root or user configuration."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import uuid

OW_RELATIVE = 'overwatch-2015/Overwatch Beta 0.8.0.24919/GameClientApp.patched.exe'
OW_SHA256 = 'f73a747b7d63a07402958b2b2c4587125a46ef8e181281669da009d352308e9f'
CONFIG = 'config/launcher.json'
MARKER = 'modpack.json'
ROOT = Path(__file__).resolve().parents[2]


def enable_no_console() -> None:
    """Opt-in policy inherited by the launcher's process tree, including tools.

    CREATE_NO_WINDOW is ignored with DETACHED_PROCESS/CREATE_NEW_CONSOLE, so
    replace those flags. A GUI game executable still owns its normal window.
    This does not change job membership or the existing breakaway/stop policy.
    Direct development CLI invocations keep their normal console behaviour.
    """
    if os.name != 'nt' or os.environ.get('OWMC_NO_CONSOLE') != '1':
        return
    if getattr(subprocess.Popen, '_owmc_no_console', False):
        return

    class NoConsolePopen(subprocess.Popen):
        _owmc_no_console = True

        def __init__(self, *args, **kwargs):
            arguments = list(args)
            flags = arguments[13] if len(arguments) > 13 else kwargs.get('creationflags', 0)
            flags = (flags & ~(subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_CONSOLE)) | subprocess.CREATE_NO_WINDOW
            if len(arguments) > 13:
                arguments[13] = flags
            else:
                kwargs['creationflags'] = flags
            if len(arguments) > 10 and arguments[10] is not None:
                arguments[10] = {**arguments[10], 'OWMC_NO_CONSOLE': '1'}
            if kwargs.get('env') is not None:
                kwargs['env'] = {**kwargs['env'], 'OWMC_NO_CONSOLE': '1'}
            super().__init__(*arguments, **kwargs)

    subprocess.Popen = NoConsolePopen


enable_no_console()


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding='utf-8-sig'))
    if not isinstance(value, dict):
        raise ValueError(f'{path.name} 必须是 JSON 对象。')
    return value


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f'.{uuid.uuid4().hex}.tmp')
    try:
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def sha256(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def local_path(root: Path, relative: str, *, _resolved_root: bool = False) -> Path:
    """Writable pack paths never escape through '..', junctions or symlinks."""
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError('整合包写入路径必须相对于根目录。')
    root = root if _resolved_root else root.resolve()
    path = (root / relative).resolve()
    root_text, path_text = os.path.normcase(str(root)), os.path.normcase(str(path))
    if path_text != root_text and not path_text.startswith(root_text.rstrip(os.sep) + os.sep):
        raise ValueError(f'路径超出整合包目录：{relative}')
    return path


def resolved_within(path: Path, root: Path) -> bool:
    """Fast lexical containment for paths already resolved by local_path/get."""
    value, prefix = os.path.normcase(str(path)), os.path.normcase(str(root))
    return value == prefix or value.startswith(prefix.rstrip(os.sep) + os.sep)


def manifest_files(root: Path, *, selected: set[Path] | None = None) -> dict[Path, dict]:
    """Read the shipped SHA256 inventory without downloading or modifying it."""
    root = root.resolve()
    manifest = read_json(local_path(root, 'manifest.json', _resolved_root=True))
    rows = manifest.get('files')
    if manifest.get('schemaVersion') != 1 or not isinstance(rows, list) or not rows:
        raise ValueError('整合包文件清单缺失或格式不受支持，请重新解压完整包。')
    result = {}
    selected_names = None if selected is None else {os.path.normcase(str(path.relative_to(root)))
        for path in selected if resolved_within(path,root)}
    names = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('整合包文件清单格式错误。')
        name=row.get('path','')
        if not isinstance(name,str) or not name or Path(name).is_absolute() or Path(name).drive or '..' in Path(name).parts:
            raise ValueError('整合包文件清单路径无效。')
        normalized=os.path.normcase(os.path.normpath(name))
        size, digest = row.get('bytes'), row.get('sha256')
        if normalized in names or type(size) is not int or size < 0 or not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest):
            raise ValueError(f'整合包文件清单记录无效：{row.get("path", "?")}')
        names.add(normalized)
        if selected_names is not None and normalized not in selected_names:continue
        path = local_path(root,name,_resolved_root=True)
        if path in result:raise ValueError('整合包文件清单有重复的实际文件。')
        result[path] = row
    return result


def verify_files(rows: dict[Path, dict]) -> int:
    for path, row in rows.items():
        if not path.is_file():
            raise ValueError(f'缺少文件：{row["path"]}，请重新解压完整包。')
        if path.stat().st_size != row['bytes'] or sha256(path) != row['sha256']:
            raise ValueError(f'文件 SHA256 校验失败：{row["path"]}，请重新解压完整包。')
    return len(rows)


class PackPaths:
    def __init__(self, root: Path, *, configuration: dict | None = None):
        self.root = root.resolve()
        self.packaged = (self.root / MARKER).is_file()
        self.config_path = local_path(self.root, CONFIG)
        self.config = configuration if configuration is not None else (read_json(self.config_path) if self.config_path.exists() else {})
        if self.config and self.config.get('schemaVersion') != 1:
            raise ValueError('启动器配置版本不受支持，请保留 config/launcher.json 后查看说明。')
        self.overrides = self.config.get('paths', {})
        if not isinstance(self.overrides, dict):
            raise ValueError('config/launcher.json 的 paths 必须是对象。')

    def get(self, key: str) -> Path:
        private = self.root / 'private-assets' if self.packaged else Path.home() / '.universal-modder/assets'
        defaults = {
            'python': 'runtime/python/python.exe' if self.packaged else '.venv/Scripts/python.exe',
            'java': 'runtime/java/bin/java.exe' if self.packaged else
                    'minecraft-1.21.1/runtime/java-runtime-delta/windows-x64/java-runtime-delta/bin/java.exe',
            'owExecutable': OW_RELATIVE, 'minecraft': 'minecraft-1.21.1',
            'owFallbackExecutable': 'overwatch-2015/offline-lab/GameClientApp.patched.exe',
            'profile': 'guest-passthrough-client', 'poseProfile': 'guest-pose-test-client',
            'aoaProfile': 'aoa3-connector-client',
            'neoProfile': 'aoa3-neoforge-client',
            'neoInstallSource': str(self.root / 'private-tools/neoforge-install-source.json') if self.packaged else
                                str(Path.home() / '.universal-modder/mod-cache/boss-mods-20261024/neoforge-install-source.json'),
            'privateAssets': str(private),
            'meshAssets': '', 'heroVoiceAssets': '',
            'owTypes': str(self.root / 'private-tools/OWLib-source/TankLib/STU/Types') if self.packaged else
                       str(Path.home() / '.universal-modder/toolchains/OWLib-source/TankLib/STU/Types'),
            'ffmpeg': str(self.root / 'tools/ffmpeg/ffmpeg.exe') if self.packaged else
                      str(Path.home() / 'AppData/Local/universal-modder/ffmpeg/bin/ffmpeg.exe'),
            'displayLease': str(self.root / 'data/runtime/native-display-lease.json') if self.packaged else
                            str(Path.home() / '.universal-modder/runtime/native-display-lease.json'),
            'backups': str(self.root / 'data/backups') if self.packaged else str(Path.home() / '.universal-modder/backups'),
        }
        if key in ('meshAssets','heroVoiceAssets') and key not in self.overrides:
            defaults[key] = str(self.get('privateAssets') / ('owmc-mesh' if key == 'meshAssets' else 'ow1-zhcn-2016/thnu-full'))
        value = self.overrides.get(key, defaults[key])
        if not isinstance(value, str) or not value.strip() or '\x00' in value:
            raise ValueError(f'路径配置无效：{key}')
        candidate = Path(value)
        resolved=candidate.resolve() if candidate.is_absolute() else local_path(self.root,value)
        if key=='owExecutable' and (self.packaged or (self.root/'game').is_dir()):
            # Explicit existing selections retain their identity/hash gate.
            # A stale path from another PC can fall back to a verified local copy.
            if key not in self.overrides or not resolved.is_file():
                from .client import discover
                found=discover(self.root)
                if found is not None:return found
        return resolved

    def store_path(self, path: Path) -> str:
        resolved = path.resolve()
        return resolved.relative_to(self.root).as_posix() if resolved.is_relative_to(self.root) else str(resolved)

    def launch_blockers(self) -> list[str]:
        blockers=[]
        if self.packaged and not (self.root/'manifest.json').is_file():
            blockers.append('整合包尚未构建完成，缺少 manifest.json；请保留目录后重新构建。')
        if self.account_mode() == 'external':
            blockers.append('MC 账号接口尚未接入。请使用合法账号启动器提供会话；显式 external 模式不会回退为离线身份。详见 docs/MODPACK.md。')
        return blockers

    def account_mode(self) -> str:
        value = self.config.get('account', {})
        if not isinstance(value, dict) or set(value) - {'mode'}:
            raise ValueError('account 仅接受 mode；禁止在启动器配置中保存登录凭据。')
        mode = value.get('mode', 'development-offline')
        if mode not in ('external', 'development-offline'):
            raise ValueError('不支持的 MC 账号方式。')
        return mode

    def auto_start(self) -> bool:
        value = self.config.get('autoStart', False)
        if type(value) is not bool:
            raise ValueError('autoStart 必须是 true 或 false。')
        return value

    def native_runtime(self, *, _inventory=None) -> dict:
        from .runtime import native_runtime
        return native_runtime(self, _inventory=_inventory)

    def child_environment(self, environment: dict | None = None) -> dict:
        from .runtime import native_environment
        return native_environment(self, environment)

    def native_allowed_paths(self) -> set[Path]:
        allowed = {self.get('owExecutable')}
        if 'owExecutable' not in self.overrides or 'owFallbackExecutable' in self.overrides:
            allowed.add(self.get('owFallbackExecutable'))
        return allowed

    def renderer_required(self) -> bool:
        value = self.config.get('rendererPolicy', 'optional-sodium' if self.packaged else 'required-sodium')
        if value not in ('required-sodium', 'optional-sodium'):
            raise ValueError('rendererPolicy 必须是 required-sodium 或 optional-sodium。')
        return value == 'required-sodium'


def paths() -> PackPaths:
    """New interpreters read one root-local config; no machine-specific import."""
    return PackPaths(ROOT)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='只读解析整合包路径；不启动、安装或登录。')
    parser.add_argument('--get', required=True)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--json', action='store_true')
    arguments = parser.parse_args()
    value = str(PackPaths(arguments.root).get(arguments.get))
    print(json.dumps(value, ensure_ascii=True) if arguments.json else value)
