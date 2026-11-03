"""Actual native Genji firing at a temporary real Naga part; no fixture damage."""
import argparse,json,math,subprocess,time,urllib.request
from calibrate_hero_actions import select
from calibrate_hero_roster import api,drive,report
from observe_overwatch import ROOT,ResearchProcess
from verify_genji_elimination_reset import post

def require(ok,message):
    if not ok:raise ValueError(message)

def trial(action):
    with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:32133/world/twilight/'+action,method='POST'),timeout=3) as r:return json.load(r)

def wait(predicate,seconds=8):
    deadline=time.monotonic()+seconds
    while True:
        value=api('world')
        if value.get('error'):raise ValueError(value['error'])
        if predicate(value):return value
        if time.monotonic()>deadline:raise ValueError('Actual Twilight fixture deadline: '+json.dumps(value))
        time.sleep(.1)

def aim(point):
    for attempt in range(3):
        p=api('health')['player'];c=api('combat')
        x=point['x']-p['x'];y=point['y']-p['eyeY'];z=point['z']-p['z']
        yaw=math.degrees(math.atan2(-x,z));pitch=-math.degrees(math.atan2(y,math.hypot(x,z)))
        dx=(yaw-c['yaw']+180)%360-180;dy=pitch-c['pitch']
        if abs(dx)<.25 and abs(dy)<.25:return
        drive('focus',f'rel {round(dx/.1)} {round(dy/.1)}','sleep 200')
    raise ValueError('Actual native camera did not align with the fixed real part')

def cleanup(saved_rule):
    """UI focus loss must not prevent independent server-side fixture cleanup."""
    out={};errors=[]
    try:drive('focus','mup','key 0x20 up')
    except Exception as error:out['inputCleanupError']=str(error)
    for name,action in [('boss',lambda:trial('native-cleanup')),('combat',lambda:post('cleanup'))]:
        try:action()
        except Exception as error:errors.append(name+': '+str(error))
    try:
        time.sleep(.6);final=api('world');combat=api('combat')
        out.update(cleanedWorld=final,cleanedCombat=combat)
        out['cleaned']=not final.get('probeActive') and final.get('mobGriefing')==saved_rule and not any(e['type']=='twilightforest:naga' for e in final.get('nearby',[])) and combat['wallBlocks']==0
        if not out['cleaned']:errors.append('Fixture/rule restoration failed')
    except Exception as error:out['cleaned']=False;errors.append('verification: '+str(error))
    if errors:out['cleanupError']='; '.join(errors)
    return out

def main(pid):
    identity=ResearchProcess(pid);identity.close()
    out={'pid':pid,'kind':'actual-native-fire-at-real-mod-part','passed':False};prefix=ROOT/f'research/twilight-native-fire-{pid}-{time.time_ns()}'
    savedRule=None
    try:
        before=api('world');savedRule=before.get('mobGriefing');out['initial']=before
        require(before.get('enabled') and before.get('dimension')=='twilightforest:twilight_forest','Separate mod trial must be loaded')
        actor=select(pid,'Genji');deadline=time.monotonic()+18
        while True:
            status=report(ROOT/'research/session-status.json')
            if status.get('ready') and not status.get('error') and status.get('hero',{}).get('modelId')==actor['modelId']:break
            if time.monotonic()>deadline:raise ValueError('Supervisor did not bind current native hero')
            time.sleep(.2)
        post('flight-open');time.sleep(.3);require(not api('combat').get('testError'),'Safe air lab unavailable')
        post('cleanup');drive('focus','hold 0x20 1800','sleep 400')
        c=api('combat');drive('focus',f'rel 0 {round(-c["pitch"]/.1)}','sleep 250')
        require(api('health')['player']['flying'],'Creative air flight required')
        trial('native-naga')
        before=wait(lambda w:w.get('probeActive') and w.get('multipartProbe',{}).get('targets') and not w['multipartProbe'].get('pending'))
        # Let the original segment-following animation settle sideways. The
        # fixture never writes a part position or changes its original boxes.
        time.sleep(3);before=api('world')
        out['fixtureBefore']=before;probe=before['multipartProbe']
        require(probe.get('kind')=='native-fire-only','Wrong fixture kind: server damage is forbidden in this acceptance')
        p=api('health')['player'];root=next(e for e in before['nearby'] if e['id']==probe['ownerId'])
        # Pick a real segment away from the root's sightline, so the root cannot
        # masquerade as multipart admission. Exact original boxes remain intact.
        def separation(t):
            ax=t['x']-p['x'];az=t['z']-p['z'];bx=root['x']-p['x'];bz=root['z']-p['z']
            return abs(math.atan2(ax*bz-az*bx,ax*bx+az*bz))
        target=max((t for t in probe['targets'] if t['width']>.1 and t['height']>.1),key=separation)
        out['target']=target;require(separation(target)>.10,'Part does not have a separate root-free sightline')
        aim(target);time.sleep(.2);before=wait(lambda w:bool(w.get('bossHud',{}).get('bars')) and w['bossHud'].get('pixelsReady'))
        out['beforeFire']=before;out['combatBefore']=api('combat')
        drive('focus','mdown 1280 720','sleep 120','mup','sleep 1100')
        after=wait(lambda w:w.get('multipartProbe',{}).get('health',probe['before'])<probe['before'] and any(b['percent']<.999 for b in w.get('bossHud',{}).get('bars',[])),5)
        combat=api('combat');out['afterFire']=after;out['combatAfter']=combat
        require(after.get('probeActive') and after['multipartProbe']['health']<before['multipartProbe']['health'],'Actual native shots did not damage the real Naga')
        receipts=after['multipartProbe'].get('damageReceipts',[])
        require(any(r['part']=='NagaSegment' and r['ownerId']==probe['ownerId'] and r['entityId']!=probe['ownerId'] and not r['explosion'] and r['healthLost']>0 for r in receipts),'No actual segment damage receipt; root hits do not establish multipart acceptance')
        barId=before['bossHud']['bars'][0]['id'];bar=next(b for b in after['bossHud']['bars'] if b['id']==barId)
        require(not after['multipartProbe']['aiDisabled'] and abs(bar['percent']-after['multipartProbe']['health']/probe['before'])<.015,'Original mod AI/boss bar did not track actual health')
        require(combat['admitted']>out['combatBefore']['admitted'] and combat['entityHits']>out['combatBefore']['entityHits'],'No corresponding actual native combat admissions/hits')
        post('replay');time.sleep(.4);out['replay']=api('world');out['combatReplay']=api('combat')
        require(out['replay']['multipartProbe']['health']==after['multipartProbe']['health'] and out['combatReplay']['damageApplied']==combat['damageApplied'] and out['replay']['multipartProbe']['damageReceipts']==receipts,'Replay applied boss damage twice')
        native=report(ROOT/f'native-host/build/native-emissions-{pid}.json');out['native']=native
        require(native['enabled'] and native['failures']==0 and native['refused']==0 and combat['rejected']==0,'Native admission failure')
        for exe,suffix in [('GameClientApp.patched.exe','native'),('java.exe','mc')]:
            subprocess.run(['um','win','shot','--exe',exe,str(prefix)+f'-{suffix}.png','--scale','.33'],cwd=ROOT,capture_output=True,check=True,timeout=20)
        out['passed']=True
    except Exception as error:out['error']=str(error)
    finally:
        out.update(cleanup(savedRule))
        if not out.get('cleaned') or out.get('cleanupError') or out.get('inputCleanupError'):out['passed']=False
        # Keep flight on; caller lands safely and parks the picker after review.
        path=prefix.with_suffix('.json');path.write_text(json.dumps(out,indent=2)+'\n')
        print(json.dumps({'path':str(path),'passed':out['passed'],'error':out.get('error'),'cleaned':out.get('cleaned'),'cleanupError':out.get('cleanupError')},indent=2))
    return out['passed']

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pid',type=int,required=True)
    raise SystemExit(0 if main(parser.parse_args().pid) else 1)
