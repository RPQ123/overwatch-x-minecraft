"""Compare original view/crosshair/eye state without input or game writes."""
import argparse,json,math,struct,time
from pathlib import Path
from observe_overwatch import ROOT,ResearchProcess,PoseReader

def sample(reader):
    admin=reader.pointer(reader.memory.base+0x17b7f90)
    iterations=reader.pointer(admin+0xb0)
    component=reader.pointer(reader.pointer(iterations+0x4f*0x18))
    camera=reader.pointer(component+0x40);view=reader.pointer(camera+0x260);crosshair=reader.pointer(component+0x48)
    raw=reader.unpack('<12f',view+0x10);matrices=reader.unpack('<32f',crosshair+0x50)
    m=matrices[:16]
    origin=[-sum(m[12+j]*m[4*i+j] for j in range(3)) for i in range(3)]
    table=reader.memory.read(reader.pointer(admin+0x10),65536)
    controller=reader.entity(table,reader.unpack('<I',admin+0x220)[0]);local=reader.component(controller,0x2f)
    reference=reader.component(controller,0x20);model=reader.entity(table,reader.unpack('<I',reference+0x94)[0])
    mover=reader.component(model,0x15)
    eye=reader.unpack('<3f',local+0x1500);copied=reader.unpack('<3f',local+0x1510);foot=reader.unpack('<3f',mover+0xa50+0x220)
    return {'camera':raw[:3],'forward':raw[4:7],'up':raw[8:11],'matrixOrigin':origin,
            'eye':eye,'copiedEye':copied,'foot':foot,'worldToView':m,'viewToClip':matrices[16:],
            'cameraMatrixDifference':math.dist(raw[:3],origin),'viewport':reader.unpack('<4f',crosshair+0x1f0)}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pid',type=int,required=True)
    parser.add_argument('--seconds',type=int,default=60)
    parser.add_argument('--output',type=Path,default=ROOT/'research/projection-observation.json');args=parser.parse_args()
    if not 1<=args.seconds<=120:parser.error('1..120 seconds required')
    process=ResearchProcess(args.pid);reader=PoseReader(process);samples=[];start=time.monotonic()
    try:
        while time.monotonic()-start<args.seconds:
            try:samples.append({'elapsed':time.monotonic()-start,**sample(reader)})
            except (OSError,ValueError):pass
            time.sleep(.02)
    finally:process.close()
    args.output.write_text(json.dumps({'playerWrites':False,'samples':samples}),encoding='utf-8')
    if not samples:raise RuntimeError('No valid original camera samples captured')
    print(json.dumps({'samples':len(samples),'maxCameraMatrixDifference':max(s['cameraMatrixDifference'] for s in samples),
        'positionSpan':[max(s['camera'][i] for s in samples)-min(s['camera'][i] for s in samples) for i in range(3)],
        'forwardSpan':[max(s['forward'][i] for s in samples)-min(s['forward'][i] for s in samples) for i in range(3)]}))
