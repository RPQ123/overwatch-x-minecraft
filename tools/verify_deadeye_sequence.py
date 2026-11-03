"""Actual native-animation receipts must gate individually timed MC damage."""
import argparse,json,subprocess,time,sys
from pathlib import Path
from calibrate_hero_roster import api,drive,report
from calibrate_hero_actions import select
from verify_bastion_tank_movement import stable
from verify_native_light_angles import point
from verify_genji_elimination_reset import post
from observe_overwatch import ROOT,ResearchProcess

def main(pid,output,transport_hitch=False):
    folder=(ROOT/output).resolve();assert ROOT/'research' in folder.parents;folder.mkdir(parents=True,exist_ok=True)
    p=ResearchProcess(pid);p.close();r={'pid':pid,'passed':False,'samples':[]}
    assert api('health')['worldName'].startswith('Overwatch Twilight Switch ')
    try:
        select(pid,'McCree');stable(pid,api('world')['dimension']);point(180,0)
        # Keep naturally spawning mobs outside the70m native target radius;
        # never delete unrelated entities to make a test pass.
        for _ in range(4):
            post('flight-open');time.sleep(.25);assert not api('combat').get('testError')
        post('beam');time.sleep(.25)
        r['before']=api('combat');r['nativeBefore']=report(ROOT/f'native-host/build/body-sync-{pid}.json')
        rec=subprocess.Popen(['um','win','record','--pid',str(pid),'--exe','GameClientApp.patched.exe','--out',str(folder/'actual'),'--seconds','10','--fps','60'],stdout=open(folder/'record.log','w'),stderr=subprocess.STDOUT)
        mc=api('health')['sourcePid'];mcRec=subprocess.Popen(['um','win','record','--pid',str(mc),'--exe','java.exe','--out',str(folder/'mc'),'--seconds','10','--fps','30'],stdout=open(folder/'mc-record.log','w'),stderr=subprocess.STDOUT)
        r['clock']={'wall':time.time(),'qpc':time.perf_counter()}
        command=subprocess.Popen(['um','win','drive','--proc','GameClientApp.patched.exe','focus','key 0x7A','sleep 200','key 0x51','sleep 2600','click 1280 720','sleep 3200'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        start=time.monotonic()
        while command.poll() is None or time.monotonic()-start<7:
            if time.monotonic()-start>15:raise RuntimeError('Bounded input deadline')
            r['samples'].append({'t':time.monotonic()-start,'combat':api('combat')});time.sleep(.025)
        o,e=command.communicate(timeout=1);r['input']=o.decode(errors='replace');assert not command.returncode and b'fail' not in o,(o+e).decode(errors='replace')
        r['after']=api('combat');r['nativeAfter']=report(ROOT/f'native-host/build/body-sync-{pid}.json');rec.wait(timeout=15);mcRec.wait(timeout=15)
        assert r['after']['beamTargets'] and all(v==0 for v in r['after']['beamTargets'].values()),'Not all four fixture targets were shot'
        old=r['before']['deadeye']['shots'];new=r['after']['deadeye']['shots'];shots=new-old
        assert 4<=shots<=6,('Unexpected shot count',shots,r['after']['deadeye'])
        receipts=r['after']['deadeye']['shotReceipts'][-shots:];r['receipts']=receipts
        assert len({v['sequence'] for v in receipts})==shots,'Duplicate animation receipt'
        gaps=[b['nativeTick']-a['nativeTick'] for a,b in zip(receipts,receipts[1:])]
        r['nativeShotGapsMs']=gaps
        # Native simulation timestamps are16ms quantized; wall admission still
        # enforces >=134ms. One quantized native step can read128ms.
        if transport_hitch:
            assert r['after']['deadeyePresentationIoFailures']>r['before']['deadeyePresentationIoFailures'],'No actual transport failure observed'
            assert all(128<=gap<=1100 for gap in gaps) and sum(gap>250 for gap in gaps)==1,'Unexpected recovery cadence after one bounded IO hold'
        else:assert all(128<=gap<=250 for gap in gaps) and sum(gaps)/len(gaps)<220,'Original target-loop cadence was not restored'
        assert all(50<=b['wall']-a['wall']<=(1200 if transport_hitch else 300) and b['serverTick']>a['serverTick'] for a,b in zip(receipts,receipts[1:])),'Damage was batched or native shots were replayed'
        assert r['nativeAfter']['deadeyeAnimationCalls']-r['nativeBefore']['deadeyeAnimationCalls']==shots,'Native animation and MC shot count disagree'
        assert r['nativeAfter']['deadeyeAnimationCompleted']-r['nativeBefore']['deadeyeAnimationCompleted']==shots,'Native shot animations did not complete'
        assert not r['after']['nativeCharge']['active'] and any(s['combat']['nativeCharge'].get('charge',9999)==0 for s in r['samples']),'Native Q did not end or spend charge'
        post('replay');time.sleep(.2);assert api('combat')['deadeye']['shots']==r['after']['deadeye']['shots'],'Replay duplicated damage'
        post('start');time.sleep(.2);drive('focus','click 1280 720','sleep 500');r['ordinaryShot']=api('combat');assert r['ordinaryShot']['targetHealth']==13,'Ordinary revolver failed after sequence'
        r['passed']=True
    except Exception as failure:r['error']=repr(failure)
    finally:
        try:drive('mup','mup right');post('cleanup');r['cleaned']=api('combat').get('wallBlocks')==0
        except Exception as failure:r['cleanupError']=repr(failure)
        (folder/'result.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({k:r.get(k) for k in ('pid','passed','error','receipts','cleaned','cleanupError')}),flush=True)
    return 0 if r['passed'] else 1

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pid',type=int,required=True);p.add_argument('--output',required=True);p.add_argument('--transport-hitch',action='store_true');a=p.parse_args();sys.exit(main(a.pid,a.output,a.transport_hitch))
