"""Real dimension/hero/MC restart regression in cloned Twilight Switch saves."""
import argparse,json,math,subprocess,time,urllib.request
from calibrate_hero_actions import select
from calibrate_hero_roster import api,drive,report
from native_health_binding import inspect_health
from observe_overwatch import ROOT,ResearchProcess
from verify_genji_elimination_reset import post

def require(ok,message):
    if not ok:raise ValueError(message)

def native(pid):
    p=ResearchProcess(pid)
    try:
        r,b,verify=inspect_health(p);rows=[r.unpack('<Iff',b['health']+v['offset']) for v in b['pools']]
        model=r.pointer(b['health']+8);mover=r.component(model,0x15);pos=r.unpack('<fff',mover+0x7e0+0x220);verify()
        return dict(hero=b['hero'],modelId=b['modelId'],hp=sum(v[2] for v in rows),maximum=sum(v['amount'] for v in b['pools']),position=pos)
    finally:p.close()

def ready(pid,dimension=None,world=None,seconds=50):
    end=time.monotonic()+seconds
    while True:
        try:
            s=report(ROOT/'research/session-status.json');h=api('health');w=api('world');b=report(ROOT/f'native-host/build/body-sync-{pid}.json')
            if w.get('switchTrialError'):raise RuntimeError(w['switchTrialError'])
            if s.get('nativePid')==pid and s.get('ready') and not s.get('error') and b.get('worldStable') and b.get('sourcePid')==h['sourcePid'] and (dimension is None or w.get('dimension')==dimension) and (world is None or h['worldName']==world):
                require(not b['failures'] and h['player']['alive'] and h['player']['health']==20,'Dead player or failed body')
                n=native(pid)
                if s.get('hero',{}).get('modelId')==b['modelId']==n['modelId'] and s['hero']['id']==b['hero']==n['hero']:
                    return {'status':s,'health':h,'world':w,'body':b,'native':n}
        except (OSError,ValueError,KeyError):pass
        if time.monotonic()>end:raise ValueError('World/hero did not settle: '+str(report(ROOT/'research/session-status.json').get('error')))
        time.sleep(.15)

def shot(pid,name):
    actor=select(pid,name);row=ready(pid);require(row['native']['modelId']==actor['modelId'] and row['native']['hp']==row['native']['maximum']>0,'Stale or non-full native hero')
    before=api('health')['player'];drive('focus','hold 0x57 120','sleep 180');after=api('health')['player']
    row['movement']=math.dist([before['x'],before['feetY'],before['z']],[after['x'],after['feetY'],after['z']]);require(.05<row['movement']<3,'MC movement stuck or jumped')
    drive('focus','move 1280 720','sleep 300');pitch=api('combat')['pitch']
    drive('focus',f'rel 0 {round(-pitch/.1)}','sleep 500')
    post('start');time.sleep(.2);c=api('combat');require(c.get('targetHealth')==20 and not c.get('testError'),'Air target unavailable')
    drive('focus','mdown 1280 720','sleep 120','mup','sleep 600');row['combat']=api('combat');post('replay');time.sleep(.2);row['replay']=api('combat')
    expected=9.5 if name=='Genji' else 13
    if not (row['combat'].get('targetHealth')==expected and row['replay'].get('targetHealth')==expected and row['combat']['damageApplied']==row['replay']['damageApplied'] and row['combat']['rejected']==0):
        (ROOT/f'research/switch-failed-shot-{pid}-{time.time_ns()}.json').write_text(json.dumps(row,indent=2)+'\n');raise ValueError('Native weapon/ammo-to-real-damage/replay failed')
    post('cleanup');row['heroName']=name;return row

def main(pid,restart_world=None,reload=False):
    result={'pid':pid,'passed':False,'rows':[]};path=ROOT/f'research/world-hero-switch-{pid}-{time.time_ns()}.json'
    try:
        h=api('health');require(h['worldName'].startswith('Overwatch Twilight Switch '),'Use a backed-up isolated Switch clone')
        select(pid,'Genji');ready(pid)
        if reload:
            result['beforeReload']=ready(pid);beforeFrames=h['captured']
            with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:32133/world/switch-test/reload',method='POST'),timeout=3):pass
            deadline=time.monotonic()+100;departed=False;samples=[];result['gapSamples']=samples
            while True:
                n=native(pid);b=report(ROOT/f'native-host/build/body-sync-{pid}.json');samples.append({'native':n,'body':b});require(n['hp']>0 and not b['failures'],'Actor died/body failed during in-process reload')
                now=api('health');departed=departed or now.get('player') is None or b.get('sourceAgeMs',0)>250
                if departed and now.get('player') and now['captured']>beforeFrames:break
                if time.monotonic()>deadline:raise ValueError('In-process reload did not finish')
                time.sleep(.2)
            result['afterReload']=ready(pid);require(result['afterReload']['health']['sourcePid']==h['sourcePid'],'MC PID changed during same-process test')
            post('flight-open');time.sleep(.3);require(not api('combat').get('testError'),'Air lab unavailable');post('cleanup')
            result['rows'].append(shot(pid,'Genji'))
            post('melee');time.sleep(.3);drive('focus','key 0x56','sleep 800');result['sameModelMelee']=api('combat');require(result['sameModelMelee'].get('targetHealth')==15,'New server retained a stale ability owner');post('cleanup')
        elif restart_world:
            require(restart_world.startswith('Overwatch Twilight Switch ') and (ROOT/'guest-passthrough-client/saves'/restart_world/'level.dat').is_file(),'Precreate the regression clone')
            settings=ROOT/'passthrough-settings.json';cfg=json.loads(settings.read_text());cfg.update(worldName=restart_world,createWorld=False);settings.write_text(json.dumps(cfg,indent=2)+'\n')
            before=ready(pid);result['beforeRestart']=before
            with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:32133/shutdown',method='POST'),timeout=3):pass
            deadline=time.monotonic()+110;samples=[];result['gapSamples']=samples
            while True:
                n=native(pid);b=report(ROOT/f'native-host/build/body-sync-{pid}.json')
                require(n['hp']>0 and not b['failures'] and b['enabled'],'Native hero died/body stopped during MC reload')
                try:
                    now=api('health')
                    if now['sourcePid']!=h['sourcePid'] and (now.get('player') or {}).get('alive'):break
                except (OSError,ValueError,TypeError):pass
                samples.append({'native':n,'body':b})
                if time.monotonic()>deadline:raise ValueError('Standalone supervisor did not reopen MC')
                time.sleep(.3)
            result['afterRestart']=ready(pid,world=restart_world)
            heights=[s['native']['position'][1] for s in samples if s['body'].get('sourceAgeMs',0)>250];require(heights and max(heights)-min(heights)<1,'Original actor fell during source gap')
            require(result['afterRestart']['body']['sessionResumes']>before['body']['sessionResumes'],'Replacement MC session was not resumed')
            post('flight-open');time.sleep(.3);require(not api('combat').get('testError'),'Air lab unavailable');post('cleanup')
            for name in ('McCree','Genji'):result['rows'].append(shot(pid,name))
        else:
            for short,dimension in [('overworld','minecraft:overworld'),('nether','minecraft:the_nether'),('end','minecraft:the_end'),('twilight','twilightforest:twilight_forest')]:
                with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:32133/world/switch-test/'+short,method='POST'),timeout=3):pass
                # Deliberately recreate a hero while MC is changing dimension.
                select(pid,'McCree');ready(pid,dimension=dimension)
                for name in ('McCree','Genji'):
                    row=shot(pid,name);require(row['world']['dimension']==dimension,'Wrong actual dimension');result['rows'].append(row)
                subprocess.run(['um','win','shot','--exe','GameClientApp.patched.exe',str(path.with_suffix(''))+'-'+short+'.png','--scale','.33'],cwd=ROOT,capture_output=True,check=True,timeout=20)
                print(json.dumps({'dimension':dimension,'heroes':'McCree/Genji','passed':True}),flush=True)
        result['passed']=True
    except Exception as error:result['error']=str(error)
    finally:
        try:post('cleanup');time.sleep(.3);result['cleaned']=api('combat')['wallBlocks']==0 and 'targetHealth' not in api('combat')
        except Exception as error:result['cleanupError']=str(error);result['passed']=False
        path.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'path':str(path),'passed':result['passed'],'error':result.get('error'),'rows':len(result['rows']),'cleaned':result.get('cleaned')},indent=2))
    return result['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pid',type=int,required=True);p.add_argument('--restart-world');p.add_argument('--reload',action='store_true')
    a=p.parse_args();raise SystemExit(0 if main(a.pid,a.restart_world,a.reload) else 1)
