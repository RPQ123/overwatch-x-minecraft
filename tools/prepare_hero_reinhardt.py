"""Read-only offline24919 Reinhardt bindings. Never activates skills or starts games.

HERO-BRIEFS-NEW8-20261025 §2: E/Q declaration candidates are diagnostic ONLY;
Shift110 is an attempt, movement6/slam11 have not been observed. No forged input.
Damage31/38/63/128 and shatter3/13 are read-only diagnostic candidates, not enabled effects.
Assets checked with ow_asset_chain: 04000000000001ea -> NO LOD0 mesh/texture.
Future pack (needs mesh recovery first, run by Claude outside this sandbox):
  .venv/Scripts/python.exe tools/build_mesh_pack.py reinhardt-fire 04000000000001ea
Shield entity GUID is unknown; do not substitute the fire projectile for it.
"""
import ctypes
import json
import struct

HERO = 0x02e0000000000007
GRAPHS = [
    ('reinhardtHammer', 0x0580000000000048, 57,
     [('left', 9, 0x619d9e95), ('right', 10, 0x619d9e95)]),
    ('reinhardtBarrier', 0x0580000000000095, 86, [('pet', 58, 0x4cced352)]),
    ('reinhardtCharge', 0x058000000000007d, 139,
     [('anim', 110, 0x7fb4bf64), ('movement', 6, 0x8de7e50f), ('slam', 11, 0x76391dd3),
      ('damage31', 31, 0x619d9e95), ('damage38', 38, 0x619d9e95),
      ('damage63', 63, 0x619d9e95), ('damage128', 128, 0x619d9e95)]),
    ('reinhardtFire', 0x05800000000000e2, 27, [('volley', 3, 0x860ee5fc)]),
    ('reinhardtShatter', 0x05800000000000be, 62,
     [('shockwave', 1, 0x8d50485a), ('damage', 3, 0x619d9e95), ('aura', 13, 0xd78490d1)]),
]
PENDING = {'charge': 'animation110 observed; movement6/slam11/damage uncalibrated',
           'fire': 'declaration only; no successful fresh cast evidence; disabled',
           'shatter': 'declaration only; no successful fresh cast evidence; disabled',
           'passive': 'no independent native event', 'barrierModel': 'entity GUID unknown'}


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
        raise ValueError('Reinhardt binding requires current Reinhardt')
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
    # Validate every graph before publishing any request. NativeSkillReader also
    # revalidates process creation/owner/model/graph for every actual snapshot.
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
