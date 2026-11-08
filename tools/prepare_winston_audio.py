"""Prepare W3 audio on D: only; no game process, profile installation or playback.

Classic Mandarin lines are explicitly user-approved; their24919 date is unverified.
Four SFX are hash-pinned media from the owned24919 archive. Audio never enters JAR.
"""
from __future__ import annotations
import argparse,hashlib,json,re,shutil,struct,subprocess,urllib.request
from pathlib import Path
from modpack.config import ROOT,paths
from voice_download import approved_url,ApprovedRedirect,is_mp3

RECIPE=ROOT/'tools/winston-audio-assets.json'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def member(root,relative):
    p=(root/relative).resolve()
    if not p.is_relative_to(root.resolve()):raise ValueError('Asset path escapes root')
    return p
def copy_guard(source,target,pin):
    if sha(source)!=pin:raise ValueError('Source SHA256 changed: '+str(source))
    if target.exists():
        if sha(target)!=pin:raise ValueError('Preserve changed private audio: '+str(target))
        return
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    if sha(target)!=pin:raise ValueError('Private copy readback mismatch')
def encode(ffmpeg,source,target):
    subprocess.run([str(ffmpeg),'-v','error','-nostdin','-i',str(source),'-map_metadata','-1','-fflags','+bitexact','-flags:a','+bitexact',
                    '-c:a','libvorbis','-q:a','5','-y',str(target)],capture_output=True,timeout=30,check=True)
def audio_packets(p):
    raw=p.read_bytes();at=0;packet=bytearray();packets=[];last=0
    while at<len(raw):
        if at+27>len(raw) or raw[at:at+4]!=b'OggS':raise ValueError('OGG page bounds')
        last=struct.unpack_from('<q',raw,at+6)[0];n=raw[at+26];sizes=raw[at+27:at+27+n];pos=at+27+n
        for size in sizes:
            if pos+size>len(raw):raise ValueError('OGG packet bounds')
            packet+=raw[pos:pos+size];pos+=size
            if size<255:packets.append(bytes(packet));packet.clear()
        at=pos
    if packet or len(packets)<4 or packets[0][:7]!=b'\x01vorbis':raise ValueError('Vorbis packets')
    return {'audioPacketSha256':hashlib.sha256(b''.join(packets[3:])).hexdigest(),'audioPacketCount':len(packets)-3,
            'sampleRate':struct.unpack_from('<I',packets[0],12)[0],'lastGranule':last}
def repage(ffmpeg,source,target):
    before=audio_packets(source)
    subprocess.run([str(ffmpeg),'-v','error','-nostdin','-fflags','+genpts','-i',str(source),'-map_metadata','-1','-fflags','+bitexact',
                    '-c:a','copy','-y',str(target)],capture_output=True,timeout=30,check=True)
    after=audio_packets(target)
    if before['audioPacketSha256']!=after['audioPacketSha256'] or before['audioPacketCount']!=after['audioPacketCount'] or after['lastGranule']<=0:raise ValueError('Lossless OGG repaging failed')
    return {'before':before,'after':after,'audioUnchanged':True}
def configure(root):
    file=ROOT/'config/launcher.json';before=file.read_bytes();text=before.decode('utf-8-sig');data=json.loads(text)
    selected=root.relative_to(ROOT).as_posix() if root.is_relative_to(ROOT) else str(root)
    block=re.search(r'"paths"\s*:\s*\{([^{}]*)\}',text)
    if not block:raise ValueError('Expected flat launcher paths object; preserve other configuration')
    body=block.group(1);value=json.dumps(selected,ensure_ascii=False);found=re.search(r'("heroVoiceAssets"\s*:\s*)("(?:\\.|[^"\\])*")',body)
    if found:
        start=block.start(1)+found.start(2);end=block.start(1)+found.end(2);after=text[:start]+value+text[end:]
    else:
        nl='\r\n' if '\r\n' in text else '\n';tail=len(body.rstrip());separator=',' if body.strip() else ''
        start=block.start(1)+tail;after=text[:start]+separator+nl+'    "heroVoiceAssets": '+value+text[start:]
    result=json.loads(after);expected=json.loads(text);expected.setdefault('paths',{})['heroVoiceAssets']=selected
    if result!=expected:raise ValueError('Only heroVoiceAssets may change')
    if file.read_bytes()!=before:raise ValueError('Launcher config changed concurrently')
    file.write_bytes((b'\xef\xbb\xbf' if before.startswith(b'\xef\xbb\xbf') else b'')+after.encode('utf-8'))
    return {'beforeSha256':hashlib.sha256(before).hexdigest(),'afterSha256':sha(file),'onlyChangedPath':'paths.heroVoiceAssets','value':selected}

def prepare(args):
    config=paths();donor=(args.donor or config.get('heroVoiceAssets')).resolve();root=args.output.resolve()
    if root.drive.upper()!='D:':raise ValueError('W3 writes audio only on D:')
    recipe=load(RECIPE);donor_manifest=donor/'manifest.json';baseline_bytes=donor_manifest.read_bytes();baseline=load(donor_manifest)
    baseline=baseline.get('entries',baseline)
    if not args.apply_private:return {'dryRun':True,'donor':str(donor),'output':str(root),'existingEntries':len(baseline),'newClips':7}
    root.mkdir(parents=True,exist_ok=True);(root/'ogg').mkdir(exist_ok=True);ffmpeg=config.get('ffmpeg')
    if sha(ffmpeg)!=recipe['ffmpegSha256']:raise ValueError('Pinned ffmpeg changed')
    merged={};cache_reused=converted=0
    profile_cache=config.get('profile')/'resourcepacks/owmc-private-full-voice/assets/owmcguest/sounds/private/full'
    for h,row in baseline.items():
        if not re.fullmatch('[0-9a-f]{32}',h):raise ValueError('Invalid existing voice identity')
        direct=row.get('format')=='ogg';source=member(donor,row['file'] if direct else row['hero']+'/'+h+'.mp3')
        if sha(source)!=row['sha256']:raise ValueError('Existing source changed: '+h)
        target=root/'ogg'/(h+'.ogg');original=row.get('originalMp3Sha256',row['sha256'])
        mp3=donor/row['hero']/(h+'.mp3')
        if mp3.is_file():copy_guard(mp3,root/row['hero']/(h+'.mp3'),sha(mp3))
        if direct:copy_guard(source,target,row['sha256'])
        elif target.exists():
            prior=load(root/'manifest.json') if (root/'manifest.json').exists() else {}
            old=prior.get(h,{})
            if old.get('originalMp3Sha256')!=original or old.get('sha256')!=sha(target):raise ValueError('Preserve unreceipted converted audio '+h)
        else:
            cache=profile_cache/(h+'.ogg');receipt=profile_cache/(h+'.json');adopt=False
            if cache.is_file() and receipt.is_file():
                proof=load(receipt);adopt=proof.get('sourceSha256')==original and proof.get('oggSha256')==sha(cache)
            if adopt:copy_guard(cache,target,proof['oggSha256']);cache_reused+=1
            else:encode(ffmpeg,source,target);converted+=1
        merged[h]={**row,'format':'ogg','file':'ogg/'+h+'.ogg','sha256':sha(target)}
        if not direct or 'originalMp3Sha256' in row:merged[h]['originalMp3Sha256']=original
    # Keep the metadata-only legacy hash lookup consistent with the new voice root.
    legacy=donor.parent/'thnu-three/manifest.json'
    if legacy.is_file():copy_guard(legacy,root.parent/'thnu-three/manifest.json',sha(legacy))
    for row in recipe['voices']:
        h=row['hash'];mp3=root/'winston'/(h+'.mp3');cached=args.chinese_cache/(h+'.mp3') if args.chinese_cache else mp3
        if not mp3.exists():
            if cached.exists():copy_guard(cached,mp3,row['sha256'])
            else:
                if not approved_url(row):raise ValueError('Unapproved Chinese source URL')
                req=urllib.request.Request(row['url'],headers={'User-Agent':'OWMC-private-audio'})
                with urllib.request.build_opener(ApprovedRedirect(row)).open(req,timeout=30) as response:raw=response.read(5_000_001)
                if len(raw)>5_000_000 or not is_mp3(raw) or hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('Chinese source changed')
                mp3.parent.mkdir(parents=True,exist_ok=True);mp3.write_bytes(raw)
        if sha(mp3)!=row['sha256']:raise ValueError('Chinese MP3 pin differs')
        target=root/'ogg'/(h+'.ogg')
        if not target.exists():encode(ffmpeg,mp3,target)
        if sha(target)!=row['oggSha256']:raise ValueError('Chinese OGG pin differs')
        merged[h]={**row,'format':'ogg','file':'ogg/'+h+'.ogg','sha256':row['oggSha256'],'originalMp3Sha256':row['sha256']}
    for row in recipe['sfx']:
        h=row['hash'];target=root/'ogg'/(h+'.ogg')
        if target.exists() and sha(target)==row.get('decodedOggSha256'):
            temporary=target.with_name(h+'.repage.ogg');repage(ffmpeg,target,temporary)
            if sha(temporary)!=row['oggSha256'] or sha(target)!=row['decodedOggSha256']:raise ValueError('Preserve modified original SFX')
            temporary.replace(target)
        if not target.exists():
            cached=args.sfx_cache/(row['media']+'.ogg') if args.sfx_cache else None
            if cached and cached.is_file():
                if sha(cached)!=row['decodedOggSha256']:raise ValueError('Decoded native OGG changed')
                repage(ffmpeg,cached,target)
            else:
                from ow_asset_chain import Archive
                import voice_wem_decode as decoder
                archive=Archive('winston-audio');raw=archive.fetch(row['ckey'],row['media']+'.wem')
                if hashlib.md5(raw).hexdigest()!=row['ckey'] or hashlib.sha256(raw).hexdigest()!=row['sourceSha256']:raise ValueError('Original24919 media changed')
                exe=ROOT/'research/voice-20261027-feedback6/wem-decoder/voice-wem-decode.exe'
                if not exe.is_file() or sha(exe)!=recipe['decoderSha256']:raise ValueError('Existing pinned offline WEM decoder required')
                decoded=archive.out/(row['media']+'.ogg')
                if not decoded.exists():decoder.decode(archive.out/(row['media']+'.wem'),decoded,exe)
                if sha(decoded)!=row['decodedOggSha256']:raise ValueError('Decoded native OGG changed')
                repage(ffmpeg,decoded,target)
        if sha(target)!=row['oggSha256']:raise ValueError('Original SFX OGG pin differs')
        merged[h]={**row,'format':'ogg','file':'ogg/'+h+'.ogg','sha256':row['oggSha256'],'localOnly':True,'optional':False}
    if donor_manifest.read_bytes()!=baseline_bytes:raise ValueError('Donor manifest changed concurrently')
    # Every actual input is checked; there is no conversion or profile mutation at runtime setup here.
    for h,row in merged.items():
        p=member(root,row['file'])
        if sha(p)!=row['sha256'] or not p.read_bytes().startswith(b'OggS'):raise ValueError('Prepared OGG verification failed '+h)
    manifest=root/'manifest.json';manifest.write_text(json.dumps(merged,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
    proof={'voiceRoot':str(root),'entries':len(merged),'newChineseVoices':3,'newOriginalSfx':4,'reusedProfileOggs':cache_reused,'convertedLegacyMp3s':converted,
           'donorRoot':str(donor),'donorManifestSha256':hashlib.sha256(baseline_bytes).hexdigest(),'donorManifestUnchanged':donor_manifest.read_bytes()==baseline_bytes,
           'manifestSha256':sha(manifest),'recipeSha256':sha(RECIPE),'gameActions':[],'profileWrites':[],'mandarin24919DateVerified':False}
    if args.configure:proof['configuration']=configure(root)
    (root/'winston-preparation-proof.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return proof

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply-private',action='store_true');p.add_argument('--configure',action='store_true')
    p.add_argument('--donor',type=Path);p.add_argument('--output',type=Path,default=ROOT/'private-assets/ow1-zhcn-2016/thnu-full')
    p.add_argument('--chinese-cache',type=Path);p.add_argument('--sfx-cache',type=Path);p.add_argument('--evidence',type=Path)
    args=p.parse_args();proof=prepare(args)
    if args.evidence:args.evidence.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(proof,ensure_ascii=False))
if __name__=='__main__':main()
