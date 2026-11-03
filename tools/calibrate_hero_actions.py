"""Record real native states and factory events for each authorized action."""
from modpack.config import paths
import argparse,json,re,struct,subprocess,time,zlib
from pathlib import Path
from observe_overwatch import ROOT,ResearchProcess
from observe_native_weapon_states import WeaponStates,changed_records
from calibrate_hero_roster import ROSTER,observe,drive,report,api
from launch_passthrough_session import first_person_ready
from native_charge import grant_for_test
from native_factory_calibration import enabled as factory_calibration

def names():
    root=paths().get('owTypes')
    out={}
    for file in root.glob('*.cs'):
        for name in re.findall(r'public (?:abstract )?class (\w+)',file.read_text(encoding='utf-8-sig')):out[f'{zlib.crc32(name.lower().encode()):08x}']=name
    return out

def select(pid,name):
    suffix,x=next((s,x) for n,s,x in ROSTER if n==name)
    current=observe(pid)
    if current['hero']==0x02e0000000000000+suffix and first_person_ready(pid):return current
    commands=['focus','mup']
    if first_person_ready(pid):commands+=['key 0x48','sleep 650']
    drive(*commands,f'click {x} 1224','sleep 650','click 1280 1358','sleep 1700')
    deadline=time.monotonic()+8
    while True:
        current=observe(pid)
        if current['hero']==0x02e0000000000000+suffix and first_person_ready(pid):return current
        if time.monotonic()>deadline:raise ValueError('Hero selection mismatch')
        time.sleep(.2)

def _record_action(pid,reader,action,commands,types):
    before=reader.sample_weapon(require_volley=False,all_scripts=True)
    definitions={}
    for (instance,graph,resource),definition in reader.graph_cache.items():
        nodes=reader.graph_nodes(graph)
        definitions[instance]={n['index']:dict(type=n.get('hash'),name=types.get(n.get('hash'))) for n in nodes}
    previous=before['records'];rows=[];start=time.monotonic();errors=[]
    command=subprocess.Popen(['um','win','drive','--proc','GameClientApp.patched.exe','focus',*commands],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    while time.monotonic()-start<1.2 or command.poll() is None:
        if time.monotonic()-start>12:command.kill();raise RuntimeError('Input process deadline')
        try:
            sample=reader.sample_weapon(require_volley=False,all_scripts=True);changes=changed_records(previous,sample['records']);previous=sample['records']
            if changes:rows.append(dict(elapsed=time.monotonic()-start,changes=[dict(v,**definitions.get(v['instanceAddress'],{}).get(v['node'],{})) for v in changes]))
        except (OSError,ValueError) as error:errors.append(str(error))
        time.sleep(.03)
    stdout,stderr=command.communicate(timeout=1)
    if command.returncode or b'focus -> fail' in stdout:raise RuntimeError((stdout+stderr).decode(errors='replace')[-1000:])
    native=report(ROOT/f'native-host/build/native-emissions-{pid}.json')
    return dict(action=action,before=before,after=reader.sample_weapon(require_volley=False,all_scripts=True),changes=rows,readErrors=errors,input=stdout.decode(errors='replace'),factoryObservations=native.get('factoryObservations',[]))

def record_action(pid,reader,action,commands,types):
    with factory_calibration(pid):return _record_action(pid,reader,action,commands,types)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pid',type=int,required=True);parser.add_argument('--heroes',nargs='+',required=True);parser.add_argument('--actions',nargs='+');args=parser.parse_args()
    types=names();out=ROOT/'research/hero-action-calibration';out.mkdir(exist_ok=True)
    actions=[('primary',['mdown 1280 720','sleep 650','mup']),('alternate',['mdown 1280 720 right','sleep 1000','mup right']),
             ('shift',['hold 0x10 900']),('e',['key 0x45','sleep 650','click 1280 720']),('melee',['key 0x56']),
             ('ultimate',['key 0x51','sleep 1600','mdown 1280 720','sleep 500','mup'])]
    for name in args.heroes:
        path=out/(name+'.json');result={'hero':name,'pid':args.pid,'inputAuthorized':True,'actions':[]}
        try:
            result['initial']=select(args.pid,name);p=ResearchProcess(args.pid)
            try:
                reader=WeaponStates(p)
                for action,commands in actions:
                    if args.actions and action not in args.actions:continue
                    if action=='ultimate':
                        try:result['ultimateGrant']=grant_for_test(p,args.pid)
                        except (OSError,ValueError) as e:result['ultimateGrantError']=str(e)
                    value=record_action(args.pid,reader,action,commands,types);result['actions'].append(value)
                    path.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'hero':name,'action':action,'changedNodes':sum(len(v['changes']) for v in value['changes']),'errors':len(value['readErrors'])}),flush=True)
                    time.sleep(.6)
            finally:p.close()
        except Exception as e:result['error']=str(e);print(json.dumps({'hero':name,'error':str(e)}),flush=True)
        path.write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
