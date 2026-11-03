"""Offline color/skin pack round trip, generated data stays in ignored cache."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import json
from pathlib import Path

import numpy as np
from PIL import Image

import build_mesh_pack as packer
from ow_asset_chain import Archive

ROOT = Path(__file__).resolve().parents[2]
JOBS = ROOT/'tools/ow-colors-pack-jobs.json'


def main():
    # Check exact offline executable and reader before trusting local extracts.
    archive = Archive('colors-20261026')
    rows = []
    for job in json.loads(JOBS.read_text(encoding='utf-8')):
        result = packer.build(**job,out_root=archive.out/'validation-packs')
        out = Path(result['output'])
        proof = json.loads((out/'provenance.json').read_text())
        pack = json.loads((out/'pack.json').read_text())
        mesh = json.loads(Path(proof['source']).read_text())
        for key in ('positions','normals','uv'):
            assert pack[key]==[c for row in mesh[key] for c in row],key
        assert packer.sha(Path(proof['source']))==proof['sourceSha256']
        triangle_materials=[None]*len(mesh['triangleTextureIds'])
        for submesh in mesh['submeshes']:
            for i in range(submesh['triangleStart'],submesh['triangleStart']+submesh['triangleCount']):
                triangle_materials[i]=submesh.get('binding',{}).get('material')
        expected={}
        for i,t in enumerate(mesh['triangleTextureIds']):
            expected.setdefault((t or 'grey',triangle_materials[i]),[]).extend(mesh['indices'][i*3:i*3+3])
        assert {(g['texture'],g['material']):g['indices'] for g in pack['groups']}==expected
        assert proof['inGameVerified'] is False
        pngs = {}
        for file,digest in proof['files'].items():
            assert packer.sha(out/file)==digest,file
            if file.endswith('-color.png') or file.endswith('-emission.png'):
                with Image.open(out/file) as image:
                    a = np.asarray(image.convert('RGBA'))
                    assert np.all(a[:,:,:3][a[:,:,3]==0]==0),'ONE/ONE transparent edge'
                    pngs[file] = dict(size=list(image.size),meanRGB=a[:,:,:3].mean(axis=(0,1)).tolist(),
                                      nonzeroRGB=int(np.any(a[:,:,:3]!=0,axis=2).sum()))
        skin = pack.get('skin')
        if skin:
            assert skin['weightsUnorm8']==mesh['skin']['weightsUnorm8']
            assert skin['boneIndices']==mesh['skin']['boneIndices']
            assert all(sum(w)==255 for w in skin['weightsUnorm8'])
        rows.append(dict(name=job['name'],vertices=pack['vertices'],
                         triangles=sum(len(g['indices'])//3 for g in pack['groups']),
                         arraysAndHashesVerified=True,groupIndicesVerified=True,skinBones=len(skin['parents']) if skin else 0,
                         materials={g:{k:v for k,v in m.items() if k in ('colorLinearHDR','emissive','emissiveTerms','blendMode','resolved','limits','reason')}
                                    for g,m in pack['materialParameters'].items()},generatedPNGs=pngs))
    evidence = dict(packs=rows,archiveGuardPassed=True,inGameVerified=False,
                    nativeShaderEvaluated=False,nativeAnimationEvaluated=False)
    (archive.out/'pack-audit.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(packs=len(rows),arraysAndHashesVerified=True,
                         skinnedPacks=sum(r['skinBones']>0 for r in rows),inGameVerified=False)))


if __name__=='__main__':
    main()
