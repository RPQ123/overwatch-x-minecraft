"""Read-only Zenyatta24919 bindings; no activation/charge/calibration/callback install.

Weapon28 single shots; release32 B/E needs existing emission16 per-orb factory
observations (never assume three/five orbs). Harmony46/Discord41/Q19 only count
attempts. Health11/Aura6/health17/Aura30 are now bound separately to actual future
execution (no fresh phase in saved generic2 trace). No guessed protection/passive event.
"""
import ctypes
import json
import struct
from observe_overwatch import ROOT
from observe_native_weapon_states import WeaponStates
from provided_plugin_symbols import provided_plugin

HERO = 0x02e0000000000020
GRAPHS = [
    ('zenWeapon', 0x0580000000000164, 152,
     [('primary', 28, 0x860ee5fc), ('release', 32, 0x860ee5fc)]),
    ('zenHarmony', 0x05800000000002f3, 75,
     [('search', 46, 0x498b421a), ('heal', 11, 0x619d9e95)]),
    ('zenDiscord', 0x0580000000000176, 70,
     [('search', 41, 0x498b421a), ('aura', 6, 0xd78490d1)]),
    ('zenTranscendence', 0x058000000000017b, 49,
     [('windup', 19, 0xf7d6498c), ('heal', 17, 0x619d9e95), ('aura', 30, 0xd78490d1)]),
]
UNAVAILABLE = {
    'shift': '02f3:11 fresh health phase wired; saved generic2 trace has only search46; native target prerequisite unresolved',
    'e': '0176:6 fresh Aura phase wired to MC Weakness I (not universal damage amplification); no saved native commit',
    'q': '017b:17 healing phase wired; :30 is tracked separately and grants no guessed invulnerability; neither executed in saved trace',
    'passive': 'No dedicated graph/event; shared0033 HealthPool does not prove recovery',
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
        raise ValueError('Zenyatta bindings require current Zenyatta')
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
                paths=paths, unavailable=UNAVAILABLE,
                secondary='Requires already-owned emission16 scoped factoryCalibration; no new owner')


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
