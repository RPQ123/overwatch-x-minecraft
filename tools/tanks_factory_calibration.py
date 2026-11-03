"""Tanks-only calibration scope with bounded Windows sharing-error retries.

Same read-only native identity/previous-control contract as
native_factory_calibration.enabled; never changes the shared helper or DLL.
Each restore retry checks ownership again. Permanent failures remain errors.
"""
from contextlib import contextmanager
import ctypes
import errno
from pathlib import Path
import struct
import time
import traceback
import uuid


def _sharing_error(error):
    code = getattr(error, 'winerror', None)
    return code in (32, 33) or (code is None and isinstance(error, PermissionError)
                                and error.errno == errno.EACCES)


def retry_io(operation, path, action, diagnostics, attempts=20, delay=.05):
    """Retry only transient sharing errors; preserve the actual failing stack."""
    retries = []
    for attempt in range(attempts):
        try:
            value = action()
        except OSError as error:
            if not _sharing_error(error):
                raise
            item = dict(operation=operation, path=str(path), attempt=attempt + 1,
                        error=repr(error), winerror=getattr(error, 'winerror', None),
                        filename=getattr(error, 'filename', None),
                        filename2=getattr(error, 'filename2', None),
                        traceback=traceback.format_exc(), recovered=False)
            diagnostics.setdefault('ioRetries', []).append(item)
            retries.append(item)
            if attempt + 1 == attempts:
                raise
            time.sleep(delay)
        else:
            for item in retries:
                item['recovered'] = True
            return value


def _optional_bytes(path):
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return None


@contextmanager
def control_file(path, payload, diagnostics):
    """File-only implementation, also exercised without opening any game."""
    path = Path(path)
    diagnostics.update(path=str(path), completed=False, phase='enter')
    before = retry_io('enter-read-previous', path, lambda: _optional_bytes(path), diagnostics)
    # A per-invocation temporary avoids the shared helper's fixed .tmp collision.
    tmp = path.with_name(path.name + '.tanks-' + uuid.uuid4().hex + '.tmp')
    body_failed = False
    try:
        tmp.write_bytes(payload)

        def enable():
            if _optional_bytes(path) != before:
                raise RuntimeError('Calibration control changed before publication')
            tmp.replace(path)

        retry_io('enter-replace-control', path, enable, diagnostics)
        diagnostics['phase'] = 'body'
        try:
            yield
        except BaseException:
            body_failed = True
            raise
        finally:
            diagnostics['phase'] = 'exit'

            def restore():
                current = _optional_bytes(path)
                if current != payload:
                    return 'already-absent' if current is None else 'foreign-control-preserved'
                if before is None:
                    path.unlink(missing_ok=True)
                    return 'removed-owned-control'
                tmp.write_bytes(before)
                tmp.replace(path)
                return 'restored-previous-control'

            try:
                operation = 'exit-remove-owned-control' if before is None else 'exit-restore-previous-control'
                diagnostics['outcome'] = retry_io(operation, path, restore, diagnostics)
                diagnostics['completed'] = True
                diagnostics['phase'] = 'done'
            except Exception as error:
                diagnostics.update(error=repr(error), traceback=traceback.format_exc())
                if not body_failed:
                    raise
                # Keep an original assertion/read failure as the primary error.
                # The restoration failure is still saved independently above.
    finally:
        tmp.unlink(missing_ok=True)


@contextmanager
def enabled(pid, diagnostics):
    from observe_overwatch import ROOT, ResearchProcess
    from stop_passthrough import read_report
    process = ResearchProcess(pid)
    try:
        times = [ctypes.create_string_buffer(8) for _ in range(4)]
        process.kernel.GetProcessTimes.argtypes = [ctypes.c_void_p, *([ctypes.c_void_p] * 4)]
        if not process.kernel.GetProcessTimes(process.handle, *times):
            raise ctypes.WinError(ctypes.get_last_error())
        creation = struct.unpack('<Q', times[0].raw)[0]
        report = read_report(ROOT / f'native-host/build/native-emissions-{pid}.json')
        if (report.get('pid') != pid or report.get('creation') != creation
                or not report.get('enabled') or report.get('failures')):
            raise ValueError('No current native owner for factory calibration')
    finally:
        process.close()
    path = ROOT / f'native-host/build/native-factory-calibration-{pid}.txt'
    with control_file(path, (str(creation) + '\n').encode(), diagnostics):
        time.sleep(.06)
        yield
