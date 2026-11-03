"""Actual Pharah charge/damage feedback and native Barrage; reversible MC targets."""
import argparse,json,subprocess,time
from observe_overwatch import ROOT,ResearchProcess
from calibrate_hero_actions import select
from calibrate_hero_roster import api,drive,report
from verify_genji_elimination_reset import post
from native_charge import grant_for_test

def wait_ready():
    deadline=time.monotonic()+12
    while True:
        c=api('combat')
        if c.get('nativeCharge',{}).get('ready') and not c.get('feedError'):return c
        if time.monotonic()>deadline:raise ValueError('Original charge binding did not settle: '+str(c.get('nativeCharge')))
        time.sleep(.1)

def fire_barrage(pid,phase):
    p=ResearchProcess(pid)
    try:grant=grant_for_test(p,pid)
    finally:p.close()
    rows=[];start=time.monotonic()
    command=subprocess.Popen(['um','win','drive','--proc','GameClientApp.patched.exe','focus','key 0x51','sleep 4200'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    while command.poll() is None or time.monotonic()-start<4.5:
        if time.monotonic()-start>10:command.kill();raise ValueError('Barrage input deadline')
        c=api('combat');rows.append(dict(t=time.monotonic()-start,charge=c.get('nativeCharge'),targetHealth=c.get('targetHealth'),blockHits=c.get('blockHits'),entityHits=c.get('entityHits'),damage=c.get('damageApplied'),rejected=c.get('rejected'),player=api('health')['player']));time.sleep(.05)
    out,err=command.communicate(timeout=1)
    if command.returncode or b'-> fail' in out:raise ValueError((out+err).decode(errors='replace'))
    native=report(ROOT/f'native-host/build/native-emissions-{pid}.json')
    subprocess.run(['um','win','shot','--exe','GameClientApp.patched.exe',str(ROOT/f'research/barrage-{phase}-{pid}.png'),'--scale','.33'],cwd=ROOT,capture_output=True,check=True)
    return dict(labGrant=grant,rows=rows,after=api('combat'),native=dict(accepted=native.get('armoryAccepted'),failures=native.get('failures'),refused=native.get('refused'),factories=[v for v in native.get('factoryObservations',[]) if v['resource']==0x0400000000000052]))

def main(pid):
    d=dict(pid=pid,passed=False)
    try:
        select(pid,'Pharah');wait_ready();post('flight-open');time.sleep(.5)
        if api('combat').get('testError'):raise ValueError('No safe air volume')
        post('cleanup');time.sleep(.2)
        before=wait_ready()['nativeCharge'];time.sleep(1);after=wait_ready()['nativeCharge'];d['passive']=dict(before=before,after=after)
        post('start');time.sleep(.2);d['primaryBefore']=wait_ready();drive('focus','click 1280 720','sleep 700');d['primaryAfter']=wait_ready()
        if d['primaryAfter'].get('targetHealth')!=8:raise ValueError('Native primary damage/charge prerequisite failed')
        post('start');time.sleep(.15);post('wall');time.sleep(.15);d['covered']=fire_barrage(pid,'covered')
        post('open');time.sleep(.2);d['open']=fire_barrage(pid,'open')
        post('replay');time.sleep(.2);d['replay']=api('combat')
        covered=d['covered']['after'];opened=d['open']['after'];rows=d['open']['rows']
        active=[v['charge'] for v in rows if v.get('charge',{}).get('ready') and v['charge'].get('active')]
        d['passed']=after['charge']>before['charge'] and d['primaryAfter']['nativeCharge']['charge']-d['primaryBefore']['nativeCharge']['charge']>=120
        d['passed'] &= covered.get('targetHealth')==20 and opened.get('targetHealth',20)<20 and opened.get('targetHealth')==d['replay'].get('targetHealth')
        d['passed'] &= bool(active) and min(v['charge'] for v in active)==0 and opened.get('rejected')==0 and d['open']['native']['accepted']>0
    except Exception as e:d['error']=str(e)
    finally:
        drive('focus','mup','mup right');post('cleanup');time.sleep(.2);d['cleaned']=api('combat').get('wallBlocks')==0
        (ROOT/f'research/native-barrage-{pid}-{time.time_ns()}.json').write_text(json.dumps(d,indent=2)+'\n')
        print(json.dumps({k:d[k] for k in ('pid','passed','error','cleaned') if k in d}))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--pid',required=True,type=int);args=a.parse_args();main(args.pid)
