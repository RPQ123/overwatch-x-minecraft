"""Build the models thread's ONE private batch, without building/deploying a JAR.

Uses build_mesh_pack's verified arrays, then optional explicit MC material recipes.
Recipes may select ONLY actual refType=3 samplers of that exact material. They
are static UV0/fullbright/blend approximations, not native shader evaluation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile

from PIL import Image
from build_mesh_pack import build, CACHE, OUT
from ow_asset_chain import decode_asset_texture
from ow_material_params import bake_additive


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked(source, chain, guid):
    resource = chain['resources'][guid]
    path = source/resource['file']
    raw = path.read_bytes()
    if digest(path) != resource['sha256'] or hashlib.md5(raw).hexdigest() != resource['ckey']:
        raise ValueError('Archive SHA256/CKey mismatch: '+guid)
    return raw


def prepare(job, out_root):
    args = {k: job[k] for k in ('name', 'entity', 'model', 'material') if k in job}
    receipt = build(**args, out_root=out_root)
    target = Path(receipt['output'])
    source = CACHE/job['entity']
    chain = json.loads((source/'chain.json').read_text(encoding='utf-8'))
    data = json.loads((target/'pack.json').read_text(encoding='utf-8'))
    proof = json.loads((target/'provenance.json').read_text(encoding='utf-8'))
    for material, recipe in job.get('materials', {}).items():
        parameters = data['materialParameters'][material]
        texture = recipe['texture']
        if texture not in {s['guid'] for s in parameters['textureSlots'] if s['refType'] == 3}:
            raise ValueError('Recipe texture not bound to selected material: '+material)
        info = chain['resources'][texture]['texture']
        if info.get('status') != 'decoded':
            raise ValueError('Recipe texture not decoded: '+texture)
        decoded = decode_asset_texture(checked(source, chain, texture),
                                       checked(source, chain, info['payload']),
                                       plane_layout=chain.get('texturePlaneLayout', 'fields')).convert('RGBA')
        with Image.open(source/info['file']) as image:
            if image.convert('RGBA').tobytes() != decoded.tobytes() or image.size != decoded.size:
                raise ValueError('PNG differs from verified original decode')
        mode = recipe.get('blend', 'additive')
        if mode not in ('cutout', 'alpha', 'additive'):
            raise ValueError('Invalid MC blend')
        intensity = recipe.get('intensity', False)
        if mode == 'additive':
            rendered = bake_additive(decoded, intensity=intensity)
        elif intensity:
            rendered = Image.new('RGBA', decoded.size, (255,255,255,255))
            rendered.putalpha(decoded.getchannel('R'))
        else:
            rendered = decoded
        filename = material+'-models.png'
        rendered.save(target/filename)
        proof['files'][filename] = digest(target/filename)
        parameters.update(renderTexture=filename, tint=[1,1,1,1], emissive=recipe.get('emissive', 1),
                          blendMode=mode, resolved=True, nativeShaderEvaluated=False,
                          approximation=True, modelsRecipe=dict(**recipe, nativeBlendAuthenticated=False),
                          limits='MC static UV0 sampler selection/fullbright/blend; no emitter, dynamic inputs, HDR or native shader evaluation')
    # Never silently render minecraft:iron_block for a missing effect material.
    for group in data['groups']:
        parameters = data['materialParameters'].get(group.get('material'))
        if group['texture'] == 'grey' and parameters and 'renderTexture' not in parameters:
            parameters.update(blendMode='skip', resolved=False,
                              reason='No audited color/MC mask recipe; no iron-block fallback')
    proof['materialParameters'] = data['materialParameters']
    proof['modelsPose'] = job.get('pose', {})
    (target/'pack.json').write_text(json.dumps(data, separators=(',', ':'))+'\n', encoding='utf-8')
    proof['files']['pack.json'] = digest(target/'pack.json')
    (target/'provenance.json').write_text(json.dumps(proof, indent=2)+'\n', encoding='utf-8')
    receipt['skippedMaterials'] = sum(p.get('blendMode') == 'skip' for p in data['materialParameters'].values())
    return receipt


def pack(job, out_root):
    root = out_root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.models-', dir=root) as temporary:
        receipt = prepare(job, Path(temporary))
        staged = Path(receipt['output'])
        target = root/job['name']
        if target.is_symlink() or target.is_junction() or target.resolve().parent != root:
            raise ValueError('Output is linked or outside the named pack root')
        previous = Path(temporary)/'previous'
        if target.exists():
            target.replace(previous)
        try:
            staged.replace(target)
        except OSError:
            if previous.exists():
                previous.replace(target)
            raise
    receipt['output'] = str(target)
    return receipt


def audit(jobs, out_root):
    rows = []
    for job in jobs:
        target = out_root/job['name']
        data = json.loads((target/'pack.json').read_text(encoding='utf-8'))
        proof = json.loads((target/'provenance.json').read_text(encoding='utf-8'))
        source = json.loads(Path(proof['source']).read_text(encoding='utf-8'))
        for key in ('positions', 'normals', 'uv'):
            if data[key] != [v for row in source[key] for v in row]:
                raise ValueError('Original array differs: '+job['name']+'/'+key)
        expected = {}
        for sub in source['submeshes']:
            binding = sub.get('binding', {})
            texture = binding.get('colorTexture') if binding.get('status')=='bound' else 'grey'
            key = (texture or 'grey', binding.get('material'))
            at, count = sub['triangleStart']*3, sub['triangleCount']*3
            expected.setdefault(key, []).extend(source['indices'][at:at+count])
        actual = {(g['texture'], g.get('material')):g['indices'] for g in data['groups']}
        if expected != actual:
            raise ValueError('Group indices differ: '+job['name'])
        if any(digest(target/name) != value for name,value in proof['files'].items()):
            raise ValueError('Pack hash mismatch: '+job['name'])
        pixels = {}
        for material,parameters in data['materialParameters'].items():
            if 'renderTexture' in parameters:
                with Image.open(target/parameters['renderTexture']) as image:
                    image=image.convert('RGBA')
                    coverage=sum(image.getchannel('A').histogram()[1:])
                    pixels[material]=dict(size=list(image.size), extrema=image.getextrema(), nonzeroAlpha=coverage)
        rows.append(dict(name=job['name'], originalArraysEqual=True, groupIndicesEqual=True,
                         allHashesEqual=True, vertices=data['vertices'],
                         triangles=sum(len(g['indices'])//3 for g in data['groups']), pixels=pixels,
                         skipped=sum(p.get('blendMode')=='skip' for p in data['materialParameters'].values())))
    path=CACHE/'models-20261026/pack-audit.json'
    path.write_text(json.dumps(dict(inGameVerified=False, jarBuilt=False, deployed=False, packs=rows),indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(packs=len(rows), vertices=sum(r['vertices'] for r in rows),
                          triangles=sum(r['triangles'] for r in rows), skipped=sum(r['skipped'] for r in rows))))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch', type=Path, required=True)
    parser.add_argument('--out-root', type=Path, default=OUT)
    parser.add_argument('--audit', action='store_true', help='Read-only array/group/hash/pixel checks of built packs')
    args = parser.parse_args()
    jobs = json.loads(args.batch.read_text(encoding='utf-8'))
    if len({j['name'] for j in jobs}) != len(jobs):
        raise ValueError('Duplicate pack names')
    if args.audit:
        audit(jobs, args.out_root)
        return
    for job in jobs:
        print(json.dumps(pack(job, args.out_root)), flush=True)


if __name__ == '__main__':
    main()
