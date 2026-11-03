"""One read-only native snapshot for tanks, for Claude's later calibration.

Never launches a game, sends input, writes a variable/request/ACK or adds hooks.
Use before and after a real skill with --previous; this is a bounded ONE-SHOT,
not a watcher. DVa permits a changed hero so form identity is observed before
assuming a pilot binding. Logger/variable changes are diagnostic, not commits.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import time

from inspect_tanks_evidence import ROOT, HEROES, profile, load


def capture(pid, created, hero):
    # Import native helpers only for an explicitly requested snapshot.
    import psutil
    from observe_overwatch import ResearchProcess
    from observe_native_weapon_states import WeaponStates
    from inspect_native_impact import describe
    from inspect_native_volley import inspect as volley

    if abs(psutil.Process(pid).create_time() - created) > .001:
        raise ValueError('Native process creation identity mismatch')
    process = ResearchProcess(pid)  # exact allowed path/SHA256 + VM_READ only
    try:
        import ctypes
        import struct
        times = [ctypes.create_string_buffer(8) for _ in range(4)]
        process.kernel.GetProcessTimes.argtypes = [ctypes.c_void_p, *([ctypes.c_void_p] * 4)]
        if not process.kernel.GetProcessTimes(process.handle, *times):
            raise ctypes.WinError(ctypes.get_last_error())
        creation = struct.unpack('<Q', times[0].raw)[0]
        r = WeaponStates(process)

        def identity():
            admin = r.pointer(process.base + 0x17b7f90)
            local = r.unpack('<I', admin + 0x220)[0]
            table = process.read(r.pointer(admin + 16), 65536)
            controller = r.entity(table, local)
            ref, info = r.component(controller, 0x20), r.component(controller, 0x3f)
            model = r.unpack('<I', ref + 0x94)[0]
            return dict(pid=pid, created=created, creationFileTime=creation, admin=admin, localId=local,
                        controller=controller, modelId=model,
                        hero=r.unpack('<Q', info + 0x98)[0])

        before = identity()
        sample = r.sample_weapon(False, True)
        expected, graphs = profile(hero)
        wanted = {guid: (count, nodes) for _, guid, count, nodes in graphs}
        result = dict(kind='read-only-native-snapshot', wallMs=int(time.time() * 1000),
                      requestedHero=hero, identity=before, matchesPilotOrKnownHero=before['hero'] == expected,
                      skillCommitVerified=False, mcEffectsVerified=False,
                      records=sample['records'], variables=sample['observedVariables'],
                      graphs=[], candidates={}, volleys={})
        for (instance, graph, guid), definition in r.graph_cache.items():
            nodes = r.stu_list(graph + 0x50)
            result['graphs'].append(dict(resource=f'{guid:016x}', instance=instance,
                                          nodeCount=len(nodes), nodes=r.graph_nodes(graph)))
            if guid in wanted:
                count, candidates = wanted[guid]
                if count != len(nodes):
                    raise ValueError(f'Known {guid:016x} node count changed')
                for name, index, kind in candidates:
                    if r.bindings.metadata(nodes[index])[1] != kind:
                        raise ValueError(f'Known {guid:016x}:{index} type changed')
                    result['candidates'][f'{guid:016x}:{index}'] = dict(
                        name=name, definition=describe(r.bindings, nodes[index]))
            # Include unknown mech graphs, without inventing their ability names.
            for index in definition['volleyNodes']:
                key = f'{guid:016x}:{index}'
                try:
                    result['volleys'][key] = volley(process, before['hero'], guid, index, len(nodes))
                except (OSError, ValueError) as error:
                    result['volleys'][key] = dict(error=repr(error))
        if (identity() != before or sample['modelId'] != before['modelId']
                or abs(psutil.Process(pid).create_time() - created) > .001):
            raise ValueError('Native hero/model/controller changed during snapshot; retry once settled')
        # Preserve existing factory diagnostics, including unknown resources and
        # owners, for parent/child inspection. Never enables calibration itself.
        factory_path = ROOT / f'native-host/build/native-emissions-{pid}.json'
        if factory_path.is_file() and factory_path.stat().st_size <= 524288:
            emission = load(factory_path)
            age = int(time.time() * 1000) - emission.get('heartbeat', 0)
            if (emission.get('pid') == pid and -50 <= age <= 150
                    and emission.get('creation') == creation
                    and emission.get('hero') == before['hero'] and emission.get('modelId') == before['modelId']):
                result['factoryDiagnostics'] = {key: emission.get(key) for key in
                    ('creation', 'epoch', 'factoryCalls', 'factoryCalibration', 'overflow', 'factoryObservations')}
                result['factoryDiagnostics']['commitVerified'] = False
        return result
    finally:
        process.close()


def compare(previous, current):
    same = previous.get('identity') == current['identity']
    result = dict(sameIdentity=same, identityChanged=not same,
                  before=previous.get('identity'), after=current['identity'],
                  # Cross-model ticks cannot be compared as a stream.
                  changes=[], requiresBaseline=not same, formCommitVerified=False)
    if same:
        old = previous.get('records', {})
        result['changes'] = [v for key, v in current['records'].items() if old.get(key) != v]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid', required=True, type=int)
    parser.add_argument('--created', required=True, type=float)
    parser.add_argument('--hero', required=True, choices=HEROES)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--previous', type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if ROOT / 'research' not in output.parents:
        parser.error('Snapshots must stay under private research/')
    result = capture(args.pid, args.created, args.hero)
    if args.previous:
        result['comparison'] = compare(load(args.previous), result)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps(dict(identity=result['identity'], graphs=len(result['graphs']),
                         candidates=len(result['candidates']), output=str(output))))


if __name__ == '__main__':
    main()
