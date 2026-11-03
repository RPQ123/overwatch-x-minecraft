"""只用本机pip缓存的公开wheel与既有Whisper模型；不读受限安装目录、不联网下载。"""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'research/voice-20261027-reaper-en'
RUNTIME=OUT/'asr-runtime'
NEEDED={'faster-whisper','ctranslate2','av','tokenizers','onnxruntime','huggingface-hub','tqdm','hf-xet',
        'fsspec','filelock','packaging','typing-extensions','pyyaml','flatbuffers','protobuf','certifi',
        'anyio','httpx2','httpcore2','idna','h11','click','colorama'}


def runtime():
    wheels=json.loads((OUT/'compatible-wheels.json').read_text(encoding='utf-8'));RUNTIME.mkdir(parents=True,exist_ok=True)
    proof=[]
    for row in wheels:
        if re.sub('[-_.]+','-',row['name']).lower() not in NEEDED:continue
        source=Path(row['file']);pin=hashlib.sha256(source.read_bytes()).hexdigest();proof.append(dict(name=row['name'],version=row['version'],sha256=pin,source=str(source)))
        marker=RUNTIME/('.wheel-'+row['name']+'.sha256')
        if marker.exists() and marker.read_text()==pin:continue
        with zipfile.ZipFile(source) as z:
            for name in z.namelist():
                if not (RUNTIME/name).resolve().is_relative_to(RUNTIME.resolve()):raise ValueError('wheel traversal')
            z.extractall(RUNTIME)
        marker.write_text(pin)
    (OUT/'asr-runtime-provenance.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
    sys.path.insert(0,str(RUNTIME));return RUNTIME


def main(args):
    runtime()
    from faster_whisper import WhisperModel
    models=Path.home()/'.universal-modder/assets/owmc-mccree/asr-model'
    roots=list((models/('models--Systran--faster-whisper-'+args.model)/'snapshots').glob('*/model.bin'))
    if len(roots)!=1:raise ValueError('Existing local model snapshot not found; no downloads allowed')
    model=WhisperModel(str(roots[0].parent),device='cpu',compute_type='int8',cpu_threads=4,local_files_only=True)
    corpus=json.loads(args.corpus.read_text(encoding='utf-8'));clips=corpus['clips']
    result=json.loads(args.output.read_text(encoding='utf-8')) if args.output.exists() else {}
    for i,row in enumerate(clips):
        if row['wem'] not in result:
            segments,info=model.transcribe(row['ogg'],language='en',beam_size=3,condition_on_previous_text=False)
            text=' '.join(s.text.strip() for s in segments);words=re.findall('[a-z]+',text.lower())
            result[row['wem']]=dict(text=text,dieCount=words.count('die'),seconds=info.duration,model=args.model,sourceSha256=row['sourceSha256'])
            args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        if (i+1)%20==0:print('ASR',i+1,'/',len(clips),flush=True)
    best=sorted(result.items(),key=lambda v:(v[1]['dieCount'],v[1]['text'].lower().count('die')),reverse=True)[:8]
    print(json.dumps(dict(total=len(result),best=best),ensure_ascii=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--corpus',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--model',default='tiny.en');main(p.parse_args())
