"""2361条无字幕候选的纯本地辅助分析。无下载、无在线模型、绝不自动启用播放。

默认只分析32条已存在的音频；--limit 0分析全部本地文件。可选Vosk仅接受存在的模型目录。
时长/能量不能可靠区分死亡、受伤、跳跃，因此声学规则只产生听辨优先级和候选。
"""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
PRIVATE=Path.home()/'.universal-modder/assets/ow1-zhcn-2016/thnu-full'

def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def local_audio(roots,hero,hash_):
    if not re.fullmatch('[a-z0-9]+',hero) or not re.fullmatch('[a-f0-9]{32}',hash_):return None
    for root in roots:
        for path in [root/hero/(hash_+'.mp3'),root/(hash_+'.mp3')]:
            if path.is_file() and path.stat().st_size<=5_000_000:return path
    return None

def decode(ffmpeg,path):
    run=subprocess.run([str(ffmpeg),'-v','error','-nostdin','-i',str(path),'-t','30','-ac','1','-ar','16000',
                        '-f','f32le','pipe:1'],capture_output=True,check=True,timeout=30)
    value=np.frombuffer(run.stdout,dtype='<f4').astype(np.float64)
    if not len(value) or not np.isfinite(value).all():raise ValueError('empty/nonfinite decoded audio')
    return value

def features(value):
    length=len(value);window=400;hop=160
    padded=np.pad(value,(0,max(0,window-length)))
    frames=np.lib.stride_tricks.sliding_window_view(padded,window)[::hop]
    energy=np.sqrt(np.mean(frames*frames,axis=1));threshold=max(.003,float(energy.max())*.12)
    active=energy>threshold;power=np.abs(np.fft.rfft(frames*np.hanning(window),axis=1))**2+1e-12
    frequency=np.fft.rfftfreq(window,1/16000)
    spectrum=power[active].mean(axis=0) if active.any() else power.mean(axis=0)
    flatness=float(np.exp(np.log(spectrum).mean())/spectrum.mean())
    centroid=float((spectrum*frequency).sum()/spectrum.sum())
    zero_cross=float(np.mean(np.signbit(value[1:])!=np.signbit(value[:-1]))) if length>1 else 0
    rms=float(np.sqrt(np.mean(value*value)));active_indices=np.flatnonzero(active)
    envelope=[float(np.sqrt(np.mean(part*part))) if len(part) else 0 for part in np.array_split(value,8)]
    return dict(duration=length/16000,rmsDb=20*math.log10(max(rms,1e-9)),peak=float(np.max(np.abs(value))),
                activeRatio=float(active.mean()),onsetSeconds=float(active_indices[0]*hop/16000) if len(active_indices) else None,
                activeSeconds=float(active.sum()*hop/16000),spectralFlatness=flatness,centroidHz=centroid,
                zeroCrossRate=zero_cross,envelope=envelope,pcmSha256=hashlib.sha256(value.astype('<f4').tobytes()).hexdigest())

def acoustic_bucket(f):
    if f['rmsDb']<-55 or f['activeRatio']<.03:return 'silence_or_very_quiet',.8
    if f['duration']<.55 and f['spectralFlatness']<.6:return 'short_effort_like',.35
    if f['duration']>2 and f['activeRatio']>.6:return 'long_cry_or_continuous_sound',.25
    if f['spectralFlatness']>.65 or f['zeroCrossRate']>.35:return 'noise_or_mechanical_like',.4
    return 'possible_speech_or_tonal_vocal',.3

def distance(a,b):
    # 仅用于同英雄的已听辨参考近邻；相似声学特征不是相同事件的证据。
    va=np.array([math.log(max(.03,a['duration'])),a['activeRatio'],a['centroidHz']/5000,a['spectralFlatness'],a['zeroCrossRate']])
    vb=np.array([math.log(max(.03,b['duration'])),b['activeRatio'],b['centroidHz']/5000,b['spectralFlatness'],b['zeroCrossRate']])
    return float(np.linalg.norm(va-vb))

ASR_RULES=[(re.compile('需要治疗|需要医疗|帮我治疗'),'healing_request'),
           (re.compile('终极技能.*(准备|就绪)|大招.*(准备|就绪)'),'ult_ready'),
           (re.compile('谢谢|你好|集合|收到|了解'),'comm'),
           (re.compile('重新装弹|正在装弹|换弹匣'),'reload')]

def transcribe(model,pcm):
    from vosk import KaldiRecognizer
    recognizer=KaldiRecognizer(model,16000);recognizer.SetWords(True)
    raw=(np.clip(pcm,-1,1)*32767).astype('<i2').tobytes();parts=[]
    for at in range(0,len(raw),16000):
        if recognizer.AcceptWaveform(raw[at:at+16000]):parts.append(json.loads(recognizer.Result()))
    parts.append(json.loads(recognizer.FinalResult()))
    text=''.join(part.get('text','').replace(' ','') for part in parts)
    confidences=[word.get('conf',0) for part in parts for word in part.get('result',[])]
    return text,float(np.mean(confidences)) if confidences else 0

def run(args):
    output=args.output.resolve()
    if not output.is_relative_to((ROOT/'research').resolve()):raise ValueError('输出必须留在research，不写素材目录')
    output.mkdir(parents=True,exist_ok=True)
    roots=[path.resolve() for path in (args.audio_root or [PRIVATE])]
    ffmpeg=args.ffmpeg or Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'AppData/Local')))/'universal-modder/ffmpeg/bin/ffmpeg.exe'
    if not ffmpeg.is_file():raise ValueError('需要已有本地ffmpeg，脚本不会下载安装')
    jobs=json.loads(args.jobs.read_text(encoding='utf-8'))
    model=None
    if args.asr_model:
        if not args.asr_model.is_dir():raise ValueError('--asr-model只能是已存在的本地Vosk模型目录')
        from vosk import Model,SetLogLevel
        SetLogLevel(-1);model=Model(str(args.asr_model.resolve())) # 不传lang/model_name，杜绝自动下载。
    approved=[]
    if args.reviewed_reference:
        for row in json.loads(args.reviewed_reference.read_text(encoding='utf-8')):
            if not row.get('human_verified') or row.get('event') in ['uncertain','skip']:continue
            path=local_audio(roots,row['hero'],row['hash'])
            if path is None or hashlib.sha256(path.read_bytes()).hexdigest()!=row.get('sha256'):continue
            approved.append(dict(row,features=features(decode(ffmpeg,path))))
    rows=[];processed=0
    for job in jobs:
        row=dict(job,event='uncertain',deployment_allowed=False,requires_listen=True)
        path=local_audio(roots,job['hero'],job['hash'])
        if path is None:row['analysis']='missing_local_audio';rows.append(row);continue
        if args.limit and processed>=args.limit:row['analysis']='pending_limit';rows.append(row);continue
        try:
            pcm=decode(ffmpeg,path);f=features(pcm);processed+=1
            bucket,confidence=acoustic_bucket(f)
            row.update(analysis='features_only',path=str(path),sourceSha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                       features=f,acousticBucket=bucket,acousticConfidence=confidence)
            candidates=[ref for ref in approved if ref['hero']==job['hero']]
            if candidates:
                best=min(candidates,key=lambda ref:distance(f,ref['features']))
                exact=f['pcmSha256']==best['features']['pcmSha256']
                row['referenceMatch']=dict(hash=best['hash'],event=best['event'],distance=distance(f,best['features']),exactPcm=exact)
                if exact:row.update(suggested_event=best['event'],suggestion_confidence=.98,analysis='exact_reviewed_reference')
                elif distance(f,best['features'])<.35:row.update(suggested_event=best['event'],suggestion_confidence=.5,analysis='acoustic_neighbour_only')
            if model is not None:
                text,conf=transcribe(model,pcm);row.update(asrText=text,asrConfidence=conf)
                if len(text)>=2 and conf>=.8:
                    for rule,event in ASR_RULES:
                        if rule.search(text):row.update(suggested_event=event,suggestion_confidence=min(.8,conf),analysis='local_asr_candidate');break
            row['reason']='仅提示候选：时长/能量不能决定死亡/痛叫/跳跃；本人、年代、语境和双声仍需听辨'
        except Exception as error:row.update(analysis='error',error=str(error))
        rows.append(row)
    write(output/'review.json',rows)
    write(output/'missing-download-candidates.json',[{k:r[k] for k in ('hero','hash','url')} for r in rows if r['analysis']=='missing_local_audio'])
    summary=dict(total_jobs=len(jobs),processed_local=processed,missing_local=sum(r['analysis']=='missing_local_audio' for r in rows),
                 pending_limit=sum(r['analysis']=='pending_limit' for r in rows),network_used=False,auto_deployed=0,
                 policy='所有event保持uncertain；suggested_event只能供人工审核，不回写classified或播放manifest')
    write(output/'summary.json',summary);print(json.dumps(summary,ensure_ascii=False))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jobs',type=Path,default=ROOT/'research/voice-20261026/unvoiced-jobs.json')
    parser.add_argument('--audio-root',type=Path,action='append')
    parser.add_argument('--output',type=Path,default=ROOT/'research/voice-20261026/unvoiced-analysis')
    parser.add_argument('--ffmpeg',type=Path);parser.add_argument('--asr-model',type=Path)
    parser.add_argument('--reviewed-reference',type=Path);parser.add_argument('--limit',type=int,default=32)
    args=parser.parse_args()
    if args.limit<0:parser.error('--limit必须>=0')
    run(args)
