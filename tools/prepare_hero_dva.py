"""Read-only offline24919 D.Va PILOT bindings, never activates an ability.

02b8:12 is a multi-shot channel; individual bullets require original factories.
026a:41 hash160c4f1d is unresolved call-mech precursor, NOT a form commit.
Pilot Shift/E have no changed nodes. No mech weapon/boosters/matrix/self-destruct
or ejection binding can honestly be emitted from the current evidence.
Call25/109/50/77/96/107/17/39 are diagnostic candidates only;109 writes003bc=1.27.
"""
import ctypes
import json
import struct
from observe_overwatch import ROOT
from observe_native_weapon_states import WeaponStates
from provided_plugin_symbols import provided_plugin

HERO = 0x02E000000000007A
GRAPHS = [
    ('dvaPistol', 0x05800000000002B8, 52, [('firing', 12, 0x860EE5FC)]),
    ('dvaCallMech', 0x058000000000026A, 124, [
        ('attempt', 41, 0x160C4F1D), ('switch', 25, 0xE811ECBB), ('write', 109, 0x4698E4B6),
        ('enterAnim', 50, 0x7FB4BF64), ('exitAnim', 77, 0x7FB4BF64),
        ('move96', 96, 0xC1035274), ('move107', 107, 0xC1035274),
        ('health17', 17, 0x619D9E95), ('health39', 39, 0x619D9E95)]),
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
        raise ValueError('DVa bindings require current DVa')
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
        raise ValueError('DVa changed before publishing bindings')
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
