"""SHA-guarded file-only builders graph/resource scan; no native process access."""
import json
from pathlib import Path
import struct
from ow_asset_chain import Archive, CACHE


def inspect():
    out = CACHE/'builders-graphs'
    out.mkdir(parents=True, exist_ok=True)
    archive = Archive(out)
    rows = []
    for hero, graphs in [('02e0000000000065', ['0580000000000232','0580000000000233','058000000000022a']),
                         ('02e0000000000006', ['05800000000000f3','05800000000001c2'])]:
        archive.load_package(hero)
        for guid in graphs:
            record = archive.resolve(guid)
            if record is None:
                raise ValueError('missing graph '+guid)
            raw = archive.fetch(record['ckey'], guid+'.raw')
            refs = []
            for offset in range(len(raw)-7):
                resource, = struct.unpack_from('<Q', raw, offset)
                target = f'{resource:016x}'
                if target in archive.records and resource >> 48 in (0x0400,0x0600,0x0580):
                    refs.append(dict(offset=offset, resource=target))
            rows.append(dict(hero=hero, graph=guid, bytes=len(raw), refs=refs))
    (out/'refs.json').write_text(json.dumps(rows, indent=2)+'\n', encoding='utf-8')
    return rows


if __name__ == '__main__':
    print(json.dumps(inspect()))
