"""Reproducible explicit selections, plus numeric pose/material audit; no install."""
import json
from pathlib import Path

from build_mesh_pack import CACHE, select_mesh

ROOT = Path(__file__).resolve().parents[1]
JOBS = []


def add(name, root, model, material=None, *, recipes=None, additive=False):
    entity = (('030000000000' if root.startswith('e:') else '040000000000') + root.removeprefix('e:'))
    model = '0d0000000000'+model
    material = '0e000000'+material if material else None
    chain = json.loads((CACHE/entity/'chain.json').read_text(encoding='utf-8'))
    path, selected = select_mesh(CACHE/entity, chain, model, material)
    mesh = json.loads(path.read_text(encoding='utf-8'))
    bounds = [[f(v[i] for v in mesh['positions']) for i in range(3)] for f in (min, max)]
    materials = dict(recipes or {})
    if additive:
        for sub in mesh['submeshes']:
            binding = sub.get('binding', {})
            if binding.get('colorTexture'):
                materials.setdefault(binding['material'], dict(texture=binding['colorTexture'], blend='additive'))
    job = dict(name=name, entity=entity, model=model)
    if material:
        job['material'] = material
    if materials:
        job['materials'] = materials
    job['pose'] = dict(bounds=bounds, originalArraysUnchanged=True,
                       limits='Renderer centering/scale/billboard/beam length are MC presentation adaptations')
    JOBS.append(job)


def main():
    add('pharah-rocket', '0033', '084c')
    add('pharah-flight-glow', '0033', '0801', '4f47ebdc', additive=True)
    add('pharah-impact', '0033', '0801', '1a1a7d5f', additive=True)
    add('pharah-trail', '0033', '07f5', 'd599b3d4', additive=True)
    add('pharah-barrage', '0052', '084c')
    add('pharah-barrage-trail', '0052', '07f5', '6773ddf6', additive=True)
    add('pharah-barrage-impact', '0052', '0801', '811b6b59', additive=True)
    add('pharah-concussive', '010f', '084c')
    add('pharah-concussive-trail', '010f', '07f5', '91c59bd1', additive=True)
    # Refractive 085b uses built-in/dynamic samplers only; no invented shell.
    add('pharah-concussive-impact', '010f', '0801', '9f477a75', additive=True)
    add('mccree-flashbang', '037d', '11d8')
    add('mccree-flash-impact', '037d', '0801', '520140d2', additive=True)
    add('soldier-helix', '072c', '1883')
    helix=json.loads((CACHE/'040000000000072c/0d00000000001883.lod0.mesh.json').read_text(encoding='utf-8'))
    bands=[0 if p[0]<-.09 else 1 if p[0]<.04 else 2 for p in helix['positions']]
    counts=[bands.count(i) for i in range(3)]
    if counts!=[186,186,186] or any(len({bands[i] for i in helix['indices'][at:at+3]})!=1
                                  for at in range(0,len(helix['indices']),3)):
        raise ValueError('Original three-missile partition changed')
    JOBS[-1]['pose']['helixPartVertices']=counts
    add('soldier-helix-trail', '072c', '0801', '40763e21', additive=True)
    add('soldier-biotic', '068a', '1acf', recipes={
        '0e0000000000141d': dict(texture='0c00000000003851', intensity=True, blend='additive')})
    add('soldier-biotic-field', 'e:0b06', '0801', '093b98c0', additive=True)
    add('bastion-tank-shell', '03ce', '0801', '36545914', additive=True)
    add('bastion-tank-trail', '03ce', '07f5', 'cdf08941', additive=True)
    add('winston-projector', '01c2', '0c03')
    add('winston-barrier', '01c3', '0d02', recipes={
        '0e000000000005c6': dict(texture='0c0000000000234f', blend='alpha')})
    add('reinhardt-barrier', '011a', '0a3c', recipes={
        '0e000000000003a5': dict(texture='0c00000000002074', blend='alpha')})
    add('zarya-barrier', '03da', '10d7', recipes={
        '0e00000000000aae': dict(texture='0c0000000000234f', blend='alpha')})
    add('zarya-beam', 'e:0585', '07f5', '023170db', additive=True)
    add('mercy-heal-beam', 'e:01ed', '07f5', 'b6d432d2', recipes={
        '0e000000b6d432d2': dict(texture='0c00000000001344', intensity=True, blend='additive')})
    add('mercy-target-glow', 'e:0198', '0801', '0343c80c', additive=True)
    add('lucio-sound-barrier', 'e:11bf', '2345', '5f47fe48', additive=True)
    add('lucio-sonic', '05ff', '19f2', 'ad76d20e', additive=True)
    add('lucio-sonic-glow', '05ff', '19b6', 'ad36ab78', additive=True)
    add('winston-tesla', 'e:0840', '0e71', '1ce93094', additive=True)
    add('widow-grapple-flash', 'e:0291', '0801', '3ee794c0', additive=True)
    add('symmetra-orb', '022e', '0801', 'a6da5c50', additive=True)
    add('reaper-shadow-start', 'e:028b', '0801', '9f0bd6ab', additive=True)
    add('reaper-shadow-end', 'e:028c', '0801', 'a989a7eb', additive=True)
    add('reaper-wraith', 'e:004a', '0801', 'd0f8daeb', additive=True)
    add('reaper-blossom', 'e:00ac', '0801', '0b24b23c', additive=True)
    add('widow-venom-gas', 'e:00f9', '0801', '3b94cf4a', additive=True)
    add('tracer-blink', 'e:00bb', '0801', '2621b845', additive=True)
    add('genji-dash-wind', 'e:0305', '0801', '13e6d292', additive=True)
    add('mei-freeze-snow', 'e:0b89', '0801', 'a7d83fee', additive=True)
    add('mei-blizzard-shard', 'e:15ce', '28a6', '7f592e0d', additive=True)
    add('roadhog-hook', '03f7', '092a')
    add('widow-hook', '00d3', '0711')
    # Existing clients already consume these names; preserve special colors recipes.
    for name, root, model, material in [
        ('mercy-pistol','0158','0801','d6b19e91'),
        ('dva-pistol','1000','0801','6ccc2cd2'),
        ('roadhog-scrap','029a','07f5','2f8f5991'),
        ('roadhog-secondary','0295','14c0','8caa7d7c'),
        ('roadhog-whole-hog','0405','0801','2e4a449f')]:
        add(name, root, model, material, additive=True)
    next(j for j in JOBS if j['name']=='roadhog-whole-hog')['materials']={
        '0e0000002e4a449f': dict(texture='0c00000000000510', intensity=True, blend='additive')}
    for name, root, model, material in [
        ('symmetra-beam','e:02e7','07f5','f90a566c'),
        # The sphere uses unresolved refraction targets. Use the same effect's
        # actual colored sibling, and hand off a billboard call for this layer.
        ('symmetra-shield','e:0401','0801','82141096'),
        ('symmetra-turret','0250','0c02',None),
        ('symmetra-teleporter','0241','0c16',None)]:
        add(name, root, model, material, additive=material is not None)
    # Keep the colors thread's authenticated recipes intact for the projectiles
    # this inventory covers. Hanzo is outside this thread's renderer scope.
    colors=json.loads((ROOT/'tools/ow-colors-pack-jobs.json').read_text(encoding='utf-8'))
    for job in colors:
        if job['name'].startswith(('zenyatta-', 'zarya-')):
            add(job['name'], job['entity'][-4:], job['model'][-4:],
                job.get('material','')[8:] or None)
    path = ROOT/'tools/models-20261026-pack-jobs.json'
    path.write_text(json.dumps(JOBS, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    renderer = ROOT/'guest/src/client/java/lab/owmcguest/OriginalWorldRenderer.java'
    text = renderer.read_text(encoding='utf-8')
    start = text.index('    static {')
    end = text.index('    private record Source', start)
    lines = ['    static {']
    for job in JOBS:
        lo, hi = job['pose']['bounds']
        values = [(a+b)/2 for a,b in zip(lo,hi)] + [b-a for a,b in zip(lo,hi)]
        numbers = ','.join(format(v,'.9g')+'f' for v in values)
        lines.append('        CENTERS.put('+json.dumps(job['name'])+',new Spec('+numbers+'));')
    lines.append('    }\n')
    renderer.write_text(text[:start]+'\n'.join(lines)+text[end:], encoding='utf-8')
    print(json.dumps(dict(jobs=len(JOBS), output=str(path))))


if __name__ == '__main__':
    main()
