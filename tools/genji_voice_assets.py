"""Install the private, hash-pinned OW1/classic Dragonblade recording.

Archive upload dates do not establish the recording's earliest release date.
"""
from modpack.config import paths
import hashlib,json
from pathlib import Path

SOURCE=paths().get('privateAssets')/'ow-early-reference/genji-ow1-dragonblade.ogg'
SHA256='1dcda15f9f4a10451be06679c1b32be73f72b8b7e6983648a3638e02fa2723d5'
PREVIOUS_SHA256='e8787b207de16eb9d8125d8990a241fe0f2098eb3a83f055547b98850ce1c7ae'
PACK='owmc-private-voice'

def prepare(profile,source=SOURCE):
    profile=Path(profile);source=Path(source)
    if not source.is_file():
        print('Optional Genji voice missing; existing game audio remains available.')
        return False
    data=source.read_bytes()
    if hashlib.sha256(data).hexdigest()!=SHA256:raise ValueError('Genji voice asset hash differs')
    pack=profile/'resourcepacks'/PACK
    sound=pack/'assets/owmcguest/sounds/private/genji_dragonblade.ogg'
    if sound.exists() and hashlib.sha256(sound.read_bytes()).hexdigest() not in (SHA256,PREVIOUS_SHA256):
        raise ValueError('Existing private Genji sound differs; preserve it before updating')
    sound.parent.mkdir(parents=True,exist_ok=True);sound.write_bytes(data)
    (pack/'pack.mcmeta').write_text(json.dumps({'pack':{'pack_format':34,'description':'Local OW Dragonblade voice (private)'}}),encoding='utf-8')
    (pack/'assets/owmcguest/sounds.json').write_text(json.dumps({'genji.dragonblade':{'sounds':[{'name':'owmcguest:private/genji_dragonblade','preload':True}]}}),encoding='utf-8')
    (pack/'provenance.json').write_text(json.dumps({'recordingFamily':'OW1/classic original00000001FEDD (not successor000000059BBD)','guid':'00000001FEDD.0B2','sha256':SHA256,'source':str(source),'sourcePage':'https://theomnictalking.altervista.org/en/hero-dialogues/genji/','catalogUploadDateIsNotRecordingDate':True,'exact2015RecordingDateVerified':False},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    options=profile/'options.txt';lines=options.read_text(encoding='utf-8').splitlines()
    rows=[i for i,line in enumerate(lines) if line.startswith('resourcePacks:')]
    if len(rows)>1:raise ValueError('Duplicate resourcePacks option')
    packs=json.loads(lines[rows[0]].split(':',1)[1]) if rows else ['vanilla','fabric']
    name='file/'+PACK
    if name not in packs:packs.append(name)
    entry='resourcePacks:'+json.dumps(packs,separators=(',',':'))
    if rows:lines[rows[0]]=entry
    else:lines.append(entry)
    options.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return True

if __name__=='__main__':
    from launch_minecraft import ROOT
    print(json.dumps({'installed':prepare(paths().get('profile'))}))
