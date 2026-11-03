"""Actual fixed-position hero/angle capture; review images before visual acceptance."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,time,os,sys,subprocess
from pathlib import Path
from calibrate_hero_actions import select
from verify_world_hero_switch import ready
from verify_native_light_angles import main as angles
from make_native_light_sheet import main as sheet
from observe_overwatch import ROOT

def main(pid,folder,heroes,pitches,yaws,persistent=False):
    folder=folder.resolve()
    if ROOT/'research' not in folder.parents:raise ValueError('Private evidence folder required')
    folder.mkdir(parents=True,exist_ok=True);out=dict(pid=pid,heroes=[],passed=False,visualAcceptance='pending-image-review')
    driver=None;sender=None
    try:
        if persistent:
            # Reuse the installed UM foreground-protected WinDrive protocol,
            # avoiding a fresh PowerShell process at every sampled angle.
            package=Path(os.environ['APPDATA'])/'uv/tools/universal-modder/Lib/site-packages'
            if not (package/'um/win.py').is_file():raise ValueError('Installed UM drive API unavailable')
            sys.path.insert(0,str(package));from um.win import Drive,ps_exe,tool_path,text_utf8
            driver=object.__new__(Drive)
            driver.p=subprocess.Popen([ps_exe(),'-NoProfile','-ExecutionPolicy','Bypass','-File',tool_path('WinDrive.ps1'),'-Proc','GameClientApp.patched.exe'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,bufsize=1,creationflags=subprocess.CREATE_NO_WINDOW,**text_utf8())
            driver.ready=driver.p.stdout.readline().strip()
            if driver.ready!='ready window':raise ValueError('No unique offline game input window')
            def sender(*commands):
                for command in commands:
                    result=driver.cmd(command,retry=False)
                    if result=='fail':raise ValueError('Protected input failed: '+command)
        for hero in heroes:
            print(json.dumps(dict(hero=hero,phase='starting')),flush=True);select(pid,hero);ready(pid)
            target=folder/hero;angles(pid,['baseline'],target,pitches,yaws,sender);sheet(target)
            record=json.loads((target/'angles.json').read_text());out['heroes'].append(dict(hero=hero,passed=record['passed'],views=len(record['profiles']['baseline'])))
            (folder/'progress.json').write_text(json.dumps(out,indent=2));print(json.dumps(dict(hero=hero,phase='captured',views=out['heroes'][-1]['views'])),flush=True)
        out['passed']=True
    except Exception as error:out['error']=str(error);raise
    finally:
        if driver is not None:
            driver.p.stdin.close()
            try:driver.p.wait(3)
            except subprocess.TimeoutExpired:driver.p.terminate();driver.p.wait(3)
        (folder/'progress.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--pid',type=int,required=True);a.add_argument('--output',type=Path,required=True);a.add_argument('--heroes',nargs='+',default=['Genji','McCree','Pharah','Soldier76']);a.add_argument('--pitches',nargs='+',type=float,default=[-85,-45,0,45,85]);a.add_argument('--yaws',nargs='+',type=float,default=[0,45,90,135,180,-135,-90,-45]);a.add_argument('--persistent-input',action='store_true');args=a.parse_args();main(args.pid,args.output,args.heroes,args.pitches,args.yaws,args.persistent_input)
