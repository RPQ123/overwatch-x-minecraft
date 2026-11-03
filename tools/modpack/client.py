"""Bounded offline OW client discovery; hash checks only, never executes clients."""
from __future__ import annotations

import ctypes
import os
from pathlib import Path

from .config import OW_RELATIVE, OW_SHA256, sha256

FOLDER = 'Overwatch Beta 0.8.0.24919'
_hashes: dict[tuple, bool] = {}


def local_drives() -> list[Path]:
    if os.name != 'nt':
        return []
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.GetLogicalDrives.restype=ctypes.c_uint32
    kernel.GetDriveTypeW.argtypes=[ctypes.c_wchar_p]
    mask=kernel.GetLogicalDrives()
    return [Path(f'{chr(65+i)}:/') for i in range(26) if mask&(1<<i)
            and kernel.GetDriveTypeW(f'{chr(65+i)}:/') in (2,3)]


def valid(path: Path, expected_sha256: str | None = None) -> bool:
    try:
        expected=expected_sha256 or OW_SHA256
        stat=path.stat()
        if not path.is_file():return False
        key=(str(path.resolve()),stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns,expected)
        if key not in _hashes:_hashes[key]=sha256(path)==expected
        return _hashes[key]
    except (OSError,ValueError):
        return False


def executable_candidates(folder: Path):
    for name in ('GameClientApp.patched.exe','GameClientApp.exe'):
        yield folder/name
    try:
        yield from sorted(folder.glob('GameClientApp*.exe'))
    except OSError:
        return


def discover(root: Path, *, drives: list[Path] | None = None, expected_sha256: str | None = None) -> Path | None:
    root=root.resolve()
    # game/ is always preferred over automatic legacy/common-location choices.
    folders=[root/'game'/FOLDER,root/'game',root/FOLDER,
             root.parent/FOLDER,root.parent/'overwatch-2015'/FOLDER,
             (root/OW_RELATIVE).parent]
    for drive in local_drives() if drives is None else drives:
        for base in ('','Games','Game','Program Files','Program Files (x86)',
                     'Blizzard','Battle.net','Downloads','Desktop','Users/Public/Downloads'):
            folders.append(drive/base/FOLDER)
            if base in ('Games','Game','Blizzard','Battle.net'):
                folders.append(drive/base/'Overwatch'/FOLDER)
    if drives is None:
        folders.extend([Path.home()/'Desktop'/FOLDER,Path.home()/'Downloads'/FOLDER])
    seen=set()
    for folder in folders:
        for path in executable_candidates(folder):
            name=str(path).casefold()
            if name in seen:continue
            seen.add(name)
            if valid(path,expected_sha256):return path.resolve()
    return None


def choose(root: Path, *, current: Path | None = None, picker=None, allow_picker=False,
           expected_sha256: str | None = None, drives=None) -> Path | None:
    if current is not None and valid(current,expected_sha256):return current.resolve()
    found=discover(root,drives=drives,expected_sha256=expected_sha256)
    if found is not None:return found
    if not allow_picker:return None
    if picker is None:
        from tkinter import filedialog
        picker=lambda: filedialog.askopenfilename(title='未找到客户端，请选择已有离线 OW 可执行文件',
                                                  filetypes=[('GameClientApp 可执行文件','GameClientApp*.exe')])
    selected=picker()
    if not selected:return None
    path=Path(selected)
    if path.is_dir():
        path=next((p for p in executable_candidates(path) if valid(p,expected_sha256)),path)
    if not valid(path,expected_sha256):
        raise ValueError('所选 OW 客户端 SHA256 不匹配；未复制或启动该文件。')
    return path.resolve()
