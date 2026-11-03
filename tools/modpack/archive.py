"""Offline ZIP64 packaging and static Windows compatibility audit; never run a game.

Examples (use the project Python 3.13):
  tools/modpack/archive.py --audit dist/OWMC-1.0.0 --report research/oneclick/C4-compatibility.json
  tools/modpack/archive.py dist/OWMC-1.0.0
  tools/modpack/archive.py --verify dist/OWMC-1.0.0.zip

Existing outputs and failed .partial files are retained. No downloads, DLL loading,
profile changes, extraction, or build-manifest edits are performed.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import mmap
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import struct
import sys
import time
import zipfile

CHUNK = 4 * 1024 * 1024
PE_SUFFIXES = {'.exe', '.dll', '.pyd'}
CONFIG_SUFFIXES = {'.json', '.ini', '.cfg', '.conf', '.config', '.xml', '.toml',
                   '.yaml', '.yml', '.properties', '.vmoptions', '.pth', '._pth', '.txt'}
ABSOLUTE = re.compile(r'(?<![A-Za-z0-9])[A-Za-z]:[\\/][^\r\n\"<>|,;]*|\\\\[^\\\s]+\\[^\r\n\"<>|,;]+')
VC_RUNTIME = re.compile(r'(?:vcruntime\d+.*|msvcp\d+.*|msvcr\d+.*|concrt\d+.*|vcomp\d+.*)\.dll$', re.I)
LEGACY_DX = re.compile(r'(?:d3dx\d+_\d+|d3dcompiler_(?:4[0-6]|[0-3]\d)|xinput1_[123]|xaudio2_[0-7]|xapofx\d+_\d+)\.dll$', re.I)


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def fingerprint(path: Path) -> tuple[int, int, int, int]:
    value = path.stat()
    return value.st_size, value.st_mtime_ns, value.st_dev, value.st_ino


def is_link(path: Path) -> bool:
    value = path.lstat()
    return stat.S_ISLNK(value.st_mode) or bool(getattr(value, 'st_file_attributes', 0) & 0x400)


def safe_name(name: str) -> str:
    parts = PurePosixPath(name).parts
    if (not parts or name != '/'.join(parts) or name.startswith('/')
            or any(p in ('.', '..') or ':' in p or '\\' in p or p.endswith((' ', '.'))
                   or any(ord(character) < 32 or character in '<>\"|?*' for character in p)
                   or re.match(r'^(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)', p, re.I) for p in parts)):
        raise ValueError(f'不安全或不兼容 Windows 的包内路径：{name}')
    return name


def snapshot(root: Path) -> dict[str, tuple[int, int, int, int]]:
    if is_link(root) or not root.is_dir():
        raise ValueError('压缩源必须是普通目录，不能是链接或联接点。')
    result = {}
    folded = set()
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in sorted(dirs + files):
            path = Path(directory) / name
            if is_link(path):
                raise ValueError(f'拒绝链接或重解析点：{path.relative_to(root)}')
            if name in files:
                relative = safe_name(path.relative_to(root).as_posix())
                if not stat.S_ISREG(path.stat().st_mode):
                    raise ValueError(f'拒绝非普通文件：{relative}')
                if relative.casefold() in folded:
                    raise ValueError(f'Windows 大小写路径冲突：{relative}')
                folded.add(relative.casefold())
                result[relative] = fingerprint(path)
    return dict(sorted(result.items()))


def assert_snapshot(root: Path, expected: dict) -> None:
    if snapshot(root) != expected:
        raise ValueError('压缩期间源目录发生变化；保留 partial，等其他线程完成后使用新输出名重试。')


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def create_archive(root: Path, output: Path | None = None, *, level: int = 1) -> dict:
    root = root.absolute()
    # Check before resolving: resolve() would hide a source junction/symlink.
    before = snapshot(root)
    root = root.resolve()
    safe_name(root.name)
    output = (output or root.with_name(root.name + '.zip')).absolute()
    if output.suffix.lower() != '.zip' or output.resolve().is_relative_to(root):
        raise ValueError('输出必须是源目录以外的 .zip 文件。')
    checksum = output.with_name(output.name + '.sha256')
    inventory_path = output.with_name(output.name + '.manifest.json')
    if output.exists() or checksum.exists() or inventory_path.exists():
        raise FileExistsError('输出或校验文件已存在；请先保留到 _archive 或指定新输出名。')
    total = sum(row[0] for row in before.values())
    output.parent.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(output.parent).free < total + 128 * 1024 * 1024:
        raise ValueError('可用空间不足以保留完整压缩包；源文件未修改。')
    partial = output.with_name(output.name + '.partial-' + time.strftime('%Y%m%d-%H%M%S') + f'-{os.getpid()}')
    inventory = dict(schemaVersion=1, rootDirectory=root.name,
                     createdUtc=datetime.now(timezone.utc).isoformat(),
                     purpose='local-offline-snapshot', files=[])
    with zipfile.ZipFile(partial, 'x', compression=zipfile.ZIP_DEFLATED,
                         compresslevel=level, allowZip64=True, strict_timestamps=False) as archive:
        archive.mkdir(root.name + '/')
        for name, identity in before.items():
            source = root / name
            if fingerprint(source) != identity or is_link(source):
                raise ValueError(f'文件压缩前已改变：{name}')
            hashed = hashlib.sha256()
            count = 0
            info = zipfile.ZipInfo.from_file(source, root.name + '/' + name, strict_timestamps=False)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.compress_level = level
            with source.open('rb') as reader, archive.open(info, 'w', force_zip64=True) as writer:
                while chunk := reader.read(CHUNK):
                    hashed.update(chunk)
                    count += len(chunk)
                    writer.write(chunk)
            if fingerprint(source) != identity or count != identity[0]:
                raise ValueError(f'文件压缩时发生变化：{name}')
            inventory['files'].append(dict(path=name, bytes=count, sha256=hashed.hexdigest()))
        assert_snapshot(root, before)
    # Read actual compressed data back, checking both ZIP CRC and file SHA256.
    result = verify_archive(partial, expected_root=root.name, expected_inventory=inventory)
    assert_snapshot(root, before)
    archive_hash = digest(partial)
    if output.exists() or checksum.exists() or inventory_path.exists():
        raise FileExistsError('验证期间输出名被占用，partial 已保留。')
    # Windows rename refuses an existing destination; never replace user files.
    partial.rename(output)
    write_json(inventory_path, inventory)
    with checksum.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(archive_hash + '  ' + output.name + '\n')
    result.update(output=str(output), bytes=output.stat().st_size,
                  sha256=archive_hash, checksum=str(checksum), sourceStable=True,
                  checksumVerified=True, inventory=str(inventory_path))
    return result


def verify_archive(path: Path, *, expected_root: str | None = None,
                   expected_inventory: dict | None = None) -> dict:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if any(stat.S_ISLNK(item.external_attr >> 16) for item in archive.infolist()):
            raise ValueError('ZIP 含符号链接。')
        folded = [n.casefold() for n in names]
        if len(folded) != len(set(folded)):
            raise ValueError('ZIP 含重复或大小写冲突条目。')
        roots = {PurePosixPath(safe_name(n.rstrip('/'))).parts[0] for n in names}
        if len(roots) != 1 or (expected_root and roots != {expected_root}):
            raise ValueError('ZIP 必须只有一个指定的根目录。')
        root = next(iter(roots))
        inventory_path = path.with_name(path.name + '.manifest.json')
        inventory = (expected_inventory if expected_inventory is not None else
                     json.loads(inventory_path.read_text(encoding='utf-8')))
        if inventory.get('schemaVersion') != 1 or inventory.get('rootDirectory') != root:
            raise ValueError('压缩清单版本或根目录不匹配。')
        listed = set()
        total = 0
        for row in inventory['files']:
            name = root + '/' + safe_name(row['path'])
            if name in listed:
                raise ValueError('压缩清单含重复文件。')
            listed.add(name)
            value = hashlib.sha256()
            count = 0
            with archive.open(name) as stream:
                while chunk := stream.read(CHUNK):
                    value.update(chunk)
                    count += len(chunk)
            if count != row['bytes'] or value.hexdigest() != row['sha256']:
                raise ValueError(f'压缩包内容校验失败：{row["path"]}')
            total += count
        actual = {n for n in names if not n.endswith('/')}
        if actual != listed:
            raise ValueError('压缩清单与实际 ZIP 文件不一致。')
    checksum = path.with_name(path.name + '.sha256')
    if checksum.exists():
        if checksum.read_text(encoding='utf-8').strip() != digest(path) + '  ' + path.name:
            raise ValueError('ZIP 整体 SHA256 校验失败。')
    return dict(rootDirectory=root, files=len(listed), uncompressedBytes=total,
                verified=True, checksumVerified=checksum.exists())


def pe_metadata(data) -> dict:
    """Parse normal/delay imports and embedded UAC manifests without loading code."""
    def unpack(fmt, offset):
        if offset < 0 or offset + struct.calcsize(fmt) > len(data):
            raise ValueError('PE 数据越界。')
        return struct.unpack_from(fmt, data, offset)

    if data[:2] != b'MZ':
        raise ValueError('不是 PE/MZ 文件。')
    pe = unpack('<I', 0x3c)[0]
    if data[pe:pe + 4] != b'PE\0\0':
        raise ValueError('PE 签名无效。')
    machine, sections = unpack('<HH', pe + 4)
    optional_size = unpack('<H', pe + 20)[0]
    opt = pe + 24
    magic = unpack('<H', opt)[0]
    if magic not in (0x10b, 0x20b):
        raise ValueError('不支持的 PE 可选头。')
    is64 = magic == 0x20b
    image_base = unpack('<Q' if is64 else '<I', opt + (24 if is64 else 28))[0]
    dirs = opt + (112 if is64 else 96)
    dir_count = unpack('<I', opt + (108 if is64 else 92))[0]
    section_start = opt + optional_size
    mappings = []
    for index in range(sections):
        virtual_size, rva, raw_size, raw = unpack('<IIII', section_start + index * 40 + 8)
        mappings.append((rva, virtual_size, raw_size, raw))

    def offset(rva):
        if rva < unpack('<I', opt + 60)[0]:
            return rva
        for start, virtual_size, size, raw in mappings:
            if start <= rva < start + max(virtual_size, size) and rva - start < size:
                return raw + rva - start
        raise ValueError(f'PE RVA 不可读取：{rva:x}')

    def directory(index):
        return unpack('<II', dirs + index * 8) if index < dir_count else (0, 0)

    def cstring(rva):
        start = offset(rva)
        end = data.find(b'\0', start, min(start + 4096, len(data)))
        if end < 0:
            raise ValueError('PE 导入名未终止。')
        return data[start:end].decode('ascii').lower()

    imports = set()
    delayed = set()
    for index, stride, target in ((1, 20, imports), (13, 32, delayed)):
        address, size = directory(index)
        if not address:
            continue
        for item in range(min(size // stride, 8192)):
            values = unpack('<' + 'I' * (stride // 4), offset(address) + item * stride)
            if not any(values):
                break
            name_rva = values[3] if index == 1 else values[1] - (0 if values[0] & 1 else image_base)
            target.add(cstring(name_rva))
        else:
            raise ValueError('PE 导入表缺少结束项或超过预算。')

    levels = set()
    resource, resource_size = directory(2)
    if resource:
        base = offset(resource)

        def resources(relative, depth=0, manifest=False):
            if depth > 4 or relative < 0 or relative + 16 > resource_size:
                raise ValueError('PE 资源目录越界。')
            named, numbered = unpack('<HH', base + relative + 12)
            if named + numbered > 4096:
                raise ValueError('PE 资源数超过预算。')
            for item in range(named + numbered):
                key, child = unpack('<II', base + relative + 16 + item * 8)
                wanted = manifest or (depth == 0 and key == 24)
                if not wanted:
                    continue
                if child & 0x80000000:
                    resources(child & 0x7fffffff, depth + 1, wanted)
                else:
                    rva, size = unpack('<II', base + child)
                    if size > 1024 * 1024:
                        raise ValueError('PE manifest 过大。')
                    start = offset(rva)
                    raw = data[start:start + size]
                    text = raw.decode('utf-16' if raw.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8', errors='replace')
                    levels.update(re.findall(r'requestedExecutionLevel\b[^>]*\blevel\s*=\s*[\"\']([^\"\']+)', text))

        resources(0)
    return dict(machine=hex(machine), bits=64 if is64 else 32,
                imports=sorted(imports), delayImports=sorted(delayed),
                executionLevels=sorted(levels), managed=bool(directory(14)[0]))


def compatibility_audit(root: Path) -> dict:
    root = root.absolute()
    before = snapshot(root)
    binaries, errors, absolute_paths = [], [], []
    index = defaultdict(list)
    for name in before:
        if Path(name).suffix.lower() in PE_SUFFIXES:
            index[Path(name).name.casefold()].append(name)
    for name in before:
        path = root / name
        if path.suffix.lower() in PE_SUFFIXES:
            try:
                with path.open('rb') as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as mapped:
                    binaries.append(dict(path=name, **pe_metadata(mapped)))
            except (ValueError, OSError, UnicodeError, struct.error) as exc:
                errors.append(dict(path=name, error=str(exc)))
        # Native DLLs shipped inside LWJGL/JNA JARs also require a system audit.
        if path.suffix.lower() == '.jar':
            try:
                with zipfile.ZipFile(path) as archive:
                    for entry in archive.infolist():
                        if Path(entry.filename).suffix.lower() in PE_SUFFIXES:
                            if entry.file_size > 128 * 1024 * 1024:
                                raise ValueError('嵌套 PE 超过静态分析预算。')
                            label = name + '!/' + entry.filename
                            binaries.append(dict(path=label, **pe_metadata(archive.read(entry))))
            except (ValueError, OSError, zipfile.BadZipFile, UnicodeError, struct.error) as exc:
                errors.append(dict(path=name, error=str(exc)))
        if path.suffix.lower() in CONFIG_SUFFIXES:
            try:
                raw = path.read_bytes()
                if len(raw) > 32 * 1024 * 1024:
                    continue
                if raw.startswith((b'\xff\xfe\0\0', b'\0\0\xfe\xff')):
                    contents = raw.decode('utf-32')
                elif raw.startswith((b'\xff\xfe', b'\xfe\xff')):
                    contents = raw.decode('utf-16')
                elif b'\0' in raw[:1024]:
                    continue
                else:
                    contents = raw.decode('utf-8-sig')
                for line_number, line in enumerate(contents.splitlines(), 1):
                    matches = sorted(set(match.group(0).strip()[:300] for match in ABSOLUTE.finditer(line)))
                    if matches:
                        absolute_paths.append(dict(path=name, line=line_number, values=matches))
            except (OSError, UnicodeError):
                continue
    system32 = Path(os.environ.get('SystemRoot', 'C:/Windows')) / 'System32'
    dependencies = defaultdict(lambda: dict(normal=[], delayed=[]))
    for binary in binaries:
        for key, label in (('imports', 'normal'), ('delayImports', 'delayed')):
            for dependency in binary[key]:
                dependencies[dependency][label].append(binary['path'])
    resolved = []
    for name, consumers in sorted(dependencies.items()):
        category = ('vc-runtime' if VC_RUNTIME.fullmatch(name) else
                    'legacy-directx' if LEGACY_DX.fullmatch(name) else
                    'windows-api-set' if name.startswith(('api-ms-', 'ext-ms-')) else
                    'bundled' if index.get(name) else
                    'host-system' if (system32 / name).is_file() else 'unresolved')
        adjacent = [consumer for consumer in consumers['normal'] + consumers['delayed']
                    if any(PurePosixPath(candidate).parent == PurePosixPath(consumer).parent
                           for candidate in index.get(name, []))]
        resolved.append(dict(name=name, category=category, bundledPaths=index.get(name, []),
                             hostSystemFile=(system32 / name).is_file(), adjacentConsumers=adjacent, **consumers))
    manifest_path = root / 'manifest.json'
    manifest_status = {}
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        listed = {row['path']: row for row in manifest['files']}
        changed = []
        for name, row in listed.items():
            if name in before and (before[name][0] != row['bytes'] or digest(root / name) != row['sha256']):
                changed.append(name)
        manifest_status = dict(sha256=digest(manifest_path), registeredFiles=len(listed),
                               unregistered=sorted(set(before) - set(listed) - {'manifest.json'}),
                               missing=sorted(set(listed) - set(before)), changed=changed)
        manifest_status['completeAndMatching'] = not any(manifest_status[k] for k in ('unregistered', 'missing', 'changed'))
    assert_snapshot(root, before)
    longest = max(before, key=len, default='')
    return dict(schemaVersion=1, createdUtc=datetime.now(timezone.utc).isoformat(),
                rootDirectory=root.name, files=len(before), bytes=sum(v[0] for v in before.values()),
                longestRelativePath=longest, longestRelativePathCharacters=len(longest),
                binaries=binaries, binaryErrors=errors, dependencies=resolved,
                absolutePaths=absolute_paths, buildManifest=manifest_status,
                counts=dict(binaries=len(binaries), binaryErrors=len(errors),
                            dependencyCategories=dict(Counter(r['category'] for r in resolved)),
                            absolutePathFiles=len({row['path'] for row in absolute_paths}),
                            absolutePathLines=len(absolute_paths)),
                limits=['静态导入及延迟导入，不执行 DLL/EXE，不证明 GPU/驱动或游戏可玩。',
                        'hostSystemFile 仅反映审计机；全包同名 DLL 不保证实际搜索路径能找到。',
                        '运行时 LoadLibrary、注册表/COM、.NET 可选功能及安全软件策略仍需干净系统实测。'])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', nargs='?', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--level', type=int, choices=range(10), default=1)
    parser.add_argument('--audit', type=Path)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--verify', type=Path)
    args = parser.parse_args()
    if sum(x is not None for x in (args.source, args.audit, args.verify)) != 1:
        parser.error('请选择一个操作：源目录、--audit 或 --verify。')
    if args.audit:
        if not args.report:
            parser.error('--audit 需要 --report；报告必须放在包外。')
        if args.report.resolve().is_relative_to(args.audit.resolve()):
            parser.error('兼容性报告不能写进被审计的包。')
        result = compatibility_audit(args.audit)
        write_json(args.report, result)
        summary = dict(report=str(args.report), **result['counts'],
                       buildManifestMatching=result['buildManifest'].get('completeAndMatching'))
        print(json.dumps(summary, ensure_ascii=False))
        return 2 if result['binaryErrors'] else 0
    result = verify_archive(args.verify) if args.verify else create_archive(args.source, args.output, level=args.level)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, zipfile.BadZipFile) as error:
        print('打包/审计失败：' + str(error), file=sys.stderr)
        raise SystemExit(1)
