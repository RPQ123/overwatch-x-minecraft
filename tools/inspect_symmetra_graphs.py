"""Offline24919 Symmetra graph audit; no process, input, callback or deployment.

Uses the existing SHA-guarded ow_asset_chain reader and measured FlatGraph tool.
Private raw graphs and derived evidence stay in ignored research/asset-cache.
Reflection offsets come from saved beta observations, never modern OWLib layouts.
"""
import hashlib
import json
import re
import zlib
from pathlib import Path

from ow_asset_chain import Archive
from inspect_hanzo_dragon_assets import FlatGraph

ROOT = Path(__file__).resolve().parents[1]
GRAPHS = {'0139': 150, '017e': 73, '01c3': 46, '01c4': 14, '0169': 94, '0033': 27}


def schemas():
    result = {}

    def walk(value):
        if isinstance(value, dict):
            if isinstance(value.get('type'), str) and 'size' in value and isinstance(value.get('fields'), list):
                fields = {f['hash']: {k: f[k] for k in ('hash', 'offset', 'category', 'declared') if k in f}
                          for f in value['fields'] if 'hash' in f and 'offset' in f and 'category' in f}
                known = result.setdefault(value['type'], {})
                for key, field in fields.items():
                    if key in known and known[key] != field:
                        raise ValueError('Conflicting measured beta reflection: '+value['type']+':'+key)
                    known[key] = field
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    for p in [ROOT/'research/hanzo-skills-20261021/graphs.json',
              *sorted((ROOT/'research/sprint-20261024').glob('generic*-*/changed-definitions.json'))]:
        walk(json.loads(p.read_text(encoding='utf-8')))
    return result


def names():
    result = {}
    base = Path.home()/'.universal-modder/toolchains/OWLib-source/TankLib/STU/Types'
    for file in base.glob('*.cs'):
        for name in re.findall(r'\bm_\w+', file.read_text(encoding='utf-8-sig')):
            result[f'{zlib.crc32(name.lower().encode()):08x}'] = name
        name = file.stem
        result[f'{zlib.crc32(name.lower().encode()):08x}'] = name
    return result


def summarize(graph, at, schema, labels, depth=0, visited=()):
    kind = f'{graph.kind(at):08x}'
    out = {'type': kind, 'name': labels.get(kind), 'offset': at}
    if at in visited or depth > 5:
        return out
    try:
        out['literal'] = graph.literal(at)
        return out
    except ValueError:
        pass
    if kind == 'f8cc195d':
        out['path'] = graph.dynamic(at)
        return out
    if kind in ('04e83493', 'b709560a', '824213f0', 'd3d12aec') and graph.q(at+16) == 0xffffffffffffffff:
        out['resource'] = f'{graph.q(at+24):016x}'
        return out
    if kind in ('ec502a81', 'cc3a08f4'):
        out['expression'] = {
            'code': [graph.raw[p] for p in graph.array(at+32, 1)],
            'constants': [graph.unpack('<f', p) for p in graph.array(at+64, 4)],
            'variables': [summarize(graph, graph.q(p), schema, labels, depth+1, (*visited, at))
                          for p in graph.array(at+48, 8)]}
        return out
    fields = {}
    for f in schema.get(kind, {}).values():
        if at in graph.nodes and (f['offset'] < 120 or f['hash'] == 'a2eca5de'):
            # Exclude editor data, retaining the reflected state/action plugs.
            continue
        key = labels.get(f['hash'], f['hash'])
        pos = at + f['offset']
        if f['category'] == 2:
            ptr = graph.q(pos)
            if ptr in graph.objects:
                fields[key] = summarize(graph, ptr, schema, labels, depth+1, (*visited, at))
        elif f['category'] == 0 and f['offset'] != 8:
            fields[key] = {'offset': f['offset'], 'raw': graph.raw[pos:pos+8].hex()}
    # Flat node identity references: retain their actual offsets; do not label
    # unknown pointers as success/abort/creation without reflected field names.
    refs = []
    node_index = {offset: index for index, offset in enumerate(graph.nodes)}
    stop = min((p for p in graph.objects if p > at), default=len(graph.raw))
    for pos in range(at+8, min(stop, at+1024), 8):
        ptr = graph.q(pos)
        if ptr in node_index:
            refs.append({'fieldOffset': pos-at, 'node': node_index[ptr]})
    if refs:
        out['nodeReferences'] = refs
    if fields:
        out['fields'] = fields
    return out


def links(graph, schema, labels):
    indices = {at: i for i, at in enumerate(graph.nodes)}
    result = []
    for p in graph.array(16+56, 8):
        at = graph.q(p)
        graph.typed(at, 0x38a4b0b7)
        output, incoming = graph.q(at+8), graph.q(at+16)
        src, dst = graph.q(output+24), graph.q(incoming+24)
        if src not in indices or dst not in indices:
            raise ValueError('Graph link owner differs')
        def field(node, plug):
            return next((labels.get(f['hash'], f['hash']) for f in schema.get(f'{graph.kind(node):08x}', {}).values()
                         if f['category'] == 2 and graph.q(node+f['offset']) == plug), None)
        result.append({'source': indices[src], 'output': field(src, output),
                       'target': indices[dst], 'input': field(dst, incoming)})
    return result


def audit():
    archive = Archive('symmetra-20261026')
    archive.load_package('02e0000000000016')
    schema, labels = schemas(), names()
    report = {'offlineOnly': True, 'nativeExecutionObserved': False, 'graphs': {}}
    for suffix, count in GRAPHS.items():
        guid = '058000000000'+suffix
        row = archive.resolve(guid)
        if not row:
            raise ValueError('Graph absent: '+guid)
        raw = archive.fetch(row['ckey'], guid+'.raw')
        if len(raw) != row['bytes'] or hashlib.md5(raw).hexdigest() != row['ckey']:
            raise ValueError('Graph content-key mismatch')
        graph = FlatGraph(raw)
        if len(graph.nodes) != count:
            raise ValueError('Graph node count changed')
        report['graphs'][guid] = {'sha256': hashlib.sha256(raw).hexdigest(),
                                  'nodeCount': len(graph.nodes),
                                  'links': links(graph, schema, labels),
                                  'nodes': [summarize(graph, at, schema, labels) for at in graph.nodes]}
    out = archive.out/'evidence.json'
    out.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'graphs': {g: v['nodeCount'] for g, v in report['graphs'].items()},
                      'evidence': str(out)}))
    return report


if __name__ == '__main__':
    audit()
