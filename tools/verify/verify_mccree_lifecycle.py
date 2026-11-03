"""Actual native E/Q and full-meter F11 after real four-dimension/hero changes.
Only the pinned isolated Twilight Switch lab; reversible targets and air floors.
Uses explicit F11 grants, not a claim of naturally earned full charge.
"""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import sys,json,time,subprocess,urllib.request,argparse
from pathlib import Path

from calibrate_hero_roster import api,drive,report
from calibrate_hero_actions import select
from verify_bastion_tank_movement import stable
from verify_native_light_angles import point
from verify_genji_elimination_reset import post
from verify_switch_readiness import check_light
from verify_world_hero_switch import native
from observe_overwatch import ROOT,ResearchProcess
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pid',type=int,required=True);parser.add_argument('--output',required=True);args=parser.parse_args();pid=args.pid
folder=(ROOT/args.output).resolve()
if ROOT/'research' not in folder.parents:parser.error('Use private research output')
folder.mkdir(parents=True,exist_ok=True);result=dict(pid=pid,passed=False,rows=[])
process=ResearchProcess(pid);process.close()
if not api('health')['worldName'].startswith('Overwatch Twilight Switch '):raise ValueError('Use the isolated mod-pinned Switch lab')
D={'overworld':'minecraft:overworld','nether':'minecraft:the_nether','end':'minecraft:the_end','twilight':'twilightforest:twilight_forest'}
def save(): (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n')
def require(b,m):
 if not b:raise ValueError(m)
def run(label,commands):
 p=subprocess.Popen(['um','win','drive','--proc','GameClientApp.patched.exe','focus',*commands],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE);start=time.monotonic();samples=[]
 while p.poll() is None or time.monotonic()-start<1:
  require(time.monotonic()-start<15,'Input deadline');samples.append(dict(t=time.monotonic()-start,c=api('combat')));time.sleep(.025)
 o,e=p.communicate(timeout=1);require(p.returncode==0 and b'fail' not in o,'Input focus interference');return samples
try:
 for name,dimension in D.items():
  row=dict(dimension=dimension);result['rows'].append(row);save();post('cleanup')
  with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:32133/world/switch-test/'+name,method='POST'),timeout=3):pass
  select(pid,'Genji');select(pid,'McCree');stable(pid,dimension);point(180,0)
  # Six reversible rises put the targets outside the70m radius of natural mobs.
  # A single rise admitted31 legitimate nearby mobs in the Overworld and made
  # the old four-to-six-shot assertion an invalid crowd acceptance condition.
  for _ in range(6):
   post('flight-open');time.sleep(.25);require(not api('combat').get('testError'),'Air fixture refused')
  post('start');time.sleep(.2);before=api('combat');require(before.get('targetHealth')==20,'No fresh target')
  samples=run('E',['key 0x45','sleep 2900']);row['E']=samples;save()
  require(min(x['c'].get('targetHealth',20) for x in samples)==12.5,'Modern Flashbang damage not75 native-equivalent HP')
  slow=[x for x in samples if abs(x['c'].get('targetMovementSpeed',9)-.25)<1e-6];require(slow,'No exact50% slow')
  require(slow[-1]['t']-slow[0]['t']>1.78,'Two-second slow ended too early')
  require(max(x['c'].get('targetSlownessTicks',0) for x in samples)>=35 and any(x['c'].get('targetPotionParticles') for x in samples),'No real visible Slowness potion')
  require(samples[-1]['c']['targetMovementSpeed']==.5 and samples[-1]['c']['flashbang']['active']==0,'Slow did not restore')
  post('replay');time.sleep(.1);require(api('combat')['targetHealth']==12.5,'Flash replay applied twice')
  post('deadeye-crowd');time.sleep(.2);require(len(api('combat').get('beamTargets',{}))==12 and not api('combat').get('testError'),'No twelve-target crowd');oldShots=api('combat')['deadeye']['shots'];samples=run('Q',['key 0x7A','sleep 200','key 0x51','sleep 4000','click 1280 720','sleep 3200']);row['Q']=samples;save()
  require(max(x['c']['deadeye'].get('readyLocks',0) for x in samples)==12,'Twelve armored/absorbing MC targets were not fully locked')
  require(all(v==0 for v in samples[-1]['c']['beamTargets'].values()),'Original fire action did not kill acquired targets')
  shots=samples[-1]['c']['deadeye']['shots']-oldShots
  require(shots==12,'Original animations did not release all twelve individual shots')
  receipts=samples[-1]['c']['deadeye']['shotReceipts'][-shots:];row['shotReceipts']=receipts
  require(len({v['sequence'] for v in receipts})==shots and all(128<=b['nativeTick']-a['nativeTick']<=250 and b['serverTick']>a['serverTick'] and 50<=b['wall']-a['wall']<=300 for a,b in zip(receipts,receipts[1:])),'Shot animation receipts were batched/replayed or violated original Wait72 cadence')
  require(any(x['c']['deadeye']['shots']>oldShots and x['c']['nativeCharge']['charge']<=.1 for x in samples),'Confirmed Deadeye fire did not spend remaining meter')
  require(not samples[-1]['c']['nativeCharge']['active'],'Native Deadeye did not recover after confirmed fire')
  post('start');time.sleep(.2);drive('focus','key 0x31','key 0x32','key 0x33','wheel 120','wheel -120','click 1280 720','sleep 500')
  row['ordinaryShotAfterQ']=api('combat');require(row['ordinaryShotAfterQ'].get('targetHealth')==13,'Ordinary fire did not recover after Q')
  post('cleanup')
  # Let original Q recovery and the following revolver recoil finish before
  # comparing the separate native light/report snapshots at a fixed pose.
  time.sleep(.8);point(180,0);time.sleep(.2)
  row['nativeHealth']=native(pid);row['light']=check_light(pid,{'modelId':row['nativeHealth']['modelId']});require(row['nativeHealth']['hp']==row['nativeHealth']['maximum']>0,'Broken health after transition')
  row['passed']=True;save();print(json.dumps(dict(dimension=dimension,passed=True,grenadeFrames=api('combat').get('flashbangRenderFrames'),lockFrames=api('combat').get('deadeyeRenderFrames'))),flush=True)
 result['passed']=True
except Exception as e:result['error']=repr(e)
finally:
 try:drive('mup','mup right');post('cleanup')
 except Exception as e:result['cleanupError']=str(e)
 save();print(json.dumps({k:result.get(k) for k in ('passed','error','cleanupError')}),flush=True)

raise SystemExit(0 if result.get("passed") and not result.get("cleanupError") else 1)
