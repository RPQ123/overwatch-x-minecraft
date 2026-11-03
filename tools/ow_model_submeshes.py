"""Measured flat Beta24919 72-byte submesh reader, independent of the Venom API.

The cached OWLib RenderMesh reader confirms sparse index remap + VertexStart;
its modern descriptor layout is NOT copied over this older on-disk layout.
See docs/ASSET-SUBMESH-20261025.md for offsets and observed invariants.
"""
import struct
import json
from pathlib import Path

import numpy as np


def _parse_model_single(raw: bytes, max_extent=100.0, *, selected_lods_only=False):
    if len(raw) < 392 or struct.unpack_from('<I', raw, 72)[0] != len(raw):
        raise ValueError('Flat model size/header mismatch')
    slots, slots2 = struct.unpack_from('<HH', raw, 324)
    vb_count, ib_count, lod_mask, count = struct.unpack_from('<4B', raw, 336)
    materials, descriptors, vbo, ibo = struct.unpack_from('<4Q', raw, 352)
    if (vb_count, ib_count) != (1, 1) or not count or slots != slots2:
        raise ValueError('Unsupported flat buffer/material counts')
    if not (392 <= materials <= descriptors <= vbo < ibo < len(raw)):
        raise ValueError('Submesh table pointers out of bounds')
    if descriptors - materials != slots * 8 or vbo - descriptors != count * 72:
        raise ValueError('Submesh/material table length mismatch')
    slot_hashes = struct.unpack_from('<' + 'Q' * slots, raw, materials)
    vertex_count, = struct.unpack_from('<I', raw, vbo)
    strides = struct.unpack_from('<4B', raw, vbo + 8)
    desc, stream1, stream2 = struct.unpack_from('<3Q', raw, vbo + 32)
    index_count, index_format = struct.unpack_from('<2I', raw, ibo)
    index_data, = struct.unpack_from('<Q', raw, ibo + 16)
    expected = [(0,0,2,0,0),(4,0,6,0,0xc0000),(5,0,8,0,0x100000),
                (1,0,9,1,0),(3,0,9,1,0x40000),(9,0,4,1,0x80000),(16,0,12,1,0xc0000)]
    if strides[:3] == (20,20,8):
        expected = expected[:-1]+[(9,1,4,1,0xc0000),(16,0,12,1,0x100000)]
    if strides[:3] == (20,24,9):
        # Original hero bodies (e.g. Genji 09ec): skinned positions,
        # packed normal/tangent, RGBA8 colour and two half-float UV sets.
        expected=expected[:5]+[(8,0,8,1,0x80000),(9,0,4,1,0xc0000),
                              (9,1,4,1,0x100000),(16,0,12,1,0x140000)]
    if strides == (12,16,5,0):
        expected=expected[:1]+expected[3:]
    if strides in ((12,20,6,0),(12,24,7,0)):
        expected=[(0,0,2,0,0),(1,0,9,1,0),(3,0,9,1,0x40000),
                  (8,0,8,1,0x80000),(9,0,4,1,0xc0000)]
        if strides[1]==24:expected.append((9,1,4,1,0x100000))
        expected.append((16,0,12,1,(strides[1]-4)<<16))
    if strides not in ((20,16,7,6),(20,16,7,2),(20,20,8,2),(20,20,8,6),(20,24,9,2),(20,24,9,6),(12,16,5,0),(12,20,6,0),(12,24,7,0)) or index_format != 0:
        raise ValueError('Unsupported vertex/index format')
    actual=[struct.unpack_from('<4BI', raw, desc+i*8) for i in range(len(expected))] if desc+len(expected)*8<=len(raw) else []
    color_layout=(strides in ((12,20,6,0),(12,24,7,0),(20,24,9,2),(20,24,9,6)) and actual==expected or
                  strides[:3]==(20,20,8) and actual==expected[:5]+[(8,0,8,1,0x80000),(9,0,4,1,0xc0000),(16,0,12,1,0x100000)])
    if actual != expected and not color_layout:
        raise ValueError('Vertex semantics differ from measured flat24919')
    if not (0 < vertex_count and stream1 + vertex_count*strides[0] <= stream2 and
            stream2 + vertex_count*strides[1] <= index_data and index_data + index_count*2 <= len(raw)):
        raise ValueError('Vertex/index buffer bounds')
    positions = np.ndarray((vertex_count,3), '<f4', raw, stream1, (strides[0],4)).copy()
    normals = np.ndarray((vertex_count,3), 'i1', raw, stream2, (strides[1],1)).astype(np.float32)
    uv = np.ndarray((vertex_count,2), '<f2', raw, stream2+(12 if color_layout else 8), (strides[1],2)).astype(np.float32)
    weights = (np.ndarray((vertex_count,4), 'u1', raw, stream1+16, (20,1))
               if strides[0]==20 else np.tile(np.array([255,0,0,0],dtype='u1'),(vertex_count,1)))
    bones = (np.ndarray((vertex_count,4), 'u1', raw, stream1+12, (20,1))
             if strides[0]==20 else np.zeros((vertex_count,4),dtype='u1'))
    if strides[3] == 6 and np.any(weights != np.array([255,0,0,0], dtype='u1')):
        raise ValueError('Only measured rigid full-weight binding supported')
    if strides[3] == 2 and np.any(weights.astype(np.uint16).sum(1) != 255):
        raise ValueError('Bind-pose skin weights must sum to 255')
    if not np.isfinite(positions).all() or not np.isfinite(uv).all() or abs(positions).max() > max_extent:
        raise ValueError('Mesh arrays outside bounds')
    length = np.linalg.norm(normals, axis=1)
    if length.min() < 100 or length.max() > 140:
        raise ValueError('Unexpected packed normal range')
    normals /= length[:,None]
    indices = np.frombuffer(raw, '<u2', index_count, index_data)
    all_rows, selected, source_vertices, merged_indices = [], [], [], []
    vertex_cursor, triangle_cursor = 0, 0
    for i in range(count):
        offset = descriptors + i*72
        vertex_base, = struct.unpack_from('<I', raw, offset+52)
        start, size, unique_count, bone_offset = struct.unpack_from('<4H', raw, offset+56)
        flags, = struct.unpack_from('<H', raw, offset+64)
        buffer, material, mask = struct.unpack_from('<3B', raw, offset+66)
        if buffer != 0 or material >= slots or not mask or start+size > index_count or size % 3:
            raise ValueError(f'Invalid submesh descriptor {i}')
        row = dict(index=i, descriptorOffset=offset, indexStart=start, indexCount=size,
                   vertexBase=vertex_base, vertexCount=unique_count, boneIdOffset=bone_offset,
                   flags=flags, buffer=buffer, materialIndex=material,
                   materialSlotHash=f'{slot_hashes[material]:016x}', lodMask=mask,
                   lods=[n for n in range(8) if mask & (1 << n)])
        if selected_lods_only and not mask&1:
            row['unusedLodGeometryChecked']=False
            all_rows.append(row)
            continue
        local = indices[start:start+size].astype(np.uint32)
        used, remapped = np.unique(local, return_inverse=True)
        absolute = used + vertex_base
        placeholder=unique_count==0 and not mask&1
        if (len(used) != unique_count and not placeholder) or not len(used) or int(absolute.max()) >= vertex_count:
            raise ValueError(f'Sparse submesh vertex range/count mismatch {i}')
        row = dict(index=i, descriptorOffset=offset, indexStart=start, indexCount=size,
                   vertexBase=vertex_base, vertexCount=unique_count, boneIdOffset=bone_offset,
                   flags=flags, buffer=buffer, materialIndex=material,
                   materialSlotHash=f'{slot_hashes[material]:016x}', lodMask=mask,
                   lods=[n for n in range(8) if mask & (1 << n)])
        all_rows.append(row.copy())
        if not mask & 1:
            continue
        row.update(vertexOffset=vertex_cursor, triangleStart=triangle_cursor, triangleCount=size//3,
                   sourceVertexIndices=absolute.tolist())
        selected.append(row)
        source_vertices.extend(absolute.tolist())
        merged_indices.extend((remapped+vertex_cursor).tolist())
        vertex_cursor += len(used)
        triangle_cursor += size//3
    if not selected:
        raise ValueError('No LOD0 submesh declared')
    positions = positions[source_vertices]
    low, high = positions.min(0), positions.max(0)
    shift = np.array([-(low[0]+high[0])/2, -low[1], -(low[2]+high[2])/2], dtype=np.float32)
    positions += shift
    result = dict(schema=2, lod=0, sourceVertexCount=vertex_count, sourceIndexCount=index_count,
                sourceLodMask=lod_mask, sourceSubmeshes=all_rows, submeshes=selected,
                positions=positions, normals=normals[source_vertices], uv=uv[source_vertices],
                indices=np.asarray(merged_indices,dtype=np.uint32),
                sourceBounds=[low.tolist(),high.tolist()], originTranslation=shift.tolist(),
                height=float(high[1]-low[1]))
    if strides[3] == 2:
        result['skin'] = dict(mode='stored-bind-pose',vertexLayoutFlags=2,
                            boneIndices=bones[source_vertices].tolist(),
                            weightsUnorm8=weights[source_vertices].tolist(),
                            animationEvaluated=False,
                            note='Stored bind positions/normals preserved; no animated joint transforms applied')
    uv1_offset=16 if strides[1]==24 else 12 if strides[1]==20 and not color_layout else None
    if uv1_offset is not None:
        uv1 = np.ndarray((vertex_count,2),'<f2',raw,stream2+uv1_offset,(strides[1],2)).astype(np.float32)
        if not np.isfinite(uv1).all():
            raise ValueError('Second UV channel outside bounds')
        result['uv1'] = uv1[source_vertices]
    if color_layout:
        result['vertexColorsUnorm8']=np.ndarray((vertex_count,4),'u1',raw,stream2+8,(strides[1],1))[source_vertices].copy()
    return result


def parse_model_submeshes(raw: bytes, max_extent=100.0, *, selected_lods_only=False):
    """Parse one or several flat vertex/index buffers without changing old arrays.

    Multi-buffer headers are packed arrays of 56-byte VB / 24-byte IB rows.
    Submesh bytes65/66 select VB/IB independently. Each group is validated by
    the same single-buffer decoder through an in-memory descriptor view; source
    archive bytes are never rewritten. Only the final LOD0 geometry is merged.
    """
    if len(raw)<392:
        raise ValueError('Flat model size/header mismatch')
    vcount,icount=raw[336],raw[337]
    if (vcount,icount)==(1,1):
        return _parse_model_single(raw,max_extent,selected_lods_only=selected_lods_only)
    if not (1<=vcount<=16 and 1<=icount<=16):
        raise ValueError('Unsupported flat buffer counts')
    _,sm,vbo,ibo=struct.unpack_from('<4Q',raw,352)
    count=raw[339]
    if vbo-sm!=count*72 or vbo+vcount*56>len(raw) or ibo+icount*24>len(raw):
        raise ValueError('Multi-buffer descriptor bounds')
    groups={}
    for i in range(count):
        off=sm+i*72
        vb,ib=raw[off+65],raw[off+66]
        if vb>=vcount or ib>=icount:
            raise ValueError('Submesh VB/IB selector outside bounds')
        groups.setdefault((vb,ib),[]).append(i)
    chunks=[];all_rows=[];selected=[];vertex_cursor=triangle_cursor=0
    for (vb,ib),ids in groups.items():
        view=bytearray(raw)
        new_vbo=sm+len(ids)*72
        struct.pack_into('<2B',view,336,1,1)
        view[339]=len(ids)
        struct.pack_into('<2Q',view,368,new_vbo,ibo+ib*24)
        for j,i in enumerate(ids):
            view[sm+j*72:sm+(j+1)*72]=raw[sm+i*72:sm+(i+1)*72]
            view[sm+j*72+65:sm+j*72+67]=b'\0\0'
        view[new_vbo:new_vbo+56]=raw[vbo+vb*56:vbo+(vb+1)*56]
        has_lod0=any(raw[sm+i*72+68]&1 for i in ids)
        if not has_lod0 and selected_lods_only:
            continue
        if not has_lod0:
            view[sm+68]|=1  # validate this group's ranges, discard its geometry
        chunk=_parse_model_single(bytes(view),max_extent,selected_lods_only=selected_lods_only)
        for row in chunk['sourceSubmeshes']:
            original=ids[row['index']]
            row.update(index=original,descriptorOffset=sm+original*72,
                       vertexBuffer=vb,indexBuffer=ib,buffer=ib,lodMask=raw[sm+original*72+68])
            row['lods']=[n for n in range(8) if row['lodMask']&(1<<n)]
            all_rows.append(row)
        if not has_lod0:
            continue
        for row in chunk['submeshes']:
            original=ids[row['index']]
            row.update(index=original,descriptorOffset=sm+original*72,
                       vertexBuffer=vb,indexBuffer=ib,buffer=ib,
                       vertexOffset=row['vertexOffset']+vertex_cursor,
                       triangleStart=row['triangleStart']+triangle_cursor)
            selected.append(row)
        chunk['positions']-=np.asarray(chunk['originTranslation'],dtype=np.float32)
        chunk['indices']=chunk['indices']+vertex_cursor
        vertex_cursor+=len(chunk['positions']);triangle_cursor+=len(chunk['indices'])//3
        chunks.append(chunk)
    if not chunks:
        raise ValueError('No LOD0 submesh declared')
    positions=np.concatenate([c['positions'] for c in chunks])
    low,high=positions.min(0),positions.max(0)
    shift=np.array([-(low[0]+high[0])/2,-low[1],-(low[2]+high[2])/2],dtype=np.float32)
    positions+=shift
    result=dict(schema=2,lod=0,sourceVertexCount=sum(struct.unpack_from('<I',raw,vbo+i*56)[0] for i in range(vcount)),
                sourceIndexCount=sum(struct.unpack_from('<I',raw,ibo+i*24)[0] for i in range(icount)),
                sourceLodMask=raw[338],sourceSubmeshes=sorted(all_rows,key=lambda r:r['index']),
                sourceBufferCounts=[vcount,icount],submeshes=selected,positions=positions,
                normals=np.concatenate([c['normals'] for c in chunks]),uv=np.concatenate([c['uv'] for c in chunks]),
                indices=np.concatenate([c['indices'] for c in chunks]),sourceBounds=[low.tolist(),high.tolist()],
                originTranslation=shift.tolist(),height=float(high[1]-low[1]))
    if any('uv1' in c for c in chunks):
        result['uv1']=np.concatenate([c.get('uv1',np.zeros_like(c['uv'])) for c in chunks])
    if any('vertexColorsUnorm8' in c for c in chunks):
        result['vertexColorsUnorm8']=np.concatenate([c.get('vertexColorsUnorm8',np.full((len(c['positions']),4),255,dtype='u1')) for c in chunks])
    if any('skin' in c for c in chunks):
        result['skin']=dict(mode='stored-bind-pose',animationEvaluated=False,
            boneIndices=sum([c.get('skin',{}).get('boneIndices',[[0,0,0,0]]*len(c['positions'])) for c in chunks],[]),
            weightsUnorm8=sum([c.get('skin',{}).get('weightsUnorm8',[[255,0,0,0]]*len(c['positions'])) for c in chunks],[]))
    return result


def parse_look_materials(raw):
    """Beta SUTD Look inline array: count@112, pointer@120, 24-byte rows."""
    if len(raw) < 128 or raw[:4] != b'DUTS':
        raise ValueError('Unsupported Look container')
    count, pointer = struct.unpack_from('<2Q', raw, 112)
    if not (0 < count <= 4096 and 128 <= pointer and pointer+count*24 <= len(raw)):
        raise ValueError('Look material array bounds')
    result = {}
    for i in range(count):
        offset = pointer+i*24
        sentinel, material, slot = struct.unpack_from('<3Q',raw,offset)
        if sentinel != 0xffffffffffffffff or material and material >> 56 != 0x0e:
            raise ValueError('Unsupported Look material row')
        key, value = f'{slot:016x}', f'{material:016x}' if material else None
        if key in result and result[key]['material'] != value:
            raise ValueError('Conflicting Look slot bindings')
        result[key] = dict(material=value, offset=offset, slotHash=key)
    return result


def bind_materials(mesh, model_guid, chain, cache):
    """Resolve each LOD0 slot through the same entity's Look, never a global pick."""
    cache, resources = Path(cache), chain['resources']
    look_ids = set()
    for entity, row in resources.items():
        targets = {ref['guid'] for ref in row.get('refs',[])}
        if entity.startswith('04') and model_guid in targets:
            look_ids.update(g for g in targets if g.startswith('09') and resources.get(g,{}).get('status')=='read')
    looks, errors = {}, {}
    for look in sorted(look_ids):
        try:
            looks[look] = parse_look_materials((cache/(look+'.raw')).read_bytes())
        except (ValueError,struct.error,OSError) as error:
            errors[look] = str(error)
    triangle_textures = []
    for submesh in mesh['submeshes']:
        slot = submesh['materialSlotHash']
        matches = [(look, mapping[slot]) for look,mapping in looks.items() if slot in mapping]
        materials = {row['material'] for _,row in matches}
        binding = dict(slotHash=slot, looks=[dict(look=look,**row) for look,row in matches])
        texture_id = None
        if len(materials) != 1 or None in materials:
            binding.update(status='unresolved',reason='Missing, null or ambiguous same-entity Look slot',lookErrors=errors)
        else:
            material = next(iter(materials))
            binding['material'] = material
            candidates, rejected, missing = set(), set(), set()
            for ref in resources.get(material,{}).get('refs',[]):
                texture = ref['guid']
                if not texture.startswith('0c'):
                    continue
                path = cache/(texture+'.raw')
                header = path.read_bytes() if path.exists() else b''
                if resources.get(texture,{}).get('status') == 'unresolved' or not path.exists():
                    missing.add(texture)
                if len(header) == 32:
                    (candidates if header[3] in (72,78) else rejected).add(texture)
            binding.update(srgbCandidates=sorted(candidates),rejectedNonSrgb=sorted(rejected),missingTextureResources=sorted(missing))
            if len(candidates) == 1:
                candidate = next(iter(candidates))
                decoded = resources.get(candidate,{}).get('texture',{})
                if decoded.get('status') == 'decoded':
                    texture_id = candidate
                    binding.update(status='bound',colorTexture=candidate,textureFile=decoded['file'],format=decoded['format'])
                else:
                    binding.update(status='unresolved',reason='Bound sRGB texture has no decoded PNG')
            else:
                reason=('Texture resource absent from searched package index; cannot confirm its color format: '+', '.join(sorted(missing))
                        if missing and not candidates else 'Material has no unique sRGB(72/78) color texture')
                binding.update(status='unresolved',reason=reason)
        submesh['binding'] = binding
        triangle_textures.extend([texture_id]*submesh['triangleCount'])
    mesh['triangleTextureIds'] = triangle_textures
    mesh['materialBindingComplete'] = all(s['binding']['status']=='bound' for s in mesh['submeshes'])
    return mesh


def prepare_lod0_models(chain, cache):
    """Add corrected primary mesh exports while retaining legacy mesh files."""
    cache = Path(cache)
    for guid, resource in chain['resources'].items():
        if not guid.startswith('0d00') or resource.get('status') != 'read':
            continue
        legacy = resource.get('model',{}).copy()
        try:
            mesh = parse_model_submeshes((cache/resource['file']).read_bytes())
            bind_materials(mesh,guid,chain,cache)
            filename = guid+'.lod0.mesh.json'
            data = {k:v.tolist() if hasattr(v,'tolist') else v for k,v in mesh.items()}
            (cache/filename).write_text(json.dumps(data,separators=(',',':'))+'\n',encoding='utf-8')
            resource['model'] = dict(status='parsed',parser='ow_model_submeshes.parse_model_submeshes',
                                     file=filename,lod=0,vertices=len(mesh['positions']),
                                     triangles=len(mesh['indices'])//3,submeshes=len(mesh['submeshes']),
                                     materialBindingComplete=mesh['materialBindingComplete'],
                                     legacyFile=legacy.get('legacyFile',legacy.get('file')))
        except (ValueError,IndexError,struct.error,TypeError,OSError) as error:
            resource['model'] = dict(status='unsupported',error=str(error),
                                     legacyFile=legacy.get('legacyFile',legacy.get('file')))
