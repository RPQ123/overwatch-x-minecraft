"""Install private, hash-pinned classic Mandarin callouts above older packs.

Catalogue language tags are imperfect: McCree select is tagged English but its
actual recording/ASR is Mandarin. Recording's exact earliest date is unverified.
"""
from modpack.config import paths
from pathlib import Path
import json,hashlib

SOURCE=paths().get('privateAssets')/'ow1-zhcn-2016/thnu-three'
PACK='owmc-private-early-chinese'
CLIPS={
    'hero.genji.select':('genji-select','a2f929e8bac6f3a822a6b740e23c3375fde8e10758fd25b63b3a86a88e97a41f'),
    'hero.mccree.select':('mccree-select','a0b0bc87cc7afd2fce09a774fcf370f8e6cfd92ba7777099ea3857bdc380539e'),
    'hero.pharah.select':('pharah-select','2af6b6e2c81803e3e41ed34c911e4617c8d48e16c662939ad7b88dcaf742e648'),
    'hero.reaper.select':('reaper-select','89178e53397dbaea9f70d31a1077fead94ae71d0e1dcf2fdb521383d2d6df59e'),
    'hero.soldier76.select':('soldier76-select','a7183e7e72ee4c646e3b7bf5d6fb87b3b25c629a53aba7321ee856bc31927331'),
    'hero.hanzo.select':('hanzo-select','afd48cf4e4ea972552cf3c414a74845e789762f6b32e6c358540c988811d9bc5'),
    'hero.junkrat.select':('junkrat-select','fea610466ce54658d552f6674b573f90017fc0d8b9ac31a91e1ae72788f1b2c3'),
    'hero.mei.select':('mei-select','a8966a26c7eaa0fb631ccf8b01d3fc65430cd92f8d123b54c403c57fd7a04ce0'),
    'hero.torbjorn.select':('torbjorn-select','a84ee14063d5633e198bd6616cbbdc1e6f98c3e40b3331dd3b7923e20726664a'),
    'hero.widowmaker.select':('widowmaker-select','010037e89f439a44091c5387cdb7ec749c4b671e95385b8fcb4994fde3877d81'),
    'hero.dva.select':('dva-select','84c1c42db802af2f53920c984a9a6598e35a2aedb4eb40953cc2efb858b78e28'),
    'hero.reinhardt.select':('reinhardt-select','09af5461a64e20877b0b302b467959f0834fd323fbb79fdcb27bd9abd782ba16'),
    'hero.roadhog.select':('roadhog-select','b19e2d5d4df98cdc439761ee5a4d455ac053698b20cf7d134ddbbc4d2653bb85'),
    'hero.winston.select':('winston-select','7fd25cd341c0c02cb3caf0fd2eac3c50f918973a1038c1b2f32371a293462ab8'),
    'hero.zarya.select':('zarya-select','2202a9b40789cd403380529934168e2c9c9ddea53d9d71e0cc66d4701da6df56'),
    'hero.lucio.select':('lucio-select','4feff027fb7996288a185ce59b77f5a49fe3e3c4f622b42017e683297aebcbdb'),
    'hero.mercy.select':('mercy-select','a5520abda67d13c5e0596e9222cbfd006efd511cb391e7d4fe3fbad9a719943f'),
    'hero.symmetra.select':('symmetra-select','15a6dfb62698f565ba8c870204d78525101df5292225749b3eb1749153ded4aa'),
    'hero.zenyatta.select':('zenyatta-select','3dd22b39cd78d489c5934b54510f55066c27f2d36536ab1a98da2bf51e37d8ed'),
    'genji.dragonblade':('genji-q','4dda8a9489c2d4c92d6a8cd2cc5d8d99efb52dc9e9938833bf8dc94e5b4879a0'),
    'mccree.flashbang':('mccree-e1','1fe06e7bcdf6f72ea43d9e7f411d384aab146568ff82a4f2700e9579e371d910'),
    'pharah.barrage':('pharah-q','7aefc8d777a78550c822fbcb90a337c88bedd7f9d8ed1b0ce4f08bf91aed87b4'),
}

def prepare(profile,source=SOURCE):
    profile=Path(profile);source=Path(source)
    if any(not (source/'selected'/(name+'.ogg')).is_file() for name,_ in CLIPS.values()):
        print('Private early Chinese assets missing; existing callouts preserved.');return False
    # Validate the whole input and existing destination before changing files.
    manifest=json.loads((source/'manifest.json').read_text(encoding='utf-8'))
    pack=profile/'resourcepacks'/PACK;folder=pack/'assets/owmcguest/sounds/private/early_chinese'
    data={}
    for event,(name,pin) in CLIPS.items():
        blob=(source/'selected'/(name+'.ogg')).read_bytes()
        if not blob.startswith(b'OggS') or hashlib.sha256(blob).hexdigest()!=pin:raise ValueError('Chinese voice hash differs: '+event)
        dest=folder/(name+'.ogg')
        if dest.exists() and dest.read_bytes()!=blob:raise ValueError('Preserve modified private voice: '+event)
        data[name]=blob
    # User explicitly allows original Japanese/Chinese Dragonblade variants.
    from genji_voice_assets import SHA256 as japanese_pin
    japanese=profile/'resourcepacks/owmc-private-voice/assets/owmcguest/sounds/private/genji_dragonblade.ogg'
    if japanese.exists() and hashlib.sha256(japanese.read_bytes()).hexdigest()!=japanese_pin:
        raise ValueError('Preserve modified original Japanese Dragonblade recording')
    options=profile/'options.txt';lines=options.read_text(encoding='utf-8').splitlines();indices=[i for i,v in enumerate(lines) if v.startswith('resourcePacks:')]
    if len(indices)!=1:raise ValueError('Expected one resourcePacks option')
    packs=json.loads(lines[indices[0]].split(':',1)[1]);key='file/'+PACK
    # Last pack has priority; repeat preparation must not duplicate it.
    packs=[v for v in packs if v!=key]+[key]
    provenance={event:{**manifest[name],'convertedSha256':pin,'voiceFamily':'OW1/classic Mandarin, exact earliest date unverified','earliestRecordingDateVerified':False} for event,(name,pin) in CLIPS.items()}
    folder.mkdir(parents=True,exist_ok=True)
    for name,blob in data.items():(folder/(name+'.ogg')).write_bytes(blob)
    (pack/'pack.mcmeta').write_text(json.dumps({'pack':{'pack_format':34,'description':'Private OW1 spoken roster callouts; Tracer/Bastion selection muted'}}),encoding='utf-8')
    sounds={event:{'replace':True,'sounds':[{'name':'owmcguest:private/early_chinese/'+name,'preload':True}]} for event,(name,_) in CLIPS.items()}
    if japanese.is_file() and 'genji.dragonblade' in sounds:
        sounds['genji.dragonblade']['sounds'].append({'name':'owmcguest:private/genji_dragonblade','preload':True})
        provenance['genji.dragonblade']['randomVariants']=['classic Mandarin','original OW1 Japanese 00000001FEDD.0B2']
    (pack/'assets/owmcguest/sounds.json').write_text(json.dumps(sounds,indent=2)+'\n',encoding='utf-8')
    (pack/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8')
    lines[indices[0]]='resourcePacks:'+json.dumps(packs,separators=(',',':'));options.write_text('\n'.join(lines)+'\n',encoding='utf-8');return True
