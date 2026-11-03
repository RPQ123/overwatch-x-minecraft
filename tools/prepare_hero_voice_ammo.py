"""只读固定当前原版弹药/满弹赋值节点，供语音读数使用；无新hook/原生调用/按键。

须由Claude在真实换人/模型稳定后调用prepare(process,pid)。本轮只写代码，不运行此准备器。
"""
import argparse
import ctypes
import json
import struct
from pathlib import Path
from observe_overwatch import ROOT, ResearchProcess
from observe_native_weapon_states import WeaponStates
from native_armory_binding import primitive
from inspect_native_control_skills import ref as config_ref

ASSIGN = 0x4698e4b6

def prepare(process, pid):
    r = WeaponStates(process)
    sample = r.sample_weapon(False, True)
    admin = r.pointer(process.base + 0x17b7f90)
    controller = r.entity(process.read(r.pointer(admin + 16), 65536), sample['localId'])
    reference, info = r.component(controller, 0x20), r.component(controller, 0x3f)
    model = r.entity(process.read(r.pointer(admin + 16), 65536), sample['modelId'])
    hero = r.unpack('<Q', info + 0x98)[0]
    slots, omitted = [], []
    for (script, graph, resource), definition in r.graph_cache.items():
        outputs = {tuple(value.get('resourcePath', [])) for value in definition['ammoOutputs'].values()
                   if value.get('bindingIdentified') and len(value.get('resourcePath', [])) == 1}
        if not outputs:
            continue
        bag, nodes = r.pointer(script + 0x98), r.stu_list(graph + 0x50)
        groups = {}
        for index, node in enumerate(nodes):
            if r.bindings.metadata(node)[1] != ASSIGN:
                continue
            try:
                target = tuple(r.bindings.dynamic_path(config_ref(r.bindings, node, 0xec9f34a6, ASSIGN, 0xf8cc195d)))
                maximum_config = config_ref(r.bindings, node, 0x5180e750, ASSIGN, 0xbfd9aadd)
                if target not in outputs:
                    continue
                ammo, value, bucket = primitive(r, bag, int(target[0], 16))
                maximum_kind=r.bindings.metadata(maximum_config)[1]
                if maximum_kind==0xf8cc195d:
                    maximum=tuple(r.bindings.dynamic_path(maximum_config))
                    if len(maximum)!=1:continue
                    full,cap,full_bucket=primitive(r,bag,int(maximum[0],16))
                    cap_binding=dict(capacityKind='bag',capacity=full,capacityVtable=r.pointer(full),
                                     capacityBucket=full_bucket,maximumResource=int(maximum[0],16))
                elif maximum_kind==0x3ae7427e:
                    # 原版声明的s32字面量，既不执行getter，也不用经验弹匣大小代替。
                    owner,value_address,category,declared=r.bindings.field(maximum_config,0x5180e750)
                    if (owner,category,declared)!=(0x3ae7427e,0,0x954a3bab):continue
                    cap=r.bindings.literal_int(maximum_config);maximum=('literal-int',maximum_config)
                    cap_binding=dict(capacityKind='literal-int',capacity=maximum_config,capacityVtable=r.pointer(maximum_config),capacityValueAddress=value_address)
                else:continue
                if not (float(cap).is_integer() and 2 <= cap <= 1000 and float(value).is_integer() and 0 <= value <= cap):
                    continue
                key = target, int(cap)
                entry = groups.setdefault(key, dict(script=script, graph=graph, resource=resource, bag=bag,
                    ammo=ammo, ammoVtable=r.pointer(ammo), currentResource=int(target[0],16),
                    bucket=bucket, maximum=int(cap), nodes=[], **cap_binding))
                maximum_ref=r.bindings.field(node,0x5180e750)[1]
                entry['nodes'].append(dict(index=index, address=node, vtable=r.pointer(node),
                                          maximumRefAddress=maximum_ref, maximumConfig=maximum_config,
                                          maximumConfigVtable=r.pointer(maximum_config), maximumBinding=dict(cap_binding,bag=bag)))
            except (ValueError, OSError, StopIteration) as error:
                omitted.append(dict(resource=f'{resource:016x}', node=index, reason=str(error)))
        # 同一弹药变量的多个满值赋值节点全部保留：读数还须同时出现低->满与新赋值tick。
        # Tracer已认证reload30；equip14不作为装弹提交，Recall直接回填也不应触发它。
        for entry in groups.values():
            if len({item['maximum'] for item in groups.values() if item['currentResource']==entry['currentResource']})>1:
                omitted.append(dict(resource=f'{resource:016x}',reason='ambiguous magazine maxima; needs form-specific calibration'))
                continue
            if hero == 0x02e0000000000003 and resource == 0x0580000000000016:
                entry['nodes'] = [node for node in entry['nodes'] if node['index'] == 30]
                if entry['nodes']:
                    maximum_binding=entry['nodes'][0]['maximumBinding']
                    if entry['currentResource']!=0x0d80000000000035 or maximum_binding.get('maximumResource')!=0x0d800000000000c6 or entry['maximum']!=40:
                        entry['nodes']=[]
                    else:entry.update(maximum_binding)
                entry['evidence'] = 'tracer-original-reload30; current35/maxc6 verified in existing Recall research'
            else:
                entry['evidence'] = 'native Volley m_out_Ammo + typed maximum assignment; per-hero live calibration pending'
            if entry['nodes']:
                slots.append(entry)
    if hero==0x02e0000000000005:
        slots=[];omitted.append(dict(reason='Hanzo bow loading is not a reloadable magazine'))
    if len(slots) > 8:
        raise ValueError('弹药槽过多；需人工确定当前武器，未写绑定')
    times = [ctypes.create_string_buffer(8) for _ in range(4)]
    process.kernel.GetProcessTimes.argtypes = [ctypes.c_void_p, *([ctypes.c_void_p] * 4)]
    if not process.kernel.GetProcessTimes(process.handle, *times):
        raise ctypes.WinError(ctypes.get_last_error())
    if r.unpack('<I', reference + 0x94)[0] != sample['modelId'] or r.unpack('<Q',info+0x98)[0]!=hero:
        raise ValueError('准备期间原版英雄/模型改变')
    for entry in slots:
        if r.pointer(r.pointer(r.pointer(entry['script']+0x10)+0x450)+8)!=model:
            raise ValueError('准备期间原版武器归属改变')
    out = dict(version=1, pid=pid, creation=struct.unpack('<Q', times[0].raw)[0],
               adminAddress=process.base+0x17b7f90, admin=admin, localId=sample['localId'], modelId=sample['modelId'],
               reference=reference, model=model, heroInfo=info, hero=hero, logger=r.logger,
               readOnly=True, nativeCalls=False, newHooks=False, slots=slots, omitted=omitted[:12])
    path = ROOT / f'native-host/build/native-voice-ammo-request-{pid}.json'
    temp = path.with_suffix('.json.tmp')
    temp.write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)
    return dict(hero=hero, modelId=sample['modelId'], slots=len(slots), path=str(path), readOnly=True)

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid', type=int, required=True)
    parser.add_argument('--created', type=float, required=True)
    args=parser.parse_args()
    import psutil
    from verify_recall_empty_history import EXE, PATCHED_SHA256, digest
    process_identity=psutil.Process(args.pid)
    if process_identity.create_time()!=args.created or Path(process_identity.exe()).resolve()!=EXE.resolve() or digest(EXE)!=PATCHED_SHA256:
        raise ValueError('只允许精确路径/SHA256/创建时间匹配的离线研究进程')
    process=ResearchProcess(args.pid)
    try:print(json.dumps(prepare(process,args.pid)))
    finally:process.close()
