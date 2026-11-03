"""Read-only offline24919 Zarya bindings; no ability activation/game launch.

HERO-BRIEFS-NEW8-20261025 §6. Beam36 is an appearance channel; MC hit/damage
is explicit adaptation. E24 search is not a shield cast, Aura43 only declared.
Native energy/cleanse not known. Asset-chain03db/08ce: no LOD0/texture extracted.
Future pack commands (Claude, after mesh recovery; they currently lack inputs):
  .venv/Scripts/python.exe tools/build_mesh_pack.py zarya-grenade 04000000000003db
  .venv/Scripts/python.exe tools/build_mesh_pack.py zarya-graviton 04000000000008ce
Self/projected shield entity GUIDs remain unknown.
Projected Pet32 is collected alongside Aura43 for diagnosis, never target confirmation.
"""
import ctypes
import json
import struct

HERO = 0x02e0000000000068
GRAPHS = [
    ('zaryaPrimary', 0x0580000000000241, 87,
     [('beam', 36, 0xc0a88bb0), ('grenade', 42, 0x860ee5fc)]),
    ('zaryaSelf', 0x0580000000000244, 19, [('aura', 15, 0xd78490d1)]),
    ('zaryaProjected', 0x058000000000025c, 45,
     [('search', 24, 0x498b421a), ('aura', 43, 0xd78490d1), ('pet', 32, 0x4cced352)]),
    ('zaryaGraviton', 0x058000000000025f, 28, [('volley', 2, 0x860ee5fc)]),
]
PENDING = {'projected': 'search24 observed; successful Aura43/target mapping missing; disabled',
           'beam': 'appearance36 only, MC supplies hit/damage as explicit adaptation',
           'energy': 'native absorb->energy event/formula missing; not synchronized',
           'field': 'native field creation/despawn absent; MC contact field adaptation',
           'shieldModel': 'entity GUID unknown'}


def prepare(process, pid):
    from observe_overwatch import ROOT
    from observe_native_weapon_states import WeaponStates
    from provided_plugin_symbols import provided_plugin
    r = WeaponStates(process)
    sample = r.sample_weapon(False, True)
    admin = r.pointer(process.base + 0x17b7f90)
    table = process.read(r.pointer(admin + 16), 65536)
    controller = r.entity(table, sample['localId'])
    model = r.entity(table, sample['modelId'])
    ref, info = r.component(controller, 0x20), r.component(controller, 0x3f)
    if r.unpack('<Q', info + 0x98)[0] != HERO:
        raise ValueError('Zarya binding requires current Zarya')
    base, image, pdb = provided_plugin(process)
    logger = base + image.symbol_rva(pdb.exact('statescript_logger::s_scriptStates'))
    times = [ctypes.create_string_buffer(8) for _ in range(4)]
    process.kernel.GetProcessTimes.argtypes = [ctypes.c_void_p, *([ctypes.c_void_p] * 4)]
    if not process.kernel.GetProcessTimes(process.handle, *times):
        raise ctypes.WinError(ctypes.get_last_error())
    creation = struct.unpack('<Q', times[0].raw)[0]
    requests = []
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
            if not 0 <= index < len(nodes) or r.bindings.metadata(nodes[index])[1] != kind:
                raise ValueError(f'Original {purpose}:{index} type hash changed')
            states[name] = dict(index=index, address=nodes[index], vtable=r.pointer(nodes[index]))
        if (r.unpack('<I', ref + 0x94)[0] != sample['modelId']
                or r.unpack('<Q', info + 0x98)[0] != HERO
                or r.pointer(r.pointer(r.pointer(script + 0x10) + 0x450) + 8) != model):
            raise ValueError(f'{purpose} owner changed during binding')
        out = dict(version=1, pid=pid, creation=creation,
                   adminAddress=process.base + 0x17b7f90, admin=admin, localId=sample['localId'],
                   reference=ref, model=model, modelId=sample['modelId'], heroInfo=info, hero=HERO,
                   script=script, graph=graph, bag=r.pointer(script + 0x98),
                   resource=resource, logger=logger, states=states)
        requests.append((ROOT / f'native-host/build/native-{purpose}-request-{pid}.json', out))
    for path, out in requests:
        tmp = path.with_suffix('.tmp')
        tmp.write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8')
        tmp.replace(path)
    return dict(hero=HERO, modelId=sample['modelId'], readOnly=True,
                paths=[str(p) for p, _ in requests], pending=PENDING)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid', type=int)
    parser.add_argument('--describe', action='store_true')
    args = parser.parse_args()
    if args.describe:
        print(json.dumps(dict(hero=HERO, graphs=GRAPHS, pending=PENDING)))
    else:
        if args.pid is None:
            parser.error('--pid is required unless --describe')
        from observe_overwatch import ResearchProcess
        process = ResearchProcess(args.pid)
        try:
            print(json.dumps(prepare(process, args.pid)))
        finally:
            process.close()
