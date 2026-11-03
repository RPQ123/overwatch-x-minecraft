"""Install the owner's private original voice clips; never bundle them in the JAR."""
from modpack.config import paths
from pathlib import Path
import json,hashlib

ROOT=paths().get('privateAssets')/'owmc-mccree'
FILES={'deadeye.ogg':'c9aa7c6c46ec7d3734dceab1a10772d459802f8295b902574bcaeb1dd229ff43',
       'flashbang.ogg':'293404deb9d8e006991f86122f4892f934d91f060c765d836f73187d064c5452',
       'shot.ogg':'31b3fbf44c4b88dbb5a1db2c91aafa4c6771914595479f8d4b460dd3f42c7e13'}
SOURCES={'deadeye.ogg':'deadeye-zhcn-2016.ogg','flashbang.ogg':'flashbang.ogg','shot.ogg':'deadeye-shot-beta-recorded.ogg'}
PREVIOUS_DEADEYE='8edd442e89e1c583d4c77ec96523bbfe2056e355da90150db7ebe24bc738d2bf'

def prepare(profile):
    profile=Path(profile)
    if any(not (ROOT/SOURCES[name]).is_file() for name in FILES):
        print('Optional private McCree voice assets unavailable; skill behavior remains available.');return False
    pack=profile/'resourcepacks/owmc-private-mccree';folder=pack/'assets/owmcguest/sounds/private/mccree'
    provenance={};inputs={};migrations=[]
    for name,pin in FILES.items():
        source=SOURCES[name];data=(ROOT/source).read_bytes()
        if hashlib.sha256(data).hexdigest()!=pin:raise ValueError('Private McCree voice hash changed: '+name)
        destination=folder/name
        if destination.exists() and hashlib.sha256(destination.read_bytes()).hexdigest()!=pin:
            old=destination.read_bytes()
            if name!='deadeye.ogg' or hashlib.sha256(old).hexdigest()!=PREVIOUS_DEADEYE:raise ValueError('Preserve the existing modified private McCree voice before replacing it')
            backup=pack/'migration-backup/deadeye-english-classic.ogg'
            if backup.exists() and backup.read_bytes()!=old:raise ValueError('Preserve the existing voice migration backup')
            migrations.append((backup,old))
        inputs[name]=data;provenance[name]=json.loads((ROOT/(source[:-4]+'-source.json')).read_text(encoding='utf-8'))
    # A corrupt later gunshot must not partly migrate an earlier voice clip.
    options=profile/'options.txt';lines=options.read_text(encoding='utf-8').splitlines();rows=[i for i,v in enumerate(lines) if v.startswith('resourcePacks:')]
    if len(rows)!=1:raise ValueError('Expected one resource pack option')
    packs=json.loads(lines[rows[0]].split(':',1)[1]);path=pack/'assets/owmcguest/sounds.json';sounds=json.loads(path.read_text()) if path.exists() else {}
    folder.mkdir(parents=True,exist_ok=True)
    for backup,old in migrations:backup.parent.mkdir(exist_ok=True);backup.write_bytes(old)
    for name,data in inputs.items():(folder/name).write_bytes(data)
    (pack/'pack.mcmeta').write_text(json.dumps({'pack':{'pack_format':34,'description':'Private original McCree Flashbang/Deadeye voices'}}),encoding='utf-8')
    for name in FILES:
        key=name[:-4];sounds['mccree.'+key]={'sounds':[{'name':'owmcguest:private/mccree/'+key,'preload':True}]}
    path.write_text(json.dumps(sounds,indent=2)+'\n',encoding='utf-8');(pack/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8')
    name='file/owmc-private-mccree'
    if name not in packs:packs.append(name)
    lines[rows[0]]='resourcePacks:'+json.dumps(packs,separators=(',',':'));options.write_text('\n'.join(lines)+'\n',encoding='utf-8');return True
