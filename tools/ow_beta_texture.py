"""Decode owned offline 24919 top-mip texture payloads (planar-DWORD BC1/BC3/BC4/BC5) to PIL.
Generalizes pulse_bomb_assets.decode_top_texture (512² BC1/BC3) to the measured venom-mine set."""
import io,struct
from PIL import Image
import numpy as np
# DXGI format -> (byte planes per 4x4 block, DDS FourCC). The beta stores each block field as
# its own plane; measured by neighbour smoothness: BC1 4+4, BC3 alpha 2+6 then color 4+4, BC4 2+6.
# BC5's four DWORD planes reproduce the private Venom tex-142a.png byte-for-byte.
# Export stored R/G with B=0; this does not reconstruct normals or certify shading.
FORMATS={71:((4,4),b"DXT1"),72:((4,4),b"DXT1"),77:((2,6,4,4),b"DXT5"),78:((2,6,4,4),b"DXT5"),80:((2,6),b"ATI1"),83:((4,4,4,4),b"ATI2")}

def deplane(raw:bytes,sizes)->bytes:
    n,o,parts=len(raw)//sum(sizes),0,[]
    if n*sum(sizes)!=len(raw):raise ValueError("Invalid planar BC block dimensions")
    for size in sizes:parts.append(np.frombuffer(raw[o:o+n*size],dtype="u1").reshape(n,size));o+=n*size
    return np.concatenate(parts,axis=1).tobytes()

def decode(header:bytes,payload:bytes,*,plane_layout="fields")->Image.Image:
    """Use measured field planes by default; 'dword' reproduces older cache previews."""
    if plane_layout not in ("fields","dword"):raise ValueError("Unknown texture plane layout")
    if len(header)!=32 or len(payload)<16:raise ValueError("Unexpected beta texture header")
    fmt=header[3];width,height=struct.unpack_from("<HH",header,8)
    flags,surfaces,size,offset=struct.unpack_from("<4I",payload)
    if fmt not in FORMATS or surfaces!=1 or offset!=16 or not(4<=width<=4096 and 4<=height<=4096):raise ValueError(f"Unsupported texture fmt{fmt} {width}x{height}")
    sizes,code=FORMATS[fmt];words=sum(sizes)//4
    if plane_layout=="dword":sizes=(4,)*words
    # flags is the full mip-chain level count (7 for 512², 5-6 here); only the top level is stored.
    if not 1<=flags<=13 or size!=width*height//16*words*4 or len(payload)!=offset+size:raise ValueError("Texture payload layout mismatch")
    raw=deplane(payload[offset:],sizes)
    if fmt==83:
        blocks=np.frombuffer(raw,dtype="u1").reshape(-1,16)
        channel_header=bytearray(header);channel_header[3]=80
        channels=[]
        for start in (0,8):
            channel=blocks[:,start:start+8]
            planar=channel[:,:2].tobytes()+channel[:,2:].tobytes()
            channel_payload=struct.pack("<4I",flags,1,len(planar),16)+planar
            channels.append(np.asarray(decode(bytes(channel_header),channel_payload).convert("L")))
        return Image.fromarray(np.stack([*channels,np.zeros_like(channels[0])],axis=2))
    dds=struct.pack("<7I11I8I5I",124,0x81007,height,width,size,0,1,*([0]*11),32,4,int.from_bytes(code,"little"),0,0,0,0,0,0x1000,0,0,0,0)
    image=Image.open(io.BytesIO(b"DDS "+dds+raw));image.load()
    if image.size!=(width,height):raise ValueError("Decoded texture dimensions differ")
    return image
