"""Strict reader for the MC 1.21.1 world-only passthrough proof (OWMCFR01)."""
from dataclasses import dataclass
import ctypes
from ctypes import wintypes
import math,struct,time
import numpy as np

NAME='Local\\OWMCPassthroughFrame'
HEADER=4096
MAX_W,MAX_H=2560,1440
STRIDE=MAX_W*MAX_H*8

@dataclass
class Frame:
    sequence:int
    mc_frame:int
    host_frame:int
    width:int
    height:int
    near:float
    far:float
    fov:float
    camera:tuple
    rotation:tuple
    projection:tuple
    source_pid:int
    generation:int
    capture_ns:int
    publish_ns:int
    publish_ms:int
    rgba:np.ndarray
    depth:np.ndarray|None
    host_generation:int=0

def decode(header,descriptor,payload,now_ms=None):
    if len(header)!=HEADER or header[:8]!=b'OWMCFR01':raise ValueError('Frame mapping identity')
    version,size,slots,maxw,maxh,reserved=struct.unpack_from('<6I',header,8)
    stride,published,latest,pid,generation=struct.unpack_from('<QQiIQ',header,32)
    if (version,size,slots,maxw,maxh,reserved,stride)!=(2,HEADER,3,MAX_W,MAX_H,0,STRIDE) or not pid or not generation:
        raise ValueError('Frame mapping layout')
    if len(descriptor)!=256:raise ValueError('Frame descriptor size')
    seq,mc_frame,host_frame,w,h,near,far,fov,flags=struct.unpack_from('<QQQIIfffI',descriptor)
    camera=struct.unpack_from('<3d',descriptor,48);rotation=struct.unpack_from('<3f',descriptor,72)
    first_person,cap,pub,wall=struct.unpack_from('<IQQQ',descriptor,84)
    projection=struct.unpack_from('<16f',descriptor,112)
    host_generation,=struct.unpack_from('<Q',descriptor,176)
    if bool(host_frame)!=bool(host_generation):raise ValueError('Unpaired host frame/generation')
    if seq==0 or seq&1 or mc_frame==0 or not 0<=latest<3 or not published:raise ValueError('Incomplete frame')
    if flags not in (1,2):raise ValueError('Frame payload format')
    if not 1<=w<=MAX_W or not 1<=h<=MAX_H or len(payload)!=w*h*4*flags:raise ValueError('Frame dimensions/payload')
    if first_person!=1 or not all(math.isfinite(x) for x in (near,far,fov,*camera,*rotation,*projection)):
        raise ValueError('Frame conventions/camera')
    if not 0<near<far<=100000 or not 0<fov<179 or cap<=0 or pub<cap:raise ValueError('Frame planes/timing')
    now_ms=int(time.time()*1000) if now_ms is None else now_ms
    if not -250<=now_ms-wall<=1000:raise ValueError('Stale frame')
    pixels=w*h*4
    rgba=np.frombuffer(payload,np.uint8,pixels).reshape(h,w,4)[::-1].copy()
    depth=np.frombuffer(payload,'<f4',w*h,pixels).reshape(h,w)[::-1].copy() if flags==2 else None
    if depth is not None and (not np.isfinite(depth).all() or (depth<0).any() or (depth>1).any()):raise ValueError('Invalid depth pixels')
    return Frame(seq,mc_frame,host_frame,w,h,near,far,fov,camera,rotation,projection,pid,generation,cap,pub,wall,rgba,depth,host_generation)

class MCFrames:
    def __init__(self):
        self.kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        self.kernel.OpenFileMappingW.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.LPCWSTR];self.kernel.OpenFileMappingW.restype=wintypes.HANDLE
        self.kernel.MapViewOfFile.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.DWORD,wintypes.DWORD,ctypes.c_size_t];self.kernel.MapViewOfFile.restype=ctypes.c_void_p
        self.kernel.UnmapViewOfFile.argtypes=[ctypes.c_void_p];self.kernel.UnmapViewOfFile.restype=wintypes.BOOL
        self.kernel.CloseHandle.argtypes=[wintypes.HANDLE];self.kernel.CloseHandle.restype=wintypes.BOOL
        self.handle=self.kernel.OpenFileMappingW(4,False,NAME)
        if not self.handle:raise OSError('No live MC world-frame mapping')
        self.address=self.kernel.MapViewOfFile(self.handle,4,0,0,HEADER+3*STRIDE)
        if not self.address:self.kernel.CloseHandle(self.handle);raise ctypes.WinError(ctypes.get_last_error())
    def latest(self):
        for _ in range(4):
            header=ctypes.string_at(self.address,HEADER);latest=struct.unpack_from('<i',header,48)[0]
            if not 0<=latest<3:return None
            d=256+latest*256;descriptor=ctypes.string_at(self.address+d,256)
            seq=struct.unpack_from('<Q',descriptor)[0]
            if not seq or seq&1:continue
            w,h=struct.unpack_from('<II',descriptor,24)
            if not 1<=w<=MAX_W or not 1<=h<=MAX_H:raise ValueError('Invalid dimensions before copy')
            flags=struct.unpack_from('<I',descriptor,44)[0]
            if flags not in (1,2):raise ValueError('Invalid format before copy')
            payload=ctypes.string_at(self.address+HEADER+latest*STRIDE,w*h*4*flags)
            if ctypes.string_at(self.address+d,8)!=descriptor[:8] or ctypes.string_at(self.address+56,8)!=header[56:64]:continue
            return decode(header,descriptor,payload)
        return None
    def close(self):
        if self.address:self.kernel.UnmapViewOfFile(self.address);self.address=None
        if self.handle:self.kernel.CloseHandle(self.handle);self.handle=None
