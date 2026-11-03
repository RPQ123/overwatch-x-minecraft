"""Offline support-node audit. Reads saved calibration only; never attaches or sends input.

Uses the output of calibrate_hero_generic.py / inspect_native_volley.py and the
same metadata hashes as prepare_hero_*. A declaration is never labeled execution.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'research/sprint-20261024'
FOLDERS = {'Mercy': 'generic-Mercy', 'Zenyatta': 'generic2-Zenyatta', 'Lucio': 'generic2-Lucio'}


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def audit(hero):
    import importlib
    module = importlib.import_module('prepare_hero_' + hero.lower())
    folder = BASE / FOLDERS[hero]
    result = load(folder / 'result.json')
    definitions = load(folder / 'definitions.json')
    rows = []
    for purpose, graph, size, nodes in module.GRAPHS:
        guid = f'{graph:016x}'
        matches = [v for v in definitions.values() if v['script'] == guid]
        assert len(matches) == 1 and len(matches[0]['nodes']) == size, purpose
        definition = matches[0]
        for name, index, kind in nodes:
            node = definition['nodes'][index]
            assert node['hash'] == f'{kind:08x}', (purpose, name, node)
            changes = [(t['label'], c['nativeTick'], not c['finished'])
                       for t in result['trace'] for c in t['changes']
                       if c['script'] == guid and c['node'] == index]
            baseline = [c for c in result['baseline']['records'].values()
                        if c['script'] == guid and c['node'] == index]
            rows.append(dict(binding=purpose, name=name, node=f'{guid}:{index}',
                             type=node.get('resolvedTypeName') or node['hash'],
                             serverOnly=bool(node['serverOnly']), baselineActive=any(not c['finished'] for c in baseline),
                             newBegins=len({tick for _, tick, on in changes if on}),
                             newEnds=len({tick for _, tick, on in changes if not on}), phases=sorted({p for p, _, _ in changes})))
    out = dict(hero=hero, fixtureOnly=True, liveAcceptance=False, source=str(folder.relative_to(ROOT)),
               resultSha256=hashlib.sha256((folder / 'result.json').read_bytes()).hexdigest(), nodes=rows)
    if hero == 'Lucio':
        detail = load(folder / 'changed-definitions.json')
        def path(index, field):
            node = detail[f'0580000000000266:{index}']
            return next(f['object']['path'] for f in node['fields'] if f['hash'] == field)
        transitions = []
        for t in [result['baseline']] + result['trace']:
            variables = t.get('observedVariables', t.get('variables', {}))
            value = next((v.get('value') for v in variables.get('0580000000000266', [])
                          if v['rid'] == '0d8000000000003d'), None)
            if not transitions or value != transitions[-1]:
                transitions.append(value)
        nested = any(v['rid'] == '0d800000000006c7'
                     for t in [result['baseline']] + result['trace']
                     for values in t.get('observedVariables', t.get('variables', {})).values() for v in values)
        assert path(9, 'ec9f34a6') == ['0d80000000000004', '0d800000000006c7']
        assert path(3, 'ec9f34a6') == ['0d8000000000003d']
        assert path(3, '5180e750') == ['0d800000000001d8']
        assert transitions == [0, .25, 0] and not nested
        out['song'] = dict(commitNode=9, targetPath=path(9, 'ec9f34a6'), transitionNode=3,
                           transitionValues=transitions, nestedSongValueCaptured=nested,
                           mapping='UNRESOLVED: node9 expression bytecode/nested value not present in saved describe output; never assume 0/1 meaning')
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--hero', choices=[*FOLDERS, 'all'], default='all')
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    reports = [audit(h) for h in FOLDERS if args.hero in (h, 'all')]
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(reports, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps([dict(hero=r['hero'], bindings=len({n['binding'] for n in r['nodes']}),
                           executedNodes=sum(bool(n['newBegins'] or n['newEnds']) for n in r['nodes']),
                           noFreshPhase=[n['node'] for n in r['nodes'] if not n['newBegins'] and not n['newEnds']],
                           liveAcceptance=False) for r in reports], ensure_ascii=False))


if __name__ == '__main__':
    main()
