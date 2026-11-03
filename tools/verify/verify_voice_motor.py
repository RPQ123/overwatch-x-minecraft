"""Bounded real-input regression in the backed-up private Switch clone only."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import json,math,subprocess,time
from calibrate_hero_actions import select
from calibrate_hero_roster import api,drive,report,ROOT
from verify_genji_elimination_reset import post
from observe_overwatch import ResearchProcess
from native_charge import grant_for_test

def grounded():
    drive('focus','key 0x20 up','key 0x57 up','key 0x53 up','key 0x10 up')
    if api('health')['player']['flying']:drive('focus','key 0x75','sleep 700')
    end=time.monotonic()+5
    while time.monotonic()<end:
        p=api('health')['player']
        if p['onGround'] and not p['flying']:return p
        time.sleep(.05)
    raise ValueError('Grounded non-flying admission failed')

def sample(commands,seconds=6):
    proc=subprocess.Popen(['um','win','drive','--proc','GameClientApp.patched.exe','focus',*commands],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    start=time.monotonic();rows=[]
    while time.monotonic()-start<seconds:
        p=api('health')['player'];c=api('combat');rows.append({'t':time.monotonic()-start,'p':p,'motor':c['motor']})
        if proc.poll() is not None and len(rows)>10:break
        time.sleep(.018)
    out,err=proc.communicate(timeout=8)
    if proc.returncode or b'focus -> fail' in out:raise ValueError((out+err).decode(errors='replace'))
    return rows

def main():
    assert api('health')['worldName'].startswith('Overwatch Twilight Switch ')
    pid=report(ROOT/'research/session-status.json')['nativePid'];out={'pid':pid,'movement':[],'passed':False};path=ROOT/'research/voice-motor-fixed.json'
    try:
        for name in ('Genji','Reaper','Soldier76'):
            select(pid,name);post('flight-open');time.sleep(.5);before=grounded()
            rows=sample(['key 0x57 down','sleep 800','key 0x57 up','key 0x53 down','sleep 800','key 0x53 up','sleep 400'])
            row={'hero':name,'before':before,'rows':rows};out['movement'].append(row)
            assert all(not v['p']['flying'] and v['p']['onGround'] for v in rows),'left ground'
            if name!='Genji':
                backward=[v for v in rows if v['motor'].get('inputBits')==2]
                assert len(backward)>5 and all(v['motor'].get('responsive') for v in backward)
                # Project the first 180 ms after reversal onto the preceding forward path.
                f=[v for v in rows if v['motor'].get('inputBits')==1]
                dx=f[-1]['p']['x']-f[0]['p']['x'];dz=f[-1]['p']['z']-f[0]['p']['z'];length=math.hypot(dx,dz)
                b0=backward[0];b1=next(v for v in backward if v['t']-b0['t']>=.18)
                row['reverseProjection180ms']=((b1['p']['x']-b0['p']['x'])*dx+(b1['p']['z']-b0['p']['z'])*dz)/length
                assert row['reverseProjection180ms']<-.1,'still traveling in old direction'
                released=[v for v in rows if v['t']>backward[-1]['t']+.1]
                row['releaseDrift']=math.hypot(released[-1]['p']['x']-released[0]['p']['x'],released[-1]['p']['z']-released[0]['p']['z'])
                assert row['releaseDrift']<.03,'release drift'
            print(json.dumps({k:v for k,v in row.items() if k not in ('before','rows')}),flush=True)
            if name=='Soldier76':
                out['sprint']=sample(['key 0x57 down','key 0x10 down','sleep 1300','key 0x10 up','key 0x57 up','sleep 300'])
                out['sprintMaxSpeed']=max(v['motor'].get('horizontalSpeed',0) for v in out['sprint'])
                assert 7.5<out['sprintMaxSpeed']<10,'native sprint boost lost'
            post('cleanup')
        select(pid,'Genji');time.sleep(.5)
        end=time.monotonic()+12
        while api('combat')['ultimate']['cost']<=0:
            if time.monotonic()>end:raise ValueError('Genji ultimate binding not ready')
            time.sleep(.1)
        out['voiceBefore']=api('combat')['ultimate'];assert out['voiceBefore']['voice']['ready']
        drive('focus','key 0x51','sleep 300');out['invalidQ']=api('combat')['ultimate']
        assert out['invalidQ']['voice']['scheduled']==out['voiceBefore']['voice']['scheduled'] and not out['invalidQ']['active']
        process=ResearchProcess(pid)
        try:out['grant']=grant_for_test(process,pid)
        finally:process.close()
        mc=api('health')['sourcePid']
        recording=subprocess.Popen(['um','win','record','--pid',str(mc),'--exe','java.exe','--out',str(ROOT/'research/genji-dragonblade-voice-live'),'--seconds','10','--fps','30'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        try:
            drive('focus','sleep 1700','key 0x51','sleep 250');out['activation']=api('combat')['ultimate']
            drive('focus','key 0x51','sleep 100');out['repeatedQ']=api('combat')['ultimate']
        finally:
            stdout,stderr=recording.communicate(timeout=18);out['recording']={'exit':recording.returncode,'stdout':stdout.decode(errors='replace')[-1500:],'stderr':stderr.decode(errors='replace')[-1500:]}
        expected=out['voiceBefore']['voice']['scheduled']+1
        assert out['activation']['active'] and out['activation']['voice']['scheduled']==expected
        assert out['repeatedQ']['voice']['scheduled']==expected and out['repeatedQ']['voice']['observedPlaying']
        select(pid,'McCree');select(pid,'Genji');out['afterHeroSwitch']=api('combat')['ultimate'];assert out['afterHeroSwitch']['voice']['scheduled']==expected
        out['passed']=True
    finally:
        try:drive('focus','key 0x57 up','key 0x53 up','key 0x10 up')
        except RuntimeError as failure:out['inputCleanupError']=str(failure)
        try:
            post('cleanup');time.sleep(.3);out['cleaned']=api('combat').get('wallBlocks')==0
        except OSError as failure:out['cleanupError']=str(failure);out['cleaned']=False
        path.write_text(json.dumps(out,indent=2)+'\n')
        print(json.dumps({'passed':out['passed'],'path':str(path),'cleaned':out['cleaned']}),flush=True)

if __name__=='__main__':main()
