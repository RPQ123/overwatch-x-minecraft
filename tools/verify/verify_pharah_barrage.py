"""Real original Barrage factories, curved MC collision, visuals and recovery.

Uses the pinned full-mod isolated Switch lab and reversible fixtures. F11 is an
explicit test grant, not evidence of earning an entire ultimate naturally.
"""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,subprocess,time,urllib.request
from observe_overwatch import ROOT,ResearchProcess
from calibrate_hero_actions import select
from calibrate_hero_roster import api,drive,report
from verify_bastion_tank_movement import stable
from verify_native_light_angles import point
from verify_genji_elimination_reset import post
from native_factory_calibration import enabled
from verify_world_hero_switch import native

def require(value,message):
    if not value:raise ValueError(message)

def main(pid,folder,dimensions):
    folder=(ROOT/folder).resolve()
    require(ROOT/'research' in folder.parents and not folder.exists(),'Use a new private research directory')
    folder.mkdir(parents=True);p=ResearchProcess(pid);p.close()
    require(api('health')['worldName'].startswith('Overwatch Twilight Switch '),'Use the full-mod isolated Switch lab')
    result=dict(pid=pid,passed=False,dimensions=[])
    def save(): (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    def volley(label,record=False):
        before=api('combat');rows=[];capture=None
        if record:
            capture=subprocess.Popen(['um','win','record','--pid',str(pid),'--exe','GameClientApp.patched.exe','--out',str(folder/label),'--seconds','10','--fps','60'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            time.sleep(1.3)
        with enabled(pid):
            child=subprocess.Popen(['um','win','drive','--proc','GameClientApp.patched.exe','focus','key 0x7A','sleep 250','key 0x51','sleep 6100'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            start=time.monotonic()
            while child.poll() is None:
                require(time.monotonic()-start<15,'Input deadline')
                rows.append(dict(t=time.monotonic()-start,combat=api('combat')));time.sleep(.045)
            out,err=child.communicate();require(child.returncode==0 and b'-> fail' not in out,'Focus/input interference')
            original=report(ROOT/f'native-host/build/native-emissions-{pid}.json')
        if capture:
            out,err=capture.communicate(timeout=15);require(capture.returncode==0,'Native recording failed')
        after=api('combat');delta=after['admitted']-before['admitted']
        data=dict(before=before,after=after,samples=rows,native=original)
        (folder/(label+'.json')).write_text(json.dumps(data,indent=2))
        require(delta==90 and after['rejected']==before['rejected'],'Original ninety-shot admission failed')
        require(after['active']==0,'Barrage did not retire its bounded flights')
        require(original['barrageOracleChecks']>=96 and original['barrageOracleFailures']==0 and original['barrageOracleMaxError']<.0001,'Native Wave arithmetic oracle failed')
        require(any(x['combat'].get('nativeCharge',{}).get('charge')==0 for x in rows),'No actual native meter debit')
        require(not after.get('nativeCharge',{}).get('active'),'Native Barrage End missing')
        require(after['projectileModelsShown']>before['projectileModelsShown'] and not after['pharahVisualError'],'No visible sampled Barrage models')
        require(after['barragePresentationLaunches']-before['barragePresentationLaunches']==90,'Cosmetic cue lost/duplicated an admitted factory')
        require(after['barrageSound']['starts']-before['barrageSound']['starts']==1 and not after['barrageSound']['playing'],'Firing loop repeated or survived native End')
        require(not after['barrageVisuals']['error'] and after['barrageVisuals']['model']=='mc-barrage-mini-v1','Independent Barrage presentation unavailable')
        return data
    ids={'overworld':'minecraft:overworld','nether':'minecraft:the_nether','end':'minecraft:the_end','twilight':'twilightforest:twilight_forest'}
    try:
        for dimension in dimensions:
            row=dict(dimension=dimension);result['dimensions'].append(row);save();post('cleanup')
            with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:32133/world/switch-test/'+dimension,method='POST'),timeout=3):pass
            select(pid,'Genji');select(pid,'Pharah');stable(pid,ids[dimension]);point(180,0)
            post('flight-open');time.sleep(.3);require(not api('combat').get('testError'),'Air fixture refused')
            post('start');time.sleep(.2);post('wall');time.sleep(.2)
            covered=volley(dimension+'-covered');row['coverHealth']=covered['after']['targetHealth'];require(row['coverHealth']==20,'Barrage leaked damage through cover')
            post('open');time.sleep(.2)
            opened=volley(dimension+'-open',record=dimension=='overworld');row['openHealth']=opened['after']['targetHealth'];require(row['openHealth']==0,'Barrage did not damage actual exposed target')
            before=api('combat');post('replay');time.sleep(.3);after=api('combat')
            require(all(after[k]==before[k] for k in ('targetHealth','rocketExplosions','damageApplied')),'Replay repeated Barrage damage')
            require(after['barragePresentationLaunches']==before['barragePresentationLaunches'] and after['barragePresentationImpacts']==before['barragePresentationImpacts'] and after['barrageSound']['starts']==before['barrageSound']['starts'],'Replay repeated Barrage presentation')
            post('start');time.sleep(.2);before=api('combat');drive('focus','key 0x31','wheel 120','click 1280 720','sleep 600');after=api('combat')
            row['primaryHealth']=after['targetHealth'];require(row['primaryHealth']==8,'Primary did not recover after Q/world/hero recreation')
            row['earnedCharge']=after['nativeCharge']['charge']-before['nativeCharge']['charge'];require(row['earnedCharge']>=100,'Actual primary damage did not charge native HUD')
            post('cleanup');time.sleep(.25);row['health']=native(pid);require(row['health']['hp']==row['health']['maximum']>0,'Transition produced invalid native health')
            row['passed']=True;save();print(json.dumps(row),flush=True)
        result['passed']=True
    except Exception as error:result['error']=repr(error)
    finally:
        try:drive('mup','mup right');post('cleanup');time.sleep(.25);result['cleaned']=api('combat').get('wallBlocks')==0
        except Exception as error:result['cleanupError']=str(error)
        save();print(json.dumps({k:result.get(k) for k in ('passed','error','cleaned','cleanupError')}),flush=True)
    return result['passed']

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pid',required=True,type=int);parser.add_argument('--output',required=True);parser.add_argument('--dimensions',nargs='+',default=['overworld','nether','end','twilight']);a=parser.parse_args()
    raise SystemExit(0 if main(a.pid,a.output,a.dimensions) else 1)
