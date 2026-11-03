"""只读绑定 Symmetra 原版节点；不启动游戏、不调用技能、不安装回调。

证据：docs/HERO-BRIEFS-NEW8-20261025.md §3。
登记：SymmetraServer.INSTANCE, / SymmetraClient.INSTANCE,
资源：0139:116 -> 040000000000022e；017e 的实体引用0250/0251均指向模型0d00000000000c02，
0169 的0232/0233/0241均指向0d00000000000c16。这是离线graph引用，不是实际创建证明。
Claude打包：.venv/Scripts/python.exe tools/prepare_hero_symmetra.py --pack-assets。
调用共享build_mesh_pack.build，但先固定根实体直接引用的模型，避免按文件名取到传送器链的无关模型。
成功分支声明：017e:2.finished ->47；0169:2.finished ->66；01c3:0.finished ->39.true ->3播放01c4。
旧trace未运行上述分支，新增绑定是待实机的声明路径，不是已认证创建/加盾。
022e/02ef原版链无LOD0，不能伪造网格；素材打包须由Claude在私有目录执行。
"""
import ctypes
import json
import struct
from observe_overwatch import ROOT
from observe_native_weapon_states import WeaponStates
from provided_plugin_symbols import provided_plugin

HERO = 0x02e0000000000016
GRAPHS = [
    ('symmetraWeapon', 0x0580000000000139, 150,
     [('beam', 77, 0x498b421a), ('charge', 18, 0xf7d6498c), ('orb', 116, 0x860ee5fc),
      ('nativeDamage16', 16, 0x619d9e95), ('nativeDamage89', 89, 0x619d9e95), ('nativeDamage107', 107, 0x619d9e95)]),
    ('symmetraTurret', 0x058000000000017e, 73,
     [('turretPreview', 32, 0x7fb4bf64), ('turretGhost', 35, 0x6e81f6d4), ('turretPlace', 2, 0x65f158da), ('turretCommit', 47, 0x4e83bc01)]),
    ('symmetraShield', 0x05800000000001c3, 46,
     [('shieldAttempt', 27, 0x498b421a), ('shieldWindup', 16, 0x7fb4bf64), ('shieldCommit', 3, 0xf9ef59a6)]),
    ('symmetraPortal', 0x0580000000000169, 94,
     [('portalPreview', 42, 0x7fb4bf64), ('portalGhost', 74, 0x6e81f6d4), ('portalPlace', 2, 0x65f158da), ('portalCommit', 66, 0x8b6a3312)]),
]


def pack_assets():
    """仅Claude运行；共享build需按交接允许03效果根，原样保留原版资源身份。"""
    import build_mesh_pack
    jobs = json.loads((ROOT/'tools/symmetra-pack-jobs.json').read_text(encoding='utf-8'))
    # Explicit model/material selection keeps true chain.json provenance and
    # avoids the old staging directory that omitted the chain receipt.
    return [build_mesh_pack.build(**job) for job in jobs]


def prepare(process, pid):
    process.kernel.GetProcessId.argtypes = [ctypes.c_void_p]
    if process.kernel.GetProcessId(process.handle) != pid:
        raise ValueError('Binding PID does not match the verified process handle')
    r = WeaponStates(process)
    sample = r.sample_weapon(False, True)
    admin_address = process.base + 0x17b7f90
    admin = r.pointer(admin_address)
    table = process.read(r.pointer(admin + 16), 65536)
    controller = r.entity(table, sample['localId'])
    model = r.entity(table, sample['modelId'])
    reference = r.component(controller, 0x20)
    info = r.component(controller, 0x3f)
    if r.unpack('<Q', info + 0x98)[0] != HERO:
        raise ValueError('Symmetra bindings require current original Symmetra')
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
            if not 0 <= index < len(nodes) or r.bindings.metadata(nodes[index])[1] != kind:
                raise ValueError(f'Original {purpose}:{name} node type changed')
            states[name] = dict(index=index, address=nodes[index], vtable=r.pointer(nodes[index]))
        if (r.unpack('<I', reference + 0x94)[0] != sample['modelId']
                or r.pointer(r.pointer(r.pointer(script + 0x10) + 0x450) + 8) != model):
            raise ValueError(f'{purpose} owner changed during binding')
        out = dict(version=1, pid=pid, creation=creation, adminAddress=admin_address, admin=admin,
                   localId=sample['localId'], reference=reference, model=model, modelId=sample['modelId'],
                   heroInfo=info, hero=HERO, script=script, graph=graph, bag=r.pointer(script + 0x98),
                   resource=resource, logger=logger, states=states)
        pending.append((ROOT / f'native-host/build/native-{purpose}-request-{pid}.json', out))
    if r.pointer(admin_address) != admin or r.unpack('<Q', info + 0x98)[0] != HERO:
        raise ValueError('Original owner changed before publishing bindings')
    paths = []
    for path, out in pending:
        tmp = path.with_suffix('.symmetra.tmp')
        tmp.write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8')
        tmp.replace(path)
        paths.append(str(path))
    return dict(hero=HERO, modelId=sample['modelId'], readOnly=True, paths=paths)


if __name__ == '__main__':
    import argparse
    from observe_overwatch import ResearchProcess
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid', type=int)
    parser.add_argument('--pack-assets', action='store_true')
    args = parser.parse_args()
    if args.pack_assets:
        if args.pid is not None:
            parser.error('--pack-assets cannot attach to a process')
        print(json.dumps(pack_assets()))
    else:
        if args.pid is None:
            parser.error('--pid is required for read-only binding')
        process = ResearchProcess(args.pid)
        try:
            print(json.dumps(prepare(process, args.pid)))
        finally:
            process.close()
