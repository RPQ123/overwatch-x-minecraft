"""只读绑定 Lucio 原版节点；不启动游戏、不调用技能、不安装回调。

登记：LucioServer.INSTANCE, / LucioClient.INSTANCE,
0776:36 是多发窗口。客户端另外消费现有 emission16 的 factoryObservations，
使用现有 creation 保护采集开关并在退出时撤销自己创建的开关，不注册第二个callback owner。
0266只选SetVar9，真实写入0004/06c7；3d <- 1d8是0→.25→0过渡值，不能当歌曲枚举。
0004/06c7前后值/表达式语义尚无录证，治疗/加速保留UNKNOWN。
音爆29与滑墙0263:25只准入真实新B/E；保存的generic2均未执行，不能冒充已确认效果。
原版05ff/0600资源链无LOD0；没有可执行的lucio-sonic网格打包输入。
"""
import ctypes
import json
import struct
from observe_overwatch import ROOT
from observe_native_weapon_states import WeaponStates
from provided_plugin_symbols import provided_plugin

HERO = 0x02e0000000000079
GRAPHS = [
    ('lucioWeapon', 0x0580000000000776, 76,
     [('volley', 36, 0x860ee5fc), ('boop', 65, 0x7fb4bf64), ('boopCommit', 29, 0x619d9e95)]),
    ('lucioSong', 0x0580000000000266, 46, [('songCommit', 9, 0x4698e4b6)]),
    ('lucioAmp', 0x0580000000000277, 20,
     [('ampCast', 6, 0x7fb4bf64), ('ampWindow', 11, 0xffbfa88d)]),
    ('lucioBarrier', 0x058000000000073a, 41, [('barrier', 0, 0xd78490d1)]),
    ('lucioWall', 0x0580000000000263, 43, [('wallMove', 25, 0xf45a1956)]),
]


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
        raise ValueError('Lucio bindings require current original Lucio')
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
        tmp = path.with_suffix('.lucio.tmp')
        tmp.write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8')
        tmp.replace(path)
        paths.append(str(path))
    return dict(hero=HERO, modelId=sample['modelId'], readOnly=True, paths=paths)


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
