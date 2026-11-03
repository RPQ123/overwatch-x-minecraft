"""Exercise original weapons and retain bounded resolved-config diagnostics."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,struct,time
from observe_overwatch import ROOT,ResearchProcess
from calibrate_hero_actions import select
from calibrate_hero_roster import drive,report
from native_charge import grant_for_test
from native_factory_calibration import enabled

def collect(pid,heroes):
    result=dict(pid=pid,rows=[])
    for hero in heroes:
        row=dict(hero=hero);result['rows'].append(row)
        try:
            row['model']=select(pid,hero)['modelId'];time.sleep(1.5)
            if hero=='Hanzo':commands=['mdown 1280 720','sleep 1100','mup']
            elif hero=='Widowmaker':commands=['mdown 1280 720 right','sleep 1500','click 1280 720','sleep 200','mup right']
            elif hero=='Mei':commands=['mdown 1280 720','sleep 350','mup','mdown 1280 720 right','sleep 600','mup right']
            elif hero=='Bastion':commands=['key 0x10','sleep 1300','mdown 1280 720','sleep 300','mup']
            elif hero=='Pharah':
                p=ResearchProcess(pid)
                try:row['labGrant']=grant_for_test(p,pid)
                finally:p.close()
                commands=['key 0x51','sleep 3500']
            elif hero=='Torbjorn':commands=['click 1280 720','sleep 400','mdown 1280 720 right','sleep 300','mup right']
            else:commands=['mdown 1280 720','sleep 250','mup']
            drive('focus',*commands,'sleep 500');time.sleep(.3)
            native=report(ROOT/f'native-host/build/native-emissions-{pid}.json')
            row['configs']=native.get('factoryConfigs',[]);row['observations']=[v for v in native.get('factoryObservations',[]) if v['hero']&0xffff==dict(Hanzo=5,Junkrat=0x65,Mei=0xdd,Torbjorn=6,Bastion=0x15,Widowmaker=10,Pharah=8,Soldier76=0x6e)[hero]]
            print(json.dumps(dict(hero=hero,resources=sorted({hex(v['resource']) for v in row['observations']}))),flush=True)
        except Exception as e:row['error']=str(e);print(json.dumps(dict(hero=hero,error=str(e))),flush=True)
        (ROOT/'research/native-weapon-config-calibration-20261019.json').write_text(json.dumps(result,indent=2)+'\n')
def main(pid,heroes):
    with enabled(pid):collect(pid,heroes)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--pid',required=True,type=int);a.add_argument('--heroes',nargs='+',required=True);args=a.parse_args();main(args.pid,args.heroes)
