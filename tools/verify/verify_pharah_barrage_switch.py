"""Interrupt real airborne Barrage projectiles with actual world/hero changes."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,os,subprocess,sys,time,urllib.request
from pathlib import Path
from observe_overwatch import ROOT,ResearchProcess
from calibrate_hero_actions import select
from calibrate_hero_roster import api
from verify_genji_elimination_reset import post
from verify_native_light_angles import point
from verify_bastion_tank_movement import stable

def main(pid,output):
    folder=(ROOT/output).resolve()
    if ROOT/'research' not in folder.parents or folder.exists():raise ValueError('Use a new private output directory')
    folder.mkdir(parents=True);result=dict(pid=pid,passed=False,rows=[]);driver=None
    try:
        p=ResearchProcess(pid);p.close()
        sys.path.insert(0,str(Path(os.environ['APPDATA'])/'uv/tools/universal-modder/Lib/site-packages'))
        from um.win import Drive,ps_exe,tool_path,text_utf8
        driver=object.__new__(Drive)
        driver.p=subprocess.Popen([ps_exe(),'-NoProfile','-ExecutionPolicy','Bypass','-File',tool_path('WinDrive.ps1'),'-Proc','GameClientApp.patched.exe'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,bufsize=1,creationflags=subprocess.CREATE_NO_WINDOW,**text_utf8())
        if driver.p.stdout.readline().strip()!='ready window':raise ValueError('No protected game driver')
        def send(*commands):
            for command in commands:
                if driver.cmd(command,retry=False)=='fail':raise ValueError('Focus/input interference')
        for mode in ('world','hero'):
            select(pid,'Genji');select(pid,'Pharah');stable(pid,api('world')['dimension']);point(180,0);post('flight-open');time.sleep(.3);post('start');time.sleep(.2)
            # F11 is a 20Hz MC edge reader; a sub-tick synthetic tap is not a
            # proved grant. Release-to-arm first, hold across two real ticks,
            # then confirm the actual native meter before testing Q.
            before=api('combat');send('focus','sleep 150','hold 0x7A 120','sleep 250')
            grant=api('combat');(folder/(mode+'-grant.json')).write_text(json.dumps(grant,indent=2))
            if grant['nativeCharge']['charge']<grant['nativeCharge']['cost']*.99:raise ValueError('F11 test grant not observed; no Q interruption attempted')
            send('key 0x51');deadline=time.monotonic()+2
            while True:
                active=api('combat')
                if active['admitted']>before['admitted'] and active['active']>0:break
                if time.monotonic()>deadline:
                    (folder/(mode+'-no-flight.json')).write_text(json.dumps(active,indent=2));raise ValueError('No actual in-flight Barrage to interrupt')
                time.sleep(.01)
            row=dict(mode=mode,beforeInterrupt=active);result['rows'].append(row)
            if mode=='world':
                dimension='overworld' if api('world')['dimension']!='minecraft:overworld' else 'end'
                with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:32133/world/switch-test/'+dimension,method='POST'),timeout=3):pass
                stable(pid,'minecraft:overworld' if dimension=='overworld' else 'minecraft:the_end')
            else:select(pid,'McCree')
            time.sleep(.5);settled=api('combat');time.sleep(1.2);after=api('combat');row['settled']=settled;row['after']=after
            if after['active']!=0 or settled['damageApplied']!=after['damageApplied']:raise ValueError('Old projectile damage/flight leaked across transition')
            if after['barrageSound']['playing'] or settled['barragePresentationImpacts']!=after['barragePresentationImpacts']:raise ValueError('Old Barrage sound/impact leaked across transition')
            select(pid,'McCree' if mode=='hero' else 'Pharah');point(180,0);post('start');time.sleep(.2);send('focus','click 1280 720','sleep 600')
            row['ordinaryHealth']=api('combat')['targetHealth']
            if row['ordinaryHealth']!=(13 if mode=='hero' else 8):raise ValueError('Fresh weapon did not recover')
            post('cleanup');row['passed']=True;print(json.dumps(dict(mode=mode,passed=True)),flush=True)
        result['passed']=True
    except Exception as error:result['error']=repr(error)
    finally:
        if driver:
            try:driver.cmd('mup',retry=False)
            except Exception:pass
            driver.p.stdin.close();driver.p.wait(3)
        try:post('cleanup');time.sleep(.3);result['cleaned']=api('combat').get('wallBlocks')==0
        except Exception as error:result['cleanupError']=str(error)
        (folder/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:result.get(k) for k in ('passed','error','cleaned')}),flush=True)
    return result['passed']

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pid',type=int,required=True);parser.add_argument('--output',required=True);a=parser.parse_args()
    raise SystemExit(0 if main(a.pid,a.output) else 1)
