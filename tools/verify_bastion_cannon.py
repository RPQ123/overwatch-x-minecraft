"""Real original Tank factories -> MC collision/damage/presentation lifecycle.

Exact guarded offline process/profile only. Fixtures create ordinary targets and
reversible cover, never shots or damage. Q uses an explicit diagnostic grant.
"""
import argparse,json,subprocess,time,sys
from pathlib import Path
from stability_selection import choose as choose_stable_hero
import psutil
from observe_overwatch import ROOT,ResearchProcess
from calibrate_hero_roster import api,report,observe,ROSTER
from native_charge import grant_for_test
from observe_native_weapon_states import WeaponStates
from native_factory_calibration import enabled as calibration
from verify_recall_empty_history import Identity,PersistentDrive
from launch_passthrough_session import first_person_ready,installed_modules
from stop_passthrough import emission_owner_version
from verify_deadeye_input_lock import client_command

RESOURCE=0x04000000000003ce

def require(ok,message):
    if not ok:raise ValueError(message)

class Suite:
    def __init__(self,args):
        self.args=args;self.folder=args.output.resolve()
        require(ROOT/'research' in self.folder.parents,'Use private research evidence')
        self.folder.mkdir(parents=True,exist_ok=False)
        self.result=dict(pid=args.pid,passed=False,input=[],explicitLabQGrant=True,
                         mcAuthoredShell=True,selfKnockbackCalibrated=False)
        self.identity=Identity(args);self.result['identity']=self.identity.proof
        require(emission_owner_version(args.pid)==16,'Need the exact pinned emission16 owner')
        require(len([n for n in installed_modules(args.pid) if n.startswith('owmc-')])==6,'Expected six unique adapters')
        self.driver=PersistentDrive(self.identity,self.folder,self.result['input'])
        self.client_size=tuple(map(int,self.driver.send('rect').split()[-2:]))
        client_command('click 1280 720',self.client_size)
        self.result['clientSize']=list(self.client_size)
        self.driver.send('focus');self.recording=None
        self.native=ResearchProcess(args.pid);self.states=WeaponStates(self.native)

    def save(self):
        (self.folder/'result.json').write_text(json.dumps(self.result,indent=2)+'\n',encoding='utf-8')

    def choose(self, name):
        return choose_stable_hero(self, name)

    def post(self,action):
        from verify_recall_empty_history import request
        self.identity.health();require(self.driver.foreground(),'Input interference')
        return request('combat/test/'+action,post=True)

    def data(self):
        self.identity.health();require(self.driver.foreground(),'Input interference')
        return api('combat')

    def aim(self):
        until=time.monotonic()+8
        while True:
            c=self.data();native=report(ROOT/f'native-host/build/native-emissions-{self.args.pid}.json')
            if ('yaw' in c and 'pitch' in c and c.get('locomotion',{}).get('ready')
                    and native.get('combatReady') and native.get('armoryVariants',0)>=(3 if self.result['bastion']['hero']==0x02e0000000000015 else 1)
                    and native.get('modelId')==self.result['bastion']['modelId']):break
            require(time.monotonic()<until,'Current native armory/movement did not settle before aim');time.sleep(.05)
        for _ in range(8):
            c=self.data();delta=(180-c['yaw']+180)%360-180
            if abs(c['pitch'])<1 and abs(delta)<1:return
            self.driver.send(f'rel {round(delta/.1)} {round(-c["pitch"]/.1)}');time.sleep(.3)
        c=self.data();self.result['aimTimeout']=c
        require(abs(c['pitch'])<1 and abs((c['yaw']-180+180)%360-180)<1,'Not a horizontal native view')

    def wait_form(self,form,seconds=14):
        # The MC walking motor is intentionally inactive during creative flight.
        # Observe the supplied original logger instead of mistaking motor.ready
        # for the native transformation. This never fabricates a Begin or shot.
        until=time.monotonic()+seconds;last=None
        trace=self.result.setdefault('nativeFormTrace',[])
        while True:
            c=self.data();sample=self.states.sample_weapon(False,True)
            rows=[r for r in sample['records'].values()
                  if r['script']=='058000000000012f' and r['node'] in (8,9,105)]
            active=[r for r in rows if not r['finished']]
            state=dict(modelId=sample['modelId'],requested=form,records=rows,
                       motor=c.get('motor'),nativeCharge=c.get('nativeCharge'))
            signature=[(r['node'],r['nativeTick'],r['finished']) for r in rows]
            if signature!=last:trace.append(state);last=signature
            expected={'recon':8,'sentry':9,'tank':105}[form]
            if (sample['modelId']==self.result['bastion']['modelId']
                    and len(active)==1 and active[0]['node']==expected):
                c['observedNativeForm']=state;return c
            if time.monotonic()>=until:
                self.result['formTimeout']=state
                raise ValueError('Original native form failed to settle '+form)
            time.sleep(.05)

    def scene(self,name):
        self.post('cannon-'+name);until=time.monotonic()+2
        while True:
            c=self.data()
            require(not c.get('testError'),'Cannon fixture refused: '+str(c.get('testError')))
            if c.get('cannonLab') and (c.get('targetHealth')==20 if name!='splash' else c.get('beamTargets',{}).get('cannonNear')==20):return c
            require(time.monotonic()<until,'Cannon fixture did not become ready');time.sleep(.03)

    def fire(self,wait=.65):
        before=self.data();native_before=report(ROOT/f'native-host/build/native-emissions-{self.args.pid}.json')
        with calibration(self.args.pid):
            self.driver.send(client_command('mdown 1280 720',self.client_size))
            try:time.sleep(.08)
            finally:self.driver.send('mup')
            time.sleep(wait)
            native_after=report(ROOT/f'native-host/build/native-emissions-{self.args.pid}.json')
            after=self.data()
        rows=[r for r in native_after.get('factoryObservations',[]) if r.get('resource')==RESOURCE]
        require(len(rows)==1,'Expected exactly one actual original Tank factory: '+str(rows))
        require(rows[0]['speed']==60 and rows[0]['lifetime']==5 and rows[0]['range']==100
                and rows[0]['evaluatedDamage']==50,'Native resolved Tank config differs')
        require(native_after.get('armoryAccepted',0)==native_before.get('armoryAccepted',0)+1,'No exact-once current factory admission')
        return dict(before=before,after=after,nativeFactory=rows[0])

    def run(self):
        self.result['bastion']=self.choose('Bastion');self.aim()
        self.post('flight-open');time.sleep(.35)
        require(self.identity.health()['player']['flying'],'Need reversible creative air lab')
        self.wait_form('recon');self.scene('direct')
        p=ResearchProcess(self.args.pid)
        try:self.result['grant']=grant_for_test(p,self.args.pid)
        finally:p.close()
        if self.args.record:
            self.recording=subprocess.Popen(['um','win','record','--pid',str(self.args.mc_pid),'--exe','GameClientApp.patched.exe',
                '--out',str(self.folder/'combat'),'--seconds','8','--fps','60'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            time.sleep(1)
        self.driver.send('hold 0x51 150');self.wait_form('tank',5)
        direct=self.result['direct']=self.fire()
        d=direct['after'];b=direct['before'];targets=d.get('beamTargets',{})
        require(abs(d.get('targetHealth',20)-1)<.001,'Tank direct50+blast140 did not apply actual19MC HP: '+str(d.get('targetHealth')))
        require(0<targets.get('cannonNear',20)<targets.get('cannonEdge',0)<20,'Measured inner/outer splash did not attenuate')
        require(targets.get('cannonOutside')==20 and targets.get('cannonCovered')==20,'Range/solid exposure cover was bypassed')
        require(d['tankShellExplosions']==b['tankShellExplosions']+1,'Tank failed to explode exactly once')
        require(abs(d['rocketDirectHealthLost']-b['rocketDirectHealthLost']-5)<.001,'Direct health loss differs')
        self.post('replay');time.sleep(.2);direct['replay']=self.data()
        require(direct['replay'].get('targetHealth')==d['targetHealth'] and direct['replay']['beamTargets']==targets
                and direct['replay']['tankShellExplosions']==d['tankShellExplosions'],'Replay repeated damage/explosion')
        self.save();time.sleep(.5)
        self.scene('splash');splash=self.result['splash']=self.fire()
        d=splash['after'];b=splash['before'];targets=d.get('beamTargets',{})
        require(d['tankShellExplosions']==b['tankShellExplosions']+1 and d.get('blockHits',0)>b.get('blockHits',0),'Real block collision did not explode')
        require(0<targets.get('cannonNear',20)<20 and targets.get('cannonOutside')==20 and targets.get('cannonBehindWall')==20,'Block blast range/occlusion differs')
        require(d['testStoneRemaining']<b['testStoneRemaining'] and d['rocketDirectHealthLost']==b['rocketDirectHealthLost'],'User-custom block explosion failed to destroy stone or invented direct damage')
        self.save();time.sleep(.5)
        self.scene('far');far=self.result['far']=self.fire(1.1)
        d=far['after'];b=far['before']
        require(abs(d.get('targetHealth',20)-1)<.001,'Real48block native shell did not hit')
        require(d['tankShellModelsShown']>b['tankShellModelsShown'] and d['tankShellRenderFrames']>b['tankShellRenderFrames'],'No actual MC shell render frames')
        for shot in (splash,far):
            meter=shot['after'].get('nativeCharge',{})
            require(meter.get('active') and meter.get('skillsReady') and meter.get('charge')==0,
                    'Actual Tank wrongly earned next ultimate charge')
        end=self.result['afterNativeEnd']=self.wait_form('recon')
        until=time.monotonic()+.5
        while not end['nativeCharge']['skillsReady'] or end['nativeCharge']['active']:
            require(time.monotonic()<until,'Charge observer did not accept original Recon End')
            time.sleep(.03);end=self.data();self.result['chargeSettledAfterEnd']=end['nativeCharge']
        require(end['nativeCharge']['charge']<2,'Tank credit leaked across original End')
        time.sleep(.6);self.result['idleChargeAfterEnd']=self.data()['nativeCharge']
        require(self.result['idleChargeAfterEnd']['charge']>end['nativeCharge']['charge'],
                'Natural idle charge did not resume after original End')
        time.sleep(.25);require(self.data()['tankShellExplosions']==end['tankShellExplosions'],'Idle End invented another explosion')
        self.post('start');time.sleep(.2);before=self.data()
        self.driver.send(client_command('mdown 1280 720',self.client_size));time.sleep(.15);self.driver.send('mup');time.sleep(.4)
        self.result['reconAfterEnd']=self.data()
        require(self.result['reconAfterEnd'].get('targetHealth',20)<20,'Original Recon fire did not recover after Tank End')
        self.result['passed']=True

    def close(self):
        if self.recording:
            stdout,stderr=self.recording.communicate(timeout=20)
            self.result['recordingExit']=self.recording.returncode
            if self.recording.returncode:self.result['recordingError']=stderr.decode(errors='replace')[-1000:]
        try:
            self.post('cleanup');time.sleep(.25);d=self.data()
            self.result['cleaned']=not d.get('cannonLab') and 'targetHealth' not in d and d['wallBlocks']==0
        finally:self.native.close();self.driver.close();self.save()

def main(args):
    suite=None
    try:suite=Suite(args);suite.run()
    except Exception as error:
        if suite:suite.result['error']=repr(error)
        else:raise
    finally:
        if suite:
            try:suite.close()
            except Exception as error:suite.result['cleanupError']=repr(error);suite.save()
            print(json.dumps({k:suite.result.get(k) for k in ['passed','error','cleaned','cleanupError','recordingExit']}),flush=True)
    return bool(suite and suite.result['passed'] and suite.result.get('cleaned'))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name,kind in [('pid',int),('created',float),('mc-pid',int),('mc-created',float),('world',str),('guest-sha256',str)]:parser.add_argument('--'+name,required=True,type=kind)
    parser.add_argument('--output',required=True,type=Path);parser.add_argument('--record',action='store_true')
    raise SystemExit(0 if main(parser.parse_args()) else 1)
