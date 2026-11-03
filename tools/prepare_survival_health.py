"""Publish a typed, exact-process original HealthPool binding; no native calls."""
import ctypes
import json
import struct
from observe_overwatch import ROOT
from native_health_binding import inspect_health, health_plan


def prepare(process, pid):
    r, binding, verify = inspect_health(process)
    admin = r.pointer(process.base + 0x17b7f90)
    table = process.read(r.pointer(admin + 0x10), 65536)
    local = r.unpack('<I', admin + 0x220)[0]
    controller = r.entity(table, local)
    reference = r.component(controller, 0x20)
    model = r.entity(table, binding['modelId'])
    info = r.component(controller, 0x3f)
    # The existing initializer's strict three-base-slot policy also rejects
    # additional native temporary pools; never erase their metadata.
    health_plan([process.read(binding['health'] + p['offset'], 320) for p in binding['pools']],
                [p['amount'] for p in binding['pools']])
    times = [ctypes.create_string_buffer(8) for _ in range(4)]
    process.kernel.GetProcessTimes.argtypes = [ctypes.c_void_p, *([ctypes.c_void_p] * 4)]
    if not process.kernel.GetProcessTimes(process.handle, *times):
        raise ctypes.WinError(ctypes.get_last_error())
    record = dict(version=1, pid=pid, creation=struct.unpack('<Q', times[0].raw)[0],
                  adminAddress=process.base + 0x17b7f90, admin=admin, localId=local,
                  reference=reference, model=model, heroInfo=info,
                  modelId=binding['modelId'], hero=binding['hero'], health=binding['health'],
                  healthVtable=process.base + 0x15c5aa0, numericVtable=process.base + 0x1608248,
                  pools=[dict(offset=p['offset'], amount=p['amount'], variable=p['variable'],
                              amountRaw=p['amountRaw'].hex()) for p in binding['pools']],
                  executableSha256='f73a747b7d63a07402958b2b2c4587125a46ef8e181281669da009d352308e9f',
                  nativeCalls=False)
    verify()
    path = ROOT / f'native-host/build/native-health-request-{pid}.json'
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)
    return record
