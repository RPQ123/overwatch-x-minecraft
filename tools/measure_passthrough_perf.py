"""Bounded live frame cadence/status sample; no gameplay input or pixel readback."""
import argparse,json,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def summarize(rows):
    first,last=rows[0],rows[-1];span=last['elapsed']-first['elapsed']
    a,b=first['native'],last['native']
    for key in ('pid','generation','probeVersion'):
        if a.get(key)!=b.get(key):raise ValueError('Native sample identity changed: '+key)
    native_span=(b['sampleWallMs']-a['sampleWallMs'])/1000 if 'sampleWallMs' in a and 'sampleWallMs' in b else span
    frames=b['frames']-a['frames']
    if span<=0 or native_span<=0 or frames<=0:raise ValueError('No advancing native sample')
    result={'seconds':span,'nativeSampleSeconds':native_span,
            'mcFps':(last['health']['published']-first['health']['published'])/span,
            'hostFps':frames/native_span,
            'distinctComposedFps':(b['colorUploads']-a['colorUploads'])/native_span,
            'heldFrames':b['heldFrames']-a['heldFrames'],
            'unmaskedFrames':b['unmaskedFrames']-a['unmaskedFrames']}
    counters=('drawObserveCpuNs','bufferObserveCpuNs','hudBlendCpuNs','presentCopyCpuNs','presentCpuNs','pacingNs')
    result['cpuMsPerNativeFrame']={k.removesuffix('Ns'):(b[k]-a[k])/frames/1e6 for k in counters if k in a and k in b}
    if 'drawObservations' in a and 'drawObservations' in b:result['drawCallsPerFrame']=(b['drawObservations']-a['drawObservations'])/frames
    # These are report windows, not individual frame-time percentiles or 1% lows.
    windows=[];previous=None
    for row in rows:
        current=row['native']
        if any(current.get(key)!=a.get(key) for key in ('pid','generation','probeVersion')):raise ValueError('Native window identity changed')
        stamp=current.get('sampleWallMs')
        if stamp is None:continue
        if previous is not None and stamp>previous['sampleWallMs']:
            duration=(stamp-previous['sampleWallMs'])/1000
            windows.append((duration,(current['colorUploads']-previous['colorUploads'])/duration))
        if previous is None or stamp>previous['sampleWallMs']:previous=current
    if windows:
        result['distinctReportWindows']={'samples':len(windows),'minSeconds':min(s for s,_ in windows),
            'maxSeconds':max(s for s,_ in windows),'minimumFps':min(f for _,f in windows),
            'below150':sum(f<150 for _,f in windows)}
    return result
def get(route):
    with urllib.request.urlopen('http://127.0.0.1:32133/'+route,timeout=2) as response:return json.load(response)
def read_report(path):
    # Retry the same report during the native writer's brief Windows file lock.
    for attempt in range(6):
        try:return json.loads(path.read_text()),attempt
        except (PermissionError,json.JSONDecodeError):
            if attempt==5:raise
            time.sleep(.05)

def measure(pid,seconds,output):
    rows=[];start=time.monotonic();retries=0
    while time.monotonic()-start<seconds:
        health=get('health');native,attempts=read_report(ROOT/f'native-host/build/world-live-{pid}.json');retries+=attempts
        if native['pid']!=pid or not native['enabled'] or native['failures'] or health['failed']:raise ValueError('live producer unhealthy')
        if not -500<=time.time()*1000-native['sampleWallMs']<=2000:raise ValueError('live native report is stale')
        rows.append({'elapsed':time.monotonic()-start,'health':health,'native':native,'timings':get('performance')});time.sleep(.5)
    result={**summarize(rows),'reportReadRetries':retries,'rows':rows}
    output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pid',required=True,type=int);p.add_argument('--seconds',type=int,default=25);p.add_argument('--output',required=True);a=p.parse_args()
    output=(ROOT/a.output).resolve()
    if not 5<=a.seconds<=60 or ROOT/'research' not in output.parents:p.error('5..60 seconds and private research output required')
    measure(a.pid,a.seconds,output)
