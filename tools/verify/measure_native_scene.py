"""Read-only scene cadence with explicit foreground identity, excluding focus gaps."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,ctypes,json,time,psutil
from ctypes import wintypes as w
from pathlib import Path
from calibrate_hero_roster import api,report,drive
from observe_overwatch import ROOT,ResearchProcess
from native_bootstrap_maps import read_loaded_map

def measure(pid,seconds,output):
    process=ResearchProcess(pid)
    try:scene=read_loaded_map(process)
    finally:process.close()
    user=ctypes.windll.user32;user.GetForegroundWindow.restype=w.HWND
    user.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)]
    def foreground():
        owner=w.DWORD();user.GetWindowThreadProcessId(user.GetForegroundWindow(),ctypes.byref(owner));return owner.value
    rows=[];start=time.monotonic();native=psutil.Process(pid);guest=psutil.Process(api('health')['sourcePid'])
    drive('focus')
    while time.monotonic()-start<seconds:
        h=api('health');r=report(ROOT/f'native-host/build/world-live-{pid}.json')
        if h['sourcePid']!=guest.pid or r.get('pid')!=pid or not r.get('enabled') or r.get('failures'):raise ValueError('Scene process changed or producer failed')
        if time.time()*1000-r['sampleWallMs']>2000:raise ValueError('Native cadence report stale')
        rows.append({'elapsed':time.monotonic()-start,'foregroundPid':foreground(),'native':r,'published':h['published'],'player':h['player']});time.sleep(.5)
    valid=[]
    for a,b in zip(rows,rows[1:]):
        if a['foregroundPid']!=pid or b['foregroundPid']!=pid:continue
        if any(a['native'].get(k)!=b['native'].get(k) for k in ['pid','generation','probeVersion']):raise ValueError('Scene generation changed')
        dt=(b['native']['sampleWallMs']-a['native']['sampleWallMs'])/1000
        if dt<=0:continue
        valid.append({'seconds':dt,'frames':b['native']['frames']-a['native']['frames'],'composed':b['native']['colorUploads']-a['native']['colorUploads']})
    span=sum(v['seconds'] for v in valid)
    result={'pid':pid,'map':scene,'foregroundSeconds':span,'excludedRowPairs':len(rows)-1-len(valid),'hostFps':sum(v['frames'] for v in valid)/span if span else None,'distinctComposedFps':sum(v['composed'] for v in valid)/span if span else None,'memory':{name:{'workingSet':p.memory_info().rss,'privateBytes':p.memory_info().private} for name,p in [('native',native),('mc',guest)]},'rows':rows,'limits':'Foreground identity sampled every .5s, not an exhaustive focus trace; native report windows are not frame-time percentiles.'}
    output.write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='rows'}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--pid',type=int,required=True);parser.add_argument('--seconds',type=int,default=15);parser.add_argument('--output',required=True);args=parser.parse_args()
    output=(ROOT/args.output).resolve()
    if not 5<=args.seconds<=60 or ROOT/'research' not in output.parents:parser.error('Use5..60seconds and a private research output')
    measure(args.pid,args.seconds,output)
