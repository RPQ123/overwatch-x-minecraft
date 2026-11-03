"""One read-only support snapshot for an ALREADY RUNNING guarded offline24919 process.

Never launches games, writes native memory, calls a skill, installs a callback or
publishes production bindings. Run before/after real native actions under Claude's
normal session guards. Output stays local. For song semantics capture expression
bytes AND nested varbags; neither a fade timer nor SetVar counts infer a song.
"""
import argparse
import importlib
import json
import math
import struct
from pathlib import Path

from inspect_native_impact import describe
from observe_native_weapon_states import WeaponStates
from observe_overwatch import ResearchProcess


def expression(reader, obj):
    if reader.metadata(obj)[1] != 0xec502a81:
        return None
    def array(at, stride):
        storage, flag = reader.unpack('<QQ', at)
        if not storage or flag not in (1, 2):
            raise ValueError('Expression representation')
        a, b = reader.unpack('<QQ', storage)
        items, count = (a, b) if flag == 1 else (b, a)
        if not 0 <= count <= 256 or count and not items:
            raise ValueError('Expression bounds')
        return reader.memory.read(items, count * stride) if count else b''
    code, values = array(obj + 0x20, 1), array(obj + 0x40, 4)
    return dict(code=code.hex(), constantsHex=values.hex(),
                constantsFloat=[x[0] if math.isfinite(x[0]) else None for x in struct.iter_unpack('<f', values)], evaluated=False)


def inspect(process, hero):
    module = importlib.import_module('prepare_hero_' + hero.lower())
    reader = WeaponStates(process)
    sample = reader.sample_weapon(False, True)
    admin = reader.pointer(process.base + 0x17b7f90)
    table = process.read(reader.pointer(admin + 16), 65536)
    controller = reader.entity(table, sample['localId'])
    info = reader.component(controller, 0x3f)
    if reader.unpack('<Q', info + 0x98)[0] != module.HERO:
        raise ValueError('Current native hero differs')
    out = dict(hero=hero, modelId=sample['modelId'], nativeCalls=False, nativeWrites=False,
               newCallbackOwners=False, readOnly=True, records=list(sample['records'].values()),
               variables=sample['observedVariables'], definitions={})
    for name, guid, size, profile in module.GRAPHS:
        matches = [key for key in reader.graph_cache if key[2] == guid]
        if len(matches) != 1:
            raise ValueError('Graph not unique: ' + name)
        instance, graph, _ = matches[0]
        nodes = reader.stu_list(graph + 0x50)
        if len(nodes) != size:
            raise ValueError('Graph size changed: ' + name)
        for label, index, kind in profile:
            node = nodes[index]
            if reader.bindings.metadata(node)[1] != kind:
                raise ValueError('Node type changed: ' + name + ':' + label)
            detail = describe(reader.bindings, node)
            if name == 'lucioSong':
                value = next(f for f in detail['fields'] if f['hash'] == '5180e750')
                detail['unevaluatedExpression'] = expression(reader.bindings, value['pointer'])
            out['definitions'][f'{guid:016x}:{index}'] = detail
    confirm = reader.sample_weapon(False, True)
    if confirm['modelId'] != sample['modelId'] or confirm['localId'] != sample['localId']:
        raise ValueError('Native owner changed during snapshot')
    return out


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pid', type=int, required=True)
    p.add_argument('--hero', choices=['Mercy', 'Zenyatta', 'Lucio'], required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    process = ResearchProcess(args.pid)
    try:
        out = inspect(process, args.hero)
    finally:
        process.close()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps(dict(readOnly=True, hero=args.hero, nodes=len(out['definitions']), output=str(args.output))))
