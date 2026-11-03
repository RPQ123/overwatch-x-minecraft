"""离线分析 capture_blocked_skills 的原版记录；候选永远不自动授权效果。"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path


def definition_index(capture):
    out = {}
    for definition in capture.get('definitions', {}).values():
        for node in definition.get('nodes', []):
            key = (definition['identity']['hero'], definition['identity']['modelId'],
                   definition['role'], definition['instance'], definition['script'], definition['graph'],
                   definition['nodePointers'][node['index']], node['index'])
            out[key] = node
    return out


def node_definition(index, sample, event):
    g = sample['graphs'][event['graphKey']]
    identity = sample['identity']
    key = (identity['hero'], identity['modelId'], g['role'], event['instance'],
           event['script'], g['graph'], g['nodePointers'][event['node']], event['node'])
    return index.get(key, {})


def events_from_samples(capture):
    """Recompute edges from raw snapshots; do not trust supplied candidate lists."""
    from capture_native_graphs import Edges
    edges = Edges()
    for row in capture.get('samples', []):
        if 'readError' in row:
            edges.gap()
            continue
        raw = {key: row[key] for key in ('identity', 'graphs', 'records', 'variables')}
        derived = edges.add(raw, row['phase'], row['elapsed'])
        yield row, derived


def analyze(captures):
    """Rank post-only nodes, then specificity across other tested actions.

    Comparison includes native hero and role/resource/type/node, not recycled
    instance addresses. Per-attempt stream checks still include model and graph
    pointers. A SetVar event plus a changed bag is an association, not a proven
    writer. Missing targets/dynamic paths remain unknown.
    """
    stats = {}
    action_sets = defaultdict(set)
    sources, variable_changes, health, rejected = [], [], [], []
    for capture in captures:
        c = capture['case']
        source = capture.get('_source', c['id'])
        require_kind = capture.get('kind') == 'native-blocked-skill-capture'
        if not require_kind:
            raise ValueError('Unsupported capture schema: '+source)
        if not capture.get('qualityPassed'):
            rejected.append(dict(source=source, reason='incomplete/input/read/cadence failure; diagnostic rows retained'))
        sources.append(dict(source=source, case=c['id'], qualityPassed=capture.get('qualityPassed'),
                            nativeSceneAcknowledged=capture.get('nativeSceneAcknowledged'),
                            cadence=capture.get('cadence'), errors=capture.get('errors', [])))
        definitions = definition_index(capture)
        sample_health = defaultdict(list)
        for raw, derived in events_from_samples(capture):
            identity = raw['identity']
            native_hero = identity['hero']
            action_sets[native_hero].add(c['id'])
            for event in derived['events']:
                role = raw['graphs'][event['graphKey']]['role']
                definition = node_definition(definitions, raw, event)
                kind = definition.get('hash', 'unknown')
                key = (native_hero, role, event['script'], event['node'], kind)
                if key not in stats:
                    stats[key] = dict(nativeHero=native_hero, ownerRole=role, script=event['script'],
                                      node=event['node'], typeHash=kind, typeName=definition.get('name'),
                                      serverOnly=definition.get('serverOnly'),
                                      baselineEvents=0, baselineAttempts=set(), actions={},
                                      setVarDefinition=definition.get('setVarDefinition'))
                item = stats[key]
                if raw['phase'] != 'action':
                    item['baselineEvents'] += 1
                    item['baselineAttempts'].add(source)
                    continue
                action = item['actions'].setdefault(c['id'], dict(events=0, begins=0, ends=0,
                                                  samples=[], sources=set(), goodSources=set()))
                action['events'] += 1
                action['begins' if event['event'] == 'Begin' else 'ends'] += 1
                action['sources'].add(source)
                if capture.get('qualityPassed') and capture.get('nativeSceneAcknowledged'):
                    action['goodSources'].add(source)
                action['samples'].append(dict(elapsed=raw['elapsed'], event=event['event'], tick=event['tick'],
                                              modelId=identity['modelId'], controller=identity['controller'],
                                              segment=derived['segment'], firstObserved=event['firstObserved']))
            for change in derived['variableChanges']:
                set_vars = [dict(script=e['script'], node=e['node'], event=e['event'])
                            for e in derived['events']
                            if node_definition(definitions, raw, e).get('hash') == '4698e4b6']
                variable_changes.append(dict(source=source, case=c['id'], phase=raw['phase'],
                                             elapsed=raw['elapsed'], nativeHero=native_hero,
                                             modelId=identity['modelId'], **change,
                                             sameSampleSetVarEvents=set_vars))
            if raw.get('healthPools', {}).get('ownerVerified'):
                sample_health[(native_hero, identity['modelId'])].append(
                    dict(phase=raw['phase'], elapsed=raw['elapsed'], pools=raw['healthPools']['pools']))
        for (hero, model), values in sample_health.items():
            health.append(dict(source=source, nativeHero=hero, modelId=model,
                               before=values[0], after=values[-1],
                               minTotal=min(sum(p['current'] for p in v['pools']) for v in values),
                               maxTotal=max(sum(p['current'] for p in v['pools']) for v in values)))
    candidates = []
    for item in stats.values():
        actions = item['actions']
        for action_id, action in actions.items():
            other_events = sorted(set(actions)-{action_id})
            compared = sorted(action_sets[item['nativeHero']]-{action_id})
            post_only = item['baselineEvents'] == 0
            unique = post_only and not other_events if compared else None
            candidates.append({k: v for k, v in item.items() if k not in ('actions', 'baselineAttempts')}
                              | dict(action=action_id, events=action['events'], begins=action['begins'], ends=action['ends'],
                                     postOnly=post_only, uniqueToTestedAction=unique,
                                     otherActionsWithEvents=other_events, otherActionsTested=compared,
                                     evidenceSources=sorted(action['sources']),
                                     goodEvidenceSources=sorted(action['goodSources']),
                                     controlSourcesWithEvents=sorted(item['baselineAttempts']),
                                     firstLatencySeconds=min(s['elapsed'] for s in action['samples']),
                                     samples=action['samples'], commitVerified=False,
                                     eligibleForReview=bool(action['goodSources']) and post_only))
    candidates.sort(key=lambda c: (not c['postOnly'], c['uniqueToTestedAction'] is not True,
                                   not c['eligibleForReview'], len(c['otherActionsWithEvents']),
                                   -len(c['goodEvidenceSources']), c['firstLatencySeconds'], c['script'], c['node']))
    return dict(kind='native-capture-candidate-report', skillCommitVerified=False,
                fixtureOnly=all(c.get('fixtureOnly', False) for c in captures),
                lossless=False, userPlayAccepted=False, sources=sources,
                rejectedForReview=rejected, candidates=candidates,
                variableChanges=variable_changes, healthPoolChanges=health,
                limitations=[
                    '只在动作后出现是相关性，搜索、动画、等待、声明、身份变化均不是成功提交。',
                    '没有其他动作对照时，uniqueToTestedAction为null；负结果不证明Beta不支持。',
                    '原版logger只存各节点最后一次状态，3秒窗口不能保证捕获同帧Begin/End或完整Q生命周期。',
                    '变量变化与同样本SetVar是候选关联，未观测到真实CPU写入方；动态跨实体路径可能不可见。',
                    '只读当前controller/model；原版目标上运行的图不在此作用域，不能将缺图解释为技能不存在。',
                    'factory诊断未主动开启；没有新鲜工厂记录不能证明没有子弹或子工厂。'])


def markdown(report):
    lines = ['# 原版技能候选提交信号（未认证）', '',
             f"采证 {len(report['sources'])} 份；候选 {len(report['candidates'])}；质量不合格 {len(report['rejectedForReview'])} 份。", '',
             '| 动作 | 原版hero | graph:节点 | 类型 | 仅动作后 | 其他动作出现 | B/E | 可复核 |',
             '|---|---|---|---|---|---|---|---|']
    for c in report['candidates']:
        lines.append(f"| {c['action']} | {c['nativeHero']:016x} | {c['script']}:{c['node']} | {c['typeHash']} | "
                     f"{c['postOnly']} | {','.join(c['otherActionsWithEvents']) or '未见'} | {c['begins']}/{c['ends']} | {c['eligibleForReview']} |")
    lines.extend(['', f"变量前后值变化 {len(report['variableChanges'])} 条；完整路径、raw/type、同样本SetVar字段与HP/盾池趋势见JSON。", ''])
    lines.extend('- '+s for s in report['limitations'])
    return '\n'.join(lines)+'\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inputs', nargs='+', type=Path, help='采证JSON或capture-日期目录（忽略prepare/其他报告）')
    parser.add_argument('--output', required=True, type=Path, help='新建JSON报告，旁边同时写.md')
    args = parser.parse_args()
    paths = set()
    for path in args.inputs:
        if not path.exists():
            parser.error('Input does not exist: '+str(path))
        paths.update(path.glob('*.json') if path.is_dir() else [path])
    captures = []
    for path in sorted(paths):
        data = json.loads(path.read_text(encoding='utf-8-sig'))
        if data.get('kind') != 'native-blocked-skill-capture':
            continue
        data['_source'] = str(path.resolve())
        captures.append(data)
    if not captures:
        parser.error('No native-blocked-skill-capture inputs')
    output = args.output.resolve()
    root = Path(__file__).resolve().parents[1]/'research'
    if not output.is_relative_to(root) or output.suffix != '.json':
        parser.error('Output must be a new private research/*.json')
    text_output = output.with_suffix('.md')
    if output.exists() or text_output.exists():
        parser.error('Preserve previous reports; choose another output filename')
    report = analyze(captures)
    report['sourceSha256'] = {str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in sorted(paths) if str(p.resolve()) in {c['_source'] for c in captures}}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    with text_output.open('x', encoding='utf-8') as stream:
        stream.write(markdown(report))
    print(json.dumps(dict(captures=len(captures), candidates=len(report['candidates']),
                          rejected=len(report['rejectedForReview']), output=str(output)), ensure_ascii=False))


if __name__ == '__main__':
    main()
