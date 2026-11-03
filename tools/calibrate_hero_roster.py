"""Explicit unattended offline hero observation, not a gameplay acceptance claim.

Uses only the verified research executable and the existing single callback
owners. Records native ammo/state/factory evidence plus actual window captures.
"""
import argparse,json,struct,subprocess,time,urllib.request
from pathlib import Path
from observe_overwatch import ROOT,ResearchProcess
from observe_native_weapon_states import WeaponStates
from native_hero_profiles import camera_definition
from launch_passthrough_session import first_person_ready

ROSTER=[('Genji',0x29,218),('McCree',0x42,312),('Pharah',8,402),('Reaper',2,497),
 ('Soldier76',0x6e,585),('Tracer',3,680),('Bastion',0x15,864),('Hanzo',5,961),
 ('Junkrat',0x65,1052),('Mei',0xdd,1146),('Torbjorn',6,1241),('Widowmaker',10,1334),
 ('DVa',0x7a,1525),('Reinhardt',7,1619),('Roadhog',0x40,1714),('Winston',9,1808),
 ('Zarya',0x68,1902),('Lucio',0x79,2088),('Mercy',4,2179),('Symmetra',0x16,2272),('Zenyatta',0x20,2365)]

def api(route):
    with urllib.request.urlopen('http://127.0.0.1:32133/'+route,timeout=3) as r:return json.load(r)

def report(path):
    for attempt in range(8):
        try:return json.loads(path.read_text())
        except (OSError,ValueError):
            if attempt==7:raise
            time.sleep(.03)

def drive(*commands):
    result=subprocess.run(['um','win','drive','--proc','GameClientApp.patched.exe',*commands],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=30)
    if result.returncode or 'ready no-window' in result.stdout or 'focus -> fail' in result.stdout:raise RuntimeError((result.stderr+result.stdout)[-1000:])
    return result.stdout

def observe(pid):
    p=ResearchProcess(pid)
    try:
        r=WeaponStates(p);sample=r.sample_weapon(require_volley=False);admin=r.pointer(p.base+0x17b7f90)
        table=p.read(r.pointer(admin+0x10),65536);controller=r.entity(table,sample['localId']);model=r.entity(table,sample['modelId'])
        hero=r.unpack('<Q',r.component(controller,0x3f)+0x98)[0];scripts=[]
        for (instance,graph,resource),definition in r.graph_cache.items():
            if not definition['volleyNodes']:continue
            nodes=r.stu_list(graph+0x50);volleys=[]
            for index in definition['volleyNodes']:
                try:damage=r.bindings.impact_damage(nodes[index])
                except (OSError,ValueError) as e:damage={'error':str(e)}
                volleys.append({'node':index,'damage':damage})
            scripts.append({'resource':f'{resource:016x}','flags':r.unpack('<I',instance+0x258)[0],
                            'volleys':volleys,'variables':r.varbag(r.pointer(instance+0x98))})
        local=r.component(controller,0x2f);scene=r.component(model,1)
        eye=r.unpack('<3f',local+0x1500);feet=r.unpack('<3f',scene+0x60)
        return {'hero':hero,'modelId':sample['modelId'],'camera':camera_definition(r.bindings,model),
                'observedEyeHeight':eye[1]-feet[1],'scripts':scripts,'nativeVariables':sample['observedVariables']}
    finally:p.close()

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pid',type=int,required=True)
    parser.add_argument('--heroes',nargs='*');parser.add_argument('--audio',action='store_true');args=parser.parse_args()
    out=ROOT/'research/hero-roster-calibration';out.mkdir(exist_ok=True)
    selected=[r for r in ROSTER if not args.heroes or r[0] in args.heroes]
    for name,suffix,x in selected:
        record={'name':name,'pid':args.pid,'expectedHero':0x02e0000000000000+suffix,'inputAuthorized':True}
        try:
            commands=['focus','mup']
            if first_person_ready(args.pid):commands+=['key 0x48','sleep 450']
            commands += [f'click {x} 1224','sleep 450','click 1280 1358','sleep 1800']
            drive(*commands)
            deadline=time.monotonic()+6
            while True:
                before=observe(args.pid);record['selectedObservation']=before
                if before['hero']==record['expectedHero'] and first_person_ready(args.pid):break
                if time.monotonic()>deadline:raise RuntimeError('Native hero differs from selected menu card or picker was not confirmed')
                time.sleep(.25)
            deadline=time.monotonic()+6
            while True:
                body=report(ROOT/f'native-host/build/body-sync-{args.pid}.json')
                if body.get('hero')==before['hero'] and body.get('modelId')==before['modelId'] and body.get('writes',0) and not body.get('failures'):break
                if time.monotonic()>deadline:raise RuntimeError('Body did not bind the actual selected hero')
                time.sleep(.2)
            # Aim slightly upward, away from the saved terrain and mobs. Mouse
            # vertical gain0.1degree/pixel was measured in this native client.
            pitch=api('combat').get('pitch',0);drive('focus',f'rel 0 {round((-12-pitch)/.1)}','sleep 350')
            record['before']=observe(args.pid);record['body']=body
            native_before=report(ROOT/f'native-host/build/native-emissions-{args.pid}.json')
            record['factoryBefore']=native_before.get('factoryCalls',0)
            recording=None
            if args.audio:
                recording=subprocess.Popen(['um','win','record','--pid',str(args.pid),'--exe','GameClientApp.patched.exe','--out',str(out/(name+'-native')),'--seconds','4','--fps','30'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                time.sleep(.8)
            drive('focus','mdown 1280 720','sleep 650','mup','sleep 600')
            record['after']=observe(args.pid)
            if recording:
                stdout,stderr=recording.communicate(timeout=20);record['recordingExit']=recording.returncode
                if recording.returncode:record['recordingError']=stderr.decode(errors='replace')[-1000:]
            else:
                subprocess.run(['um','win','shot','--exe','GameClientApp.patched.exe',str(out/(name+'.png')),'--scale','0.33'],cwd=ROOT,check=True,capture_output=True,timeout=15)
            native=report(ROOT/f'native-host/build/native-emissions-{args.pid}.json')
            record['factoryAfter']=native.get('factoryCalls',0)
            record['factoryObservations']=[v for v in native.get('factoryObservations',[]) if v.get('hero')==record['expectedHero']]
            record['combatReady']=native.get('combatReady');record['guest']=api('combat')
        except Exception as error:record['error']=str(error)
        (out/(name+'.json')).write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'hero':name,'error':record.get('error'),'factoryDelta':record.get('factoryAfter',0)-record.get('factoryBefore',0),'mcCombatReady':record.get('combatReady')}),flush=True)


if __name__=='__main__':main()
