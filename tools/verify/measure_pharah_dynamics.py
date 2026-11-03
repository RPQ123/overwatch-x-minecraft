"""Sample actual native/MC flight under identical real input phases in a clone."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,subprocess,time
from calibrate_hero_actions import select
from calibrate_hero_roster import api,drive
from observe_overwatch import ROOT,ResearchProcess
from observe_native_weapon_states import WeaponStates
from inspect_pharah_abilities import snapshot
from verify_genji_elimination_reset import post
from verify_world_hero_switch import ready,require

def main(pid,label):
    out={'pid':pid,'label':label,'rows':[]};p=None
    try:
        require(api('health')['worldName'].startswith('Overwatch Twilight Switch '),'Use an isolated regression clone')
        select(pid,'Pharah');ready(pid);post('flight-open');time.sleep(.5)
        require(not api('combat').get('testError'),'Air fixture unavailable')
        drive('focus','hold 0x75 150','sleep 500')
        p=ResearchProcess(pid);r=WeaponStates(p);s=r.sample_weapon(False,True)
        admin=r.pointer(p.base+0x17b7f90);table=p.read(r.pointer(admin+16),65536);mover=r.component(r.entity(table,s['modelId']),0x15)
        out['initial']=snapshot(p);out['fixture']=api('combat')
        for phase,commands,duration in [('hover',['mdown 1280 720 right','sleep 1300','mup right'],2.5),('coast',[],1.2),('jet',['hold 0x10 100','sleep 1300'],2.5),('space-hover',['hold 0x20 1400'],2.5),('release',[],2)]:
            command=subprocess.Popen(['um','win','drive','--proc','GameClientApp.patched.exe','focus',*commands],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE) if commands else None
            started=time.monotonic()
            while time.monotonic()-started<duration or command and command.poll() is None:
                if time.monotonic()-started>12:raise RuntimeError('Input phase deadline')
                h=api('health');c=api('combat');out['rows'].append({'t':time.monotonic(),'phase':phase,'player':h['player'],'flight':c.get('flight'),'nativeVelocity':r.unpack('<3f',mover+0x7e0+0x230),'nativeGravity':r.unpack('<3f',mover+0x7e0+0x250)})
                time.sleep(.01)
            if command:
                stdout,stderr=command.communicate(timeout=1)
                require(command.returncode==0 and b'-> fail' not in stdout,(stdout+stderr).decode(errors='replace'))
            out.setdefault('resources',{})[phase]=snapshot(p)
        out['passed']=all(v['player']['alive'] and v['player']['health']==20 for v in out['rows'])
    finally:
        if p:p.close()
        if not api('health')['player']['flying']:drive('focus','hold 0x75 150','sleep 200')
        post('cleanup');time.sleep(.2)
        path=ROOT/f'research/pharah-dynamics-{label}-{pid}.json';path.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'path':str(path),'samples':len(out['rows']),'passed':out.get('passed'),'readySamples':sum(v.get('flight',{}).get('ready',False) for v in out['rows']),'phases':{phase:{'minY':min(v['player']['feetY'] for v in out['rows'] if v['phase']==phase),'maxY':max(v['player']['feetY'] for v in out['rows'] if v['phase']==phase),'maxVy':max(v['player']['velocityY'] for v in out['rows'] if v['phase']==phase)} for phase in out.get('resources',{})}}),flush=True)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--pid',type=int,required=True);a.add_argument('--label',required=True);s=a.parse_args();main(s.pid,s.label)
