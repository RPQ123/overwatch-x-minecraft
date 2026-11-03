"""Scoped private diagnostics; original event transport stays enabled without it."""
import ctypes,struct,time
from contextlib import contextmanager
from observe_overwatch import ROOT,ResearchProcess
from stop_passthrough import read_report

@contextmanager
def enabled(pid):
    p=ResearchProcess(pid)
    try:
        times=[ctypes.create_string_buffer(8) for _ in range(4)];p.kernel.GetProcessTimes.argtypes=[ctypes.c_void_p,*([ctypes.c_void_p]*4)]
        if not p.kernel.GetProcessTimes(p.handle,*times):raise ctypes.WinError(ctypes.get_last_error())
        creation=struct.unpack('<Q',times[0].raw)[0]
        report=read_report(ROOT/f'native-host/build/native-emissions-{pid}.json')
        if report.get('pid')!=pid or report.get('creation')!=creation or not report.get('enabled') or report.get('failures'):raise ValueError('No current native owner for factory calibration')
    finally:p.close()
    path=ROOT/f'native-host/build/native-factory-calibration-{pid}.txt';before=path.read_bytes() if path.exists() else None;payload=(str(creation)+'\n').encode()
    tmp=path.with_suffix('.tmp');tmp.write_bytes(payload);tmp.replace(path);time.sleep(.06)
    try:yield
    finally:
        if path.exists() and path.read_bytes()==payload:
            if before is None:path.unlink()
            else:tmp.write_bytes(before);tmp.replace(path)
