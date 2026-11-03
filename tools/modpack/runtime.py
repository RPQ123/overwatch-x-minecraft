"""Pin the pack's native VC++ search directory without loading game DLLs."""
from __future__ import annotations

import os
from pathlib import Path
import struct

from .config import manifest_files, sha256, verify_files

VC_DLLS = ('msvcp140.dll', 'vcruntime140.dll', 'vcruntime140_1.dll')


def pe_linkage(path: Path) -> dict:
    """Read bounded x64 PE import/export tables, including ordinal imports."""
    if not 0 < path.stat().st_size <= 32 * 1024 * 1024:
        raise ValueError(f'运行库 PE 大小无效：{path.name}')
    data = path.read_bytes()

    def unpack(fmt, offset):
        if offset < 0 or offset + struct.calcsize(fmt) > len(data):
            raise ValueError(f'运行库 PE 数据越界：{path.name}')
        return struct.unpack_from(fmt, data, offset)

    pe = unpack('<I', 0x3c)[0]
    if data[:2] != b'MZ' or data[pe:pe + 4] != b'PE\0\0':
        raise ValueError(f'不是有效 PE 文件：{path.name}')
    machine, count = unpack('<HH', pe + 4)
    optional_size = unpack('<H', pe + 20)[0]
    opt = pe + 24
    if machine != 0x8664 or unpack('<H', opt)[0] != 0x20b:
        raise ValueError(f'需要 x64 运行库：{path.name}')
    if not 0 < count <= 96 or optional_size < 112:
        raise ValueError(f'运行库 PE 头无效：{path.name}')
    headers = unpack('<I', opt + 60)[0]
    image_base = unpack('<Q', opt + 24)[0]
    directories = unpack('<I', opt + 108)[0]
    if directories > 16 or 112 + directories * 8 > optional_size:
        raise ValueError(f'运行库 PE 目录越界：{path.name}')
    sections = [unpack('<IIII', opt + optional_size + index * 40 + 8) for index in range(count)]

    def offset(rva):
        if 0 <= rva < min(headers, len(data)):
            return rva
        for virtual_size, address, size, raw in sections:
            if address <= rva < address + max(virtual_size, size) and rva - address < size:
                return raw + rva - address
        raise ValueError(f'运行库 PE 地址不可读取：{path.name}')

    def string(rva):
        start = offset(rva)
        end = data.find(b'\0', start, min(start + 4096, len(data)))
        if end < 0:
            raise ValueError(f'运行库 PE 名称未终止：{path.name}')
        return data[start:end].decode('ascii')

    def directory(index):
        return unpack('<II', opt + 112 + index * 8) if index < directories else (0, 0)

    imports = {}
    for index, stride in ((1, 20), (13, 32)):
        rva, size = directory(index)
        if not rva:
            continue
        for item in range(min(size // stride, 8192)):
            row = unpack('<' + 'I' * (stride // 4), offset(rva + item * stride))
            if not any(row):
                break
            if index == 1:
                name, thunk = row[3], row[0] or row[4]
            else:
                bias = 0 if row[0] & 1 else image_base
                name, thunk = row[1] - bias, (row[4] or row[3]) - bias
            symbols = imports.setdefault(string(name).casefold(), set())
            for slot in range(65536):
                entry = unpack('<Q', offset(thunk + slot * 8))[0]
                if not entry:
                    break
                symbols.add(entry & 0xffff if entry & (1 << 63) else string(entry + 2))
            else:
                raise ValueError(f'运行库 PE 导入符号超过上限：{path.name}')
        else:
            raise ValueError(f'运行库 PE 导入表未结束：{path.name}')

    exports = set()
    rva, size = directory(0)
    if rva:
        base, functions, names, addresses, strings, ordinals = unpack('<IIIIII', offset(rva) + 16)
        if functions > 65536 or names > functions:
            raise ValueError(f'运行库 PE 导出表超过上限：{path.name}')
        for index in range(functions):
            if unpack('<I', offset(addresses + index * 4))[0]:
                exports.add(base + index)
        for index in range(names):
            ordinal = unpack('<H', offset(ordinals + index * 2))[0]
            if ordinal >= functions or base + ordinal not in exports:
                raise ValueError(f'运行库 PE 导出序号无效：{path.name}')
            exports.add(string(unpack('<I', offset(strings + index * 4))[0]))
    return dict(machine=machine, imports=imports, exports=exports)


def native_runtime(paths, *, _inventory=None) -> dict:
    """Select one complete, SHA-pinned directory and check the plugin's imports."""
    if not paths.packaged:
        return dict(verified=False, source='development-system', directory=None, libraries=[])
    plugin = paths.get('owExecutable').with_name('inject.dll')
    candidates = (plugin.parent, paths.get('java').parent, paths.get('python').parent)
    selected = {plugin} | {directory/name for directory in candidates for name in VC_DLLS}
    inventory = manifest_files(paths.root,selected=selected) if _inventory is None else _inventory
    if not plugin.is_file():
        raise ValueError('缺少离线客户端 inject.dll，请重新解压完整包。')
    if plugin.is_relative_to(paths.root):
        if plugin not in inventory:
            raise ValueError('客户端 inject.dll 未列入 SHA256 清单。')
        verify_files({plugin: inventory[plugin]})
    consumer = pe_linkage(plugin)
    failures = []
    for directory in dict.fromkeys(candidates):
        libraries = [directory / name for name in VC_DLLS]
        if not directory.is_relative_to(paths.root) or not all(path in inventory for path in libraries):
            continue
        try:
            verify_files({path: inventory[path] for path in libraries})
            images = {path.name: pe_linkage(path) for path in libraries}
            required = {name: set() for name in VC_DLLS}
            for image in (consumer, *images.values()):
                for name, symbols in image['imports'].items():
                    if name in required:
                        required[name].update(symbols)
            for name, symbols in required.items():
                missing = symbols - images[name]['exports']
                if missing:
                    first = sorted(str(symbol) for symbol in missing)[0]
                    raise ValueError(f'{name} 缺少所需导出：{first}')
            return dict(verified=True, source='bundled-sha256-x64-imports',
                        directory=paths.store_path(directory), pluginSha256=sha256(plugin),
                        pluginPinned=plugin in inventory,
                        libraries=[dict(path=paths.store_path(path), sha256=inventory[path]['sha256'],
                                        requiredExports=len(required[path.name]),
                                        exportIdentifiers=len(images[path.name]['exports'])) for path in libraries])
        except (OSError, ValueError, UnicodeError) as error:
            failures.append(str(error))
    detail = '；'.join(failures) or '包内没有同目录、已登记 SHA256 的三个 x64 VC++ 运行库'
    raise ValueError('离线 VC++ 运行库检查失败：' + detail)


def native_environment(paths, environment: dict | None = None) -> dict:
    """PATH is inherited by the actual OW child; no system installation/edit."""
    result = dict(os.environ if environment is None else environment)
    report = native_runtime(paths)
    if not report['verified']:
        return result
    directory = str((paths.root / report['directory']).resolve())
    old_path = next((value for key, value in result.items() if key.upper() == 'PATH'), '')
    for key in list(result):
        if key.upper() == 'PATH':
            del result[key]
    result['PATH'] = os.pathsep.join([directory] + [part for part in old_path.split(os.pathsep)
                                                   if part and os.path.normcase(part) != os.path.normcase(directory)])
    result['OWMC_NATIVE_RUNTIME_DIR'] = directory
    return result
