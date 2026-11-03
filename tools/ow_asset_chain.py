"""Read an owned offline 24919 entity asset chain; never starts or attaches to a game.

Usage: .venv/Scripts/python.exe tools/ow_asset_chain.py 04000000000000af
All generated data stays under research/asset-cache/<GUID>. Unsupported model or
texture layouts are recorded explicitly; no invented geometry/shader parameters.
"""
from __future__ import annotations
from modpack.config import paths

import argparse
from collections import deque
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import subprocess

from PIL import Image, ImageDraw

from pulse_bomb_assets import EXE_SHA256, READER_SHA256, MANIFESTS, package_records
from ow_beta_texture import decode
from venom_mine_assets import parse_model
from ow_model_submeshes import prepare_lod0_models, parse_look_materials, parse_model_submeshes, bind_materials

ROOT = Path(__file__).resolve().parents[1]
GAME = paths().get('owExecutable').parent
READER = ROOT / 'research/casc-read-local.exe'
CACHE = ROOT / 'research/asset-cache'
FOLLOW = {0x04, 0x0d, 0x09, 0x0e, 0x0c, 0x03}
LIMIT = 16 * 1024 * 1024


def manifest_packages(raw):
    """24919 main APM: preserve *every* primary/secondary package version.

    CascLib's named tree keys these rows by PrimaryGUID only, so duplicate names
    hide packages (notably default diffuse headers). CKey@56 is unambiguous.
    Layout: local CascLib src/overwatch/overwatch.h CASC_APM_PACKAGE_ENTRY_V1.
    """
    if len(raw) < 24:
        return []
    count, lookup = struct.unpack_from('<2I', raw, 12)
    start = 24 + lookup * 12
    if not (0 < count <= 100000 and start + count * 72 == len(raw)):
        return []
    return [dict(guid=f'{struct.unpack_from("<Q",raw,o+8)[0]:016x}',
                 secondary=f'{struct.unpack_from("<Q",raw,o+16)[0]:016x}',
                 bytes=struct.unpack_from('<I',raw,o+44)[0], ckey=raw[o+56:o+72].hex(),
                 manifestOffset=o) for o in range(start,len(raw),72)]


def parse_material_slots(raw):
    """Measured flat24919 material: pointer@32, byte count@96, QII rows.

    refType=3 is a texture asset; refType=2 is a shader variable, even if its
    bits happen to start with 0c. Never resolve the latter as a texture GUID.
    """
    if len(raw) < 112 or struct.unpack_from('<Q',raw)[0] >> 48 != 0x0e10:
        raise ValueError('Unsupported flat material header')
    pointer, end = struct.unpack_from('<2Q',raw,32)
    count = raw[96]
    if not count:
        return []
    if not (112 <= pointer and pointer + count*16 == end <= len(raw)):
        raise ValueError('Material texture table bounds')
    result = []
    for offset in range(pointer,end,16):
        texture, slot, kind = struct.unpack_from('<QII',raw,offset)
        if kind == 3 and texture >> 48 != 0x0c00:
            raise ValueError('Unexpected texture reference type')
        result.append(dict(offset=offset,guid=f'{texture:016x}',slot=f'{slot:08x}',refType=kind))
    return result


def parse_effect(raw):
    """Flat beta effect tables, not modern ECMD chunks or opaque 0320 mips.

    Render rows are 336 bytes between pointers@32/@48; each binds model@184
    and material@248. Trail rows at pointer@80 are 320 bytes, model@184 and
    material@216. Keep the individual renderer bindings; do not collapse them
    into an invented static composite. All offsets are retained for auditing.
    """
    if len(raw) < 432:
        raise ValueError('Truncated flat effect header')
    emitters, renderers = struct.unpack_from('<2Q',raw,24)
    following = struct.unpack_from('<Q',raw,48)[0]
    empty = emitters==renderers==following==0
    if not empty:
        # Hanzo 0497 has five emitters and trails, with no particle-renderer
        # table (pointer@32=0). Its emitters end at pointer@48, not at zero.
        if renderers == 0:
            if not (432 <= emitters <= following <= len(raw) and (following-emitters)%240 == 0):
                raise ValueError('Unsupported emitter-only effect bounds')
        elif not (432 <= emitters <= renderers < following <= len(raw)
                  and (renderers-emitters)%240 == 0 and (following-renderers)%336 == 0):
            raise ValueError('Unsupported flat effect table bounds')
    rows = []
    def row(offset, material_offset, kind):
        model = struct.unpack_from('<Q',raw,offset+184)[0]
        material = struct.unpack_from('<Q',raw,offset+material_offset)[0]
        if model >> 48 != 0x0d00 or material >> 48 != 0x0e00:
            return False
        rows.append(dict(offset=offset,kind=kind,model=f'{model:016x}',
                         material=f'{material:016x}',modelOffset=offset+184,
                         materialOffset=offset+material_offset))
        return True
    for offset in range(renderers,following if renderers else 0,336):
        if not row(offset,248,'particle-renderer'):
            raise ValueError('Unsupported effect renderer binding')
    trail = struct.unpack_from('<Q',raw,80)[0]
    if trail:
        if not following <= trail < len(raw):
            raise ValueError('Effect trail table bounds')
        for offset in range(trail,min(len(raw)-319,trail+320*256),320):
            if not row(offset,216,'trail-renderer'):
                break
    return dict(emitterCount=((renderers or following)-emitters)//240,renderers=rows,
                geometryOnly=True,animationEvaluated=False)


def parse_asset_model(raw):
    """Also accept the measured 0cae three-UV layout, without editing the old API."""
    try:
        return parse_model_submeshes(raw)
    except ValueError as error:
        if str(error)!='Vertex semantics differ from measured flat24919':
            raise
    if len(raw)<392 or tuple(raw[336:338])!=(1,1):
        raise ValueError('Unsupported effect model buffers')
    vb = struct.unpack_from('<Q',raw,368)[0]
    if vb+56>len(raw) or tuple(raw[vb+8:vb+12])!=(12,24,7,0):
        raise ValueError('Unsupported effect vertex layout')
    count = struct.unpack_from('<I',raw,vb)[0]
    descriptor, _, stream = struct.unpack_from('<3Q',raw,vb+32)
    expected = [(0,0,2,0,0),(1,0,9,1,0),(3,0,9,1,0x40000),
                (9,0,4,1,0x80000),(9,1,4,1,0xc0000),
                (9,2,4,1,0x100000),(16,0,12,1,0x140000)]
    if (descriptor+56>len(raw) or stream+count*24>len(raw) or
            [struct.unpack_from('<4BI',raw,descriptor+i*8) for i in range(7)]!=expected):
        raise ValueError('Unsupported three-UV descriptors')
    # A temporary view puts UV0/UV1 where the validated color-layout decoder
    # expects them. Original bytes and their three independent UVs are retained.
    view = bytearray(raw)
    translated = expected[:3]+[(8,0,8,1,0x80000),(9,0,4,1,0xc0000),
                               (9,1,4,1,0x100000),expected[-1]]
    for i,row in enumerate(translated):
        struct.pack_into('<4BI',view,descriptor+i*8,*row)
    for i in range(count):
        off = stream+i*24
        view[off+8:off+12] = bytes([255])*4
        view[off+12:off+20] = raw[off+8:off+16]
    mesh = parse_model_submeshes(bytes(view))
    mesh.pop('vertexColorsUnorm8',None)
    vertices = [v for row in mesh['submeshes'] for v in row['sourceVertexIndices']]
    mesh['uv2'] = [list(struct.unpack_from('<2e',raw,stream+v*24+16)) for v in vertices]
    if any(not all(math.isfinite(c) for c in row) for row in mesh['uv2']):
        raise ValueError('Third UV channel outside bounds')
    mesh['sourceVertexLayout'] = 'position/normal/tangent/uv0/uv1/uv2/clip'
    return mesh


def decode_asset_texture(header, payload, *, plane_layout='fields'):
    # Single-payload ramps have no lower mip chain (flags=0); the existing
    # decoder accepts only flags>=1. Normalize that count in a temporary view,
    # retaining all surface/size/offset checks and the original archive bytes.
    if len(header)==32 and header[6]==1 and len(payload)>=16 and struct.unpack_from('<I',payload)[0]==0:
        payload = struct.pack('<I',1)+payload[4:]
    return decode(header,payload,plane_layout=plane_layout)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def guid_arg(value):
    value = value.lower().removeprefix('0x')
    if not re.fullmatch('[0-9a-f]{16}', value) or int(value, 16) == 0:
        raise argparse.ArgumentTypeError('Expected a nonzero 16-digit hexadecimal GUID')
    return value


def package_candidates(raw):
    """All package GUIDs in the SHA-pinned main manifest, then verify each APM.

    Parse the measured table when present; the byte scan remains a conservative
    fallback for small fixtures. A candidate is never a resource declaration
    until package_records passes.
    """
    candidates = set()
    # Exact24919 main manifest: 24-byte header, lookup_count*12 lookup table,
    # then record_count*72 rows. Each row's package GUID is at +8. Scanning only
    # hero/entity types misses map/shared packages carrying color textures.
    if len(raw) >= 24:
        record_count, lookup_count = struct.unpack_from('<2I',raw,12)
        start = 24 + lookup_count*12
        if 0 < record_count <= 100000 and start+record_count*72 == len(raw):
            candidates.update(f'{struct.unpack_from("<Q",raw,start+i*72+8)[0]:016x}' for i in range(record_count))
    for offset in range(len(raw) - 7):
        value, = struct.unpack_from('<Q', raw, offset)
        if value >> 48 in (0x02e0, 0x0400, 0x0250) and 0 < value & 0xffffffffffff < 0x100000:
            candidates.add(f'{value:016x}')
    return sorted(candidates, key=lambda g: ({'02e0': 0, '0400': 1, '0250': 2}.get(g[:4],3), g))


def scan_refs(raw, guid, records, *, material_textures=False):
    """Scan every byte, including unaligned and not-yet-indexed model/Look fields."""
    if guid.startswith('0320'):
        return []  # compressed image bytes must never become graph edges
    if guid.startswith('0d00'):
        return []  # flat vertex/index bytes are not GUID containers either
    if guid.startswith('0980'):
        try:
            return [dict(offset=row['offset']+8,guid=row['material'],via='look-material-slot')
                    for row in parse_look_materials(raw).values() if row['material']]
        except ValueError:
            pass
    if guid.startswith('0300'):
        refs = []
        try:
            for row in parse_effect(raw)['renderers']:
                refs.extend([dict(offset=row['modelOffset'],guid=row['model'],via='effect-model'),
                             dict(offset=row['materialOffset'],guid=row['material'],via='effect-material')])
        except ValueError:
            pass
        # Nested effect/entity references are DWORD aligned in this flat layout;
        # a byte scan admits false GUIDs in float/curve data (e.g. @337 in 058b).
        for offset in range(0,len(raw)-7,4):
            value = struct.unpack_from('<Q',raw,offset)[0]
            target = f'{value:016x}'
            if (value >> 48 in (0x0300,0x0400,0x0900,0x0980) and
                    target in records and target != guid):
                refs.append(dict(offset=offset,guid=target,via='effect-registered'))
        return refs
    if guid.startswith('0e00'):
        try:
            return [dict(offset=r['offset'],guid=r['guid'],via='material-texture-slot',slot=r['slot'])
                    for r in parse_material_slots(raw) if r['refType']==3]
        except ValueError:
            pass
    refs = []
    for offset in range(len(raw) - 7):
        value, = struct.unpack_from('<Q', raw, offset)
        target = f'{value:016x}'
        kind = value >> 56
        registered = target in records and kind in FOLLOW
        # Entity-only heuristic: canonical 09/0980/0d IDs, never arbitrary pointers.
        candidate = (guid.startswith('04') and value >> 48 in (0x0900, 0x0980, 0x0d00, 0x0300, 0x0400)
                     and value & 0x0000ffff00000000 == 0 and 0 < value & 0xffffffff < 0x100000)
        if value >> 48 in (0x0300,0x0400) and offset%8:
            candidate = False
        material_texture = (material_textures and guid.startswith('0e') and offset % 8 == 0
                            and value >> 32 == 0x0c000000 and value & 0xffffffff != 0)
        if target != guid and (registered or candidate or material_texture):
            refs.append({'offset': offset, 'guid': target, 'via': 'registered' if registered else
                         'material-texture-offset-scan' if material_texture else 'entity-offset-scan'})
    if guid.startswith('0c') and len(raw) == 32:
        # Small single-payload ramps (e.g. 256x4 241c) have payload count=1;
        # larger split-mip textures have count=2 and use 03200001 for the top.
        prefix = '03200000' if raw[6]==1 else '03200001'
        refs.append({'offset': -1, 'guid': prefix + guid[8:], 'via': 'texture-top-mip'})
    return refs


class Archive:
    def __init__(self, entity):
        self.out = CACHE / entity
        self.out.mkdir(parents=True, exist_ok=True)
        if sha(READER.read_bytes()) != READER_SHA256 or sha((GAME / 'GameClientApp.patched.exe').read_bytes()) != EXE_SHA256:
            raise ValueError('Unverified local reader or offline research executable')
        self.build = (GAME / '.build.info').read_bytes()
        if b'24919' not in self.build:
            raise ValueError('Archive build changed')
        self.records, self.owners, self.packages, self.attempted = {}, {}, {}, set()
        name, (entry, size, digest) = next(iter(MANIFESTS.items()))
        raw = self.fetch(entry, name)
        if len(raw) != size or sha(raw) != digest:
            raise ValueError('Main manifest identity mismatch')
        self.candidates = package_candidates(raw)
        self.manifest_rows = {}
        for row in manifest_packages(raw):
            self.manifest_rows.setdefault(row['guid'],[]).append(row)

    def fetch(self, entry, name, optional=False):
        target = self.out / name
        if not target.exists():
            temporary = target.with_suffix(target.suffix + '.partial')
            run = subprocess.run([str(READER), str(GAME), entry, str(temporary), str(LIMIT)],
                                 cwd=self.out, capture_output=True, timeout=45)
            if run.returncode:
                temporary.unlink(missing_ok=True)
                if optional:
                    return None
                raise ValueError(f'Local archive read failed: {name}, exit {run.returncode}')
            temporary.replace(target)
        raw = target.read_bytes()
        if len(raw) > LIMIT:
            raise ValueError('Reader byte limit exceeded: ' + name)
        return raw

    def load_package(self, guid):
        if guid in self.attempted:
            return
        self.attempted.add(guid)
        versions = getattr(self,'manifest_rows',{}).get(guid,[])
        if versions:
            for version in versions:
                self.load_package_version(version)
            return
        entry = 'AppPackageManifests\\Windows-RCN\\enUS\\' + guid
        raw = self.fetch(entry, 'package-' + guid + '.apm', optional=True)
        if raw is None:
            self.packages[guid] = {'entry': entry, 'status': 'not-found'}
            return
        if (len(raw) == 80 and struct.unpack_from('<Q',raw)[0] == 80 and
                struct.unpack_from('<2I',raw,24) == (0,0)):
            self.packages[guid] = {'entry':entry,'bytes':80,'sha256':sha(raw),'records':0,'status':'empty'}
            return
        try:
            rows = package_records(raw)
        except ValueError as error:
            self.packages[guid] = {'entry': entry, 'bytes': len(raw), 'sha256': sha(raw),
                                   'status': 'unsupported-or-empty', 'error': str(error)}
            return
        self.packages[guid] = {'entry': entry, 'bytes': len(raw), 'sha256': sha(raw), 'records': len(rows)}
        for resource, row in rows.items():
            if resource in self.records and any(row[k] != self.records[resource][k] for k in ('bytes', 'ckey')):
                raise ValueError('Conflicting package declarations: ' + resource)
            self.records[resource] = row
            self.owners.setdefault(resource, []).append(guid)

    def load_package_version(self, version):
        key = version['ckey']
        identity = version['guid'] + ':' + key
        if identity in self.packages:
            return
        # Reuse private APMs by content hash, including older named caches.
        # Every reused file is checked against the SHA-pinned main manifest.
        if not hasattr(self,'cached_packages'):
            self.cached_packages = {}
            for path in sorted(CACHE.glob('*/*.apm')):
                if path.name.startswith('package-') or re.fullmatch('[0-9a-f]{32}',path.stem):
                    self.cached_packages.setdefault(hashlib.md5(path.read_bytes()).hexdigest(),path)
        path = self.cached_packages.get(key)
        raw = path.read_bytes() if path else self.fetch(key,'package-'+version['guid']+'-'+key+'.apm',optional=True)
        if raw is None:
            self.packages[identity] = dict(**version,status='not-found')
            return
        if len(raw)!=version['bytes'] or hashlib.md5(raw).hexdigest()!=key:
            raise ValueError('Main manifest package content-key/size mismatch: '+identity)
        receipt = dict(**version,sha256=sha(raw),entry=key)
        if len(raw)==80 and struct.unpack_from('<Q',raw)[0]==80 and struct.unpack_from('<2I',raw,24)==(0,0):
            self.packages[identity] = dict(**receipt,records=0,status='empty')
            return
        rows = package_records(raw)
        self.packages[identity] = dict(**receipt,records=len(rows))
        for resource,row in rows.items():
            if resource in self.records and any(row[k]!=self.records[resource][k] for k in ('bytes','ckey')):
                raise ValueError('Conflicting package declarations: '+resource)
            self.records[resource] = row
            owners = self.owners.setdefault(resource,[])
            if identity not in owners:
                owners.append(identity)

    def resolve(self, guid):
        if guid not in self.records:
            self.load_package(guid)
        if guid not in self.records:
            for package in self.candidates:
                self.load_package(package)
                if guid in self.records:
                    break
        return self.records.get(guid)


def contact_sheet(out, textures):
    tiles = []
    for guid, filename in textures:
        with Image.open(out / filename) as source:
            thumb = source.convert('RGBA')
            thumb.thumbnail((224, 200))
            tile = Image.new('RGB', (256, 232), '#303030')
            tile.paste(thumb, ((256 - thumb.width) // 2, 4), thumb)
            ImageDraw.Draw(tile).text((6, 212), guid, fill='white')
            tiles.append(tile)
    cols = min(3, max(1, len(tiles)))
    sheet = Image.new('RGB', (cols * 256, max(1, (len(tiles) + cols - 1) // cols) * 232), '#303030')
    for i, tile in enumerate(tiles):
        sheet.paste(tile, ((i % cols) * 256, (i // cols) * 232))
    if not tiles:
        ImageDraw.Draw(sheet).text((8, 8), 'No supported textures; see chain.json', fill='white')
    sheet.thumbnail((768, 768))
    sheet.save(out / 'contact.jpg', quality=80)
    return list(sheet.size)


def color_binding(material, resources, out):
    """Select within one material; a known diffuse slot outranks other sRGB maps."""
    binding = dict(material=material)
    source = resources.get(material,{})
    if source.get('status')!='read':
        return dict(**binding,status='unresolved',reason='Material unavailable')
    try:
        slots = parse_material_slots((out/source['file']).read_bytes())
    except ValueError as error:
        return dict(**binding,status='unresolved',reason=str(error))
    textures = [r for r in slots if r['refType']==3]
    binding['textureSlots'] = slots
    srgb, missing, rejected = [], [], []
    for row in textures:
        resource = resources.get(row['guid'],{})
        if resource.get('status')!='read':
            missing.append(row['guid'])
            continue
        header = (out/resource['file']).read_bytes()
        if len(header)==32 and header[3] in (72,78):
            srgb.append(row['guid'])
        else:
            rejected.append(row['guid'])
    diffuse = {r['guid'] for r in textures if r['slot']=='ad10f602'}
    candidates = diffuse if diffuse else set(srgb)
    binding.update(srgbCandidates=sorted(set(srgb)),rejectedNonSrgb=sorted(set(rejected)),
                   missingTextureResources=sorted(set(missing)),
                   selection='diffuse-slot-ad10f602' if diffuse else 'unique-material-srgb')
    if len(candidates)==1:
        candidate = next(iter(candidates))
        decoded = resources.get(candidate,{}).get('texture',{})
        if candidate in srgb and decoded.get('status')=='decoded':
            return dict(**binding,status='bound',colorTexture=candidate,
                        textureFile=decoded['file'],format=decoded['format'])
    return dict(**binding,status='unresolved',reason='No unique decoded color texture in this material')


def export_bound_meshes(report, out):
    """Rebind direct Looks and export each effect model/material pair separately."""
    resources = report['resources']
    exports = []
    def bind(mesh, material=None):
        ids = []
        for submesh in mesh['submeshes']:
            previous = submesh.get('binding',{})
            mat = material or previous.get('material')
            if mat:
                submesh['binding'] = {**previous,**color_binding(mat,resources,out)}
            binding = submesh.get('binding',{})
            ids.extend([binding.get('colorTexture') if binding.get('status')=='bound' else None]*submesh['triangleCount'])
        mesh['triangleTextureIds'] = ids
        mesh['materialBindingComplete'] = all(s.get('binding',{}).get('status')=='bound' for s in mesh['submeshes'])
        return mesh
    for guid, resource in resources.items():
        model = resource.get('model',{})
        if guid.startswith('0d00') and resource.get('status')=='read' and model.get('status')!='parsed':
            try:
                mesh = parse_asset_model((out/resource['file']).read_bytes())
                bind_materials(mesh,guid,report,out)
                filename = guid+'.lod0.mesh.json'
                data = {k:v.tolist() if hasattr(v,'tolist') else v for k,v in mesh.items()}
                (out/filename).write_text(json.dumps(data,separators=(',',':'))+'\n',encoding='utf-8')
                resource['model'] = model = dict(status='parsed',lod=0,file=filename,
                    parser='ow_asset_chain.parse_asset_model',vertices=len(mesh['positions']),
                    triangles=len(mesh['indices'])//3,submeshes=len(mesh['submeshes']),
                    materialBindingComplete=False,legacyFile=model.get('legacyFile'))
            except (ValueError,IndexError,struct.error,TypeError,OSError):
                pass
        if model.get('status')!='parsed' or model.get('lod')!=0:
            continue
        filename = model['file']
        mesh = bind(json.loads((out/filename).read_text(encoding='utf-8')))
        (out/filename).write_text(json.dumps(mesh,separators=(',',':'))+'\n',encoding='utf-8')
        model['materialBindingComplete'] = mesh['materialBindingComplete']
        # Only direct entity/Look exports can be chosen without an explicit
        # effect material. Unbound effect meshes remain available for inspection.
        exports.append(dict(model=guid,file=filename,material=None,
                            materialBindingComplete=mesh['materialBindingComplete']))
    pairs = {}
    for effect, resource in resources.items():
        for row in resource.get('effect',{}).get('renderers',[]):
            pairs.setdefault((row['model'],row['material']),[]).append(dict(effect=effect,**row))
    for (model,material), renderers in sorted(pairs.items()):
        row = dict(model=model,material=material,renderers=renderers)
        try:
            resource = resources[model]
            mesh = bind(parse_asset_model((out/resource['file']).read_bytes()),material)
            filename = model+'.'+material+'.lod0.mesh.json'
            mesh.update(effectRenderers=renderers,geometryOnly=True,animationEvaluated=False)
            data = {k:v.tolist() if hasattr(v,'tolist') else v for k,v in mesh.items()}
            (out/filename).write_text(json.dumps(data,separators=(',',':'))+'\n',encoding='utf-8')
            row.update(status='parsed',file=filename,vertices=len(mesh['positions']),
                       triangles=len(mesh['indices'])//3,materialBindingComplete=mesh['materialBindingComplete'])
            exports.append(row.copy())
        except (KeyError,ValueError,IndexError,struct.error,TypeError,OSError) as error:
            row.update(status='unsupported',error=str(error))
        report.setdefault('effectModelBindings',[]).append(row)
    report['meshExports'] = exports


def collect(entity, max_resources=2048, texture_layout='fields', *, archive=None):
    # Batch offline inventories may provide a SHA-guarded Archive preloaded with
    # the hero's verified dependency catalog, avoiding repeated package reads.
    archive = Archive(entity) if archive is None else archive
    resources, queue = {}, deque([entity])
    while True:
        if not queue:
            active_materials = set()
            for source, resource in resources.items():
                if source.startswith('09') and resource['status'] == 'read':
                    try:
                        mapping = parse_look_materials((archive.out/resource['file']).read_bytes())
                        active_materials.update(r['material'] for r in mapping.values() if r['material'])
                    except (ValueError,struct.error):
                        pass
                if source.startswith('0300') and resource['status']=='read':
                    try:
                        active_materials.update(r['material'] for r in parse_effect((archive.out/resource['file']).read_bytes())['renderers'])
                    except ValueError:
                        pass
            # Later model/Look resolution may load a shared package declaring an
            # earlier entity's references. Revisit until the graph is closed.
            for source, resource in resources.items():
                if resource['status'] == 'read' and not source.startswith('0320'):
                    resource['refs'] = scan_refs((archive.out / resource['file']).read_bytes(), source, archive.records,
                                                material_textures=source in active_materials)
                    queue.extend(r['guid'] for r in resource['refs'] if r['guid'] not in resources)
            if not queue:
                break
        guid = queue.popleft()
        if guid in resources:
            continue
        if len(resources) >= max_resources:
            raise ValueError('Resource limit reached; refusing a silently truncated chain')
        row = archive.resolve(guid)
        if row is None:
            resources[guid] = {'status': 'unresolved', 'refs': []}
            continue
        try:
            raw = archive.fetch(row['ckey'], guid + '.raw')
        except ValueError as error:
            if not str(error).startswith('Local archive read failed:'):
                raise
            resources[guid] = {'status':'unavailable','declaredBytes':row['bytes'],'ckey':row['ckey'],
                               'error':str(error),'refs':[]}
            continue
        if len(raw) != row['bytes'] or hashlib.md5(raw).hexdigest() != row['ckey']:
            raise ValueError('Resource size/content-key mismatch: ' + guid)
        # Only 0320 records are terminal mip payloads. 0300 is a visual effect.
        refs = scan_refs(raw, guid, archive.records)
        resources[guid] = {'status': 'read', 'bytes': len(raw), 'sha256': sha(raw),
                           'ckey': row['ckey'], 'file': guid + '.raw', 'refs': refs}
        queue.extend(ref['guid'] for ref in refs)
    textures = []
    for guid, resource in resources.items():
        resource['packages'] = archive.owners.get(guid, [])
        if resource['status'] != 'read':
            continue
        raw = (archive.out / resource['file']).read_bytes()
        if guid.startswith('0300'):
            try:
                resource['effect'] = dict(status='parsed',**parse_effect(raw))
            except ValueError as error:
                resource['effect'] = dict(status='unsupported',error=str(error))
        if guid.startswith('0d'):
            try:
                geo = parse_model(raw, max_extent=3.0)
                filename = guid + '.mesh.json'
                data = {k: (v.tolist() if hasattr(v, 'tolist') else v) for k, v in geo.items()}
                (archive.out / filename).write_text(json.dumps(data, separators=(',', ':')) + '\n', encoding='utf-8')
                resource['model'] = {'status': 'parsed', 'parser': 'venom_mine_assets.parse_model', 'file': filename,
                                     'vertices': len(geo['positions']), 'triangles': len(geo['indices']) // 3}
            except (ValueError, IndexError, struct.error, TypeError) as error:
                resource['model'] = {'status': 'unsupported', 'error': str(error)}
        if guid.startswith('0c'):
            try:
                payload_guid = ('03200000' if raw[6]==1 else '03200001') + guid[8:]
                payload = resources.get(payload_guid, {})
                if len(raw) != 32 or payload.get('status') != 'read':
                    raise ValueError('Not a measured 32-byte header or missing top-mip payload')
                image = decode_asset_texture(raw, (archive.out / payload['file']).read_bytes(), plane_layout=texture_layout)
                filename = guid + '.png'
                image.save(archive.out / filename)
                resource['texture'] = {'status': 'decoded', 'file': filename, 'size': list(image.size), 'format': raw[3],
                                       'payload':payload_guid}
                textures.append((guid, filename))
            except (ValueError, OSError, struct.error) as error:
                resource['texture'] = {'status': 'unsupported', 'error': str(error)}
    if (GAME / '.build.info').read_bytes() != archive.build:
        raise ValueError('Archive identity changed during read')
    report = {'schema': 1, 'build': '0.8.0.24919', 'entity': entity, 'online': False, 'archiveReadOnly': True,
              'readerSha256': READER_SHA256, 'executableSha256': EXE_SHA256, 'buildInfoSha256': sha(archive.build),
              'scanPolicy': 'canonical entity effect/model/Look/parent; flat effect renderer tables; material texture slots; 0320 terminal mips; all main APM CKey versions',
              'texturePlaneLayout': texture_layout, 'packages': archive.packages, 'resources': resources,
              'contact': {'file': 'contact.jpg', 'size': contact_sheet(archive.out, textures)},
              'complete': all(r['status'] == 'read' for r in resources.values()),
              'inGameVerified': False}
    prepare_lod0_models(report,archive.out)
    export_bound_meshes(report,archive.out)
    (archive.out / 'chain.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report


def compare_reference(report, reference):
    """Read-only byte identity comparison, including resources missed by an old walk."""
    checks, pixels = {}, {}
    for guid, resource in report['resources'].items():
        path = reference / (guid + '.raw')
        if resource['status'] == 'read':
            checks[guid] = 'match' if path.exists() and sha(path.read_bytes()) == resource['sha256'] else 'absent-or-different'
        texture = resource.get('texture', {})
        old_png = reference / ('tex-' + guid[-4:] + '.png')
        if texture.get('status') == 'decoded' and old_png.exists():
            with Image.open(old_png) as old, Image.open(CACHE / report['entity'] / texture['file']) as new:
                pixels[guid] = old.size == new.size and old.convert('RGBA').tobytes() == new.convert('RGBA').tobytes()
    missing = sorted(p.stem for p in reference.glob('*.raw') if p.stem not in checks)
    return {'directory': str(reference), 'resources': checks, 'missingReferenceResources': missing,
            'referencePngPixelsEqual': pixels,
            'allReferencePngPixelsEqual': bool(pixels) and all(pixels.values()),
            'allRawMatch': bool(checks) and not missing and all(v == 'match' for v in checks.values())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('entity', type=guid_arg)
    parser.add_argument('--compare', type=Path, help='Read-only raw-resource reference directory')
    parser.add_argument('--texture-layout', choices=('fields', 'dword'), default='fields',
                        help='fields: current decoder; dword: reproduce legacy reference PNGs')
    args = parser.parse_args()
    report = collect(args.entity, texture_layout=args.texture_layout)
    if args.compare:
        comparison = compare_reference(report, args.compare.resolve())
        (CACHE / args.entity / 'comparison.json').write_text(json.dumps(comparison, indent=2) + '\n', encoding='utf-8')
    summary = {'entity': args.entity, 'resources': len(report['resources']), 'complete': report['complete'],
               'decodedTextures': sum(r.get('texture', {}).get('status') == 'decoded' for r in report['resources'].values()),
               'output': str(CACHE / args.entity)}
    if args.compare:
        summary['referenceRawAllMatch'] = comparison['allRawMatch']
        summary['referencePngPixelsEqual'] = comparison['allReferencePngPixelsEqual']
    print(json.dumps(summary))
    return 0 if report['complete'] and (not args.compare or
                (comparison['allRawMatch'] and comparison['allReferencePngPixelsEqual'])) else 1


if __name__ == '__main__':
    raise SystemExit(main())
