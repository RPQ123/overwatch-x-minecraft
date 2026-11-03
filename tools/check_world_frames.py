"""Inspect real MC-only frames; never attaches to or controls Overwatch."""
import argparse,json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bridge'))
from world_frames import MCFrames
import numpy as np
from PIL import Image

parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--seconds',type=int,default=10);parser.add_argument('--capture',type=Path);args=parser.parse_args()
if not 1<=args.seconds<=60:parser.error('1..60 seconds required')
reader=MCFrames();frames=set();last=None;rejected=0;start=time.monotonic()
try:
    while time.monotonic()-start<args.seconds:
        try:
            f=reader.latest()
            if f is not None:frames.add((f.generation,f.sequence));last=f
        except ValueError:rejected+=1
        time.sleep(.03)
finally:reader.close()
if last is None:raise SystemExit('No complete fresh actual-world frame received')
if args.capture:
    args.capture.parent.mkdir(parents=True,exist_ok=True);Image.fromarray(last.rgba,'RGBA').save(args.capture)
result={'sourcePid':last.source_pid,'generation':last.generation,'size':[last.width,last.height],'uniqueFrames':len(frames),'rejected':rejected,
        'hasDepth':last.depth is not None,
        'depthRange':[float(last.depth.min()),float(last.depth.max())] if last.depth is not None else None,
        'depthGeometryPixels':int(np.count_nonzero(last.depth<.99999)) if last.depth is not None else None,
        'camera':last.camera,'fov':last.fov,'hostPoseConnected':last.host_frame!=0,'owAttached':False}
print(json.dumps(result));Path('research/mc-world-frame-proof.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
