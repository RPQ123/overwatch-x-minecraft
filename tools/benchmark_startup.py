"""Finite normal-launch/normal-stop benchmark; no input, screenshots or force-kill."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
from pathlib import Path
import statistics
import subprocess
import time

from dev_cycle_support import ROOT, PYTHON, backup_profiles, project_processes
from minecraft_crash_evidence import snapshot, detect
from project_launcher import SessionBackend, read_object


@contextmanager
def benchmark_settings(output, strategy=None, shaders=None):
    """Explicit experiments restore settings/Iris only after a clean normal stop."""
    if strategy is None and shaders is None:
        yield
        return
    if project_processes() or SessionBackend().supervisors():
        raise RuntimeError('Stop the existing session normally before changing benchmark settings.')
    path=ROOT/'passthrough-settings.json'
    original=path.read_bytes();settings=json.loads(original)
    if shaders and shaders!='off':
        from minecraft_shaders import PROFILE, IRIS, PACK
        if not ((PROFILE/'mods'/IRIS[0]).is_file() or (PROFILE/'owmc-disabled-mods'/IRIS[0]).is_file()) or not (PROFILE/'shaderpacks'/PACK[0]).is_file():
            raise RuntimeError('Shader experiment requires the already-downloaded pinned Iris/pack; no download requested.')
    changed=dict(settings)
    if strategy is not None:changed['startupParallel']=strategy=='parallel'
    if shaders is not None:changed['shaders']=shaders
    encoded=(json.dumps(changed,indent=2)+'\n').encode('utf-8')
    output.parent.mkdir(parents=True,exist_ok=True)
    backup=output.with_name(output.name+'-settings-before.json')
    with backup.open('xb') as stream:stream.write(original)
    path.write_bytes(encoded)
    receipt=dict(originalSettings=str(backup),restored=False)
    try:
        yield
    finally:
        if project_processes() or SessionBackend().supervisors():
            receipt['reason']='Live session preserved; no settings/Iris restoration while it is running.'
        elif path.read_bytes()!=encoded:
            receipt['reason']='Concurrent settings edit preserved; original bytes remain in backup.'
        else:
            try:
                if shaders is not None:
                    from minecraft_shaders import prepare
                    prepare(settings.get('shaders','off'))
                path.write_bytes(original)
                receipt['restored']=True
            except Exception as error:
                receipt['error']=repr(error)
                path.write_bytes(original)
        output.with_name(output.name+'-settings-restoration.json').write_text(
            json.dumps(receipt,indent=2)+'\n',encoding='utf-8')


def action(name, path):
    with path.open('w', encoding='utf-8') as log:
        process = subprocess.Popen([str(PYTHON), 'tools/project_launcher.py', '--action', name,
                                    '--log', str(path.with_suffix('.session.log'))],
                                   cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        # Popen.wait never terminates the child on timeout (subprocess.run does).
        return process.wait(600)


def benchmark(output, runs):
    backend = SessionBackend()
    if backend.supervisors() or project_processes():
        raise RuntimeError('Existing session preserved; stop it normally before benchmarking.')
    output.mkdir(parents=True, exist_ok=False)
    backup = backup_profiles(output)
    report = dict(schemaVersion=1, backup=backup, samples=[], forcedTermination=False)
    destination = output / 'results.json'
    def save():
        destination.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    save()
    for index in range(1, runs+1):
        if backend.supervisors() or project_processes():
            raise RuntimeError('Previous session did not close; no second launch.')
        crash_baseline = snapshot(ROOT)
        previous_timelines = set((ROOT/'research/launcher').glob('startup-timeline-*.json'))
        before = time.perf_counter_ns()
        row = dict(run=index)
        report['samples'].append(row)
        try:
            row['startExitCode'] = action('toggle', output / f'run-{index}-start.log')
            row['actionElapsedMs'] = round((time.perf_counter_ns()-before)/1e6, 3)
            status = read_object(backend.status_path)
            row.update(phase=status.get('phase'), startup=status.get('startup'),
                       nativePid=status.get('nativePid'))
            row['startupAttempts'] = [read_object(path) for path in sorted(
                set((ROOT/'research/launcher').glob('startup-timeline-*.json'))-previous_timelines)]
            if row['startup']:
                timeline = read_object(Path(row['startup']['path']))
                row['timeline'] = timeline
            row['crashEvidence'] = detect(crash_baseline)
            if row['startExitCode'] or row['phase'] not in ('hero-selection', 'gameplay') or row['crashEvidence']:
                raise RuntimeError('Normal startup did not reach a healthy picker; see evidence.')
        except Exception as error:
            row['error'] = repr(error)
        finally:
            # The established strict stop restores native callbacks and saves MC.
            row['stopExitCode'] = action('stop', output / f'run-{index}-stop.log')
            row['remainingGames'] = project_processes()
            row['remainingSupervisors'] = [p.pid for p in backend.supervisors()]
            save()
        print(json.dumps({k: row.get(k) for k in ('run', 'actionElapsedMs', 'phase', 'error', 'stopExitCode',
                                                'remainingGames', 'remainingSupervisors')}, ensure_ascii=False), flush=True)
        if row.get('error') or row['stopExitCode'] or row['remainingGames'] or row['remainingSupervisors']:
            raise RuntimeError('Benchmark stopped on failure; no automatic extra game launches.')
    report['medianActionMs'] = statistics.median(row['actionElapsedMs'] for row in report['samples'])
    report['medianTimelineMs'] = statistics.median(row['timeline']['totalMs'] for row in report['samples'])
    save()
    print(json.dumps(dict(report=str(destination), medianActionMs=report['medianActionMs'],
                          medianTimelineMs=report['medianTimelineMs'])), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--runs', type=int, default=3, choices=range(1, 4))
    parser.add_argument('--strategy', choices=('serial','parallel'))
    parser.add_argument('--shaders', choices=('off','low','medium'))
    args = parser.parse_args()
    with benchmark_settings(args.output,args.strategy,args.shaders):
        benchmark(args.output, args.runs)
