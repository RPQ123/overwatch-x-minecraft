"""Read OWLib exports; keep all game-derived output outside this repository.

Binary layouts follow overtools/OWLib TankLib/ExportFormats/OverwatchModel.cs
and DataTool/Writers at develop 546efa19516d7df7ba138802d221c73ad886df28.
This reads converted assets only, never opens or modifies a game process.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import shutil
import struct

import numpy as np


class Reader:
    def __init__(self, data):
        self.data = io.BytesIO(data)

    def take(self, count):
        if not 0 <= count <= 64 * 1024 * 1024:
            raise ValueError("asset read bounds")
        value = self.data.read(count)
        if len(value) != count:
            raise ValueError("truncated OWLib export")
        return value

    def unpack(self, fmt):
        return struct.unpack('<' + fmt, self.take(struct.calcsize('<' + fmt)))

    def string(self):
        count = 0
        for shift in range(0, 35, 7):
            value = self.take(1)[0]
            count |= (value & 127) << shift
            if value < 128:
                if count > 4096:
                    raise ValueError("asset string bounds")
                return self.take(count).decode('utf-8')
        raise ValueError("invalid .NET string length")

    def array(self, count, width, dtype='<f4'):
        result = np.frombuffer(self.take(count * width * np.dtype(dtype).itemsize), dtype=dtype).reshape(count, width).copy()
        if not np.isfinite(result).all():
            raise ValueError("nonfinite asset data")
        return result

    def end(self):
        if self.data.read(1):
            raise ValueError("unexpected trailing asset data")


def model(path):
    r = Reader(Path(path).read_bytes())
    if r.unpack('HH') != (2, 0):
        raise ValueError("expected OWMDL 2.0")
    look, name = r.string(), r.string()
    guid, bones, count, hardpoints = r.unpack('IHII')
    if bones > 4096 or count > 1024 or hardpoints > 4096:
        raise ValueError("model count bounds")
    for _ in range(bones):
        r.string(); r.unpack('h'); r.array(3, 3)
    meshes = []
    for _ in range(count):
        mesh_name = r.string()
        material, uv_count, vertices, triangles, influences = r.unpack('QB IIB'.replace(' ', ''))
        if not 0 < vertices <= 1_000_000 or triangles > 2_000_000 or uv_count > 8 or influences > 16:
            raise ValueError("mesh count bounds")
        positions = r.array(vertices, 3)
        normals = r.array(vertices, 3)
        r.array(vertices, 4)  # tangents
        uvs = [r.array(vertices, 2) for _ in range(uv_count)]
        r.array(vertices, influences, '<u2')
        r.array(vertices, influences)
        colors = [r.array(vertices, 4), r.array(vertices, 4)]
        indices = r.array(triangles, 3, '<u4')
        if indices.size and indices.max() >= vertices:
            raise ValueError("mesh index out of bounds")
        meshes.append(dict(name=mesh_name, material=material, positions=positions,
                           normals=normals, uvs=uvs, colors=colors, indices=indices))
    for _ in range(hardpoints):
        r.string(); r.string(); r.array(1, 3); r.array(1, 4)
    r.end()
    return dict(guid=guid, name=name, look=look, bones=bones, meshes=meshes)


def material(path):
    r = Reader(Path(path).read_bytes())
    if r.unpack('HH') != (3, 0):
        raise ValueError("expected OWMAT 3.0")
    kind, = r.unpack('I')
    if kind == 1:
        count, = r.unpack('Q')
        if count > 1024: raise ValueError("material look count")
        result = dict(kind='look', entries=[(r.unpack('Q')[0], r.string()) for _ in range(count)])
    elif kind == 0:
        count, statics, shader = r.unpack('QQI')
        if count > 128 or statics > 4096: raise ValueError("material count")
        textures = [(r.string(), r.unpack('I')[0]) for _ in range(count)]
        values = []
        for _ in range(statics):
            key, size = r.unpack('II'); values.append((key, r.take(size).hex()))
        result = dict(kind='material', shader=shader, textures=textures, statics=values)
    else:
        raise ValueError("material type")
    r.end()
    return result


def entity(path):
    r = Reader(Path(path).read_bytes())
    if r.string() != 'owentity' or r.unpack('HH') != (2, 1):
        raise ValueError("expected OWENTITY 2.1")
    name, mdl, effect = r.string(), r.string(), r.string()
    guid, model_guid, effect_guid, count = r.unpack('IIII')
    if count > 1024: raise ValueError("entity child count")
    children = []
    for _ in range(count):
        child = r.string(); r.unpack('QQII'); r.string(); children.append(child)
    result = dict(name=name, model=mdl, effect=effect, guid=guid, modelGuid=model_guid,
                  effectGuid=effect_guid, children=children, look=r.string(), relative=r.string())
    r.end()
    return result


def preview(value, out):
    from PIL import Image, ImageDraw
    meshes = value['meshes']
    points = np.concatenate([m['positions'] for m in meshes])
    bounds = points.max(axis=0) - points.min(axis=0)
    canvas = Image.new('RGB', (1080, 400), '#202831')
    draw = ImageDraw.Draw(canvas)
    for panel, (a, b, depth) in enumerate(((0, 1, 2), (0, 2, 1), (1, 2, 0))):
        center = (points.max(axis=0) + points.min(axis=0)) / 2
        scale = 300 / max(bounds[a], bounds[b], .001)
        faces = []
        for m in meshes:
            p = m['positions']; n = m['normals']
            for ids in m['indices']:
                xyz = p[ids]; light = .35 + .65 * abs(n[ids].mean(axis=0)[depth])
                faces.append((xyz[:, depth].mean(), xyz, int(light * 220)))
        for _, xyz, shade in sorted(faces, key=lambda x: x[0]):
            poly = [(panel*360+180+(p[a]-center[a])*scale, 180-(p[b]-center[b])*scale) for p in xyz]
            draw.polygon(poly, fill=(shade, shade, shade), outline=None)
        draw.text((panel*360+10, 350), f'axes {a}/{b}, bounds {bounds.round(4).tolist()}', fill='white')
    canvas.save(out)


def pack_projectile(root, out):
    """Package the confirmed original Genji 7CA -> 29F9 chain, never guess a mesh.

    Uses DataTool's targeted extract-anything output without skin replacements.
    No copied game assets enter the source tree or the compiled guest jar.
    """
    from PIL import Image
    root, out = Path(root).resolve(), Path(out).resolve()
    repo = Path(__file__).resolve().parents[1]
    if out.is_relative_to(repo):
        raise ValueError('Game-derived pack must be outside the repository')
    ep, = root.rglob('0000000007CA.003.owentity')
    source_entity = entity(ep)
    if source_entity['modelGuid'] != 0x29F9:
        raise ValueError('Unverified Genji projectile model binding')
    mp, = root.rglob('0000000029F9.owmdl')
    mdl = model(mp)
    if mdl['bones'] or len(mdl['meshes']) != 1:
        raise ValueError('Only the measured rigid original projectile is supported')
    look_path = (mp.parent / mdl['look'].replace('\\', '/')).resolve()
    look = material(look_path)
    source_files = [ep, mp, look_path]
    render_meshes = []
    out.mkdir(parents=True, exist_ok=True)
    for index, mesh in enumerate(mdl['meshes']):
        mat_name, = [p for key, p in look['entries'] if key == mesh['material']]
        # OWLib model-look references are relative to the model directory,
        # rather than to the ModelLooks subdirectory containing the file.
        mat_path = (mp.parent / mat_name.replace('\\', '/')).resolve()
        mat = material(mat_path)
        if mat['shader'] != 217 or len(mesh['uvs']) != 1:
            raise ValueError('Unverified original material shader/UV layout')
        textures = {key: (mat_path.parent / p.replace('\\', '/')).resolve() for p, key in mat['textures']}
        # Texture meanings are declared in overtools/io_scene_owm shader_metadata.py.
        albedo, emission = textures[0xAD10F602], textures[0xBCBE747D]
        source_files += [mat_path, albedo, emission]
        for path in source_files:
            if not path.is_relative_to(root): raise ValueError('Asset escaped the extraction root')
        color_name, glow_name = f'genji-{index}-color.png', f'genji-{index}-emission.png'
        shutil.copy2(albedo, out / color_name)
        # Keep source color and emission mask; bake their product for the MC
        # emissive layer. This does not port OW's PBR shader, bloom or trails.
        color = Image.open(albedo).convert('RGBA')
        mask = Image.open(emission).convert('RGB').resize(color.size, Image.Resampling.BILINEAR)
        pixels = np.asarray(color).copy()
        pixels[:, :, 3] = np.asarray(mask).max(axis=2)
        Image.fromarray(pixels).save(out / glow_name)
        render_meshes.append(dict(texture=color_name, emission=glow_name,
            positions=mesh['positions'].reshape(-1).tolist(), normals=mesh['normals'].reshape(-1).tolist(),
            uv=mesh['uvs'][0].reshape(-1).tolist(), indices=mesh['indices'].reshape(-1).tolist()))
    data = dict(schema=1, nativeResource='04000000000007ca', model='0000000029F9.00C',
                units='meters', geometry='unscaled-original-owlib-export', meshes=render_meshes)
    (out / 'genji.json').write_text(json.dumps(data, separators=(',', ':')), encoding='utf-8')
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [out/'genji.json',out/'genji-0-color.png',out/'genji-0-emission.png']}
    provenance = dict(schema=1, owlib='2.25.0.0+1151+68397365', clientBuild='2.25.0.0.154088',
        originalEntity='0000000007CA.003', originalModel='0000000029F9.00C', files=hashes,
        sourceFiles={str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files},
        limitations=['MC material adaptation; not original OW PBR/bloom', 'Original effect graph, trails and impact effects not implemented'])
    (out/'provenance.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
    return provenance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model', type=Path, nargs='?')
    parser.add_argument('--preview', type=Path)
    parser.add_argument('--pack-root', type=Path)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    if args.pack_root:
        if not args.out: parser.error('--pack-root requires --out')
        print(json.dumps(pack_projectile(args.pack_root, args.out), indent=2)); return
    if not args.model: parser.error('model or --pack-root required')
    value = model(args.model)
    points = np.concatenate([m['positions'] for m in value['meshes']])
    print(json.dumps(dict(path=str(args.model), sha256=hashlib.sha256(args.model.read_bytes()).hexdigest(),
        guid=value['guid'], bones=value['bones'], look=value['look'],
        bounds=[points.min(axis=0).tolist(), points.max(axis=0).tolist()],
        meshes=[dict(name=m['name'], material=f"{m['material']:016x}", vertices=len(m['positions']),
                     triangles=len(m['indices'])) for m in value['meshes']]), indent=2))
    if args.preview: preview(value, args.preview)


if __name__ == '__main__': main()
