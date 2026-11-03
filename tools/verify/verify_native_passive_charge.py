"""Real idle-only native meters and original HUD captures across the beta roster.

Never grants charge, attacks, changes time, or synthesizes ultimate activation.
Use a fresh artifact directory. Pass/fail concerns passive meter growth; inspect
the original paired HUD screenshots separately before claiming visible progress.
"""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,subprocess,time
from pathlib import Path
from calibrate_hero_actions import select
from calibrate_hero_roster import api,ROSTER,report,drive
from observe_overwatch import ROOT,ResearchProcess
from native_charge import inspect


def main(pid,folder,heroes,seconds,require_growth):
    folder.mkdir(parents=True,exist_ok=False)
    result=dict(pid=pid,seconds=seconds,idleOnly=True,meterGrantsUsed=False,heroes=[],passed=False)
    def save():(folder/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    def meter():
        p=ResearchProcess(pid)
        try:return inspect(p)
        finally:p.close()
    def shot(path):
        subprocess.run(['um','win','shot','--exe','GameClientApp.patched.exe',str(path),'--scale','.33'],cwd=ROOT,check=True,capture_output=True,timeout=15)
    try:
        for name in heroes:
            actor=select(pid,name);time.sleep(.3)
            start=meter();before=api('combat');row=dict(hero=name,actorModel=actor['modelId'],before=start,combatBefore=before);result['heroes'].append(row);save()
            shot(folder/(name+'-before.png'));samples=[];wall=time.monotonic()
            while time.monotonic()-wall<seconds:
                samples.append(dict(t=time.monotonic()-wall,meter=meter(),combat=api('combat').get('nativeCharge')));time.sleep(.15)
            row.update(samples=samples,after=meter(),combatAfter=api('combat'));shot(folder/(name+'-after.png'))
            first,last=samples[0],samples[-1];elapsed=last['t']-first['t'];delta=last['meter']['chargeValue']-first['meter']['chargeValue'];row.update(delta=delta,elapsed=elapsed,rate=delta/elapsed)
            assert all(s['meter']['modelId']==actor['modelId'] and s['meter']['hero']==start['hero'] and s['meter']['costValue']==start['costValue'] for s in samples),'Native owner/cost changed during idle capture'
            row['growthPassed']=delta>0 and 3.5<delta/elapsed<6.5
            if require_growth:assert row['growthPassed'],f'{name} passive growth failed: {delta}/{elapsed}'
            row['passed']=True;save();print(json.dumps(dict(hero=name,delta=delta,rate=row['rate'],growth=row['growthPassed'],cost=start['costValue'])),flush=True)
        result['passed']=True
    except Exception as e:result['error']=repr(e)
    finally:
        try:drive('mup')
        except Exception:pass
        save();print(json.dumps({k:result.get(k) for k in ('passed','error')}),flush=True)
    return result['passed']


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--pid',type=int,required=True);a.add_argument('--output',type=Path,required=True);a.add_argument('--heroes',nargs='+',choices=[r[0] for r in ROSTER],default=[r[0] for r in ROSTER]);a.add_argument('--seconds',type=float,default=8);a.add_argument('--require-growth',action='store_true');v=a.parse_args();raise SystemExit(0 if main(v.pid,v.output,v.heroes,v.seconds,v.require_growth) else 1)
