"""Hash-pinned private OW hit/elimination pack; audio is never bundled in the mod."""
from modpack.config import paths
from pathlib import Path
import hashlib
import json

ROOT=paths().get('privateAssets')/'owmc-combat-feedback'
FILES={'hit.ogg':'e328fa1b16a9dad4caab785691172b1a34b21624b77df2b3e0affd715b45bf6c',
       'kill.ogg':'40ef511ec844bc11a77c69a701c7bfbfaafab229da73b31d032f69a7836b89dd'}

def prepare(profile):
    profile=Path(profile)
    if any(not (ROOT/name).is_file() for name in FILES):
        print('Optional private OW combat feedback unavailable.');return False
    pack=profile/'resourcepacks/owmc-private-combat-feedback'
    folder=pack/'assets/owmcguest/sounds/private/combat'
    inputs={}
    for name,pin in FILES.items():
        data=(ROOT/name).read_bytes()
        if hashlib.sha256(data).hexdigest()!=pin:raise ValueError('Private combat audio hash changed: '+name)
        dst=folder/name
        if dst.exists() and dst.read_bytes()!=data:raise ValueError('Preserve modified private combat audio: '+name)
        inputs[name]=data
    provenance=json.loads((ROOT/'source.json').read_text(encoding='utf-8'))
    options=profile/'options.txt';lines=options.read_text(encoding='utf-8').splitlines()
    rows=[i for i,line in enumerate(lines) if line.startswith('resourcePacks:')]
    if len(rows)!=1:raise ValueError('Expected one resource pack option')
    packs=json.loads(lines[rows[0]].split(':',1)[1]);path=pack/'assets/owmcguest/sounds.json'
    sounds=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    folder.mkdir(parents=True,exist_ok=True)
    for name,data in inputs.items():(folder/name).write_bytes(data)
    (pack/'pack.mcmeta').write_text(json.dumps({'pack':{'pack_format':34,'description':'Private classic Overwatch hit/elimination feedback'}}),encoding='utf-8')
    for key,name in {'hit':'hit','elimination':'kill'}.items():
        sounds['combat.'+key]={'sounds':[{'name':'owmcguest:private/combat/'+name,'preload':True}]}
    path.write_text(json.dumps(sounds,indent=2)+'\n',encoding='utf-8')
    (pack/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8')
    name='file/owmc-private-combat-feedback'
    if name not in packs:packs.append(name)
    lines[rows[0]]='resourcePacks:'+json.dumps(packs,separators=(',',':'))
    options.write_text('\n'.join(lines)+'\n',encoding='utf-8');return True
