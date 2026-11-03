"""Build the ice entity's DIRECT native model, never a recursively found hero.

Output is explicit and must be new; existing private packs remain available.
"""
import argparse,hashlib,json,shutil
from pathlib import Path
from build_mesh_pack import build,CACHE
from ow_asset_chain import color_binding

ENTITY='0400000000000932'
MODEL='0d00000000002a64'

def prepare(out_root):
    out_root=Path(out_root)
    if (out_root/'mei-pillar').exists():raise FileExistsError('Existing pack retained; choose a new output root')
    chain=json.loads((CACHE/ENTITY/'chain.json').read_text(encoding='utf-8'))
    direct={r['guid'] for r in chain['resources'][ENTITY]['refs']}
    if MODEL not in direct:raise ValueError('Original ice entity no longer references the measured pillar model')
    result=build('mei-pillar',ENTITY,model=MODEL,out_root=out_root)
    folder=out_root/'mei-pillar';source=CACHE/ENTITY
    pack=json.loads((folder/'pack.json').read_text(encoding='utf-8'))
    proof=json.loads((folder/'provenance.json').read_text(encoding='utf-8'))
    # Old cache predates diffuse-slot selection and marks both ice materials
    # ambiguous. Resolve each SAME-ENTITY material's measured diffuse slot;
    # never recolor a hero mesh or use a generic Minecraft ice texture.
    bindings={}
    for previous in proof['materialBindings']:
        binding={**previous,**color_binding(previous['material'],chain['resources'],source)}
        if binding['status']!='bound':raise ValueError('Original ice diffuse unresolved: '+str(binding))
        texture=binding['colorTexture'];filename=binding['textureFile']
        shutil.copy2(source/filename,folder/filename)
        proof['files'][filename]=hashlib.sha256((folder/filename).read_bytes()).hexdigest()
        bindings[binding['material']]=binding
    for group in pack['groups']:group['texture']=bindings[group['material']]['colorTexture']
    pack['materialBindingComplete']=True
    proof['materialBindings']=list(bindings.values())
    (folder/'pack.json').write_text(json.dumps(pack,separators=(',',':'))+'\n',encoding='utf-8')
    proof['files']['pack.json']=hashlib.sha256((folder/'pack.json').read_bytes()).hexdigest()
    (folder/'provenance.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    return {**result,'groups':{g['texture']:len(g['indices'])//3 for g in pack['groups']},
            'diffuseTextures':{m:b['colorTexture'] for m,b in bindings.items()}}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out-root',required=True,type=Path)
    print(json.dumps(prepare(p.parse_args().out_root)))
