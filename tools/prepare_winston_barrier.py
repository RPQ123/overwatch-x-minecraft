"""W5: original24919 hex sampler, private D: mesh package only; no game/process."""
from pathlib import Path
import argparse,hashlib,json,shutil
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
SOURCE_SHA='8784fbf22db68c26d4fb07f55c1349d954287eee39e9bf8916d5ec117c5ccf45'
GRID='0c0000000000116e.png'
GRID_SHA='d45c2a313d4994a09ab338f7e334aef52be854e5b49478031f12775694a2ce50'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def prepare(apply=False):
    config=json.loads((ROOT/'config/launcher.json').read_text(encoding='utf-8'))
    mesh=Path(config['paths']['meshAssets']);mesh=(ROOT/mesh).resolve() if not mesh.is_absolute() else mesh.resolve()
    if mesh.drive.upper()!='D:':raise ValueError('Private asset root must stay on D:')
    source=mesh/'winston-barrier';target=mesh/'winston-barrier-w5'
    if sha(source/'pack.json')!=SOURCE_SHA or sha(source/GRID)!=GRID_SHA:raise ValueError('Original Winston pack/grid SHA differs')
    d=json.loads((source/'pack.json').read_text(encoding='utf-8'));proof=json.loads((source/'provenance.json').read_text(encoding='utf-8'))
    for f,h in proof['files'].items():
        p=(source/f).resolve()
        if not p.is_relative_to(source.resolve()) or sha(p)!=h:raise ValueError('Original private file hash/path differs: '+f)
    if proof['clientBuild']!='0.8.0.24919' or d['entity']!='04000000000001c3' or d['model']!='0d00000000000d02':raise ValueError('Original barrier identity')
    with Image.open(source/GRID) as im:
        if im.size!=(256,256):raise ValueError('Original hex texture dimensions')
    result={'originalBuild':proof['clientBuild'],'sourcePackSha256':SOURCE_SHA,'gridResource':'0c0000000000116e',
        'gridPayload':'032000010000116e','gridSha256':GRID_SHA,'oldCrackSampler':'0c0000000000234f',
        'material':'0e000000000005c6','shaderSource':'0e10000000000032','privateRoot':str(target),
        'nativeShaderExecuted':False,'mcApproximation':{'blue':[.08,.30,1.0],'bodyAlpha':.16,'gridRepeats':8,'gridGain':.42},
        'originalConstantBufferFirstVector':[0,0,1,.5],'constantBufferColorSemanticsCertified':False}
    if not apply:return result
    if target.exists():
        previous=json.loads((target/'provenance.json').read_text(encoding='utf-8'))
        if previous.get('w5',{}).get('sourcePackSha256')!=SOURCE_SHA:raise ValueError('Refusing to replace a foreign private package')
    target.mkdir(parents=True,exist_ok=True)
    for f in proof['files']:
        if f!='pack.json':shutil.copy2(source/f,target/f)
    Image.new('RGBA',(1,1),(255,255,255,255)).save(target/'w5-flat-white.png')
    d['name']='winston-barrier-w5';d['winstonBarrierBaseTexture']='w5-flat-white.png'
    for group in d['groups']:group['texture']=GRID[:-4]
    material=d['materialParameters']['0e000000000005c6']
    material.update(renderTexture=GRID,emissive=1,blendMode='additive',resolved=True,nativeShaderEvaluated=False,approximation=True,
        limits='Original24919 BC4 hex sampler; MC blue/alpha/UV-repeat/Fresnel adaptation, no native GPU shader execution')
    d['winstonBarrierStyle']=result
    (target/'pack.json').write_text(json.dumps(d,separators=(',',':'))+'\n',encoding='utf-8')
    proof['name']='winston-barrier-w5';proof['w5']=result
    proof['files']['pack.json']=sha(target/'pack.json');proof['files']['w5-flat-white.png']=sha(target/'w5-flat-white.png')
    proof['limits']='Original geometry/UV/hex texture unchanged. MC-authored flat white support, blue translucency and fullbright additive Fresnel rim.'
    (target/'provenance.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    assert sha(target/GRID)==GRID_SHA
    result.update(packSha256=sha(target/'pack.json'),provenanceSha256=sha(target/'provenance.json'),flatWhiteSha256=sha(target/'w5-flat-white.png'))
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply-private',action='store_true');p.add_argument('--output',type=Path);a=p.parse_args()
    r=prepare(a.apply_private)
    if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print('PASS W5 original0116e hex SHA; private assets '+('prepared' if a.apply_private else 'verified (dry run)'))
