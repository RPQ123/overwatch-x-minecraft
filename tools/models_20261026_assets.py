"""SHA-guarded, file-only model inventory. No process, game, build or deployment.

Graph references are declarations, never proof of an executed skill. Private
receipts stay in ignored research/asset-cache/models-20261026.
"""
import argparse
import bisect
import hashlib
import json
from pathlib import Path
import struct

from ow_asset_chain import Archive, CACHE, collect, scan_refs, parse_asset_model
from inspect_hanzo_dragon_assets import FlatGraph
from inspect_symmetra_graphs import names

HEROES = dict(Genji='0029', McCree='0042', Pharah='0008', Reaper='0002',
              Soldier='006e', Tracer='0003', Bastion='0015', Hanzo='0005',
              Junkrat='0065', Mei='00dd', Torbjorn='0006', Widowmaker='000a',
              DVa='007a', Reinhardt='0007', Roadhog='0040', Winston='0009',
              Zarya='0068', Lucio='0079', Mercy='0004', Symmetra='0016',
              Zenyatta='0020')


def index():
    archive = Archive('models-20261026')
    labels = names()
    result = dict(offlineOnly=True, inGameVerified=False, heroes={}, errors=[])
    for hero, suffix in HEROES.items():
        package = '02e000000000' + suffix
        archive.load_package(package)
        graphs = sorted(g for g in archive.records if g.startswith('0580') and
                        any(o.startswith(package) for o in archive.owners[g]))
        rows = []
        for guid in graphs:
            record = archive.records[guid]
            raw = archive.fetch(record['ckey'], guid + '.raw')
            if len(raw) != record['bytes'] or hashlib.md5(raw).hexdigest() != record['ckey']:
                raise ValueError('Graph content-key mismatch: ' + guid)
            try:
                graph = FlatGraph(raw)
            except ValueError as error:
                result['errors'].append(dict(graph=guid, error=str(error)))
                continue
            objects = sorted(graph.objects)
            refs = []
            for at in range(0, len(raw)-7, 8):
                value, = struct.unpack_from('<Q', raw, at)
                if value >> 48 not in (0x0300, 0x0400):
                    continue
                obj = objects[max(0, bisect.bisect_right(objects, at)-1)]
                owners = []
                # Find direct node->typed resource config pointers. A reference
                # not owned directly remains explicitly unclassified.
                for i, node in enumerate(graph.nodes):
                    stop = min((o for o in objects if o > node), default=len(raw))
                    for ptr in range(node+8, stop-7, 8):
                        if graph.q(ptr) == obj:
                            kind = f'{graph.kind(node):08x}'
                            owners.append(dict(node=i, type=labels.get(kind, kind), field=ptr-node))
                refs.append(dict(offset=at, guid=f'{value:016x}', config=obj,
                                 configType=f'{graph.kind(obj):08x}', owners=owners))
            if refs:
                rows.append(dict(graph=guid, sha256=hashlib.sha256(raw).hexdigest(),
                                 nodes=len(graph.nodes), refs=refs))
        result['heroes'][hero] = dict(package=package, graphsScanned=len(graphs), graphs=rows)
    path = archive.out/'graph-index.json'
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({h: dict(graphs=v['graphsScanned'], refs=sum(len(g['refs']) for g in v['graphs']))
                      for h, v in result['heroes'].items()}))


def extract(guids):
    archive = Archive('models-20261026')
    for suffix in HEROES.values():
        archive.load_package('02e000000000'+suffix)
    for guid in guids:
        archive.out = CACHE/guid
        archive.out.mkdir(parents=True, exist_ok=True)
        report = collect(guid, archive=archive)
        print(json.dumps(dict(guid=guid, complete=report['complete'],
                              meshes=len(report.get('meshExports', [])),
                              resources=len(report['resources']))))


def entities(hero):
    archive = Archive('models-20261026')
    package = '02e000000000'+HEROES[hero]
    archive.load_package(package)
    guids = sorted(g for g in archive.records if g.startswith('0400') and
                   any(o.startswith(package) for o in archive.owners[g]))
    rows = []
    for guid in guids:
        record = archive.records[guid]
        raw = archive.fetch(record['ckey'], guid+'.raw')
        if hashlib.md5(raw).hexdigest() != record['ckey']:
            raise ValueError('Entity content-key mismatch')
        refs = scan_refs(raw, guid, archive.records)
        models = []
        for ref in refs:
            model = ref['guid']
            if not model.startswith('0d00'):
                continue
            r = archive.resolve(model)
            if not r:
                models.append(dict(guid=model, error='No registered resource record'))
                continue
            data = archive.fetch(r['ckey'], model+'.raw')
            if hashlib.md5(data).hexdigest() != r['ckey']:
                raise ValueError('Model content-key mismatch')
            try:
                mesh = parse_asset_model(data)
                pos = mesh['positions']
                bounds = [[float(f(v[i] for v in pos)) for i in range(3)] for f in (min,max)]
                models.append(dict(guid=model, vertices=len(pos), bounds=bounds))
            except ValueError as error:
                models.append(dict(guid=model, error=str(error)))
        rows.append(dict(entity=guid, refs=refs, models=models))
    path = archive.out/(hero.lower()+'-entities.json')
    path.write_text(json.dumps(rows, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(hero=hero, entities=len(rows), directModels=sum(len(r['models']) for r in rows))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index', action='store_true')
    parser.add_argument('--extract', nargs='+')
    parser.add_argument('--hero-entities', choices=HEROES)
    args = parser.parse_args()
    if args.index:
        index()
    if args.extract:
        extract(args.extract)
    if args.hero_entities:
        entities(args.hero_entities)
