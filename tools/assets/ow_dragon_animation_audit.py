"""Bounded native dragon clip-reference audit; never invent a swim clip."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import hashlib
import json
import struct

from ow_asset_chain import Archive


def main():
    archive=Archive('colors-20261026')
    archive.load_package('02e0000000000005')
    archive.load_package('0400000000000141')
    rows=[]
    for guid in ('0580000000000132','040000000000033b','040000000000033c',
                 '0400000000000237','0400000000000239'):
        record=archive.records.get(guid)
        if not record:
            rows.append(dict(guid=guid,status='undeclared-in-bounded-packages'));continue
        raw=archive.fetch(record['ckey'],guid+'.raw')
        if len(raw)!=record['bytes'] or hashlib.md5(raw).hexdigest()!=record['ckey']:
            raise ValueError('Dragon animation source CKey mismatch')
        references=[]
        for offset in range(0,len(raw)-7,8):
            target=f'{struct.unpack_from("<Q",raw,offset)[0]:016x}'
            if target.startswith('0a00') and target in archive.records:
                references.append(dict(offset=offset,guid=target,kind='registered-006-animation-candidate'))
        rows.append(dict(guid=guid,sha256=hashlib.sha256(raw).hexdigest(),
                         bytes=len(raw),animationCandidates=references))
    result=dict(sources=rows,nativeAnimationEvaluated=False,
                scope='Direct aligned registered type006 references in graph0132 and its four dragon entities only; not a global absence proof',
                fallback='Native 67-joint bind skeleton and UNORM8 weights, MC-authored spine travelling wave')
    (archive.out/'dragon-animation-audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(sources=len(rows),clipCandidates=sum(len(r.get('animationCandidates',[])) for r in rows),nativeAnimationEvaluated=False)))


if __name__=='__main__':main()
