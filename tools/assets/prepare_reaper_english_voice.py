"""死神本地英文WEM研究候选；用户接受已验证中文后，本轮不再安装英文。"""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

import numpy as np

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'research/voice-20261027-feedback6'
REVIEW=Path(tempfile.gettempdir())/'owmc-reaper-english-review-20261027'
FFMPEG=Path(os.environ.get('LOCALAPPDATA',''))/'universal-modder/ffmpeg/bin/ffmpeg.exe'


def rank(row):
    run=subprocess.run([str(FFMPEG),'-v','error','-i',row['ogg'],'-t','8','-ac','1','-ar','16000','-f','f32le','pipe:1'],capture_output=True,timeout=20)
    if run.returncode:raise ValueError('Cannot decode candidate OGG')
    x=np.frombuffer(run.stdout,dtype='<f4');hop=160
    if len(x)<hop:return None
    rms=np.sqrt(np.mean(x[:len(x)//hop*hop].reshape(-1,hop)**2,axis=1));smooth=np.convolve(rms,np.ones(5)/5,mode='same')
    active=np.where(smooth>max(1e-5,float(smooth.max())*.08))[0]
    if not len(active):return None
    a,b=int(active[0]),int(active[-1])+1;duration=(b-a)*.01
    if not 1.25<=duration<=4.5:return None
    e=smooth[a:b];mask=e>e.max()*.23
    # Fill tiny within-syllable gaps; this is repetition ranking, NOT speech recognition.
    for i in range(1,len(mask)-6):
        if mask[i-1] and not mask[i]:
            end=next((j for j in range(i,min(i+7,len(mask))) if mask[j]),None)
            if end is not None:mask[i:end]=True
    edges=np.diff(np.r_[False,mask,False].astype(int));starts=np.where(edges==1)[0];ends=np.where(edges==-1)[0]
    parts=[(s,t) for s,t in zip(starts,ends) if t-s>=8]
    seg=[np.interp(np.linspace(0,len(v)-1,80),np.arange(len(v)),v) for v in np.array_split(e,3)]
    similarities=[]
    for u,v in [(seg[0],seg[1]),(seg[1],seg[2]),(seg[0],seg[2])]:
        u=u-u.mean();v=v-v.mean();similarities.append(float(np.dot(u,v)/(np.linalg.norm(u)*np.linalg.norm(v)+1e-12)))
    similarity=float(np.mean(similarities));pulse_score=1-abs(len(parts)-3)/3
    durations=[(t-s)*.01 for s,t in parts];balance=1-float(np.std(durations)/(np.mean(durations)+1e-9)) if durations else -1
    score=4*pulse_score+2*similarity+balance-.15*abs(duration-2.4)
    return dict(row,score=score,activeSeconds=duration,totalSeconds=len(x)/16000,bursts=len(parts),burstSeconds=durations,repetitionCorrelation=similarity,
                languageAutomaticallyConfirmed=False,phraseAutomaticallyConfirmed=False)


def candidates():
    proof=json.loads((EVIDENCE/'reaper-native-clips.json').read_text(encoding='utf-8'))
    with ThreadPoolExecutor(max_workers=4) as pool:ranked=[r for r in pool.map(rank,proof['clips']) if r is not None]
    previous=EVIDENCE/'reaper-candidates.json';old=json.loads(previous.read_text(encoding='utf-8')) if previous.exists() else {}
    rejected=set(old.get('rejectedWems',[]))|{r['wem'] for r in old.get('candidates',[]) if r.get('userRejected')}
    ranked=[r for r in ranked if r['wem'] not in rejected]
    ranked.sort(key=lambda r:r['score'],reverse=True);chosen=ranked[:3];REVIEW.mkdir(parents=True,exist_ok=True)
    for i,row in enumerate(chosen,1):
        target=REVIEW/f'{i:02d}-reaper-native-{row["wem"]}-UNCONFIRMED.mp3'
        run=subprocess.run([str(FFMPEG),'-v','error','-i',row['ogg'],'-ac','1','-ar','48000','-c:a','libmp3lame','-b:a','192k','-f','mp3','pipe:1'],capture_output=True,timeout=20)
        if run.returncode:raise ValueError('Candidate MP3 conversion failed')
        if target.exists() and target.read_bytes()!=run.stdout:raise ValueError('Preserve changed review clip: '+str(target))
        target.write_bytes(run.stdout)
        row['candidate']=i;row['review']=str(target);row['reviewSha256']=hashlib.sha256(target.read_bytes()).hexdigest()
    report=dict(schema=1,source='native owned24919 enUS Reaper voice collection',selection='three-pulse repetition features only; NOT language/phrase confirmation',
                asrUnavailable='private faster_whisper package directory/access denied; no network/model downloads',rejectedWems=sorted(rejected),candidates=chosen)
    (EVIDENCE/'reaper-candidates.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--install',action='store_true',help='已停用：本轮采用已验证中文');a=p.parse_args()
    if a.install:p.error('三个英文候选均已被用户否定；本轮不提供英文安装入口')
    result=candidates();print(json.dumps([dict(candidate=r['candidate'],file=r['review'],bursts=r['bursts'],seconds=r['activeSeconds']) for r in result['candidates']],ensure_ascii=False))
