"""Real native movement modifiers and MC displacement, with a reversible floor."""
import argparse,json,math,subprocess,time
from observe_overwatch import ROOT
from calibrate_hero_actions import select
from calibrate_hero_roster import api,drive
from verify_genji_elimination_reset import post

def action(commands):
    before=api('health')['player'];rows=[];start=time.monotonic()
    process=subprocess.Popen(['um','win','drive','--proc','GameClientApp.patched.exe','focus',*commands],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    while process.poll() is None or time.monotonic()-start<1:
        if time.monotonic()-start>10:process.kill();raise RuntimeError('Movement input deadline')
        rows.append(dict(t=time.monotonic()-start,player=api('health')['player'],motor=api('combat').get('motor')));time.sleep(.03)
    out,err=process.communicate(timeout=1)
    if process.returncode or b'-> fail' in out:raise ValueError((out+err).decode(errors='replace'))
    after=api('health')['player'];speed=max((v.get('motor') or {}).get('horizontalSpeed',0) for v in rows)
    original=[math.hypot(v['motor']['nativeVelocity'][0],v['motor']['nativeVelocity'][2]) for v in rows if v.get('motor') and 'nativeVelocity' in v['motor']]
    return dict(before=before,after=after,displacement=math.hypot(after['x']-before['x'],after['z']-before['z']),peakNativeSpeed=speed,
        peakOriginalSpeed=max(original,default=0),minOriginalSpeed=min(original,default=0),rows=rows)

def main(pid,heroes,output=None):
    folder=(ROOT/output).resolve() if output else ROOT/'research'
    if ROOT/'research'!=folder and ROOT/'research' not in folder.parents:raise ValueError('Private research output required')
    folder.mkdir(parents=True,exist_ok=True)
    result=dict(pid=pid,heroes=[])
    for name in heroes:
        row=dict(hero=name);result['heroes'].append(row)
        try:
            select(pid,name)
            deadline=time.monotonic()+8
            while 'yaw' not in api('combat'):
                if time.monotonic()>deadline:raise ValueError('Current combat context did not settle')
                time.sleep(.1)
            post('flight-open');time.sleep(.5)
            fixture=api('combat')
            if fixture.get('testError') or 'flightFloorY' not in fixture:raise ValueError('Safe floor unavailable')
            yaw=api('combat')['yaw'];turn=(180-yaw+180)%360-180
            drive('focus',f'rel {round(turn/.1)} 0','sleep 100','key 0x75','sleep 600')
            row['walk']=action(['hold 0x57 400','sleep 200'])
            if name=='Soldier76':commands=['key 0x57 down','sleep 120','key 0x10','sleep 400','key 0x57 up','sleep 200']
            elif name=='Widowmaker':commands=['mdown 1280 720 right','sleep 1200','hold 0x57 400','mup right','sleep 200']
            elif name=='Hanzo':commands=['mdown 1280 720','sleep 500','hold 0x57 400','mup','sleep 200']
            else:commands=['key 0x10','sleep 1500' if name=='Bastion' else 'sleep 300','hold 0x57 400','sleep 200']
            row['skill']=action(commands)
            walk=row['walk'];skill=row['skill']
            row['passed']=walk['displacement']>1 and walk['peakNativeSpeed']>4.5 and skill['after']['alive'] and skill['after']['onGround']
            if name in ('Bastion','Mei'):row['passed'] &= skill['displacement']<.03 and skill['peakNativeSpeed']<.1
            elif name in ('Soldier76','Reaper'):row['passed'] &= skill['peakOriginalSpeed']>walk['peakOriginalSpeed']*1.05
            else:row['passed'] &= skill['minOriginalSpeed']<walk['peakOriginalSpeed']*.95 and skill['peakNativeSpeed']<walk['peakNativeSpeed'] and skill['displacement']>.1
            print(json.dumps(dict(hero=name,passed=row['passed'],walkDistance=walk['displacement'],walkSpeed=walk['peakNativeSpeed'],skillDistance=skill['displacement'],skillSpeed=skill['peakNativeSpeed'])),flush=True)
        except Exception as e:row.update(passed=False,error=str(e));print(json.dumps(dict(hero=name,passed=False,error=str(e))),flush=True)
        finally:
            drive('focus','mup','mup right','key 0x57 up')
            if not api('health')['player']['flying']:drive('focus','key 0x75','sleep 150')
            post('cleanup');time.sleep(.2);row['cleaned']=api('combat').get('wallBlocks')==0
            result['passed']=all(v.get('passed') and v.get('cleaned') for v in result['heroes'])
            (folder/'native-motor-live-result.json').write_text(json.dumps(result,indent=2)+'\n')
            (folder/f'native-motor-{name}-{pid}-{time.time_ns()}.json').write_text(json.dumps(row,indent=2)+'\n')
            # Cryo uses a different native camera. Wait for its actual exit before
            # the next menu selection; do not mistake that camera for the picker.
            if name=='Mei':
                from launch_passthrough_session import first_person_ready
                deadline=time.monotonic()+8
                while not first_person_ready(pid) and time.monotonic()<deadline:time.sleep(.1)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--pid',required=True,type=int);a.add_argument('--heroes',nargs='+',default=['Soldier76','Bastion','Reaper','Mei','Widowmaker','Hanzo']);a.add_argument('--output');args=a.parse_args();main(args.pid,args.heroes,args.output)
