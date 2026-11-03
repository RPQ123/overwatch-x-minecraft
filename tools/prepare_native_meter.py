"""Bind current native charge primitives for actual MC damage feedback."""
import ctypes,json,struct
from observe_overwatch import ROOT
from native_charge import inspect
from observe_native_weapon_states import WeaponStates

def prepare(process,pid):
    record=inspect(process)
    r=WeaponStates(process)
    for name,rid in [('charge',0x0d80000000000156),('cost',0x0d80000000000152)]:
        matches=[bucket for bucket in range(16) if any(key==rid and value==record[name] for key,value in struct.iter_unpack('<QQ',r.vector(record['bag']+0xa0+bucket*0x30,16)))]
        if len(matches)!=1:raise ValueError('Meter primitive membership changed')
        record[name+'Bucket']=matches[0]
    times=[ctypes.create_string_buffer(8) for _ in range(4)];process.kernel.GetProcessTimes.argtypes=[ctypes.c_void_p,*([ctypes.c_void_p]*4)]
    if not process.kernel.GetProcessTimes(process.handle,*times):raise ctypes.WinError(ctypes.get_last_error())
    record.update(version=1,pid=pid,creation=struct.unpack('<Q',times[0].raw)[0],adminAddress=process.base+0x17b7f90)
    path=ROOT/f'native-host/build/native-meter-request-{pid}.json';tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(record,indent=2)+'\n');tmp.replace(path)
    return dict(pid=pid,hero=record['hero'],modelId=record['modelId'],cost=record['costValue'],path=str(path))
