"""Real native shots kill an MC fixture and must reset the original Shift timer."""
import argparse,json,subprocess,time,urllib.request
from observe_overwatch import ROOT,ResearchProcess
from calibrate_hero_roster import drive,api
from test_genji_reset_data import binding

def post(action):
    with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:32133/combat/test/'+action,method='POST'),timeout=3) as r:return json.load(r)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pid',type=int,required=True);args=parser.parse_args();p=ResearchProcess(args.pid);result={};recording=None
    try:
        result['initial']=binding(p)[1]
        post('flight-open');time.sleep(.4)
        if api('combat').get('testError'):raise ValueError('No loaded air volume for elimination test')
        post('cleanup');time.sleep(.2)
        deadline=time.monotonic()+10
        while binding(p)[1]['remaining']>0:
            if time.monotonic()>deadline:raise ValueError('Original Shift cooldown did not expire before test')
            time.sleep(.1)
        recording=subprocess.Popen(['um','win','record','--pid',str(args.pid),'--exe','GameClientApp.patched.exe','--out',str(ROOT/'research/genji-elimination-reset-live'),'--seconds','12','--fps','30'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        drive('focus','key 0x10','sleep 550');result['firstDash']=binding(p)[1];post('start');time.sleep(.2)
        result['fixture']=api('combat')
        if result['fixture'].get('testError') or result['fixture'].get('targetHealth')!=20:raise ValueError('No healthy empty-space fixture')
        drive('focus','mdown 1280 720','sleep 100','mup','sleep 350');result['hit']=api('combat');result['afterHit']=binding(p)[1]
        drive('focus','mdown 1280 720','sleep 100','mup','sleep 400');result['kill']=api('combat');result['afterKill']=binding(p)[1]
        drive('focus','key 0x10','sleep 450');result['secondDash']=binding(p)[1];result['afterSecondDash']=api('combat')
        post('replay');time.sleep(.2);result['replay']=api('combat')
        result['passed']=(result['firstDash']['remaining']>0 and result['hit'].get('targetHealth',0)>0 and result['hit'].get('dashResetsApplied')==0
            and result['kill'].get('targetHealth')==0 and result['kill'].get('dashResetsApplied')==1 and result['kill'].get('genjiEliminations')==1
            and result['afterKill']['remaining']==0 and result['secondDash']['tick']>result['firstDash']['tick']
            and result['replay'].get('genjiEliminations')==1 and result['replay'].get('dashResetsApplied')==1)
        print(json.dumps({k:result[k] for k in ('firstDash','afterHit','afterKill','secondDash','passed')},indent=2),flush=True)
        print('MC',[(k,result[k].get('targetHealth'),result[k].get('genjiEliminations'),result[k].get('dashResetsApplied')) for k in ('fixture','hit','kill','replay')],flush=True)
    finally:
        if recording:
            stdout,stderr=recording.communicate(timeout=20);result['recordingExit']=recording.returncode
        post('cleanup');result['cleaned']=api('combat').get('wallBlocks')==0
        (ROOT/'research/genji-elimination-reset-live-result.json').write_text(json.dumps(result,indent=2)+'\n');p.close()

if __name__=='__main__':main()
