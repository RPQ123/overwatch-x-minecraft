"""Measured flat24919 material tables and explicitly bounded MC presentation.

Texture refType=2 is a runtime binding, never an archive image. Constant buffers
are retained verbatim as numbers; only individually audited offsets get colour
semantics. Generated PNGs are private derivatives, not native shader execution.
"""
import hashlib
import math
import struct

import numpy as np
from PIL import Image

from ow_asset_chain import parse_material_slots, decode_asset_texture


def parse(raw):
    slots = parse_material_slots(raw)
    features, variables, blocks = [], [], []
    feature_at, variable_at, block_at = struct.unpack_from('<3Q', raw, 40)
    feature_count = struct.unpack_from('<H', raw, 94)[0]
    if feature_count and (feature_at<112 or feature_at+feature_count*8>len(raw)):
        raise ValueError('Material feature table bounds')
    if raw[100] and (variable_at<112 or variable_at+raw[100]*16>len(raw)
                     or feature_at+feature_count*8!=variable_at
                     or raw[97] and variable_at+raw[100]*16!=block_at):
        raise ValueError('Material shader binding table bounds')
    if raw[97] and (block_at<112 or block_at + raw[97]*16 > len(raw)):
        raise ValueError('Material constant descriptor bounds')
    for i in range(feature_count):
        at = feature_at+i*8
        name, value = struct.unpack_from('<2I', raw, at)
        features.append(dict(offset=at, nameHash=f'{name:08x}', valueHash=f'{value:08x}'))
    for i in range(raw[100]):
        at = variable_at+i*16
        name, pad, target = struct.unpack_from('<IIQ', raw, at)
        if pad:
            raise ValueError('Material shader binding padding')
        variables.append(dict(offset=at, nameHash=f'{name:08x}', target=f'{target:016x}'))
    for i in range(raw[97]):
        at = block_at+i*16
        relative, stage, register, size, key = struct.unpack_from('<QBBHI', raw, at)
        start = at+relative
        if stage not in (1,2) or register>15 or size%4 or start < block_at+raw[97]*16 or start+size > len(raw):
            raise ValueError('Material constant payload bounds')
        values = list(struct.unpack_from('<'+'f'*(size//4), raw, start))
        if any(not math.isfinite(x) for x in values):
            raise ValueError('Material nonfinite constants')
        blocks.append(dict(descriptorOffset=at, offset=start, stage=stage, register=register, byteSize=size,
                           key=f'{key:08x}', values=values))
    return dict(shaderSource=f'{struct.unpack_from("<Q",raw)[0]:016x}',
                sha256=hashlib.sha256(raw).hexdigest(), textureSlots=slots,
                features=features, shaderBindings=variables, constantBuffers=blocks,
                blendHash=next((f['valueHash'] for f in features if f['nameHash']=='22944c2a'), None))


def rgb_at(parameters, stage, offset):
    blocks = [b for b in parameters['constantBuffers'] if b['stage']==stage]
    if len(blocks)!=1 or offset<0 or offset%4 or offset+12>blocks[0]['byteSize']:
        raise ValueError('Audited material color offset no longer exists')
    value = blocks[0]['values'][offset//4:offset//4+3]
    if min(value)<0 or max(value)>256:
        raise ValueError('Audited HDR color outside bounds')
    return value


def linear_to_srgb(rgb):
    return np.where(rgb<=.0031308, rgb*12.92, 1.055*np.maximum(rgb,0)**(1/2.4)-.055)


def srgb_to_linear(rgb):
    return np.where(rgb<=.04045, rgb/12.92, ((rgb+.055)/1.055)**2.4)


def bake_additive(image, hdr=(1,1,1), *, intensity=False, ramp=None):
    """ONE/ONE needs RGB masked even where alpha=0. Preserve source alpha once."""
    a = np.asarray(image.convert('RGBA'), dtype=np.float32)/255
    coverage = a[:,:,0] if intensity else a[:,:,3]
    rgb = np.ones_like(a[:,:,:3]) if intensity else srgb_to_linear(a[:,:,:3])
    if ramp is not None:
        # Static UV0 lookup of the original noise/mask into the original ramp.
        # Native scroll, view ramp and animated emitter inputs remain unevaluated.
        r = np.asarray(ramp.convert('RGB'), dtype=np.float32)/255
        rgb = srgb_to_linear(r[r.shape[0]//2, np.rint(coverage*(r.shape[1]-1)).astype(int)])
    peak = max(1.0, max(hdr))
    rgb = linear_to_srgb(np.clip(rgb*np.asarray(hdr)/peak, 0, 1))*coverage[:,:,None]
    return Image.fromarray(np.rint(np.dstack((rgb,coverage))*255).astype('uint8'))


# Offsets are bytes within the stage2 material CB. Shader .086 part hashes
# describe generic float4 parameter vectors; matched .087 assembly verifies the
# RGB swizzles. No claim is made that the complete permutation selector is run.
COLORS = {
    '0e0000006b4d8661': (32, '06100000bd45cdf8', 'CB4[2].xyz', '0c00000000001298'),
    '0e0000005a069daf': (32, '06100000bd45cdf8', 'CB4[2].xyz', '0c00000000001298'),
    '0e000000115641cb': (96, '061000003e6fede9', 'CB4[6].xyz', '0c000000000007a8'),
    '0e000000bae0e512': (96, '061000003e6fede9', 'CB4[6].xyz', '0c000000000007a8'),
    '0e0000008a92fe7f': (128, '0610000094608b7d', 'CB4[8].xyz', '0c00000000001298'),
    '0e0000007b543afe': (4, '0610000000c27ccc', 'CB4[0].yzw', '0c00000000001298'),
    '0e0000001dbb9ff2': (64, None, 'generic CB4[4].xyz; layout-based approximation', '0c00000000001603'),
}
DISTORTION = {'0e000000e06922b3','0e000000b815a1f6'}
ZEN_COLOR = {'0e0000005443ff5c','0e000000b66cb8c5','0e000000e7fd885a','0e000000d8edbb06'}
DRAGON = {'0e000000000007a5','0e00000000000810'}
DRAGON_TRAILS = {'0e0000008e2eb8c3','0e000000cfa17e2d','0e0000002a74326b','0e0000002391004a','0e000000c41c6344'}


def prepare(material, binding, source, chain, stage):
    """Return JSON parameters + generated filename hashes, fail closed on changes."""
    resource = chain['resources'].get(material,{})
    filename = resource.get('file')
    if not filename:
        return dict(tint=[1,1,1,1], emissive=0, blendMode='cutout', resolved=False), {}
    raw = (source/filename).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=resource['sha256'] or hashlib.md5(raw).hexdigest()!=resource['ckey']:
        raise ValueError('Material chain SHA256/CKey mismatch: '+material)
    data = parse(raw)
    data.update(tint=[1,1,1,1], emissive=0, blendMode='cutout', resolved=False,
                nativeShaderEvaluated=False, approximation=True)
    generated = {}

    def load(guid):
        if guid not in {s['guid'] for s in data['textureSlots'] if s['refType']==3}:
            raise ValueError('Texture is not bound by this material: '+guid)
        t = chain['resources'].get(guid,{}).get('texture',{})
        if t.get('status')!='decoded' or t['file']!=guid+'.png':
            raise ValueError('Audited material texture missing: '+guid)
        def checked(resource_guid):
            r=chain['resources'][resource_guid]
            b=(source/r['file']).read_bytes()
            if hashlib.sha256(b).hexdigest()!=r['sha256'] or hashlib.md5(b).hexdigest()!=r['ckey']:
                raise ValueError('Material texture archive SHA256/CKey mismatch')
            return b
        decoded=decode_asset_texture(checked(guid),checked(t['payload']),plane_layout=chain.get('texturePlaneLayout','fields')).convert('RGBA')
        with Image.open(source/t['file']) as image:
            image=image.convert('RGBA')
            if image.size!=decoded.size or image.tobytes()!=decoded.tobytes():
                raise ValueError('Material PNG differs from verified archive decode')
            return image

    def save(image, suffix):
        name = material+'-'+suffix+'.png'
        image.save(stage/name)
        generated[name] = hashlib.sha256((stage/name).read_bytes()).hexdigest()
        return name

    if material in DISTORTION:
        # Selected 085b is a refraction surface, not a grey physical orb. It has
        # no static RGB map. Native dynamic t1/t2 and the distortion render target
        # cannot be reproduced by a textured entity layer.
        data.update(blendMode='skip', reason='Native refraction/variable textures unresolved; draw original colored sibling layers',
                    shaderEvidence='06100000a8061dd1 distortion candidate; runtime permutation unresolved')
    elif material in COLORS:
        if any(b['register']!=4 for b in data['constantBuffers'] if b['stage']==2):
            raise ValueError('Audited color CB4 register changed')
        offset, code, swizzle, mask = COLORS[material]
        hdr = rgb_at(data, 2, offset)
        is_graviton=material in {'0e000000115641cb','0e000000bae0e512'}
        ramp = load('0c0000000000241c' if material=='0e000000115641cb' else '0c00000000002848') if is_graviton else None
        data.update(colorLinearHDR=hdr, colorBufferStage=2, colorByteOffset=offset,
                    shaderEvidence=dict(code=code, swizzle=swizzle, permutationAuthenticated=False),
                    emissive=max(hdr), blendMode='additive', resolved=True,
                    renderTexture=save(bake_additive(load(mask),hdr,intensity=True,ramp=ramp),'color'),
                    intensityTexture=mask, rampTexture=('0c0000000000241c' if material=='0e000000115641cb' else '0c00000000002848') if ramp else None,
                    limits='Native RGB data; static mask/ramp UV0, normalized HDR into MC LDR; runtime variables/emitter colors/fresnel/UV animation unresolved')
    elif material in ZEN_COLOR:
        texture = binding.get('colorTexture')
        if not texture:
            raise ValueError('Original Zenyatta colored sibling must have its own RGB map')
        data.update(emissive=1, blendMode='additive', resolved=True,
                    renderTexture=save(bake_additive(load(texture)),'color'),
                    limits='Original colored sibling image, static UV0; native emitter size/orientation/timing not evaluated')
    elif material in DRAGON:
        if any(b['register']!=5 for b in data['constantBuffers'] if b['stage']==2):
            raise ValueError('Audited dragon CB5 register changed')
        terms = [rgb_at(data,2,offset) for offset in (144,160)]
        hdr = [(a+b)*.5 for a,b in zip(*terms)]
        mask = load('0c00000000000754')
        data.update(resolved=True, emissive=max(hdr), emissiveColorLinearHDR=hdr,
                    emissiveTerms=[dict(stage=2,offset=o,rgb=c) for o,c in zip((144,160),terms)],
                    emissiveSemanticAuthenticated=False,
                    emissiveTexture=save(bake_additive(mask,hdr,intensity=True),'emission'),
                    shaderEvidence=dict(code='06100000e955e2fd',swizzle='CB5[9].xyz + CB5[10].xyz',permutationAuthenticated=False),
                    limits='Original base RGB + native ramp color terms, interpreted as MC emission; equal ramp weights/static 0754 mask are approximation; native emission semantics and dynamic 581a3da4 ramp unbound')
    elif material in DRAGON_TRAILS:
        data.update(blendMode='skip',reason='Unresolved runtime trail color/ramp; preserved constants and bindings, no grey fallback')
    return data, generated
