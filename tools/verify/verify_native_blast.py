"""Actual Pharah direct/splash/terrain/replay checks; no synthetic shot events."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,time,subprocess
from calibrate_hero_roster import api,drive,observe,report
from observe_overwatch import ROOT
from verify_genji_elimination_reset import post

def require(ok,message):
    if not ok:raise ValueError(message)

def fire():drive('focus','mdown 1280 720','sleep 150','mup','sleep 850')

def main(pid):
    result={'pid':pid,'passed':False};stamp=time.time_ns();prefix=ROOT/f'research/native-blast-{pid}-{stamp}'
    try:
        require(observe(pid)['hero']==0x02e0000000000008,'Select the actual native Pharah first')
        post('flight-open');time.sleep(.4);require(not api('combat').get('testError'),'No loaded air platform')
        post('cleanup');drive('focus','move 1280 720','sleep 300');pitch=api('combat')['pitch']
        drive('focus',f'rel 0 {round(-pitch/.1)}','sleep 400')
        post('start');time.sleep(.25);before=api('combat');result['directBefore']=before
        require(not before.get('testError') and before.get('targetHealth')==20,'Direct target corridor unavailable')
        require(api('health')['player']['flying'],'Expected the preserved creative flight for the air-only lab')
        fire();after=api('combat');result['directAfter']=after
        post('replay');time.sleep(.2);again=api('combat');result['directReplay']=again
        direct=after['rocketDirectHealthLost']-before['rocketDirectHealthLost'];splash=after['rocketSplashHealthLost']-before['rocketSplashHealthLost']
        require(abs(direct-4)<.001 and abs(splash-8)<.001 and abs(after['targetHealth']-8)<.001,'Actual native40+80 did not cause separate4+8 MC damage')
        require(again['targetHealth']==after['targetHealth'] and again['rocketDirectHealthLost']==after['rocketDirectHealthLost'] and again['rocketSplashHealthLost']==after['rocketSplashHealthLost'],'Replay duplicated direct/splash damage')
        post('rocket');time.sleep(.25);before=api('combat');result['terrainBefore']=before
        require(not before.get('testError') and before.get('testStoneRemaining')==23 and before.get('beamTargets')=={'rocketNear':20.0,'rocketOutside':20.0},'Air-only terrain fixture unavailable')
        fire();after=api('combat');result['terrainAfter']=after;post('replay');time.sleep(.2);again=api('combat');result['terrainReplay']=again
        keys=('rocketExplosions','rocketBlocksDestroyed','damageApplied','testStoneRemaining','testProtectedRemaining','rocketDirectHealthLost','rocketSplashHealthLost','beamTargets')
        require(all(after.get(k)==again.get(k) for k in keys),'Terrain replay duplicated a native effect')
        require(after['rocketExplosions']-before['rocketExplosions']==1 and after['testStoneRemaining']<23 and after['testProtectedRemaining']==2,'Original rocket did not destroy only the destructible test terrain')
        require(0<after['beamTargets']['rocketNear']<20 and after['beamTargets']['rocketOutside']==20,'Splash range/exposure changed')
        native=report(ROOT/f'native-host/build/native-emissions-{pid}.json');result['native']=native
        require(native['enabled'] and native['failures']==0 and native['refused']==0 and after['rejected']==0,'Native combat admission failed')
        subprocess.run(['um','win','shot','--exe','GameClientApp.patched.exe',str(prefix)+'.png','--scale','.33'],cwd=ROOT,capture_output=True,check=True)
        result['passed']=True
    except Exception as error:result['error']=str(error)
    finally:
        try:post('cleanup');time.sleep(.2);result['cleaned']=api('combat')['wallBlocks']==0
        except Exception as error:result['cleanupError']=str(error);result['passed']=False
        # Caller lands afterward; returning here with flight on prevents a fall
        # while the temporary blocks and projectile targets are being restored.
        path=prefix.with_suffix('.json');path.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({'path':str(path),'passed':result['passed'],'error':result.get('error'),'cleaned':result.get('cleaned')},indent=2))
    return result['passed']

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pid',required=True,type=int)
    raise SystemExit(0 if main(parser.parse_args().pid) else 1)
