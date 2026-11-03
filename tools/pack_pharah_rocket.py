"""Convert the confirmed local retail33 ->84C rigid rocket; assets remain private."""
import argparse,hashlib,json,shutil
from pathlib import Path
import numpy as np
from PIL import Image
from owlib_projectile_assets import entity,model,material

def additive_rgba(image,tint=(255,255,255)):
    source=np.asarray(image.convert('RGBA')).astype(np.uint16)
    intensity=(source[:,:,:3].max(axis=2)*source[:,:,3]//255).astype(np.uint8)
    rgba=np.empty((*intensity.shape,4),dtype=np.uint8)
    rgba[:,:,:3]=(intensity[:,:,None].astype(float)*np.asarray(tint)/255).astype(np.uint8)
    rgba[:,:,3]=intensity
    return Image.fromarray(rgba)

def pack(root,out):
    root,out=Path(root).resolve(),Path(out).resolve();repo=Path(__file__).resolve().parents[1]
    if out.is_relative_to(repo):raise ValueError('Keep game-derived assets outside the repository')
    ep,=root.rglob('000000000033.003.owentity');e=entity(ep)
    if e['modelGuid']!=0x84c:raise ValueError('Unverified original rocket model')
    mp,=root.rglob('00000000084C.owmdl');m=model(mp)
    if m['bones'] or len(m['meshes'])!=1:raise ValueError('Expected original rigid rocket')
    mesh=m['meshes'][0];lookPath=(mp.parent/m['look'].replace('\\','/')).resolve();look=material(lookPath)
    name,=[v for k,v in look['entries'] if k==mesh['material']];matPath=(mp.parent/name.replace('\\','/')).resolve();mat=material(matPath)
    if mat['shader']!=33 or len(mesh['uvs'])!=1:raise ValueError('Original rocket shader/UV changed')
    texture,=[p for p,k in mat['textures'] if k==0xad10f602];color=(matPath.parent/texture.replace('\\','/')).resolve()
    flame,=list((root/'Anything/Textures').glob('00000002A480.png'))
    for f in [ep,mp,lookPath,matPath,color,flame]:
        if not f.is_relative_to(root):raise ValueError('Extraction path escaped root')
    out.mkdir(parents=True,exist_ok=True);shutil.copy2(color,out/'body.png')
    # Additive layers use RGB intensity (ONE/ONE), not alpha as a substitute
    # for intensity. White RGB with a soft alpha mask becomes a white rectangle.
    additive_rgba(Image.open(flame),(255,190,72)).save(out/'exhaust.png')
    # Preserve original sprite intensity in both RGB and alpha so additive
    # blending contributes zero at the edge, independently of alpha semantics.
    sources=[]
    def sprite(name,dest):
        src=root/'Anything/Textures'/name;sources.append(src)
        result=additive_rgba(Image.open(src));result.save(out/dest);return result
    sprite('00000002A3E1.png','flare.png');sprite('000000004C09.png','glow.png')
    frames=[sprite('000000007ADD'+suffix+'.png','flame'+str(i)+'.png') for i,suffix in enumerate(['','_1','_2','_3'])]
    if len({f.size for f in frames})!=1:raise ValueError('Original flame frame sizes differ')
    atlas=Image.new('RGBA',(frames[0].width*4,frames[0].height))
    for i,frame in enumerate(frames):atlas.paste(frame,(i*frame.width,0))
    atlas.save(out/'flame.png')
    data={'schema':1,'resource':'0400000000000033','model':'00000000084C.00C','geometry':'unscaled-original-owlib-export','positions':mesh['positions'].reshape(-1).tolist(),'normals':mesh['normals'].reshape(-1).tolist(),'uv':mesh['uvs'][0].reshape(-1).tolist(),'indices':mesh['indices'].reshape(-1).tolist()}
    (out/'rocket.json').write_text(json.dumps(data,separators=(',',':')),encoding='utf-8')
    hashes={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in [out/name for name in ['rocket.json','body.png','exhaust.png','flare.png','glow.png','flame.png']]}
    provenance={'schema':2,'clientBuild':'2.25.0.0.154088','files':hashes,'sourceFiles':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [ep,mp,lookPath,matPath,color,flame,*sources]},'limits':['Original mesh/color and effect sprites; MC material, muzzle placement, timing and flame animation are presentation adaptations, not the complete OW effect graph','Native damage, projectile trajectory, speed and collision remain unchanged']}
    (out/'provenance.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8');return provenance

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,default=Path.home()/'.universal-modder/assets/owmc-pharah-projectile');a=p.parse_args();print(json.dumps(pack(a.root,a.out),indent=2))
