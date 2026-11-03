"""Read-only Mercy24919 node bindings; never calls native skills or installs an owner.

HERO-BRIEFS-NEW8-20261025.md: staff7/19 are search-channel B/E; guardian25 and
resurrection36 are attempts only. Pistol10/MoveTo2/passive2/4 are bound to actual
future execution, never to input/search or a replay of baseline-active self-heal4.
Their saved trace has no NEW phase. E/Q commit remain unresolved. MC effects and
unverified live status are documented by MercyServer and the support handoff.
"""
import ctypes
import json
import struct
from observe_overwatch import ROOT
from observe_native_weapon_states import WeaponStates
from provided_plugin_symbols import provided_plugin

HERO = 0x02e0000000000004
GRAPHS = [
    ('mercyStaff', 0x058000000000006b, 122,
     [('heal', 7, 0x498b421a), ('boost', 19, 0x498b421a)]),
    ('mercyPistol', 0x058000000000006d, 58, [('volley', 10, 0x860ee5fc)]),
    ('mercyGuardian', 0x058000000000006e, 61,
     [('search', 25, 0x498b421a), ('move', 2, 0xc1035274)]),
    ('mercyResurrect', 0x05800000000000ca, 48,
     [('search', 36, 0x498b421a), ('wait', 40, 0x65f158da)]),
    ('mercyPassive', 0x0580000000000071, 39,
     [('glide', 2, 0x02e4a0ab), ('selfHeal', 4, 0x619d9e95)]),
]
UNAVAILABLE = {
    'pistol': '006d:10 wired only to a fresh original Volley E; saved staff-only trace has no pistol tick/factory; live acceptance pending',
    'shift': '006e:2 MoveTo B/E wired; saved trace only has search25, no MoveTo execution; native target prerequisite unresolved',
    'e': 'No independent graph/node identified; changedNodesByPhase/E empty',
    'q': '00ca:36 search only; no resurrection commit; wait40 E is not a commit',
    'passive': '0071:2 glide and :4 self-heal wired to fresh native phases; :4 active in baseline is NOT replayed; damage/air calibration pending',
}


def prepare(process, pid):
    process.kernel.GetProcessId.argtypes = [ctypes.c_void_p]
    if process.kernel.GetProcessId(process.handle) != pid:
        raise ValueError('Binding PID differs from verified process handle')
    r = WeaponStates(process)
    sample = r.sample_weapon(False, True)
    b = r.bindings
    admin = r.pointer(process.base + 0x17b7f90)
    table = process.read(r.pointer(admin + 16), 65536)
    controller = r.entity(table, sample['localId'])
    model = r.entity(table, sample['modelId'])
    ref, info = r.component(controller, 0x20), r.component(controller, 0x3f)
    if r.unpack('<Q', info + 0x98)[0] != HERO:
        raise ValueError('Mercy bindings require current Mercy')
    base, image, pdb = provided_plugin(process)
    logger = base + image.symbol_rva(pdb.exact('statescript_logger::s_scriptStates'))
    times = [ctypes.create_string_buffer(8) for _ in range(4)]
    process.kernel.GetProcessTimes.argtypes = [ctypes.c_void_p, *([ctypes.c_void_p] * 4)]
    if not process.kernel.GetProcessTimes(process.handle, *times):
        raise ctypes.WinError(ctypes.get_last_error())
    creation = struct.unpack('<Q', times[0].raw)[0]
    prepared = []
    for purpose, resource, size, profile in GRAPHS:
        matches = [k for k in r.graph_cache if k[2] == resource]
        if len(matches) != 1:
            raise ValueError(f'Original {purpose} graph is not unique')
        script, graph, _ = matches[0]
        nodes = r.stu_list(graph + 0x50)
        if len(nodes) != size:
            raise ValueError(f'Original {purpose} graph size changed')
        states = {}
        for name, index, kind in profile:
            if b.metadata(nodes[index])[1] != kind:
                raise ValueError(f'Original {purpose}:{index} type hash changed')
            states[name] = dict(index=index, address=nodes[index], vtable=r.pointer(nodes[index]))
        if (r.pointer(process.base + 0x17b7f90) != admin
                or r.unpack('<I', ref + 0x94)[0] != sample['modelId']
                or r.unpack('<Q', info + 0x98)[0] != HERO
                or r.pointer(r.pointer(r.pointer(script + 0x10) + 0x450) + 8) != model):
            raise ValueError(f'{purpose} owner changed during binding')
        out = dict(version=1, pid=pid, creation=creation,
                   adminAddress=process.base + 0x17b7f90, admin=admin,
                   localId=sample['localId'], reference=ref, model=model,
                   modelId=sample['modelId'], heroInfo=info, hero=HERO, script=script,
                   graph=graph, bag=r.pointer(script + 0x98), resource=resource,
                   logger=logger, states=states)
        prepared.append((purpose, out))
    paths = []
    for purpose, out in prepared:
        path = ROOT / f'native-host/build/native-{purpose}-request-{pid}.json'
        temp = path.with_suffix('.tmp')
        temp.write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8')
        temp.replace(path)
        paths.append(str(path))
    return dict(hero=HERO, modelId=sample['modelId'], readOnly=True,
                paths=paths, unavailable=UNAVAILABLE)


if __name__ == '__main__':
    import argparse
    from observe_overwatch import ResearchProcess
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid', required=True, type=int)
    args = parser.parse_args()
    process = ResearchProcess(args.pid)
    try:
        print(json.dumps(prepare(process, args.pid), ensure_ascii=False))
    finally:
        process.close()
