"""Offline tanks evidence audit. No process open, input, build or deployment.

Checks prepare/Java binding agreement against the saved native graph metadata;
counts actual logger changes, not phase labels or successful fixture assertions.
A successful audit is NOT discovery/acceptance of any missing skill.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'research/sprint-20261024'
HEROES = {'Reinhardt': 'generic-Reinhardt', 'Zarya': 'generic2-Zarya',
          'DVa': 'generic2-DVa', 'Roadhog': 'generic2-Roadhog'}


def profile(hero):
    path = ROOT / f'tools/prepare_hero_{hero.lower()}.py'
    assignments = {}
    for node in ast.parse(path.read_text(encoding='utf-8')).body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in ('HERO', 'GRAPHS'):
                    assignments[target.id] = ast.literal_eval(node.value)
    return assignments['HERO'], assignments['GRAPHS']


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def nested_values(obj, key):
    if isinstance(obj, dict):
        for k, value in obj.items():
            if k == key:
                yield value
            else:
                yield from nested_values(value, key)
    elif isinstance(obj, list):
        for value in obj:
            yield from nested_values(value, key)


def audit():
    report = dict(kind='offline-saved-evidence-only', nativeProcessOpened=False,
                  runtimeAccepted=False, userPlayAccepted=False, errors=[], heroes={})
    for hero, directory in HEROES.items():
        root = BASE / directory
        r, definitions, changed = [load(root / name) for name in
                                   ('result.json', 'definitions.json', 'changed-definitions.json')]
        expected, graphs = profile(hero)
        client = (ROOT / f'guest/src/client/java/lab/owmcguest/{hero}Client.java').read_text(encoding='utf-8')
        specs = {name: (int(guid, 16), {k: int(i) for k, i in re.findall(r'"([^"]+)",(\d+)', body)})
                 for name, guid, body in re.findall(
                     r'NativeSkillReader.register\("([^"]+)".*?,0x([0-9a-f]+)L,Map.of\((.*?)\)\)\);', client, re.I)}
        h = dict(directory=str(root.relative_to(ROOT)), nativeHero=f'{expected:016x}',
                 actorModel=r['actor']['modelId'], observedModels=r['observedModelIds'],
                 nativeCalls=r.get('nativeCalls'), newCallbackOwners=r.get('newCallbackOwners'),
                 factoryCounts={k: len(v) for k, v in r['factoryObservationsByPhase'].items()},
                 sources={name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in
                          ('result.json', 'definitions.json', 'changed-definitions.json', 'volley-declarations.json')},
                 nodes={})
        for purpose, guid, count, nodes in graphs:
            g = f'{guid:016x}'
            matches = [v for v in definitions.values() if v['script'] == g]
            if len(matches) != 1 or len(matches[0]['nodes']) != count:
                report['errors'].append(f'{hero}:{purpose} saved graph/count mismatch')
                continue
            if specs.get(purpose) != (guid, {n: i for n, i, _ in nodes}):
                report['errors'].append(f'{hero}:{purpose} Java/prepare mismatch')
            for name, index, kind in nodes:
                meta = matches[0]['nodes'][index]
                if meta['index'] != index or meta['hash'] != f'{kind:08x}':
                    report['errors'].append(f'{hero}:{g}:{index} saved type mismatch')
                rows = [dict(phase=t['label'], tick=c['nativeTick'], finished=c['finished'])
                        for t in r['trace'] for c in t['changes']
                        if c['script'] == g and c['node'] == index]
                h['nodes'][purpose + '.' + name] = dict(graph=g, node=index, type=meta['hash'],
                    declaredName=meta.get('resolvedTypeName'), begins=sum(not x['finished'] for x in rows),
                    ends=sum(x['finished'] for x in rows), rows=rows)
        variables = {}
        for t in [{'label': 'actor', 'variables': r['actor'].get('nativeVariables', {})}, *r['trace']]:
            for g, values in t.get('variables', {}).items():
                if g not in ('0580000000000241', '058000000000026a'):
                    continue
                for value in values:
                    if 'value' in value:
                        key = g + ':' + value['rid']
                        variables.setdefault(key, set()).add(str(value['value']))
        h['numericVariableValues'] = {k: sorted(v) for k, v in variables.items()}
        if hero == 'DVa':
            h['callWrite109'] = dict(paths=list(nested_values(changed['058000000000026a:109'], 'path')),
                                     literals=list(nested_values(changed['058000000000026a:109'], 'literal')))
            h['modelsDuringQ'] = sorted({t['modelId'] for t in r['trace'] if t['label'] == 'Q'})
            h['heroPerTraceRecorded'] = False
            h['mechFormCommitFound'] = False
            h['blocker'] = 'Only one model observed; hero not sampled per trace. 109 writes 003bc=1.27, not a verified form. No mech graph/weapon binding.'
        elif hero == 'Zarya':
            h['blocker'] = 'E24 End-only search; Aura43/Pet32 absent. Variable changes alone do not identify energy or absorbed-damage formula.'
        elif hero == 'Reinhardt':
            h['blocker'] = 'Movement6/slam11/damage31,38,63,128 and e2:3/be:1,3,13 have no logger changes. Shift110 animation is not impact.'
        else:
            right = r['factoryObservationsByPhase']['M2-long']
            h['secondaryFactoryResources'] = sorted({str(v['resource']) for v in right})
            h['blocker'] = 'Hook ModifyHealth21 absent. Right-click has one parent resource; no authenticated child factory/split commit.'
        report['heroes'][hero] = h
    report['bindingsValid'] = not report['errors']
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=BASE / 'tanks-evidence-20261026.json')
    args = parser.parse_args()
    output = args.output.resolve()
    if ROOT / 'research' not in output.parents:
        parser.error('Evidence output must stay under research/')
    result = audit()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps(dict(bindingsValid=result['bindingsValid'], heroes=len(result['heroes']),
                         nodes=sum(len(h['nodes']) for h in result['heroes'].values()),
                         errors=result['errors'], runtimeAccepted=False, output=str(output))))
    return 0 if result['bindingsValid'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
