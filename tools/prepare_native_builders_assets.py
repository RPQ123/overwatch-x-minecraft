"""Original24919 builders meshes; --out-root research/... for sandbox preparation.

Uses ow_asset_chain/build_mesh_pack output. No game or profile writes. Turret
level assemblies are static MC presentation; native bone animation is not replayed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

import build_mesh_pack as packer

TURRET = '0400000000000143'
TURRET_MODEL = '0d0000000000092e'
LEVELS = {1: (18, 19, 20), 2: (16, 17, 18, 20), 3: (15, 16, 17, 18, 20)}
JOBS = [('junk-tire', '040000000000039c', '0d0000000000101b'),
        ('junk-death-bomb', '0400000000000515', '0d00000000002764')]


def selected_pack(mesh, pack, submeshes):
    selected = [s for s in mesh['submeshes'] if s['index'] in submeshes]
    if {s['index'] for s in selected} != set(submeshes):
        raise ValueError('Original turret submesh IDs changed')
    groups = {}
    for submesh in selected:
        for t in range(submesh['triangleStart'], submesh['triangleStart']+submesh['triangleCount']):
            groups.setdefault(mesh['triangleTextureIds'][t] or 'grey', []).extend(mesh['indices'][t*3:t*3+3])
    vertices = sorted({i for group in groups.values() for i in group})
    remap = {i: j for j, i in enumerate(vertices)}
    result = dict(pack)
    for key, width in [('positions', 3), ('normals', 3), ('uv', 2)]:
        result[key] = [pack[key][i*width+c] for i in vertices for c in range(width)]
    result.update(vertices=len(vertices), groups=[dict(texture=t, indices=[remap[i] for i in g]) for t, g in groups.items()])
    return result


def build(out_root):
    out_root = Path(out_root).resolve()
    rows = [packer.build(name, entity, model=model, out_root=out_root) for name, entity, model in JOBS]
    with tempfile.TemporaryDirectory(prefix='builders-source-', dir=out_root) as temporary:
        source = packer.build('torb-source', TURRET, model=TURRET_MODEL, out_root=Path(temporary))
        src = Path(source['output'])
        original = json.loads((src/'pack.json').read_text())
        proof = json.loads((src/'provenance.json').read_text())
        mesh = json.loads(Path(proof['source']).read_text())
        for level, parts in LEVELS.items():
            name = f'torb-turret-{level}'
            out = out_root/name
            if out.is_symlink() or out.is_junction():
                raise ValueError('Linked pack output refused')
            out.mkdir(parents=True, exist_ok=True)
            data = selected_pack(mesh, original, parts)
            data.update(name=name, turretLevel=level, sourceSubmeshIds=list(parts))
            (out/'pack.json').write_text(json.dumps(data, separators=(',', ':'))+'\n', encoding='utf-8')
            for filename in proof['files']:
                if filename != 'pack.json':
                    shutil.copy2(src/filename, out/filename)
            provenance = dict(proof, selectedSubmeshes=list(parts), turretLevel=level,
                              levelAssembly='MC static presentation; live pose/visibility unverified')
            provenance['files'] = {f: hashlib.sha256((out/f).read_bytes()).hexdigest() for f in proof['files']}
            (out/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n', encoding='utf-8')
            rows.append(dict(name=name, triangles=sum(len(g['indices'])//3 for g in data['groups']),
                             vertices=data['vertices'], selectedSubmeshes=list(parts), output=str(out)))
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-root', type=Path, default=packer.OUT)
    print(json.dumps(build(parser.parse_args().out_root)))
