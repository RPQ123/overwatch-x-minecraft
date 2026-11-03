"""本地24919/enUS死神语音集合→WEM→OGG→本地tiny.en ASR；禁止模型下载。"""

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
import re
import struct
import sys

import ow_asset_chain as ow
import voice_wem_decode as decoder

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'research/voice-20261027-feedback6'
SPEECH='Manifest\\Win_SPWin_speech_RCN_LenUS_EExt.apm'
SPEECH_SHA='4a8f8e3e4278d98b34272c8010fe74ce07427c12815da715d0bdd8a0a1ad2ce4'


def refs(raw,prefix):
    # DUTS嵌入实例含字节字段，资源GUID并非都DWORD对齐；按字节扫描后再以APM/MD5验证。
    return sorted({f'{struct.unpack_from("<Q",raw,i)[0]:016x}' for i in range(len(raw)-7)
                   if f'{struct.unpack_from("<Q",raw,i)[0]:016x}'.startswith(prefix)})


def prepare():
    OUT.mkdir(parents=True,exist_ok=True);archive=ow.Archive('reaper-voice-20261027')
    manifest=archive.fetch(SPEECH,'manifest-speech-enus.apm')
    if hashlib.sha256(manifest).hexdigest()!=SPEECH_SHA:raise ValueError('Owned enUS speech manifest changed')
    versions=ow.manifest_packages(manifest)
    for version in versions:
        if version['guid'] in {'02e0000000000002','0400000000000022'}:archive.load_package_version(version)
    speech_records=dict(archive.records)
    # 主包的WEM记录已由既有资产链缓存；不依赖DataTool的CASC初始化/远端keyring。
    index=OUT/'cached-resource-index.json'
    if not index.is_file():
        # 仅复用SHA钉住主manifest中声明的APM内容，不遍历/下载远端keyring。
        versions={v['ckey']:v for rows in archive.manifest_rows.values() for v in rows};seen=set();records={}
        for path in ow.CACHE.glob('*/*.apm'):
            body=path.read_bytes();key=hashlib.md5(body).hexdigest()
            if key in seen or key not in versions or len(body)!=versions[key]['bytes']:continue
            seen.add(key)
            try:records.update(ow.package_records(body))
            except ValueError:continue
        index.write_text(json.dumps(records),encoding='utf-8')
    archive.records={**json.loads(index.read_text(encoding='utf-8')),**speech_records}
    def fetch(guid):
        row=archive.records[guid];raw=archive.fetch(row['ckey'],guid+'.bin')
        if len(raw)!=row['bytes'] or hashlib.md5(raw).hexdigest()!=row['ckey']:raise ValueError('CASC resource content-key mismatch')
        return raw
    voice='07a0000000000001';raw=fetch(voice);definitions=refs(raw,'0590')
    # 本机CascLib的独立CLI打开不能并行；顺序读取，避免storage open失败。
    with ThreadPoolExecutor(max_workers=1) as pool:
        definitions_raw=list(pool.map(fetch,definitions))
    mapping=[]
    for definition,body in zip(definitions,definitions_raw):
        for wem in refs(body,'08d0'):
            if wem not in archive.records:raise ValueError('Missing original WEM declaration '+wem)
            mapping.append(dict(definition=definition,wem=wem,**archive.records[wem]))
    unique={r['wem']:r for r in mapping}
    with ThreadPoolExecutor(max_workers=1) as pool:list(pool.map(fetch,unique))
    exe=decoder.build();decoded=OUT/'decoded';decoded.mkdir(exist_ok=True)
    for row in unique.values():
        target=decoded/(row['wem']+'.ogg');source=archive.out/(row['wem']+'.bin')
        if not target.exists():decoder.decode(source,target,exe)
        row.update(source=str(source),sourceSha256=hashlib.sha256(source.read_bytes()).hexdigest(),ogg=str(target))
    proof=dict(schema=1,clientBuild=24919,locale='enUS',speechManifestSha256=SPEECH_SHA,voiceSet=voice,
               voiceSetSha256=hashlib.sha256(raw).hexdigest(),definitions=len(definitions),clips=list(unique.values()))
    (OUT/'reaper-native-clips.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    return proof


def transcribe(proof):
    toolchain=Path.home()/'.universal-modder/toolchains/mccree-asr';sys.path.insert(0,str(toolchain))
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
    from faster_whisper import WhisperModel
    models=Path.home()/'.universal-modder/assets/owmc-mccree/asr-model/models--Systran--faster-whisper-tiny.en/snapshots'
    paths=list(models.glob('*/model.bin'))
    if len(paths)!=1:raise ValueError('Need exactly one existing tiny.en snapshot; never download')
    model=WhisperModel(str(paths[0].parent),device='cpu',compute_type='int8',cpu_threads=4,local_files_only=True)
    dest=OUT/'reaper-native-asr.json';records=json.loads(dest.read_text(encoding='utf-8')) if dest.exists() else {}
    for i,row in enumerate(proof['clips']):
        if row['wem'] not in records:
            segments,info=model.transcribe(row['ogg'],language='en',beam_size=3,condition_on_previous_text=False)
            text=' '.join(s.text.strip() for s in segments);words=re.findall('[a-z]+',text.lower())
            records[row['wem']]=dict(text=text,dieCount=words.count('die'),duration=info.duration,model=str(paths[0].parent))
            dest.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        if (i+1)%20==0:print('ASR',i+1,'/',len(proof['clips']),flush=True)
    matches=sorted(records.items(),key=lambda p:(p[1]['dieCount'],p[1]['text'].lower().count('die')),reverse=True)[:3]
    print(json.dumps(dict(clips=len(records),best=matches),ensure_ascii=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prepare-only',action='store_true');a=p.parse_args()
    proof=prepare();print('decoded native Reaper enUS clips:',len(proof['clips']),flush=True)
    if not a.prepare_only:transcribe(proof)
