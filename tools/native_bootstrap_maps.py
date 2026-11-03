"""Explicit cold-start maps for the exact offline24919 client; no scene writes."""
import struct
from observe_overwatch import PoseReader

VERSION=10
DLL=f'owmc-session-bootstrap-v{VERSION}.dll'
MAPS={'hollywood':0x08000000000002af,'lobby-empty':0x0800000000000223,'kyoto-login':0x0800000000000664}

def selected_map(settings):
    name=settings.get('nativeMap','hollywood')
    if not isinstance(name,str) or name not in MAPS:raise ValueError('Unverified nativeMap; choose hollywood, lobby-empty or kyoto-login')
    return MAPS[name]

def read_loaded_map(process):
    r=PoseReader(process);admin=r.pointer(process.base+0x17b7f90);items,count,capacity=r.unpack('<Qii',admin+0xd8)
    if not 1<=count<=capacity<=128:raise ValueError('Native world system bounds')
    found=[]
    for system, in struct.iter_unpack('<Q',process.read(items,count*8)):
        if r.pointer(system)==process.base+0x15c3118:
            if r.pointer(system+8)!=admin:raise ValueError('Native world owner changed')
            found.append({'state':r.unpack('<B',system+0x10)[0],'mapId':r.unpack('<Q',system+0x20)[0]})
    if len(found)!=1:raise ValueError('Native world system absent or ambiguous')
    return found[0]
