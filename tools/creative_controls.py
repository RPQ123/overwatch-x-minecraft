"""Original OW input/view to isolated MC creative edits; no OS input automation."""
import argparse,http.client,json,math,struct,time
from pathlib import Path
from observe_overwatch import ROOT,ResearchProcess,PoseReader
from diagnose_projection import sample as camera_sample

PALETTE=['minecraft:stone','minecraft:oak_planks','minecraft:grass_block','minecraft:stone_bricks','minecraft:oak_log','minecraft:dirt']

def publish_hud(selected,flying):
    from PIL import Image,ImageDraw,ImageFont
    image=Image.new('RGBA',(256,64),(18,22,27,255));draw=ImageDraw.Draw(image)
    font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',12)
    draw.text((7,1),'MINECRAFT WORLD / CREATIVE',font=font,fill=(140,240,160))
    label=selected.split(':')[1].replace('_',' ').upper()
    draw.text((7,16),f'BLOCK: {label}    FLY: {"ON" if flying else "OFF"}',font=font,fill='white')
    small=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',10)
    draw.text((7,34),'J Break | K Place | B Next | Mouse Attack',font=small,fill=(225,225,225))
    draw.text((7,48),'Double Space Fly | Space Up | Ctrl Down',font=small,fill=(225,225,225))
    data=struct.pack('<8s4I',b'OWMCB001',1,6,256,64)
    for x,y in ((0,0),(1,0),(1,1),(0,0),(1,1),(0,1)):data+=struct.pack('<6f',x,y,0,x,y,1)
    data+=image.tobytes();output=ROOT/'native-host/build/creative-hud.bin';temporary=output.with_suffix('.tmp');temporary.write_bytes(data);temporary.replace(output)

def ray_hit(eye,direction,origin,blocks,reach=6):
    if not all(math.isfinite(v) for v in (*eye,*direction,*origin)):raise ValueError('Nonfinite ray')
    length=math.sqrt(sum(v*v for v in direction))
    if length<.001:raise ValueError('No aim direction')
    direction=tuple(v/length for v in direction);point=tuple(eye[i]-origin[i] for i in range(3))
    cell=[math.floor(v) for v in point]
    step=[1 if v>0 else -1 if v<0 else 0 for v in direction]
    delta=[abs(1/v) if v else math.inf for v in direction]
    maximum=[((cell[i]+1-point[i])/direction[i] if step[i]>0 else (cell[i]-point[i])/direction[i] if step[i]<0 else math.inf) for i in range(3)]
    normal=(0,0,0);distance=0
    for _ in range(128):
        if tuple(cell) in blocks:return tuple(cell),normal,distance
        axis=min(range(3),key=lambda i:maximum[i]);distance=maximum[axis]
        if distance>reach:return None
        cell[axis]+=step[axis];maximum[axis]+=delta[axis];n=[0,0,0];n[axis]=-step[axis];normal=tuple(n)
    return None

def intersects_hero(cell,foot,origin):
    lo=[origin[i]+cell[i] for i in range(3)]
    return foot[0]+.3>lo[0] and foot[0]-.3<lo[0]+1 and foot[1]+1.8>lo[1] and foot[1]<lo[1]+1 and foot[2]+.3>lo[2] and foot[2]-.3<lo[2]+1

def occupancy():
    data=(ROOT/'native-host/build/patch-mesh.bin').read_bytes()
    if len(data)<64 or data[:8] not in (b'OWMCB003',b'OWMCB004'):raise ValueError('Creative snapshot required')
    version,vertices,width,height=struct.unpack_from('<4I',data,8);session,sequence,tick,produced=struct.unpack_from('<4Q',data,24)
    count,flags=struct.unpack_from('<2I',data,56)
    if version not in (3,4) or flags or count>12288 or vertices>65536 or not 1<=width<=256 or not 1<=height<=256 or len(data)!=64+count*16+vertices*28+width*height*4 or abs(time.time()*1000-produced)>2000:raise ValueError('Invalid or stale creative snapshot')
    return session,sequence,{tuple(v[:3]):v[3] for v in struct.iter_unpack('<iiiI',data[64:64+count*16])}

def edit(cell,block):
    c=http.client.HTTPConnection('127.0.0.1',32132,timeout=1)
    try:
        c.request('POST','/v1/block',json.dumps(dict(zip(('x','y','z','block'),(*cell,block)))),{'Content-Type':'application/json'})
        r=c.getresponse();r.read()
        if r.status!=202:raise ValueError(f'Creative guest rejected edit {r.status}')
    finally:c.close()

def run(pid):
    process=ResearchProcess(pid);reader=PoseReader(process)
    previous=0;selected=0;last_edit=0;pending=None;edits=0;last_health=0;last_action=None;hud_state=None;last_observer=0;observer_center=None
    import ctypes
    user32=ctypes.WinDLL('user32',use_last_error=True);user32.GetAsyncKeyState.argtypes=[ctypes.c_int];user32.GetAsyncKeyState.restype=ctypes.c_short
    user32.GetForegroundWindow.restype=ctypes.c_void_p;user32.GetWindowThreadProcessId.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_ulong)]
    try:
        while True:
            now=time.monotonic()
            try:
                host=json.loads((ROOT/f'native-host/build/host-{pid}.json').read_text())
                if not host.get('enabled') or not host.get('creativeMode'):return
                if not host.get('patchFresh') or not host.get('creativeEntered'):time.sleep(.05);continue
                foreground_pid=ctypes.c_ulong();user32.GetWindowThreadProcessId(user32.GetForegroundWindow(),ctypes.byref(foreground_pid))
                # Read-only hotkeys, gated to this exact foreground game. No simulated OS input.
                buttons=0
                if foreground_pid.value==pid:
                    for key,bit in ((0x4a,1),(0x4b,2),(0x42,16)):
                        if user32.GetAsyncKeyState(key)&0x8000:buttons|=bit
                rising=buttons&~previous;previous=buttons
                if rising&16:selected=(selected+1)%len(PALETTE)
                pose=camera_sample(reader)
                if host.get('streamedWorld') and now-last_observer>.3:
                    center=(math.floor((pose['foot'][0]-host['patchOrigin'][0])/8)*8,math.floor((pose['foot'][2]-host['patchOrigin'][2])/8)*8)
                    if center!=observer_center:
                        c=http.client.HTTPConnection('127.0.0.1',32132,timeout=1)
                        try:
                            c.request('POST','/v1/observer',json.dumps({'x':center[0],'z':center[1]}),{'Content-Type':'application/json'});response=c.getresponse();response.read()
                            if response.status==202:observer_center=center
                        finally:c.close()
                    last_observer=now
                session,sequence,blocks=occupancy()
                if session!=host.get('appliedSession') or sequence<host.get('appliedSequence',0):time.sleep(.02);continue
                # Wait until the actual guest state reflects the last edit; no duplicate speculative edits.
                if pending is not None:
                    cell,present,deadline=pending
                    if (cell in blocks)==present or now>deadline:pending=None
                hit=ray_hit(pose['camera'],pose['forward'],host['patchOrigin'],blocks)
                if pending is None and hit and now-last_edit>=.2 and buttons&3:
                    cell,normal,_=hit
                    if buttons&1 and cell[1]>-4:
                        edit(cell,'minecraft:air');pending=(cell,False,now+2);last_action={'action':'break','cell':cell}
                    elif buttons&2 and any(normal):
                        place=tuple(cell[i]+normal[i] for i in range(3))
                        bound=1000000 if host.get('streamedWorld') else 15
                        if -bound<=place[0]<=bound and -bound<=place[2]<=bound and -3<=place[1]<=7 and place not in blocks and not intersects_hero(place,pose['foot'],host['patchOrigin']):
                            edit(place,PALETTE[selected]);pending=(place,True,now+2);last_action={'action':'place','cell':place,'block':PALETTE[selected]}
                    if pending:edits+=1;last_edit=now
                if now-last_health>=.5:
                    wanted_hud=(selected,host.get('flying',False))
                    if wanted_hud!=hud_state:publish_hud(PALETTE[selected],wanted_hud[1]);hud_state=wanted_hud
                    status={'pid':pid,'mode':'creative-superflat','selectedBlock':PALETTE[selected],'editsSubmitted':edits,'target':hit[0] if hit else None,
                            'lastAction':last_action,'controls':'J break, K place, B next block; mouse reserved for native attack; double Space flight','nativeWeaponHit':False}
                    output=ROOT/'native-host/build/creative-controls.json';temporary=output.with_suffix('.tmp');temporary.write_text(json.dumps(status));temporary.replace(output);last_health=now
            except (ValueError,OSError,http.client.HTTPException):
                pass
            time.sleep(.05)
    finally:process.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pid',type=int,required=True);args=parser.parse_args()
    if args.pid<=0:parser.error('Exact offline research PID required')
    try:run(args.pid)
    except KeyboardInterrupt:pass
