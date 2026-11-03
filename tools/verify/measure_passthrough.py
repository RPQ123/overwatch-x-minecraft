"""Measure real producer, presented and distinct composited frame rates separately."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,time
from pathlib import Path
from launch_passthrough_session import api,native_pids,BUILD
from observe_overwatch import ResearchProcess

def measure(seconds,output):
    pids=native_pids()
    if len(pids)!=1:raise RuntimeError('One verified offline client is required')
    pid=pids[0];process=ResearchProcess(pid);process.close()
    rows=[];started=time.perf_counter()
    while True:
        h=api('health');n=json.loads((BUILD/f'world-live-{pid}.json').read_text())
        if n['pid']!=pid or not n['enabled'] or n['failures'] or h['failed']:
            raise RuntimeError('Rendering failed during measurement')
        rows.append({'elapsed':time.perf_counter()-started,'guest':h,'native':n})
        if rows[-1]['elapsed']>=seconds:break
        time.sleep(.5)
    a,b=rows[0],rows[-1];elapsed=b['elapsed']-a['elapsed']
    if a['guest']['sourcePid']!=b['guest']['sourcePid'] or a['native']['generation']!=b['native']['generation']:
        raise RuntimeError('Session changed during measurement')
    delta=lambda key:b['native'][key]-a['native'][key]
    result={'nativePid':pid,'guestPid':h['sourcePid'],'seconds':elapsed,
            'mcPublishedFps':(b['guest']['published']-a['guest']['published'])/elapsed,
            'nativePresentFps':delta('frames')/elapsed,
            'distinctCompositedMcFps':delta('colorUploads')/elapsed,
            'nativeDelta':{key:delta(key) for key in ['frames','blended','colorUploads','heldFrames','unmaskedFrames','sourceRejected','coverageRejected']},
            'guestTimings':api('performance'),'climb':api('combat').get('climb'),
            'rows':rows}
    for key in ['presentCpuNs','pacingNs']:
        if key in n:result[key+'PerFrameMs']=delta(key)/max(1,delta('frames'))/1e6
    Path(output).parent.mkdir(parents=True,exist_ok=True)
    Path(output).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--seconds',type=float,default=30);p.add_argument('--output',required=True);a=p.parse_args()
    if not 5<=a.seconds<=120:p.error('Measurement must be 5..120 seconds')
    measure(a.seconds,a.output)
