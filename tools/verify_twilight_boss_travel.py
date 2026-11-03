"""Actual F12/number-key travel to original TF rooms; no simulated attacks or spawned bosses."""
import argparse,json,time,psutil,subprocess,sys
from pathlib import Path
from verify_recall_empty_history import Identity,PersistentDrive,ROOT,EXE,PROFILE,JAR,PATCHED_SHA256,digest,require,request
from calibrate_hero_roster import observe,report
from launch_passthrough_session import first_person_ready,installed_modules
sys.path.insert(0,str(ROOT/'bridge'))
from world_frames import MCFrames

BOSSES=('naga','lich','minoshroom','hydra','knight_phantom','ur_ghast','alpha_yeti','snow_queen')

class BossIdentity(Identity):
    """Separate travel-only scope; the older destructive Switch fixture guard is unchanged."""
    def __init__(self,args):
        self.args=args;self.native=psutil.Process(args.pid);self.mc=psutil.Process(args.mc_pid);self.quick()
        require(Path(self.native.exe()).resolve()==EXE.resolve() and digest(EXE)==PATCHED_SHA256,'Wrong guarded offline target')
        require(Path(self.mc.exe()).resolve().is_relative_to((ROOT/'minecraft-1.21.1/runtime').resolve()),'Wrong MC runtime')
        command=self.mc.cmdline();require('--gameDir' in command and Path(command[command.index('--gameDir')+1]).resolve()==PROFILE.resolve(),'Wrong isolated profile')
        require(args.world.startswith('Overwatch Twilight Boss Free '),'Explicit Boss Free save required')
        for value in ('-Dowmc.twilightTrial=true','-Dowmc.creativeWorld=true','-Dowmc.worldName='+args.world):require(value in command,'Missing trial argument '+value)
        settings_path=ROOT/'passthrough-settings.json';settings=json.loads(settings_path.read_text(encoding='utf-8'))
        require(settings.get('worldName')==args.world and settings.get('twilightTrial') is True,'World settings differ')
        require(digest(JAR)==args.guest_sha256.lower() and JAR.stat().st_mtime<=args.mc_created+1,'Installed JAR differs or was replaced live')
        from twilight_forest import NAME,validate
        validate(PROFILE/'mods'/NAME)
        self.files={p:(p.stat().st_size,p.stat().st_mtime_ns) for p in (EXE,JAR,settings_path)}
        self.proof=dict(pid=args.pid,creation=args.created,mcPid=args.mc_pid,mcCreation=args.mc_created,world=args.world,jar=args.guest_sha256,command=command,settings=settings)

def main(a):
    folder=a.output.resolve();require(ROOT/'research' in folder.parents,'Private research output required');folder.mkdir(parents=True,exist_ok=False)
    out={'passed':False,'input':[],'results':[],'noFixturesOrBossesSpawned':True,
         'visualDoorAcceptance':'pending manual review; telemetry alone cannot prove an accessible doorway'};driver=None;frames=None
    def save(): (folder/'result.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    try:
        require(a.profile_backed_up,'Back up the real profile before input')
        identity=BossIdentity(a);out['identity']=identity.proof;identity.health()
        frames=MCFrames()
        require(len([x for x in installed_modules(a.pid) if x.startswith('owmc-')])==6,'Unexpected callback owners')
        driver=PersistentDrive(identity,folder,out['input']);driver.send('focus')
        if not first_person_ready(a.pid):
            driver.send('click 218 1224');time.sleep(.6);driver.send('click 1280 1358')
        until=time.monotonic()+10
        while not first_person_ready(a.pid):
            identity.health();require(time.monotonic()<until,'Hero confirmation timed out');time.sleep(.1)
        time.sleep(1.2);out['nativeBefore']=observe(a.pid)
        for boss in a.bosses:
            row={'boss':boss,'samples':[]};out['results'].append(row);identity.health();require(driver.foreground(),'Input interference')
            world=request('world');menu=world.get('bossTravelMenu',{})
            if not menu.get('open'):driver.send('hold 0x7b 140');time.sleep(.4)
            world=request('world');require(world.get('bossTravelMenu',{}).get('open'),'Actual F12 menu did not open')
            if not (folder/'menu.png').exists():subprocess.run(['um','win','shot','--exe',EXE.name,str(folder/'menu.png'),'--scale','.5'],check=True,capture_output=True)
            base=world.get('bossTravel',{}).get('requestId',0);driver.send(f'hold {hex(0x31+BOSSES.index(boss))} 140');until=time.monotonic()+135
            while True:
                identity.quick();require(driver.foreground(),'Input interference; no refocus attempted')
                world=request('world');travel=world.get('bossTravel',{});row['samples'].append({'wall':round(time.time()*1000),'travel':travel,'menu':world.get('bossTravelMenu',{})});save()
                if travel.get('requestId',0)>base and not travel.get('busy'):break
                require(time.monotonic()<until,'Bounded travel test expired');time.sleep(.5)
            require(not travel.get('error') and travel.get('phase')=='complete','Travel failed: '+str(travel.get('error')))
            require(travel.get('boss')==boss and travel.get('progressionDisabled'),'Wrong destination or progression still enabled')
            require(travel.get('evidence',{}).get('releasedTickets',0)>0,'Owned loading tickets were not explicitly released')
            require(travel.get('evidence',{}).get('resolutionMethod'),'Original spawner/boss resolution was not recorded')
            destination=travel.get('destination',{});require(destination.get('dimension')=='twilightforest:twilight_forest','Did not enter the actual dimension')
            # Real dimension transfer can briefly display vanilla's loading screen.
            # Wait for the same process/save and actual destination, never send inputs through it.
            until=time.monotonic()+25
            while True:
                identity.quick();require(driver.foreground(),'Input interference during dimension load')
                fresh=request('health');player=fresh.get('player') or {}
                require(fresh.get('sourcePid')==a.mc_pid and fresh.get('worldName')==a.world,'Source changed during transfer')
                atDestination=all(abs(player.get(k,1e12)-destination.get(d,0))<.7 for k,d in [('x','x'),('z','z')])
                atFloor=abs(player.get('feetY',1e12)-destination.get('y',0))<.7
                if (player.get('alive') and not player.get('survival') and player.get('screen')=='none'
                        and atDestination and atFloor and player.get('onGround')
                        and player.get('groundBlock') not in (None,'minecraft:void_air','minecraft:air')):
                    row['health']=fresh;break
                require(time.monotonic()<until,'Actual destination gameplay did not settle');time.sleep(.2)
            time.sleep(1)
            for _ in range(6):
                frame=frames.latest()
                require(frame is not None and frame.source_pid==a.mc_pid and frame.host_frame>0,'No actual rendered camera frame')
                yaw,pitch,_=frame.rotation
                delta=(destination.get('yaw',yaw)-yaw+180)%360-180
                if abs(delta)<1 and abs(pitch)<1:break
                driver.send(f'rel {round(delta/.1)} {round(-pitch/.1)}');time.sleep(.25)
            time.sleep(1);row['after']=request('combat');row['native']=observe(a.pid)
            frame=frames.latest();row['renderedCamera']={'rotation':frame.rotation,'sourcePid':frame.source_pid,'hostFrame':frame.host_frame}
            require(abs((destination['yaw']-frame.rotation[0]+180)%360-180)<2 and abs(frame.rotation[1])<2,'Actual camera did not face the original room')
            require(row['health']['player']['alive'] and row['health']['player']['health']>0,'Destination harmed player')
            row['compositor']=dict((k,v) for k,v in report(ROOT/f'native-host/build/world-live-{a.pid}.json').items() if k in ('enabled','failures','viewMode','viewLightOwned','viewLightHero','viewLightWorldId'))
            require(row['compositor'].get('enabled') and not row['compositor'].get('failures') and row['compositor'].get('viewMode')==1,'Fusion did not resume after travel')
            subprocess.run(['um','win','shot','--exe',EXE.name,str(folder/(boss+'.png')),'--scale','.5'],check=True,capture_output=True)
            row['passed']=True;save();time.sleep(.6)
        out['passed']=True
    except Exception as error:out['error']=repr(error)
    finally:
        if driver:driver.close()
        if frames:frames.close()
        save();print(json.dumps({k:out.get(k) for k in ('passed','error')},ensure_ascii=True),flush=True)
    return out['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name,kind in [('pid',int),('created',float),('mc-pid',int),('mc-created',float),('world',str),('guest-sha256',str)]:p.add_argument('--'+name,required=True,type=kind)
    p.add_argument('--output',required=True,type=Path);p.add_argument('--bosses',nargs='+',choices=BOSSES,default=list(BOSSES));p.add_argument('--profile-backed-up',action='store_true')
    raise SystemExit(0 if main(p.parse_args()) else 1)
