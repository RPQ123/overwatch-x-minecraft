"""Real 21-hero walk/reversal/release/model survey in the isolated full-mod lab.

Reads unique MC body ticks and the original mover, never generates game motion.
All input goes through UM's foreground-protected driver. Baseline observations
are evidence, not acceptance. Screenshots need separate actual visual review.
"""
import argparse, ctypes, json, math, statistics, struct, subprocess, sys, time
from pathlib import Path
from calibrate_hero_actions import select
from calibrate_hero_roster import ROOT, ROSTER, api, drive, report
from observe_overwatch import ResearchProcess
from native_health_binding import inspect_health
from verify_world_hero_switch import ready, native
from verify_genji_elimination_reset import post
from verify_native_light_angles import point

sys.path.insert(0, str(ROOT/'bridge'))
from world_frames import MCFrames


class Ticks:
    def __init__(self, pid):
        self.pid=pid; self.frames=MCFrames(); self.process=ResearchProcess(pid)
        self.r,self.binding,self.verify=inspect_health(self.process)
        self.model=self.r.pointer(self.binding['health']+8)
        self.mover=self.r.component(self.model,0x15)
        self.pose_handle=self.frames.kernel.OpenFileMappingW(4,False,'Local\\OWMCHostPose')
        if not self.pose_handle:raise ValueError('No original host pose mapping')
        self.pose=self.frames.kernel.MapViewOfFile(self.pose_handle,4,0,0,4096)
        if not self.pose:raise ValueError('No original host pose view')

    def read(self):
        b=ctypes.string_at(self.frames.address+1536,256)
        seq=struct.unpack_from('<Q',b,64)[0]
        if not seq or seq&1 or b[:8]!=b'OWBODY01':return None
        if ctypes.string_at(self.frames.address+1600,8)!=b[64:72]:return None
        pid,source=struct.unpack_from('<II',b,16);wall=struct.unpack_from('<Q',b,72)[0]
        if pid!=self.pid or not 0<=round(time.time()*1000)-wall<=250:raise ValueError('Stale/wrong body identity')
        pose=ctypes.string_at(self.pose,4096)
        if struct.unpack_from('<Q',pose,64)[0]&1:return None
        self.verify()
        return dict(sequence=seq,wall=wall,sourcePid=source,position=struct.unpack_from('<3d',b,96),
                    bodyVelocity=struct.unpack_from('<3f',b,120),grounded=bool(struct.unpack_from('<I',b,80)[0]),
                    originalVelocity=self.r.unpack('<3f',self.mover+0x7e0+0x230),
                    bits=struct.unpack_from('<I',pose,324)[0],inputActive=bool(struct.unpack_from('<I',pose,328)[0]))

    def close(self):
        self.frames.kernel.UnmapViewOfFile(self.pose);self.frames.kernel.CloseHandle(self.pose_handle)
        self.frames.close();self.process.close()


def movement_ready(pid,actor):
    """Unimplemented combat must not hide otherwise usable native models/motion."""
    end=time.monotonic()+12
    while True:
        h=api('health');c=api('combat');b=report(ROOT/f'native-host/build/body-sync-{pid}.json')
        loc=c.get('locomotion') or {};p=h.get('player') or {}
        if (loc.get('ready') and loc.get('hero')==actor['hero'] and loc.get('modelId')==actor['modelId']
                and b.get('hero')==actor['hero'] and b.get('modelId')==actor['modelId'] and b.get('enabled')
                and b.get('worldStable') and not b.get('failures') and p.get('alive') and p.get('health')==20):
            n=native(pid)
            if n['hero']==actor['hero'] and n['modelId']==actor['modelId'] and n['hp']==n['maximum']>0:
                return dict(health=h,combat=c,body=b,native=n)
        if time.monotonic()>end:raise ValueError('Current hero movement/model did not settle')
        time.sleep(.1)


def survey(pid,folder,heroes,baseline=False,jump=False):
    folder=folder.resolve()
    if ROOT/'research' not in folder.parents:raise ValueError('Private research folder required')
    folder.mkdir(parents=True,exist_ok=True)
    checked=ResearchProcess(pid);checked.close()
    before=api('health')
    if not before['worldName'].startswith('Overwatch Twilight Switch '):raise ValueError('Full-mod isolated lab required')
    out=dict(pid=pid,baseline=baseline,heroes=[],passed=False,initial=before,visualAcceptance='pending-review')
    try:
        select(pid,'McCree');ready(pid);point(180,0);post('flight-open');time.sleep(.5)
        fixture=api('combat')
        if fixture.get('testError') or 'flightFloorY' not in fixture:raise ValueError('Reversible air platform unavailable')
        if api('health')['player']['flying']:drive('focus','key 0x75','sleep 600')
        center=api('health')['player'];out['fixture']=dict(floor=fixture['flightFloorY'],center=center)
        for name in heroes:
            row=dict(hero=name,passed=False);out['heroes'].append(row)
            actor=select(pid,name);state=movement_ready(pid,actor);row['actor']=actor;row['nativeHealth']=state['native']
            if state['health']['sourcePid']!=before['sourcePid']:raise ValueError('MC identity changed during survey')
            if not baseline:
                post('locomotion-origin');time.sleep(.4)
                if api('combat').get('testError'):raise ValueError('Safe fixture recenter failed')
            point(180,0);time.sleep(.2)
            p=api('health')['player']
            if p['flying'] or not p['onGround']:raise ValueError('Hero is not grounded without creative flight: '+name)
            reader=Ticks(pid)
            try:
                commands=['focus','key 0x57 down','sleep 650','key 0x57 up','key 0x53 down','sleep 650','key 0x53 up',
                          'sleep 350','key 0x44 down','sleep 350','key 0x44 up','key 0x41 down','sleep 350','key 0x41 up','sleep 350']
                proc=subprocess.Popen(['um','win','drive','--proc','GameClientApp.patched.exe',*commands],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                rows=[];last=0;start=time.monotonic()
                while proc.poll() is None:
                    if time.monotonic()-start>12:proc.terminate();raise ValueError('Protected input deadline')
                    sample=reader.read()
                    if sample is not None and sample['sequence']!=last:
                        last=sample['sequence'];rows.append(sample)
                    time.sleep(.009)
                stdout,stderr=proc.communicate(timeout=2)
                if proc.returncode or b'-> fail' in stdout:raise ValueError((stdout+stderr).decode(errors='replace')[-1000:])
                row['ticks']=rows;row['input']=stdout.decode(errors='replace')
                deltas=[]
                for a,b in zip(rows,rows[1:]):
                    if b['sequence']-a['sequence']!=2:continue
                    d=[b['position'][i]-a['position'][i] for i in range(3)]
                    deltas.append(dict(bits=b['bits'],previousBits=a['bits'],delta=d,speed=math.hypot(d[0],d[2])*20,
                                       bodySpeed=math.hypot(b['bodyVelocity'][0],b['bodyVelocity'][2]),grounded=b['grounded']))
                def speeds(bits):return [v['speed'] for v in deltas if v['bits']==bits and v['previousBits']==bits]
                forward=speeds(1);back=speeds(2);strafe=speeds(8)
                stopped=[v for v in deltas if v['bits']==0 and v['previousBits']==0]
                reversals=[v for v in deltas if v['bits']==2 and v['previousBits'] in (1,2)]
                row['summary']=dict(forwardMedian=statistics.median(forward) if forward else 0,
                    backwardMedian=statistics.median(back) if back else 0,strafeMedian=statistics.median(strafe) if strafe else 0,
                    forwardTicks=len(forward),backwardTicks=len(back),
                    stoppedDrift=max((v['speed']/20 for v in stopped),default=0),
                    wrongReverseTicks=sum(v['delta'][2]<-1e-4 for v in reversals),
                    airborneTicks=sum(not v['grounded'] for v in rows),
                    bodySpeedMedian=statistics.median(v['bodySpeed'] for v in deltas if v['bits']==1) if forward else 0)
                row['locomotion']=api('combat')['locomotion'];row['motor']=api('combat')['motor']
                row['body']=report(ROOT/f'native-host/build/body-sync-{pid}.json')
                row['live']=report(ROOT/f'native-host/build/world-live-{pid}.json')
                if jump and name!='Pharah':
                    height=api('health')['player']['feetY'];drive('focus','key 0x20 down','sleep 100','key 0x20 up')
                    samples=[];end=time.monotonic()+1.3
                    while time.monotonic()<end:samples.append(api('health')['player']);time.sleep(.04)
                    row['jump']=dict(height=max(v['feetY'] for v in samples)-height,landed=samples[-1]['onGround'],flying=any(v['flying'] for v in samples))
                image=folder/(name+'.png')
                subprocess.run(['um','win','shot','--exe','GameClientApp.patched.exe',str(image),'--scale','.33'],cwd=ROOT,capture_output=True,check=True,timeout=20)
                row['image']=str(image.relative_to(ROOT));row['deltas']=deltas
                s=row['summary'];base=row['locomotion']['baseSpeeds']
                row['passed']=bool(not baseline and s['forwardTicks']>=7 and s['backwardTicks']>=7
                    and abs(s['forwardMedian']-base[0])<.2 and abs(s['backwardMedian']-base[1])<.2
                    and abs(s['bodySpeedMedian']-s['forwardMedian'])<.2
                    and s['stoppedDrift']<.002 and s['wrongReverseTicks']==0 and s['airborneTicks']==0
                    and row['body']['hero']==actor['hero'] and row['body']['modelId']==actor['modelId'] and not row['body']['failures'])
                if jump and name!='Pharah':row['passed'] &= .7<row['jump']['height']<1.5 and row['jump']['landed'] and not row['jump']['flying']
                if jump and name=='Pharah':row['jumpRoute']='native-hover: requires separate real flight/resource verification'
                print(json.dumps(dict(hero=name,baseline=baseline,passed=row['passed'],**s)),flush=True)
            finally:reader.close()
            (folder/'result.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
        out['passed']=not baseline and all(v['passed'] for v in out['heroes'])
    except Exception as error:out['error']=repr(error);raise
    finally:
        try:
            drive('focus','mup','mup right',*[f'key {k} up' for k in ('0x57','0x53','0x41','0x44','0x20','0x10')])
            if not api('health')['player']['flying']:drive('focus','key 0x75','sleep 150')
            post('cleanup');time.sleep(.25);out['cleaned']=api('combat').get('wallBlocks')==0
        except Exception as failure:out['cleanupError']=repr(failure)
        (folder/'result.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pid',type=int,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--heroes',nargs='+',default=[v[0] for v in ROSTER]);p.add_argument('--baseline',action='store_true');p.add_argument('--jump',action='store_true')
    a=p.parse_args();survey(a.pid,a.output,a.heroes,a.baseline,a.jump)
