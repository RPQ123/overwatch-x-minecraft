"""Private MC-made Barrage mesh and original recorded SFX; never an OW mesh export.

The modern official demonstration is silent. The historical reference audio P02
actually says Pharah's callout (its old catalogue/paired video labels are wrong).
Only the post-callout firing portion is looped; it is a mixed gameplay recording,
not a clean original sound-bank stem. All derived assets stay outside the repo.
"""
from modpack.config import paths
import argparse,hashlib,json,math,subprocess
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=paths().get('privateAssets')/'owmc-pharah-barrage'
def digest(data):return hashlib.sha256(data).hexdigest()
def pack(out=ROOT):
 out=Path(out).resolve()
 if out.is_relative_to(Path(__file__).resolve().parents[1]):raise ValueError('Private assets only')
 out.mkdir(parents=True,exist_ok=True)
 pos=[];norm=[];uv=[];indices=[];colors=[]
 def triangle(a,b,c,color):
  v=np.asarray(b)-a;w=np.asarray(c)-a;n=np.cross(v,w);n=n/np.linalg.norm(n)
  first=len(pos)//3
  for p,t in zip((a,b,c),((0,0),(1,0),(.5,1))):pos.extend(p);norm.extend(n.tolist());uv.extend(t);colors.extend(color)
  indices.extend((first,first+1,first+2))
 # Independent .24m slender mini-rocket, nose +Y. Not a scaled primary mesh.
 rings=[(-.115,.022),(-.09,.030),(.065,.030),(.095,.022),(.125,.001)]
 for j,((y,r),(yy,rr)) in enumerate(zip(rings,rings[1:])):
  color=(80,110,143) if j==1 else (205,177,94) if j>=2 else (70,78,89)
  for k in range(12):
   a,b=2*math.pi*k/12,2*math.pi*(k+1)/12
   p=(r*math.cos(a),y,r*math.sin(a));q=(r*math.cos(b),y,r*math.sin(b));s=(rr*math.cos(a),yy,rr*math.sin(a));t=(rr*math.cos(b),yy,rr*math.sin(b))
   triangle(p,q,t,color);triangle(p,t,s,color)
 for k in range(4):
  a=k*math.pi/2;d=(math.cos(a),math.sin(a))
  triangle((.025*d[0],-.025,.025*d[1]),(.063*d[0],-.10,.063*d[1]),(.025*d[0],-.105,.025*d[1]),(165,180,192))
 data=dict(schema=1,resource='0400000000000052',model='mc-barrage-mini-v1',geometry='MC-made independent reference approximation',positions=pos,normals=norm,uv=uv,indices=indices,colors=colors)
 (out/'barrage.json').write_text(json.dumps(data,separators=(',',':')),encoding='utf-8')
 Image.new('RGBA',(1,1),(255,255,255,255)).save(out/'body.png')
 primary=paths().get('privateAssets')/'owmc-pharah-projectile'
 pin=json.loads((primary/'provenance.json').read_text(encoding='utf-8'))['files']
 for name in ('flame.png','flare.png','glow.png','exhaust.png'):
  blob=(primary/name).read_bytes()
  if digest(blob)!=pin[name]:raise ValueError('Original private sprite changed: '+name)
  (out/name).write_bytes(blob)
 # MC-made neutral soft ribbon. Reusing the orange exhaust sprite tinted the
 # supposedly white trail and exposed individual rectangular smoke cards.
 x=np.linspace(-1,1,32);y=np.linspace(1,0,64)
 intensity=(np.exp(-x*x*9)[None,:]*y[:,None]*255).astype(np.uint8)
 ribbon=np.repeat(intensity[:,:,None],4,axis=2)
 Image.fromarray(ribbon).save(out/'trail.png')
 source=paths().get('privateAssets')/'ow1-zhcn-2016/bili-BV1Hs411q779/P02-audio.m4s'
 blob=source.read_bytes()
 if digest(blob)!='0a98bf7597f2f57670c8e47271c5c6aca73925472da3309f718ecaf49e71c9d3':raise ValueError('Original recording identity changed')
 ff=paths().get('ffmpeg')
 raw=subprocess.check_output([str(ff),'-v','error','-i',str(source),'-f','f32le','-ac','2','-ar','48000','pipe:1'])
 audio=np.frombuffer(raw,dtype=np.float32).reshape(-1,2).copy()[int(2.72*48000):int(3.62*48000)]
 overlap=3840;fade=np.linspace(0,1,overlap,dtype=np.float32)[:,None]
 # Circular crossfade preserves original cadence/pitch, with no repeated voice.
 loop=np.concatenate((audio[overlap:-overlap],audio[-overlap:]*(1-fade)+audio[:overlap]*fade))
 if np.sqrt(np.mean(loop**2))<.005:raise ValueError('Silent reference cannot supply SFX')
 subprocess.run([str(ff),'-y','-v','error','-f','f32le','-ar','48000','-ac','2','-i','pipe:0','-c:a','libvorbis','-q:a','5','-fflags','+bitexact','-flags:a','+bitexact',str(out/'fire-loop.ogg')],input=loop.astype(np.float32).tobytes(),check=True)
 files={p.name:digest(p.read_bytes()) for p in out.iterdir() if p.name!='provenance.json' and p.is_file()}
 provenance=dict(schema=1,files=files,model='MC-made independent reference approximation, NOT original exported Barrage mesh',sprites='Original private retail154088 sprites adapted for orange impacts and pale curved trails',sound=dict(source='https://www.bilibili.com/video/BV1Hs411q779/?p=2',sourceSha256=digest(blob),clip=[2.72,3.62],crossfadeSeconds=.08,calloutEndsASR=2.5,role='Original gameplay recording firing-loop adaptation, includes background/effects; not isolated sound-bank stem',catalogDate='2016-06-14',recordingDateVerified=False),officialVisual='https://overwatch.blizzard.com/en-us/heroes/pharah/')
 (out/'provenance.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8');return provenance

def prepare(profile,root=ROOT):
 root=Path(root);profile=Path(profile)
 if not (root/'provenance.json').exists():print('Private Barrage sound unavailable');return False
 manifest=json.loads((root/'provenance.json').read_text(encoding='utf-8'));blob=(root/'fire-loop.ogg').read_bytes()
 if digest(blob)!=manifest['files']['fire-loop.ogg'] or not blob.startswith(b'OggS'):raise ValueError('Barrage sound hash changed')
 pack=profile/'resourcepacks/owmc-private-pharah-barrage';dest=pack/'assets/owmcguest/sounds/private/pharah/fire-loop.ogg'
 previous=None
 if dest.exists() and dest.read_bytes()!=blob:
  previous=dest.read_bytes()
  if digest(previous)!='98fe351cf61b723f793c4ea48f9c5bbc24d3b41c06bf4bc8a31c38bebff60160':raise ValueError('Preserve modified private Barrage sound')
  backup=pack/'migration-backup/fire-loop-first-nondeterministic.ogg'
  if backup.exists() and backup.read_bytes()!=previous:raise ValueError('Preserve existing Barrage migration backup')
 options=profile/'options.txt';lines=options.read_text(encoding='utf-8').splitlines();rows=[i for i,s in enumerate(lines) if s.startswith('resourcePacks:')]
 if len(rows)!=1:raise ValueError('Expected one resourcePacks option')
 packs=json.loads(lines[rows[0]].split(':',1)[1]);name='file/owmc-private-pharah-barrage'
 if previous is not None:backup.parent.mkdir(parents=True,exist_ok=True);backup.write_bytes(previous)
 dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(blob)
 (pack/'pack.mcmeta').write_text(json.dumps({'pack':{'pack_format':34,'description':'Private original Pharah gameplay firing-loop adaptation'}}),encoding='utf-8')
 (pack/'assets/owmcguest/sounds.json').write_text(json.dumps({'pharah.barrage.fire':{'sounds':[{'name':'owmcguest:private/pharah/fire-loop','preload':True}]}}),encoding='utf-8')
 (pack/'provenance.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
 if name not in packs:packs.append(name)
 lines[rows[0]]='resourcePacks:'+json.dumps(packs,separators=(',',':'));options.write_text('\n'.join(lines)+'\n',encoding='utf-8');return True

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=ROOT);a=p.parse_args();print(json.dumps(pack(a.out),indent=2))
