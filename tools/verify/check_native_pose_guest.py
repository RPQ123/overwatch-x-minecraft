"""Numerically match actual MC rendered orientation against its acknowledged native camera."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import ctypes
from ctypes import wintypes
from pathlib import Path
import argparse,json,math,struct,sys,time
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'bridge'))
from world_frames import MCFrames

def rotation(yaw,pitch,roll):
    a,b,c=math.pi-math.radians(yaw),-math.radians(pitch),math.radians(roll)
    ca,sa,cb,sb,cc,sc=math.cos(a),math.sin(a),math.cos(b),math.sin(b),math.cos(c),math.sin(c)
    return np.array([[ca,0,sa],[0,1,0],[-sa,0,ca]])@np.array([[1,0,0],[0,cb,-sb],[0,sb,cb]])@np.array([[cc,-sc,0],[sc,cc,0],[0,0,1]])

def run(seconds=10):
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenFileMappingW.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.LPCWSTR];kernel.OpenFileMappingW.restype=wintypes.HANDLE
    kernel.MapViewOfFile.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.DWORD,wintypes.DWORD,ctypes.c_size_t];kernel.MapViewOfFile.restype=ctypes.c_void_p
    kernel.UnmapViewOfFile.argtypes=[ctypes.c_void_p];kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    handle=kernel.OpenFileMappingW(4,False,'Local\\OWMCHostPose')
    if not handle:raise OSError('No original camera publisher')
    address=kernel.MapViewOfFile(handle,4,0,0,4096)
    if not address:kernel.CloseHandle(handle);raise ctypes.WinError(ctypes.get_last_error())
    frames=MCFrames();matched=set();errors=[];missing=0;native_pid=0;last=None;first_basis=None;max_change=0;started=time.monotonic()
    try:
        while time.monotonic()-started<seconds:
            data=ctypes.string_at(address,4096);seq,=struct.unpack_from('<Q',data,64)
            if data[:8]!=b'OWPOSE01' or not seq or seq&1 or ctypes.string_at(address+64,8)!=data[64:72]:time.sleep(.005);continue
            generation,=struct.unpack_from('<Q',data,24);native_pid,=struct.unpack_from('<I',data,16)
            f=frames.latest()
            if not f or f.host_generation!=generation or not f.host_frame:missing+=1;time.sleep(.01);continue
            basis=None
            for slot in range(64):
                offset=512+slot*56;frame,=struct.unpack_from('<Q',data,offset)
                if frame==f.host_frame:
                    flags,=struct.unpack_from('<I',data,offset+52)
                    if flags!=1:raise AssertionError('Not an original native camera')
                    basis=np.array(struct.unpack_from('<9f',data,offset+16)).reshape(3,3,order='F');break
            if basis is None:missing+=1;time.sleep(.01);continue
            error=float(np.max(np.abs(rotation(*f.rotation)-basis)))
            if error>2e-4:raise AssertionError(f'MC image/native acknowledged pose mismatch: {error}, frame={f.host_frame}')
            if first_basis is None:first_basis=basis.copy()
            max_change=max(max_change,float(np.max(np.abs(first_basis-basis))))
            matched.add((f.generation,f.sequence));errors.append(error);last=f;time.sleep(.02)
        if not matched:raise AssertionError('No actual MC frame matched original native camera history')
        directory=Path('research/native-pose-guest-proof');directory.mkdir(parents=True,exist_ok=True);Image.fromarray(last.rgba).save(directory/'mc-native-view.png')
        report={'kind':'original-native-world-camera-actual-minecraft','nativePid':native_pid,'mcPid':last.source_pid,'hostGeneration':last.host_generation,'uniqueMatchedFrames':len(matched),'maxBasisError':max(errors),'maxBasisChangeDuringCapture':max_change,'unmatchedPolls':missing,'lastHostFrame':last.host_frame,'lastMcFrame':last.mc_frame,'rotationRendered':last.rotation,'fovRendered':last.fov,'continuousCompositionVerified':False,'movementVerified':False}
        (directory/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    finally:frames.close();kernel.UnmapViewOfFile(address);kernel.CloseHandle(handle)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--seconds',type=float,default=10);args=parser.parse_args()
    if not 1<=args.seconds<=110:parser.error('Capture duration must be 1..110 seconds inside the bounded observer')
    run(args.seconds)
