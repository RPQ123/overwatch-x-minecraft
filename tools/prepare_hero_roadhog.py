"""Read-only offline24919 Roadhog phases; no launch, native call or new owner.

Q01c6:37 is one continuous Begin/End window. Individual weapon factories now
use the shared acknowledged emission17 journal through native_armory_binding.
Hook19 only authorizes the MC hook launch; actual MC collision owns target/damage
using the audited node21 amount30, never a claim that OW hit an MC entity.
Heal12 binds its original animation window; Heal23 binds the actual healing phase.
No calibration toggle, callback registration or diagnostic snapshot is required.
"""
import ctypes
import json
import struct
from observe_overwatch import ROOT
from observe_native_weapon_states import WeaponStates
from provided_plugin_symbols import provided_plugin

HERO = 0x02E0000000000040
GRAPHS = [
    ('roadhogWeapon', 0x05800000000001C6, 60, [
        ('primary', 30, 0x860EE5FC), ('secondary', 34, 0x860EE5FC), ('wholeHog', 37, 0x860EE5FC)]),
    ('roadhogHook', 0x05800000000001C8, 138, [
        ('cast', 11, 0x7FB4BF64), ('search', 19, 0x498B421A), ('damage', 21, 0x619D9E95)]),
    ('roadhogHeal', 0x0580000000000240, 31, [('heal', 23, 0x619D9E95), ('cast', 12, 0x7FB4BF64)]),
]


def prepare(process, pid):
    r = WeaponStates(process)
    s = r.sample_weapon(False, True)
    b = r.bindings
    admin = r.pointer(process.base + 0x17B7F90)
    table = process.read(r.pointer(admin + 16), 65536)
    controller = r.entity(table, s['localId'])
    model = r.entity(table, s['modelId'])
    ref, info = r.component(controller, 0x20), r.component(controller, 0x3F)
    if r.unpack('<Q', info + 0x98)[0] != HERO:
        raise ValueError('Roadhog bindings require current Roadhog')
    base, image, pdb = provided_plugin(process)
    logger = base + image.symbol_rva(pdb.exact('statescript_logger::s_scriptStates'))
    times = [ctypes.create_string_buffer(8) for _ in range(4)]
    process.kernel.GetProcessTimes.argtypes = [ctypes.c_void_p, *([ctypes.c_void_p] * 4)]
    if not process.kernel.GetProcessTimes(process.handle, *times):
        raise ctypes.WinError(ctypes.get_last_error())
    creation = struct.unpack('<Q', times[0].raw)[0]
    pending = []
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
                raise ValueError(f'Original {purpose}:{index} phase type hash changed')
            states[name] = dict(index=index, address=nodes[index], vtable=r.pointer(nodes[index]))
        if (r.unpack('<I', ref + 0x94)[0] != s['modelId']
                or r.pointer(r.pointer(r.pointer(script + 0x10) + 0x450) + 8) != model
                or r.unpack('<Q', info + 0x98)[0] != HERO):
            raise ValueError(f'{purpose} owner changed during binding')
        out = dict(version=1, pid=pid, creation=creation, adminAddress=process.base + 0x17B7F90,
                   admin=admin, localId=s['localId'], reference=ref, model=model, modelId=s['modelId'],
                   heroInfo=info, hero=HERO, script=script, graph=graph, bag=r.pointer(script + 0x98),
                   resource=resource, logger=logger, states=states)
        pending.append((ROOT / f'native-host/build/native-{purpose}-request-{pid}.json', out))
    if r.unpack('<I', ref + 0x94)[0] != s['modelId'] or r.unpack('<Q', info + 0x98)[0] != HERO:
        raise ValueError('Roadhog changed before publishing bindings')
    for path, out in pending:
        tmp = path.with_suffix('.tmp')
        tmp.write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8')
        tmp.replace(path)
    return dict(hero=HERO, modelId=s['modelId'], readOnly=True, paths=[str(p) for p, _ in pending])


if __name__ == '__main__':
    import argparse
    from observe_overwatch import ResearchProcess
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid', required=True, type=int)
    args = parser.parse_args()
    process = ResearchProcess(args.pid)
    try:
        print(json.dumps(prepare(process, args.pid)))
    finally:
        process.close()
