"""Exact PID/creation shutdown-state diagnostic. No input, writes or callbacks."""
import argparse
import hashlib
import json
from pathlib import Path
import psutil
from native_normal_close import EXE, PATCHED_SHA256, ResearchProcess, inspect_shutdown_system, VERIFIER, VERIFIER_SHA256


def diagnose(pid, created, output):
    result = dict(pid=pid, creation=created, admin=None, cachedSingleton=None,
                  memoryReadSucceeded=False, readOnly=True,
                  verifierSha256=hashlib.sha256(VERIFIER.read_bytes()).hexdigest())
    process = None
    try:
        native = psutil.Process(pid)
        path = Path(native.exe()).resolve()
        if (native.create_time() != created or not native.is_running() or path != EXE.resolve()
                or hashlib.sha256(path.read_bytes()).hexdigest() != PATCHED_SHA256
                or result['verifierSha256'] != VERIFIER_SHA256):
            raise ValueError('Exact native identity/verifier differs; no memory read')
        result.update(identityVerified=True, executable=str(path))
        process = ResearchProcess(pid)
        if native.create_time() != created or not native.is_running():
            raise ValueError('Native process changed before diagnostic')
        result.update(inspect_shutdown_system(process, observed=result), memoryReadSucceeded=True)
        if native.create_time() != created or not native.is_running():
            raise ValueError('Native process changed during diagnostic')
    except Exception as error:
        result.update(error=repr(error), winerror=getattr(error, 'winerror', None))
    finally:
        if process is not None:
            process.close()
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid', type=int, required=True)
    parser.add_argument('--created', type=float, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = diagnose(args.pid, args.created, args.output)
    print(json.dumps({key: result.get(key) for key in ('pid', 'memoryReadSucceeded', 'admin', 'cachedSingleton', 'classification', 'error', 'winerror')}))
    raise SystemExit(0 if result['memoryReadSucceeded'] and not result.get('error') else 1)
