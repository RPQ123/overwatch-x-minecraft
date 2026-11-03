"""Read-only Tracer Recall declarations, not a gameplay/history binding.

Unidentified native node fields stay identified by hash. Timing-like numbers,
animation and latest logger rows do not establish rewind/heal/ammo semantics.
"""
import argparse
import json

from observe_overwatch import ROOT, ResearchProcess
from observe_native_weapon_states import WeaponStates
from inspect_native_control_skills import literal, ref
from native_armory_binding import primitive

HERO = 0x02e0000000000003
RESOURCE = 0x058000000000001a


def inspect(process):
    r = WeaponStates(process)
    sample = r.sample_weapon(False, True)
    b = r.bindings
    admin = r.pointer(process.base + 0x17b7f90)
    table = process.read(r.pointer(admin + 16), 65536)
    controller = r.entity(table, sample['localId'])
    reference = r.component(controller, 0x20)
    info = r.component(controller, 0x3f)
    if r.unpack('<Q', info + 0x98)[0] != HERO:
        raise ValueError('Select original Tracer')
    model = r.entity(table, sample['modelId'])
    matches = [key for key in r.graph_cache if key[2] == RESOURCE]
    if len(matches) != 1:
        raise ValueError('Recall graph is not unique on current model')
    script, graph, _ = matches[0]
    bag = r.pointer(script + 0x98)
    nodes = r.stu_list(graph + 0x50)
    if len(nodes) != 48:
        raise ValueError('Recall graph changed')
    for index, kind in ((1, 0x7211cf70), (9, 0x7fb4bf64), (12, 0x85c28a9a),
                        (13, 0x85c28a9a), (14, 0x970ec198), (27, 0xf7d6498c)):
        if b.metadata(nodes[index])[1] != kind:
            raise ValueError('Recall definition type changed')

    def number(index, owner, key):
        return literal(b, ref(b, nodes[index], key, owner, 0xbfd9aadd))

    raw_fields = {f'{key:08x}': number(1, 0x7211cf70, key)
                  for key in (0xa9157cbb, 0x53222441, 0x05aaa790, 0xd970b2d6)}
    # Keep unknown field meanings unknown; do not name .1 a sample cadence.
    if raw_fields['a9157cbb'] != 3 or raw_fields['d970b2d6'] != 0 or any(
            abs(raw_fields[key] - .1) > 1e-6 for key in ('53222441', '05aaa790')):
        raise ValueError('Recall numeric declarations need new calibration')
    assignments = {}
    for index, identifier in ((15, 0x0d800000000000d7), (16, 0x0d800000000001d8)):
        destination = ref(b, nodes[index], 0xec9f34a6, 0x4698e4b6, 0xf8cc195d)
        if b.dynamic_path(destination) != [f'{identifier:016x}']:
            raise ValueError('Recall SetVar destination changed')
        assignments[f'{identifier:016x}'] = number(index, 0x4698e4b6, 0x5180e750)
    if abs(assignments['0d800000000000d7'] - .9) > 1e-6 or assignments['0d800000000001d8'] != 12:
        raise ValueError('Recall SetVar values need new calibration')
    _, cooldown, _ = primitive(r, bag, 0x0d800000000001d8)
    if cooldown != 12:
        raise ValueError('Recall cooldown variable changed')
    cursor = {f'{key:08x}': number(14, 0x970ec198, key)
              for key in (0x5d05b699, 0xfc7bc05c, 0x924cebfa)}
    if cursor != {'5d05b699': 1, 'fc7bc05c': 0, '924cebfa': .375}:
        raise ValueError('Recall ChaseVar declaration changed')
    flows = {}
    for index, expected in ((12, 0x0480000000000023), (13, 0x0480000000000030)):
        config = ref(b, nodes[index], 0x547d9847, 0x85c28a9a, 0xbfd9aadd)
        if b.metadata(config)[1] != 0x824213f0:
            raise ValueError('Recall dataflow config type changed')
        owner, at, category, declared = b.field(config, 0x547d9847)
        if (owner, category, declared) != (0x824213f0, 12, 0x77d4d730):
            raise ValueError('Recall dataflow reference declaration changed')
        entry, resource = r.unpack('<QQ', at)
        if not entry or resource != expected:
            raise ValueError('Recall dataflow reference changed')
        flows[str(index)] = f'{resource:016x}'
    current = process.read(r.pointer(admin + 16), 65536)
    if (r.pointer(process.base + 0x17b7f90) != admin
            or r.unpack('<I', admin + 0x220)[0] != sample['localId']
            or r.entity(current, sample['localId']) != controller
            or r.entity(current, sample['modelId']) != model
            or r.component(controller, 0x20) != reference
            or r.component(controller, 0x3f) != info
            or r.unpack('<I', reference + 0x94)[0] != sample['modelId']
            or r.unpack('<Q', info + 0x98)[0] != HERO
            or r.pointer(script + 0x160) != graph or r.pointer(script + 0x98) != bag
            or r.unpack('<Q', script + 0x150)[0] != RESOURCE
            or r.pointer(r.pointer(r.pointer(script + 0x10) + 0x450) + 8) != model):
        raise ValueError('Recall owner changed during calibration')
    return dict(version=1, hero='Tracer', heroId=f'{HERO:016x}', modelId=sample['modelId'],
                script=f'{RESOURCE:016x}', node1Type='7211cf70', node1Fields=raw_fields,
                setVarDeclarations=assignments, declaredCooldown=cooldown,
                chaseVar14Fields=cursor, dataflowReferences=flows,
                diagnosticStates=[v for v in sample['records'].values()
                                  if v['instanceAddress'] == script],
                readOnly=True, newHooksInstalled=False, nativeCalls=False,
                losslessDeploymentChannel=False, mcRecallImplemented=False,
                nativeHistorySemanticsVerified=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid', type=int, required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    path = (ROOT / args.output).resolve()
    if ROOT / 'research' not in path.parents or path.suffix != '.json':
        parser.error('Output must be a private research JSON file')
    process = ResearchProcess(args.pid)
    try:
        result = inspect(process)
    finally:
        process.close()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in result.items() if key != 'diagnosticStates'}))


if __name__ == '__main__':
    main()
