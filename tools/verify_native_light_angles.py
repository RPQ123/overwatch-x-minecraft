"""Reversible native-lighting comparison at fixed MC position; actual window pixels."""
import argparse,json,time,subprocess
from contextlib import nullcontext
from calibrate_hero_roster import api,drive,report
from observe_overwatch import ROOT,ResearchProcess
from native_runtime_settings import temporary_render_settings,settings
from native_bootstrap_maps import read_loaded_map,MAPS
from native_map_light import owned_live_light
from calibrate_hero_roster import observe

PROFILES={'baseline':{},'ambient-off':{'Render.DynamicAmbient':0},'single-point':{'Render.SinglePointAmbient':1},'reflections-off':{'Render.LocalReflections':0},'ambient-single':{'Render.DynamicAmbient':0,'Render.SinglePointAmbient':1},'fog-off':{'Render.FogEnabled':0},'compute-fog-off':{'Render.ComputeFogEnabled':0},'all-fog-off':{'Render.FogEnabled':0,'Render.ComputeFogEnabled':0}}

def point(yaw,pitch,sender=None):
    for attempt in range(2):
        c=api('combat');delta=(yaw-c['yaw']+180)%360-180
        (sender or drive)('focus',f'rel {round(delta/.1)} {round((pitch-c["pitch"])/.1)}','sleep 600')
        current=api('combat')
        if abs((yaw-current['yaw']+180)%360-180)<=2 and abs(current['pitch']-pitch)<=2:
            current['angleAttempts']=attempt+1;return current
    raise ValueError(f'View failed bounded correction: wanted {yaw}/{pitch}, actual {current["yaw"]}/{current["pitch"]}')

def main(pid,profiles,folder,pitches=(-85,-45,0,45,85),yaws=(0,45,90,135,180,-135,-90,-45),sender=None):
    if ROOT/'research' not in folder.parents:raise ValueError('Private research output required')
    folder.mkdir(parents=True,exist_ok=True);process=ResearchProcess(pid)
    initial=api('combat');health=api('health');origin=health['player'];dimension=api('world')['dimension'];hero=observe(pid)['hero'];out={'pid':pid,'hero':hero,'initialView':{'yaw':initial['yaw'],'pitch':initial['pitch']},'origin':origin,'profiles':{},'passed':False,'visualAcceptance':'pending-image-review','passMeaning':'pose/map/owner checks only; inspect native hand and weapon pixels before accepting lighting'}
    try:
        loaded=read_loaded_map(process)
        if loaded['state']!=8 or loaded['mapId'] not in (MAPS['hollywood'],MAPS['kyoto-login']):raise ValueError('Use the verified Hollywood or Kyoto login scene')
        out['nativeMap']=loaded;out['renderSettingsBefore']={k:process.read(v['address'],1 if v['type']==1 else 4).hex() for k,v in settings(process).items() if k in {'Render.DynamicAmbient','Render.SinglePointAmbient','Render.LocalReflections'}}
        for name in profiles:
            values=PROFILES[name];rows=[];out['profiles'][name]=rows
            with temporary_render_settings(process,pid,values) if values else nullcontext():
                for yaw,pitch in [(y,p) for p in pitches for y in yaws]:
                    c=point(yaw,pitch,sender);path=folder/f'{name}-{yaw}-pitch{pitch}.png'
                    subprocess.run(['um','win','shot','--exe','GameClientApp.patched.exe',str(path),'--scale','.33'],cwd=ROOT,capture_output=True,check=True,timeout=15)
                    currentHealth=api('health');player=currentHealth['player']
                    afterView=api('combat')
                    if abs((yaw-afterView['yaw']+180)%360-180)>2 or abs(afterView['pitch']-pitch)>2:raise ValueError('View changed during actual screenshot capture')
                    if currentHealth['sourcePid']!=health['sourcePid'] or api('world')['dimension']!=dimension or read_loaded_map(process)!=loaded:raise ValueError('Map/dimension/source changed during comparison')
                    if any(abs(player[k]-origin[k])>.1 for k in ['x','z','feetY']) or observe(pid)['hero']!=hero:raise ValueError('Hero/player changed during lighting comparison')
                    row={'yaw':c['yaw'],'pitch':c['pitch'],'afterCaptureYaw':afterView['yaw'],'afterCapturePitch':afterView['pitch'],'angleAttempts':c['angleAttempts'],'player':player,'image':str(path.relative_to(ROOT))}
                    live=report(ROOT/f'native-host/build/world-live-{pid}.json')
                    if live.get('pid')!=pid or not live.get('enabled') or live.get('failures'):raise ValueError('No healthy current compositor for the actual captured pixels')
                    if live.get('fixedViewLight') or live.get('fixedKyotoLight'):
                        light=owned_live_light(process,pid);dot=sum(a*b for a,b in zip(light['direction'],live['basis'][3:6]))
                        key=(.5,-2**-.5,-.5) if live.get('viewLightRig')=='camera-key' else (0,-1,0)
                        expected=[sum(key[j]*live['basis'][j*3+i] for j in range(3)) for i in range(3)]
                        error=max(abs(a-b) for a,b in zip(expected,light['direction']))
                        row.update(light=light,cameraUpDot=dot,viewLightRig=live.get('viewLightRig','overhead'),directionError=error)
                        if not live.get('viewLightOwned') or live.get('failures') or error>.025:raise ValueError('Actual native lighting did not remain camera-relative')
                    rows.append(row)
            print(json.dumps({'profile':name,'angles':len(rows),'restored':True}),flush=True)
        out['passed']=True
    finally:
        try:point(initial['yaw'],initial['pitch'],sender);out['viewRestored']=True
        except Exception as e:out['viewRestoreError']=str(e)
        process.close();(folder/'angles.json').write_text(json.dumps(out,indent=2),encoding='utf-8')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pid',required=True,type=int);p.add_argument('--profiles',nargs='+',choices=list(PROFILES),default=['baseline']);p.add_argument('--pitches',nargs='+',type=float,default=[-85,-45,0,45,85]);p.add_argument('--yaws',nargs='+',type=float,default=[0,45,90,135,180,-135,-90,-45]);p.add_argument('--output',required=True);a=p.parse_args();main(a.pid,a.profiles,(ROOT/a.output).resolve(),a.pitches,a.yaws)
