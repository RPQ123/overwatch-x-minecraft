"""Optional read-only Hanzo Scatter parameter binding (auto-discovered HERO hook).

Pins b9:26/84 and the original expressions; does not enable factory calibration,
install anything, evaluate native code or launch a game. Missing declarations
publish available=false instead of breaking the existing primary/Sonic binding.
"""
import argparse
import json
import struct
from pathlib import Path

from observe_overwatch import ROOT, ResearchProcess
from observe_native_weapon_states import WeaponStates
from native_armory_binding import projectile_resources, projectile_gravity, primitive
from inspect_native_control_skills import literal

HERO = 0x02e0000000000005
GRAPHS = []  # Reuses the existing b9:26 node binding; no new trigger owner.
GRAPH = 0x05800000000000b9
RESOURCES = {0x04000000000001a4, 0x040000000000020c}
EXPECTED = {
    'parentSpeed': ([70, 0, 70, 1, 31, 0, 102, 100, 0], [25., 65.], ['0d800000000002a5']),
    'childSpeed': ([70, 0, 70, 1, 70, 2, 31, 0, 102, 100, 102, 0], [.8, 20., 65.], ['0d800000000002a5']),
    'childDamage': ([31, 0, 0], [], ['0d80000000000980']),
    'childDamageInit': ([70, 0, 70, 1, 70, 0, 101, 31, 0, 102, 100, 0], [15., 75.], ['0d800000000002a5']),
}


def check_expression(name, code, constants, paths):
    expected_code, expected_floats, expected_paths = EXPECTED[name]
    wanted = struct.pack('<' + 'f' * len(expected_floats), *expected_floats)
    if bytes(code) != bytes(expected_code) or constants != wanted or paths != [[p] for p in expected_paths]:
        raise ValueError('Scatter original expression differs: ' + name)


def prepare(process, pid):
    path = ROOT / f'native-host/build/native-hanzoScatterContext-request-{pid}.json'
    out = dict(version=1, pid=pid, hero=HERO, available=False, readOnly=True,
               reason='Scatter declarations not yet prepared', byteGuards=[])
    try:
        base = ROOT / f'native-host/build/native-hanzoSkills-request-{pid}.json'
        if not base.is_file():
            from prepare_native_hanzo import prepare as prepare_nodes
            prepare_nodes(process, pid)
        out.update(json.loads(base.read_text(encoding='utf-8')))
        out.update(available=False, byteGuards=[])
        r = WeaponStates(process); sample = r.sample_weapon(False, True); b = r.bindings
        if sample['modelId'] != out['modelId'] or out['hero'] != HERO or out['pid'] != pid:
            raise ValueError('Scatter current node binding owner differs')
        matches = [key for key in r.graph_cache if key[2] == GRAPH]
        if len(matches) != 1: raise ValueError('Scatter graph not unique')
        instance, graph, _ = matches[0]; nodes = r.stu_list(graph + 0x50)
        if instance != out['script'] or graph != out['graph'] or len(nodes) <= 84:
            raise ValueError('Scatter current graph/instance differs')
        guards = {}

        def guard(at, length):
            if not 1 <= length <= 4096: raise ValueError('Scatter byte guard bounds')
            guards[(at, length)] = dict(address=at, hex=process.read(at, length).hex())

        def typed(obj, kind=None):
            _, actual, size = b.metadata(obj)
            if kind is not None and actual != kind: raise ValueError('Scatter config type differs')
            guard(obj, 8); return actual, size

        def ref(obj, key, target=None):
            _, at, category, _ = b.field(obj, key)
            if category != 2: raise ValueError('Scatter field is not a reference')
            guard(at, 8); result = b.pointer(at); typed(result, target); return result

        def array(at, stride, expected_count=None):
            guard(at, 16); storage, flag = b.unpack('<QQ', at)
            if not storage or flag not in (1, 2): raise ValueError('Scatter config array storage')
            guard(storage, 16); a, c = b.unpack('<QQ', storage); items, count = (a, c) if flag == 1 else (c, a)
            if not 0 <= count <= 256 or expected_count is not None and count != expected_count:
                raise ValueError('Scatter config array count')
            if count: guard(items, count * stride)
            return items, process.read(items, count * stride) if count else b''

        def dynamic(obj, expected):
            typed(obj, 0xf8cc195d)
            _, raw = array(obj + 0x10, 16, 1)
            path_values = [f'{rid:016x}' for _, rid in struct.iter_unpack('<QQ', raw)]
            if path_values != [expected] or b.dynamic_path(obj) != [expected]: raise ValueError('Scatter variable path differs')
            return path_values

        def expression(name, obj):
            if typed(obj)[0] not in (0xcc3a08f4, 0xec502a81): raise ValueError('Scatter scalar expression type differs')
            _, code = array(obj + 0x20, 1); _, constants = array(obj + 0x40, 4); _, variables = array(obj + 0x30, 8)
            paths = [dynamic(ptr, EXPECTED[name][2][i]) for i, (ptr,) in enumerate(struct.iter_unpack('<Q', variables))]
            check_expression(name, code, constants, paths)
            return dict(code=list(code), constantBytes=constants.hex(), variables=paths)

        parent = nodes[26]; typed(parent, 0x860ee5fc)
        split = ref(parent, 0x3ac99059, 0x07e34e24); child = ref(split, 0x3c26d198, 0x860ee5fc)
        for node in [parent, child]:
            resources = projectile_resources(r, node)
            if {v[0] for v in resources} != RESOURCES: raise ValueError('Scatter parent/child resource allowlist differs')
            for _, at, _, _ in resources: guard(at, 8)
            if abs(projectile_gravity(r, node) - 9.800000190734863) > 1e-6: raise ValueError('Scatter gravity differs')
            for field, value in [(0x5257be73, 10), (0x308e35d5, 300)]:
                obj = ref(node, field); kind, size = typed(obj)
                if literal(b, obj) != value: raise ValueError('Scatter lifetime/range differs')
                guard(obj, min(size, 32))
        p_impact = ref(parent, 0x3d131607, 0x4ef1dd7e); p_health = ref(p_impact, 0x89174668, 0x06a06f4e)
        dynamic(ref(p_health, 0xc43222bc), '0d800000000001dc')
        c_impact = ref(child, 0x3d131607, 0x4ef1dd7e); c_health = ref(c_impact, 0x89174668, 0x06a06f4e)
        _, size = typed(nodes[84]); guard(nodes[84], min(size, 512))
        dynamic(ref(nodes[84], 0xec9f34a6), '0d80000000000980')
        declarations = dict(parentSpeed=expression('parentSpeed', ref(parent, 0xac2f916a)),
                            childSpeed=expression('childSpeed', ref(child, 0xac2f916a)),
                            childDamage=expression('childDamage', ref(c_health, 0xc43222bc)),
                            childDamageInit=expression('childDamageInit', ref(nodes[84], 0x5180e750)))
        states = r.stu_list(graph + 0x60); state_index = states.index(parent)
        if state_index > 255: raise ValueError('Scatter Volley state token bounds')
        instance_id = r.unpack('<h', instance + 0x18)[0]
        out['volleyKey'] = ((instance_id * 8 & 0xffff) << 16) | (state_index << 8)
        # Pin both relevant original node pointers in the current graph array.
        items, _ = array(graph + 0x50, 8)
        guard(items + 26 * 8, 8); guard(items + 84 * 8, 8)
        out['numericVtable'] = process.base + 0x1608248
        out['byteGuards'] = list(guards.values())
        if len(out['byteGuards']) > 192 or sum(len(g['hex'])//2 for g in out['byteGuards'])>16384: raise ValueError('Scatter guard count/bytes limit')
        if r.sample_weapon(False, True)['modelId'] != sample['modelId']: raise ValueError('Scatter owner changed during prepare')
        out.update(available=True, reason='', expressionDeclarations=declarations, activationReadRequired=True)
        out['prepareSample'] = {}
        for name, rid in [('q2a5', 0x0d800000000002a5), ('direct1dc', 0x0d800000000001dc), ('child980', 0x0d80000000000980)]:
            try:
                address, value, bucket = primitive(r, out['bag'], rid)
                out['prepareSample'][name] = dict(value=value, address=address, bucket=bucket, runtimeReuse=False)
            except (ValueError, OSError) as error: out['prepareSample'][name] = dict(unavailable=str(error))
    except (ValueError, OSError, KeyError, IndexError, struct.error) as error:
        out.update(available=False, reason='Scatter optional context unavailable: ' + str(error), byteGuards=[])
    temporary = path.with_suffix('.tmp'); temporary.write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8'); temporary.replace(path)
    return dict(hero=HERO, readOnly=True, optional=True, available=out['available'], reason=out['reason'], path=str(path))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--pid', required=True, type=int)
    args = parser.parse_args(); process = ResearchProcess(args.pid)
    try: print(json.dumps(prepare(process, args.pid), ensure_ascii=False))
    finally: process.close()
