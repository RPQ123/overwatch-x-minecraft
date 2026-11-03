"""Calibrated original24919 Pulse Bomb file-only extraction and private preparation.

No game process, injection, input, retail fallback or renderer installation. All
Blizzard-derived files stay in the user's private asset cache, never the JAR.
"""
from __future__ import annotations
from modpack.config import paths
import argparse
import hashlib
import io
import json
from pathlib import Path
import struct
import subprocess
import zlib

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BASE = paths().get('privateAssets')
CACHE = BASE / "ow-beta-24919-pulse"
OUTPUT = BASE / "owmc-pulse-bomb"
READER_SHA256 = "f24271c8272d012c3a590ef5be839482ec28d754c41268e10df9eaf01d0246af"
EXE_SHA256 = "f73a747b7d63a07402958b2b2c4587125a46ef8e181281669da009d352308e9f"
MODEL_SHA256 = "f90dee3ea70c5ff84ba8c516dc83feb1bce2a49bd599c6a65630769f2cb6dd37"
# CKeys are content MD5 identifiers from the owned24919 manifests, not secrets.
ASSETS = {
 "0400000000000045": (1056,"70bd5fa783e8d7dae9db4cf71db039dc","0f66b6497553dec9588cefaeedb09f25d14cf0ed8f21b26cfce4f14fbea9ce47"),
 "0d00000000000b2c": (38480,"c92824fe7cfe7f57f26b02729489ecb8",MODEL_SHA256),
 "0980000000000b99": (1616,"c129c8a419a08f3a24cd17067dd02240","f314bcaf0ee2b59414b3325acf30712f560ad6b47ded6b5d6b01dec8f005c017"),
 "0e000000000000cf": (240,"22ade7c7c1a90c78a9e7039c2967f785","79ee80239ab2e4a9b32abef656ac5d77f02d79c174d15b34238ef89e8c1b24b9"),
 "0c00000000000376": (32,"acc02d114bbf10301af1dab6e4ff3936","8d5b88e7d7ce43cb8cf9e0e053035f99ceccc0f07979badfcce188a1b238810f"),
 "0c00000000000379": (32,"07aaf38c32eee44ecb58625f0a2a2e15","60f7c79b35e2cab5100e56101f4a582de7010ecef23ef175904abc0c0154ca41"),
 "0320000100000376": (131088,"d3cc0f122ccd1a0f206fad8a66ca2cb4","5502d2a931d9abef9cf70c72b6a9dc8784a9af844e7640fecf8be26bc9a412e9"),
 "0320000100000379": (262160,"0fc93136aaeb55925ee81b29025c1a39","888e6adec8316f84bb676d93e2e8f253673a26655acfb57e98dc1f7116b87ec5"),
}
MANIFESTS = {
 "manifest-rcn-enus.apm": ("Manifest\\Win_SPWin_RCN_LenUS_EExt.apm",85932,"6c20315eed82c3bb16b46314d694ed9ec0b93071335b22f0ec45081998cc3877"),
 "tracer-package.apm": ("AppPackageManifests\\Windows-RCN\\enUS\\02e0000000000003",15481,"c6c9991ae521cd394a94ca90e332e9700197c876524bd2a6a2d7eeb00c0c8c1a"),
 "package-0400000000000001.apm": ("AppPackageManifests\\Windows-RCN\\enUS\\0400000000000001",134384,"d8d8d10b64db1590780fc476c744a7f08440cd8e91c6aae97d19a8bbb8380c7f"),
}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def private_path(path: Path, base: Path | None = None) -> Path:
    path, base = path.resolve(), (BASE if base is None else base).resolve()
    configured=paths()
    selected_private_root=(base==configured.get('privateAssets')
                           and (configured.packaged or 'privateAssets' in configured.overrides))
    if path == base or not path.is_relative_to(base) or (path.is_relative_to(ROOT) and not selected_private_root):
        raise ValueError("Game-derived output must stay inside the private asset cache")
    return path


def package_records(raw: bytes) -> dict:
    if len(raw) < 80:
        raise ValueError("Truncated beta package")
    offset, = struct.unpack_from("<Q", raw)
    count, compressed = struct.unpack_from("<II", raw, 24)
    if offset != 80 or not 0 < count <= 100000 or offset + compressed > len(raw):
        raise ValueError("Unsupported beta package layout")
    decoder = zlib.decompressobj(31)
    try:
        decoded = decoder.decompress(raw[offset:offset+compressed], count*36+1)
    except zlib.error as error:
        raise ValueError("Invalid beta package compression") from error
    if (not decoder.eof or decoder.unused_data or decoder.unconsumed_tail or len(decoded) != count*36):
        raise ValueError("Beta package record expansion mismatch")
    result = {}
    for guid,size,flags,unknown,key in struct.iter_unpack("<QIII16s", decoded):
        name = f"{guid:016x}"
        value = {"bytes":size,"ckey":key.hex(),"flags":flags,"unknown":unknown}
        if name in result and result[name] != value:
            raise ValueError("Conflicting package GUID records")
        result[name] = value
    return result


def collect_owned(game: Path, reader: Path, cache: Path = CACHE) -> dict:
    """Use the already-built bounded local CascLib reader, never a retail tool retry."""
    game, reader, cache = game.resolve(), reader.resolve(), private_path(cache)
    if sha(reader.read_bytes()) != READER_SHA256:
        raise ValueError("Unverified local-only CascLib reader")
    if sha((game / "GameClientApp.patched.exe").read_bytes()) != EXE_SHA256:
        raise ValueError("Only the exact owned offline24919 archive is calibrated")
    build = (game / ".build.info").read_bytes()
    if b"24919" not in build:
        raise ValueError("Archive build changed")
    cache.mkdir(parents=True, exist_ok=True)
    receipts = []
    entries = [(name,entry,size,digest) for name,(entry,size,digest) in MANIFESTS.items()]
    entries += [(guid+".raw",key,size,digest) for guid,(size,key,digest) in ASSETS.items()]
    for name,entry,size,digest in entries:
        target = cache / name
        if not target.exists():
            run = subprocess.run([str(reader),str(game),entry,str(target),"16777216"],
                capture_output=True,text=True,cwd=cache,timeout=45)
            if run.returncode:
                raise ValueError(f"Local archive read failed {name}: {run.returncode}")
        raw = target.read_bytes()
        if len(raw) != size or sha(raw) != digest:
            raise ValueError("Source identity mismatch; do not overwrite/retry: "+name)
        receipts.append({"file":name,"archive_entry":entry,"bytes":size,"sha256":digest})
    if (game / ".build.info").read_bytes() != build:
        raise ValueError("Archive identity changed during read")
    return {"clientBuild":"0.8.0.24919","readerSha256":READER_SHA256,
            "buildInfoSha256":sha(build),"online":False,"readOnly":True,"files":receipts}


def parse_rigid_model(raw: bytes) -> dict:
    """Exact measured flat24919 layout; not a parser for other model revisions."""
    if len(raw) < 38480 or struct.unpack_from("<I",raw,72)[0] != len(raw):
        raise ValueError("Flat model size/header mismatch")
    vbo,ibo = struct.unpack_from("<QQ",raw,368)
    if vbo != 1080 or ibo != 1192:
        raise ValueError("Flat model descriptor locations changed")
    count, = struct.unpack_from("<I",raw,vbo)
    strides = struct.unpack_from("<4B",raw,vbo+8)
    descriptors,stream1,stream2 = struct.unpack_from("<QQQ",raw,vbo+32)
    index_count, index_format = struct.unpack_from("<II",raw,ibo)
    index_data, = struct.unpack_from("<Q",raw,ibo+16)
    if (count,strides,descriptors,stream1,stream2,index_count,index_format,index_data) != (
            731,(20,16,7,6),1136,1728,16352,2604,0,28048):
        raise ValueError("Measured vertex/index layout changed")
    expected=[(0,0,2,0,0),(4,0,6,0,0xc0000),(5,0,8,0,0x100000),
        (1,0,9,1,0),(3,0,9,1,0x40000),(9,0,4,1,0x80000),(16,0,12,1,0xc0000)]
    if [struct.unpack_from("<4BI",raw,descriptors+i*8) for i in range(7)] != expected:
        raise ValueError("Measured vertex semantics changed")
    positions=np.ndarray((count,3),dtype="<f4",buffer=raw,offset=stream1,strides=(20,4)).copy()
    normals=np.ndarray((count,3),dtype="i1",buffer=raw,offset=stream2,strides=(16,1)).astype(np.float32)
    uv=np.ndarray((count,2),dtype="<f2",buffer=raw,offset=stream2+8,strides=(16,2)).astype(np.float32)
    indices=np.frombuffer(raw,dtype="<u2",offset=index_data,count=index_count).copy()
    bones=np.ndarray((count,4),dtype="u1",buffer=raw,offset=stream1+12,strides=(20,1))
    weights=np.ndarray((count,4),dtype="u1",buffer=raw,offset=stream1+16,strides=(20,1))
    if np.any(bones) or np.any(weights != np.array([255,0,0,0],dtype="u1")):
        raise ValueError("Expected measured single rigid identity bone")
    if (not np.isfinite(positions).all() or not np.isfinite(uv).all()
            or abs(positions).max()>.2 or uv.min()<0 or uv.max()>1 or indices.max()>=count):
        raise ValueError("Mesh arrays outside calibrated bounds")
    length=np.linalg.norm(normals,axis=1)
    if length.min()<100 or length.max()>140:
        raise ValueError("Unexpected packed normal range")
    normals /= length[:,None]
    low,high=positions.min(axis=0),positions.max(axis=0)
    center=(low+high)/2
    positions -= center
    return {"positions":positions,"normals":normals,"uv":uv,"indices":indices,
            "sourceBounds":[low.tolist(),high.tolist()],"originTranslation":(-center).tolist(),
            "halfThickness":float((high[1]-low[1])/2)}


def deplane_words(raw: bytes, words_per_block: int) -> bytes:
    if words_per_block not in (2,4) or len(raw) % (words_per_block*4):
        raise ValueError("Invalid planar BC block dimensions")
    return np.frombuffer(raw,dtype="u1").reshape(words_per_block,-1,4).transpose(1,0,2).copy().tobytes()


def decode_top_texture(header: bytes, payload: bytes) -> Image.Image:
    if len(header)!=32 or len(payload)<16:
        raise ValueError("Unexpected beta texture header")
    fmt=header[3]; width,height=struct.unpack_from("<HH",header,8)
    flags,surfaces,size,offset=struct.unpack_from("<4I",payload)
    if (width,height,surfaces,offset,fmt) not in ((512,512,1,16,72),(512,512,1,16,78)):
        raise ValueError("Only the verified512 BC1/BC3 top payload is supported")
    words=2 if fmt==72 else 4
    if flags!=7 or size!=width*height//16*words*4 or len(payload)!=offset+size:
        raise ValueError("Texture payload expansion/layout mismatch")
    raw=deplane_words(payload[offset:],words)
    code=b"DXT1" if words==2 else b"DXT5"
    dds=struct.pack("<7I11I8I5I",124,0x81007,height,width,size,0,1,*([0]*11),
                    32,4,int.from_bytes(code,"little"),0,0,0,0,0,0x1000,0,0,0,0)
    image=Image.open(io.BytesIO(b"DDS "+dds+raw)).convert("RGBA")
    if image.size!=(width,height):
        raise ValueError("Decoded texture dimensions differ")
    return image


def validate_pack(output: Path = OUTPUT) -> dict:
    output=private_path(output)
    proof=output/"provenance.json"
    if not proof.resolve().is_relative_to(output) or not 0<proof.stat().st_size<=65536:
        raise ValueError("Pulse provenance bounds/path")
    manifest=json.loads(proof.read_text(encoding="utf-8"))
    if (manifest.get("clientBuild")!="0.8.0.24919" or manifest.get("originalModelSha256")!=MODEL_SHA256
            or manifest.get("model")!="0d00000000000b2c"):
        raise ValueError("Pulse pack original identity mismatch")
    for name in ("pulse.json","body.png","emission.png"):
        file=output/name
        if not file.resolve().is_relative_to(output) or not 0<file.stat().st_size<=4*1024**2:
            raise ValueError("Pulse pack file bounds/path")
        if sha(file.read_bytes())!=manifest["files"][name]:
            raise ValueError("Pulse pack file hash mismatch: "+name)
    return {"ready":True,"path":str(output),"originalModel":True,"clientBuild":"0.8.0.24919",
            "model":manifest["model"],"files":manifest["files"],"inGameVerified":False}


def build_pack(cache: Path = CACHE, output: Path = OUTPUT) -> dict:
    cache,output=private_path(cache),private_path(output)
    if output.exists():
        return validate_pack(output)
    raw,proof={},{}
    for guid,(size,key,digest) in ASSETS.items():
        file=cache/(guid+".raw")
        data=file.read_bytes()
        if len(data)!=size or sha(data)!=digest or hashlib.md5(data).hexdigest()!=key:
            raise ValueError("Pinned original raw asset differs: "+guid)
        raw[guid]=data;proof[guid]={"bytes":size,"sha256":digest,"ckey":key}
    package_maps=[]
    for name,(entry,size,digest) in MANIFESTS.items():
        data=(cache/name).read_bytes()
        if len(data)!=size or sha(data)!=digest:
            raise ValueError("Owned package provenance differs: "+name)
        proof[name]={"archiveEntry":entry,"bytes":size,"sha256":digest}
        if name!="manifest-rcn-enus.apm":package_maps.append(package_records(data))
    for guid,(size,key,_) in ASSETS.items():
        if not any(guid in rows and rows[guid]["bytes"]==size and rows[guid]["ckey"]==key for rows in package_maps):
            raise ValueError("Raw resource not declared by measured owner/dependency package")
    entity=raw["0400000000000045"];look=raw["0980000000000b99"];mat=raw["0e000000000000cf"]
    if (struct.unpack_from("<Q",entity,832)[0]!=0x0d00000000000b2c
            or struct.unpack_from("<Q",entity,848)[0]!=0x0980000000000b99
            or struct.unpack_from("<QQ",look,136)!=(0x0e000000000000cf,0xd3621d55261c5ab7)
            or struct.unpack_from("<QI",mat,160)!=(0x0c00000000000376,0xbcbe747d)
            or struct.unpack_from("<QI",mat,176)!=(0x0c00000000000379,0xad10f602)):
        raise ValueError("Original entity/model/look/material binding changed")
    geometry=parse_rigid_model(raw["0d00000000000b2c"])
    color=decode_top_texture(raw["0c00000000000379"],raw["0320000100000379"])
    glow=decode_top_texture(raw["0c00000000000376"],raw["0320000100000376"])
    # Opaque metal body: old PBR alpha is not used as MC cutout transparency.
    color.putalpha(255)
    glow_pixels=np.asarray(glow).copy()
    glow_pixels[:,:,3]=glow_pixels[:,:,:3].max(axis=2)
    glow=Image.fromarray(glow_pixels)
    output.mkdir(parents=True,exist_ok=False)
    color.save(output/"body.png");glow.save(output/"emission.png")
    data={"schema":1,"resource":"0400000000000045","model":"0d00000000000b2c",
        "originalModelSha256":MODEL_SHA256,"geometry":"original-beta24919-flat-model-v1",
        "units":"meters","frontAxis":"+Y","halfThickness":geometry["halfThickness"],
        "originTranslation":geometry["originTranslation"],"sourceBounds":geometry["sourceBounds"],
        **{key:geometry[key].reshape(-1).tolist() for key in ("positions","normals","uv","indices")}}
    (output/"pulse.json").write_text(json.dumps(data,separators=(",",":"))+"\n",encoding="utf-8")
    manifest={"schema":1,"clientBuild":"0.8.0.24919","resource":data["resource"],"model":data["model"],
        "originalModelSha256":MODEL_SHA256,"frontAxis":"+Y","sourceFiles":proof,
        "files":{name:sha((output/name).read_bytes()) for name in ("pulse.json","body.png","emission.png")},
        "transformations":["Unscaled original vertices; translate bounding-box center to origin",
            "Signed packed normals normalized; original half-float UV and uint16 indices",
            "Reversible DWORD-plane interleave for beta BC1/BC3, then decode actual512 top mip",
            "Opaque MC metal body; original RGB emission mask uses additive MC material"],
        "limitations":["Original model/textures, not a complete original OW shader/effect graph",
            "MC lighting/material, flight rotation and contact-normal alignment are presentation adaptations",
            "No original digit animation or exploding debris effect claimed","No in-game acceptance in this asset-only increment"],
        "inGameVerified":False,"online":False}
    (output/"provenance.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    return validate_pack(output)


def prepare(cache: Path = CACHE, output: Path = OUTPUT) -> dict:
    """Launcher entry: local verify/build only, never launches or modifies a game."""
    try:
        return validate_pack(output) if output.exists() else build_pack(cache,output)
    except (OSError,ValueError,KeyError,TypeError) as error:
        return {"ready":False,"originalModel":False,"path":str(output),"error":str(error),"inGameVerified":False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache",type=Path,default=CACHE)
    parser.add_argument("--out",type=Path,default=OUTPUT)
    parser.add_argument("--extract-game",type=Path)
    parser.add_argument("--reader",type=Path,default=ROOT/"research/casc-read-local.exe")
    args=parser.parse_args()
    if args.extract_game:collect_owned(args.extract_game,args.reader,args.cache)
    report=prepare(args.cache,args.out)
    print(json.dumps(report,indent=2))
    return 0 if report["ready"] else 1


if __name__=="__main__":raise SystemExit(main())
