"""离线裁剪已下载P10日语参考；试听文件在系统Temp，不进仓库/JAR。仅Claude用--install-private安装。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

SOURCE_SHA256='fff56d05c362f3dd43869b4d32e781aecdb0da3ea41b92e574d7459261578e1d'
START=0.0
END=2.65
RECIPE=f'owmc-hanzo-ja-v1:{SOURCE_SHA256}:{START:.3f}:{END:.3f}'
DERIVED_ID=hashlib.sha256(RECIPE.encode('ascii')).hexdigest()[:32]
LOCAL_ENTRY=dict(hero='hanzo',hash=DERIVED_ID,event='ult_cast',
                 url='https://www.bilibili.com/video/BV1Hs411q779/?p=10',localOnly=True,
                 sourceSha256=SOURCE_SHA256,sourceWindow=[START,END],language='ja')
ROOT=Path(__file__).resolve().parents[1]
ASSETS=Path(os.environ.get('USERPROFILE',str(Path.home())))/'.universal-modder/assets/ow1-zhcn-2016'
OUTPUT=Path(tempfile.gettempdir())/'owmc-voice-review-20261027'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def decode(ffmpeg,path,seconds=None):
    cmd=[str(ffmpeg),'-v','error','-nostdin','-i',str(path)]
    if seconds is not None:cmd+=['-t',str(seconds)]
    return subprocess.run(cmd+['-ac','1','-ar','16000','-f','f32le','pipe:1'],capture_output=True,check=True).stdout


def cut(ffmpeg,source,dest,end):
    temporary=dest.with_name(dest.stem+'.partial.mp3')
    subprocess.run([str(ffmpeg),'-v','error','-nostdin','-i',str(source),'-t',str(end),'-map_metadata','-1',
                    '-ac','1','-ar','24000','-c:a','libmp3lame','-b:a','128k','-id3v2_version','3','-write_xing','1','-y',str(temporary)],check=True)
    if dest.exists():
        if sha(dest)!=sha(temporary):
            temporary.unlink();raise ValueError('保留已修改的试听文件: '+str(dest))
        temporary.unlink()
    else:temporary.replace(dest)


def prepare(install=False,quiet=False,target_manifest=None):
    import numpy as np
    source=ASSETS/'bili-BV1Hs411q779/P10-audio.m4s'
    if sha(source)!=SOURCE_SHA256:raise ValueError('P10 source SHA256 mismatch')
    asr_path=ASSETS/'four-dps-20261023/actual-reference-audio-asr.json'
    asr=json.loads(asr_path.read_text(encoding='utf-8'))['P10-audio.m4s']
    if asr.get('language')!='ja' or asr.get('probability',0)<.8 or not any('我が敵' in r.get('text','') for r in asr['segments']):
        raise ValueError('本地既有ASR证据不匹配，不能自动确认日语')
    ffmpeg=Path(os.environ['LOCALAPPDATA'])/'universal-modder/ffmpeg/bin/ffmpeg.exe'
    marker=OUTPUT/'owmc-owned-voice-review-v1'
    if OUTPUT.exists() and not marker.is_file():raise ValueError('保留无所有权标记的输出目录')
    OUTPUT.mkdir(parents=True,exist_ok=True);marker.write_text('local voice review\n',encoding='utf-8')
    japanese=OUTPUT/'01-hanzo-P10-japanese-0-2p65.mp3'
    cut(ffmpeg,source,japanese,END)
    original=np.frombuffer(decode(ffmpeg,source,END),dtype='<f4')
    derived=np.frombuffer(decode(ffmpeg,japanese),dtype='<f4')
    n=min(len(original),len(derived));scores=[]
    # MP3编码器有约22ms前导延迟；允许±100ms对齐，不降低相关阈值。
    for shift in range(-1600,1601):
        a=original[max(0,shift):min(n,n+shift)].astype(np.float64)
        b=derived[max(0,-shift):min(n,n-shift)].astype(np.float64)
        a-=a.mean();b-=b.mean();scores.append((float(np.dot(a,b)/max(1e-20,np.linalg.norm(a)*np.linalg.norm(b))),shift))
    correlation,shift=max(scores)
    if correlation<.97:raise ValueError('裁剪片段与源PCM相关性不足: '+str(correlation))
    proof=dict(id=DERIVED_ID,source=str(source),sourceSHA256=SOURCE_SHA256,sourceWindow=[START,END],
               candidate=str(japanese),sha256=sha(japanese),bytes=japanese.stat().st_size,
               decodedSeconds=len(derived)/16000,correlation=correlation,shiftSamples=shift,
               languageEvidence=dict(file=str(asr_path),sha256=sha(asr_path),record=asr),
               containsGameEffects=True,languageBasis='existing local ASR + SHA-pinned source + PCM comparison; no new ASR/network',
               listeningCandidates=[str(japanese)])
    roar=ASSETS/'thnu-full/hanzo/7e6b10c991611aff98a6ff24708ab5e9.mp3'
    if roar.is_file():
        if sha(roar)!='157aeb513cee9426c7fd4e07bd8e8aa7c88d4f1ad4ccad88a9019932315035ad':raise ValueError('龙吼源文件SHA256变化')
        preview=OUTPUT/'02-hanzo-7e6-prefix-0-2p65-unconfirmed.mp3';cut(ffmpeg,roar,preview,END)
        proof['listeningCandidates'].append(str(preview))
        proof['roarPrefix']=dict(path=str(preview),language='unconfirmed',note='not the selected voice; no reliable match to P10')
    (OUTPUT/'provenance.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if install:
        manifest_path=Path(target_manifest) if target_manifest is not None else ASSETS/'thnu-full/manifest.json'
        full=manifest_path.parent
        manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
        if 'entries' in manifest:raise ValueError('安装器仅接受当前已认证的扁平manifest')
        destination=full/'hanzo'/(DERIVED_ID+'.mp3')
        if not destination.parent.resolve().is_relative_to(full.resolve()):raise ValueError('保留越出目标目录的素材链接')
        destination.parent.mkdir(parents=True,exist_ok=True)
        if destination.exists() and sha(destination)!=proof['sha256']:raise ValueError('保留已有不同的私有素材')
        if not destination.exists():shutil.copyfile(japanese,destination)
        backup=full/'manifest.before-hanzo-ja-20261027.json'
        if not backup.exists():shutil.copyfile(manifest_path,backup)
        manifest={h:r for h,r in manifest.items() if not (r.get('hero')=='hanzo' and r.get('event')=='ult_cast')}
        manifest[DERIVED_ID]=dict(LOCAL_ENTRY,sha256=proof['sha256'],bytes=proof['bytes'],provenance=proof)
        temporary=manifest_path.with_name('manifest.hanzo-ja.tmp')
        temporary.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');temporary.replace(manifest_path)
    report=ROOT/'research/voice-20261027-feedback3';report.mkdir(parents=True,exist_ok=True)
    (report/'hanzo-japanese-proof.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if not quiet:print(json.dumps({k:proof[k] for k in ['id','candidate','decodedSeconds','correlation','listeningCandidates']},ensure_ascii=False))
    return proof


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--install-private',action='store_true')
    prepare(parser.parse_args().install_private)
