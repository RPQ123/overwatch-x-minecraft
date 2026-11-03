"""Private hash-pinned OW1 Mandarin skill callouts; no audio enters the JAR."""
from modpack.config import paths
from pathlib import Path
import json,hashlib

SOURCE=paths().get('privateAssets')/'ow1-zhcn-2016/four-dps-20261023'
PACK='owmc-private-four-dps'
CLIPS={
    'reaper.shadow':[('reaper-step-a','c6e202cc1db06f3a94947f07615bfbbe5ae418a487e0556d4818567c1dca8ce5')],
    'reaper.blossom':[('reaper-blossom-ally','1d5aff1b7998a24aa681627cb26d21f4397d427b51f1c9a6524cb61523e031da')],
    'tracer.pulse':[
        ('tracer-pulse-a','7a65eb50bafac99eb4d3c4b4044b32d0c62e57eb4135c37f0e04bdcb7eccbb21'),
        ('tracer-pulse-b','1674bb72a2012897fefa3fbe83de631722b66dea9502f9af29fc8ca4db66e530')],
    'soldier76.bioticfield':[
        ('soldier76-heal-a','4e1d7eae0ac05981597c7062c9031ef1bd9f748159333cc78d5423c9e7bfc22c'),
        ('soldier76-heal-b','27a0a41d94502431de5dbdf2a5256ba157eea0f1c0c0067ab4e0d1f291f5e033'),
        ('soldier76-heal-c','6ec5e9a9b0b322a3aad834286514bbcc80f08c1866a30da45bed7f5d58e10652')],
    'soldier76.visor':[('soldier76-visor','3be69ec37966df2ba8da56ed3557bcd180c2b1f7c6d0fac9cf06103f858a7079')],
    'soldier76.bioticfield.loop':[('soldier76-field-loop','252d57fc9817bb77308e8ca786658a1e337ee30f3d1c75ae9f4739ade236c828')],
}
def prepare(profile,source=SOURCE):
    profile=Path(profile);source=Path(source)
    if not (source/'manifest.json').is_file():return False
    manifest=json.loads((source/'manifest.json').read_text(encoding='utf-8'))
    pack=profile/'resourcepacks'/PACK;folder=pack/'assets/owmcguest/sounds/private/four_dps';data={};provenance={}
    for event,clips in CLIPS.items():
        for name,pin in clips:
            file=source/(name+'.ogg')
            if not file.is_file():return False
            blob=file.read_bytes()
            if not blob.startswith(b'OggS') or hashlib.sha256(blob).hexdigest()!=pin:raise ValueError('Private skill voice hash differs: '+name)
            dest=folder/file.name
            if dest.exists() and dest.read_bytes()!=blob:raise ValueError('Preserve modified skill voice: '+name)
            data[name]=blob;provenance[name]={**manifest[name],'event':event,'convertedSha256':pin,'voiceFamily':manifest[name].get('voiceFamily','OW1 Mandarin; exact earliest recording date unverified')}
    options=profile/'options.txt';lines=options.read_text(encoding='utf-8').splitlines();indices=[i for i,v in enumerate(lines) if v.startswith('resourcePacks:')]
    if len(indices)!=1:raise ValueError('Expected one resourcePacks option')
    index=indices[0];packs=json.loads(lines[index].split(':',1)[1]);key='file/'+PACK;packs=[v for v in packs if v!=key]+[key]
    sounds={event:{'replace':True,'sounds':[{'name':'owmcguest:private/four_dps/'+name,'preload':True} for name,_ in clips]} for event,clips in CLIPS.items()}
    folder.mkdir(parents=True,exist_ok=True)
    for name,blob in data.items():(folder/(name+'.ogg')).write_bytes(blob)
    (pack/'pack.mcmeta').write_text(json.dumps({'pack':{'pack_format':34,'description':'Private classic Mandarin skill callouts'}}),encoding='utf-8')
    (pack/'assets/owmcguest/sounds.json').write_text(json.dumps(sounds,indent=2)+'\n',encoding='utf-8')
    (pack/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8')
    lines[index]='resourcePacks:'+json.dumps(packs,separators=(',',':'));options.write_text('\n'.join(lines)+'\n',encoding='utf-8');return True
