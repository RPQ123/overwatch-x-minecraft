"""Private original Venom Mine asset pack from the owned offline 24919 archive.

Chain (research/sprint-20261024/venom-asset-chain.json): Widow Volley1 projectile entity
04000000000000af -> mesh 0d000000000006f2 (offset528) + Look 0980000000000605 -> slot
b80e918f52992a64 -> material 0e00000000001b37 -> color 0c..1427 (BC3 sRGB 128x256) and glow mask
0c..1428 (BC4 128x256). Raw resources stay in ~/.universal-modder/assets/ow-beta-24919-venom
(read by research/sprint-20261024/read_venom_assets.py); output goes to owmc-venom-mine."""
from modpack.config import paths
import hashlib,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
from ow_beta_texture import decode

BASE=paths().get('privateAssets');CACHE=BASE/"ow-beta-24919-venom";OUTPUT=BASE/"owmc-venom-mine"
ENTITY,MODEL,LOOK,MATERIAL="04000000000000af","0d000000000006f2","0980000000000605","0e00000000001b37"
COLOR,GLOW="1427","1428"
GLOW_TINT=(.78,.32,1.0)  # MC presentation tint for the original glow mask (original shader colour not decoded)

def sha(b):return hashlib.sha256(b).hexdigest()

def parse_model(raw:bytes,max_extent:float=.3)->dict:
    """Same flat24919 vertex semantics as the Pulse Bomb mesh; descriptor offsets read from the header."""
    if struct.unpack_from("<I",raw,72)[0]!=len(raw):raise ValueError("Flat model size/header mismatch")
    vbo,ibo=struct.unpack_from("<QQ",raw,368)
    count,=struct.unpack_from("<I",raw,vbo);strides=struct.unpack_from("<4B",raw,vbo+8);desc,s1,s2=struct.unpack_from("<QQQ",raw,vbo+32)
    icount,ifmt=struct.unpack_from("<II",raw,ibo);idata,=struct.unpack_from("<Q",raw,ibo+16)
    expected=[(0,0,2,0,0),(4,0,6,0,0xc0000),(5,0,8,0,0x100000),(1,0,9,1,0),(3,0,9,1,0x40000),(9,0,4,1,0x80000),(16,0,12,1,0xc0000)]
    if strides!=(20,16,7,6) or ifmt!=0 or [struct.unpack_from("<4BI",raw,desc+i*8) for i in range(7)]!=expected:raise ValueError("Vertex layout differs from measured flat24919")
    if s1+count*20>s2 or s2+count*16>idata or idata+icount*2>len(raw):raise ValueError("Buffer bounds")
    pos=np.ndarray((count,3),dtype="<f4",buffer=raw,offset=s1,strides=(20,4)).copy()
    nrm=np.ndarray((count,3),dtype="i1",buffer=raw,offset=s2,strides=(16,1)).astype(np.float32)
    uv=np.ndarray((count,2),dtype="<f2",buffer=raw,offset=s2+8,strides=(16,2)).astype(np.float32)
    idx=np.frombuffer(raw,dtype="<u2",offset=idata,count=icount).copy()
    weights=np.ndarray((count,4),dtype="u1",buffer=raw,offset=s1+16,strides=(20,1))
    # Rigid parts: every vertex has exactly one full-weight bone, so the bind pose is drawn as stored.
    if np.any(weights!=np.array([255,0,0,0],dtype="u1")):raise ValueError("Expected single full-weight rigid binding")
    if not(np.isfinite(pos).all() and np.isfinite(uv).all()) or abs(pos).max()>max_extent or idx.max()>=count:raise ValueError("Mesh arrays outside bounds")
    length=np.linalg.norm(nrm,axis=1)
    if length.min()<100 or length.max()>140:raise ValueError("Unexpected packed normal range")
    nrm/=length[:,None];low,high=pos.min(0),pos.max(0)
    shift=np.array([-(low[0]+high[0])/2,-low[1],-(low[2]+high[2])/2],dtype=np.float32)  # base on y=0, centred in XZ
    pos+=shift
    return dict(positions=pos,normals=nrm,uv=uv,indices=idx,sourceBounds=[low.tolist(),high.tolist()],originTranslation=shift.tolist(),height=float(high[1]-low[1]))

def build(cache=CACHE,output=OUTPUT)->dict:
    raw={g:(cache/(g+".raw")).read_bytes() for g in (ENTITY,MODEL,LOOK,MATERIAL)}
    if struct.unpack_from("<Q",raw[ENTITY],528)[0]!=int(MODEL,16):raise ValueError("Entity no longer references the measured mesh")
    if struct.unpack_from("<QQ",raw[LOOK],144)!=(0xb80e918f52992a64,0xffffffffffffffff) or struct.unpack_from("<Q",raw[LOOK],160)[0]!=int(MATERIAL,16):raise ValueError("Look slot/material binding changed")
    if struct.unpack_from("<Q",raw[MATERIAL],176)[0]!=0x0c00000000001427 or struct.unpack_from("<Q",raw[MATERIAL],144)[0]!=0x0c00000000001428:raise ValueError("Material texture binding changed")
    geo=parse_model(raw[MODEL])
    tex=lambda t:decode((cache/f"0c{'0'*(14-len(t))}{t}.raw").read_bytes(),(cache/f"03200001{t.rjust(8,'0')}.raw").read_bytes())
    color=tex(COLOR).convert("RGBA");color.putalpha(255)
    mask=np.asarray(tex(GLOW).convert("L"),dtype=np.float32)/255
    glow=np.zeros(mask.shape+(4,),dtype=np.uint8)
    for c,k in enumerate(GLOW_TINT):glow[:,:,c]=np.clip(mask*k*255,0,255)
    glow[:,:,3]=np.clip(mask*255,0,255);glow=Image.fromarray(glow,"RGBA")
    output.mkdir(parents=True,exist_ok=True)
    color.save(output/"body.png");glow.save(output/"emission.png")
    data={"schema":1,"resource":ENTITY,"model":MODEL,"originalModelSha256":sha(raw[MODEL]),"geometry":"original-beta24919-flat-model-v1",
          "units":"meters","upAxis":"+Y","height":geo["height"],"originTranslation":geo["originTranslation"],"sourceBounds":geo["sourceBounds"],
          **{k:geo[k].reshape(-1).tolist() for k in ("positions","normals","uv","indices")}}
    (output/"venom.json").write_text(json.dumps(data,separators=(",",":"))+"\n",encoding="utf-8")
    prov={"schema":1,"clientBuild":"0.8.0.24919","entity":ENTITY,"model":MODEL,"look":LOOK,"material":MATERIAL,"color":"0c..."+COLOR,"glowMask":"0c..."+GLOW,
          "sourceSha256":{g:sha(b) for g,b in raw.items()},"files":{n:sha((output/n).read_bytes()) for n in ("venom.json","body.png","emission.png")},
          "transformations":["Unscaled original vertices; base moved to y=0 and XZ centred","Rigid single-bone parts drawn in bind pose",
                             "Planar BC3 (2+6+4+4) / BC4 (2+6) deplaned and decoded","Glow mask tinted purple for MC additive layer (original shader colour not decoded)"],
          "inGameVerified":False,"online":False}
    (output/"provenance.json").write_text(json.dumps(prov,indent=2)+"\n",encoding="utf-8")
    return {"ready":True,"vertices":len(geo["positions"]),"triangles":len(geo["indices"])//3,"height":geo["height"],"files":prov["files"]}

if __name__=="__main__":print(json.dumps(build()))
