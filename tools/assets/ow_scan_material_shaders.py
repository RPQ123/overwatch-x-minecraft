"""Bounded local24919 shader metadata search. Writes only ignored asset-cache.

No native process, network, deployment or unguarded archive reads.
"""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import hashlib
import json
import struct
import zlib
import argparse

from ow_asset_chain import Archive
from ow_shader_disassemble import extract_code, disassemble


AUDITED = (
    ('grenade','0e0000006b4d8661','0a100000ce0fd8e4','06100000bd45cdf8','cb4[2].xyzx',['a726d0a7','65bcf745']),
    ('graviton','0e000000115641cb','0a100000dc832082','061000003e6fede9','cb4[6].xyzx',['30f4092f','47f339b9','126f16c7']),
    ('pulse','0e0000008a92fe7f','0a10000035a32d70','0610000094608b7d','cb4[8].xyzx',['8c0b8364']),
    ('sense','0e0000007b543afe','0a100000dd0d909c','0610000000c27ccc','cb4[0].yzwy',['1502d2de','65bcf745']),
    ('dragon','0e000000000007a5/0810','0a100000198c2e6e','06100000e955e2fd','cb5[9].xyzx',['067e6202','ef1dc737','5cf81ebb']),
    ('zen-distortion-candidate','0e000000e06922b3/b815a1f6','0a10000095498bbb','06100000a8061dd1','mul o1.xy',['a726d0a7','65bcf745']),
)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scan-runtime-vars',action='store_true',help='Also scan all bounded hero shader metadata; first run can take minutes')
    args=parser.parse_args()
    archive = Archive('colors-20261026')
    for package in ('0400000000000141', '0400000000000216', '04000000000003bf'):
        archive.load_package(package)
    receipts=[]
    for name,material,instance,code,needle,slots in AUDITED:
        row=archive.records[instance]
        raw=archive.fetch(row['ckey'],instance+'.raw')
        if len(raw)!=row['bytes'] or hashlib.md5(raw).hexdigest()!=row['ckey']:
            raise ValueError('Shader instance CKey mismatch')
        start,end=struct.unpack_from('<2Q',raw)
        metadata=zlib.decompress(raw[start:end],31)
        bytecode=extract_code(archive,code)
        assembly=disassemble(bytecode)
        if needle not in assembly:
            raise ValueError('Audited RGB/output swizzle changed')
        bindings=[]
        for slot in slots:
            offset=metadata.find(bytes.fromhex(slot)[::-1])
            if offset<0 or metadata[offset+4:offset+8]!=b'\0\x02\0\0':
                raise ValueError('Audited shader resource binding changed')
            register=struct.unpack_from('<H',metadata,offset+8)[0]
            if register>127:raise ValueError('Shader texture register bounds')
            bindings.append(dict(nameHash=slot,register=register,metadataOffset=offset))
        (archive.out/(name+'.asm')).write_text(assembly,encoding='utf-8')
        receipts.append(dict(name=name,material=material,instance=instance,code=code,
                             instanceSha256=hashlib.sha256(raw).hexdigest(),
                             bytecodeSha256=hashlib.sha256(bytecode).hexdigest(),
                             textureRegisters=bindings,
                             colorInstructions=[s for s in assembly.splitlines() if needle in s],
                             permutationAuthenticated=False))
    (archive.out/'shader-evidence.json').write_text(json.dumps(dict(shaders=receipts,
        limits='Exact archived code/bindings and compatible CB layouts; full material permutation selection and dynamic variables not executed',
        inGameVerified=False),indent=2)+'\n',encoding='utf-8')
    if not args.scan_runtime_vars:
        print(json.dumps(dict(auditedShaders=len(receipts),permutationAuthenticated=False)))
        return
    wanted = {int(x, 16) for x in (
        'db6e69d4', '1a96e2db', 'd7d89d4a', 'f10c259c', 'c4f2bd15',
        'd8efb748', '030c9a3c', '39c8a66e', 'e03afc76', 'dec3b596',
        '08203ef6', 'd8ef8f22', '581a3da4')}
    matches = []
    count = 0
    for guid, row in archive.records.copy().items():
        if not guid.startswith('0a10'):
            continue
        raw = archive.fetch(row['ckey'], guid + '.raw')
        if len(raw) != row['bytes'] or hashlib.md5(raw).hexdigest() != row['ckey']:
            raise ValueError('Shader archive CKey mismatch')
        start, end = struct.unpack_from('<2Q', raw)
        decoder = zlib.decompressobj(31)
        decoded = decoder.decompress(raw[start:end], 16 * 1024 * 1024 + 1)
        if not decoder.eof or len(decoded) > 16 * 1024 * 1024:
            raise ValueError('Shader metadata compression bounds')
        hits = {f'{x:08x}': [i for i in range(len(decoded)-3)
                            if decoded[i:i+4] == struct.pack('<I', x)]
                for x in wanted if struct.pack('<I', x) in decoded}
        if hits:
            matches.append(dict(guid=guid, hits=hits, ckey=row['ckey'],
                                codeIndex=f'{struct.unpack_from("<I",raw,24)[0]:08x}'))
        count += 1
    output = dict(instances=count, matches=matches, inGameVerified=False)
    (archive.out / 'shader-variable-matches.json').write_text(json.dumps(output, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(instances=count, matchingInstances=len(matches))))


if __name__ == '__main__':
    main()
