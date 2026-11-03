"""Original-client physics oracle. Requires the body writer restored, not a second owner."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,struct,subprocess,time
from observe_overwatch import ROOT,ResearchProcess
from observe_native_weapon_states import WeaponStates

def main(pid):
    status=json.loads((ROOT/f'native-host/build/body-sync-{pid}.json').read_text())
    if not status.get('restored') or status.get('enabled'):raise ValueError('Restore the body callback before measuring native physics')
    process=ResearchProcess(pid);r=WeaponStates(process);sample=r.sample_weapon(False,True)
    admin=r.pointer(process.base+0x17b7f90);table=process.read(r.pointer(admin+16),65536);model=r.entity(table,sample['modelId']);controller=r.entity(table,sample['localId'])
    if r.unpack('<Q',r.component(controller,0x3f)+0x98)[0]!=0x02e0000000000008:raise ValueError('Original Pharah required')
    mover=r.component(model,0x15);flight=next(key for key in r.graph_cache if key[2]==0x0580000000000025);bag=r.pointer(flight[0]+0x98)
    numeric={v['rid']:v for v in r.varbag(bag)};rows=[];start=time.monotonic()
    command=subprocess.Popen(['um','win','drive','--proc','GameClientApp.patched.exe','focus','sleep 250','mdown 1280 720 right','sleep 2000','mup right','sleep 800','key 0x10','sleep 1500'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=ROOT)
    try:
        while command.poll() is None or time.monotonic()-start<6:
            if time.monotonic()-start>10:raise RuntimeError('Oracle input deadline')
            if r.unpack('<I',admin+0x220)[0]!=sample['localId']:raise ValueError('Native owner changed')
            values=r.varbag(bag)
            rows.append(dict(t=time.monotonic()-start,states=[dict(position=r.unpack('<3f',mover+offset+0x220),velocity=r.unpack('<3f',mover+offset+0x230),gravity=r.unpack('<3f',mover+offset+0x250),flags=r.unpack('<I',mover+offset+0x198)[0]) for offset in (0x7e0,0xa50)],variables={v['rid']:v.get('value') for v in values if v['rid'] in ('0d80000000000057','0d8000000000054e')}))
            time.sleep(.01)
        stdout,stderr=command.communicate(timeout=1)
        result=dict(pid=pid,bodyRestored=True,input=stdout.decode(errors='replace'),inputError=stderr.decode(errors='replace'),inputExit=command.returncode,rows=rows)
        path=ROOT/'research/pharah-native-flight-oracle.json';path.write_text(json.dumps(result,indent=2)+'\n');print('saved',path,'samples',len(rows))
        for n in range(0,len(rows),30):print(rows[n])
    finally:
        if command.poll() is None:command.kill()
        process.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--pid',required=True,type=int);main(parser.parse_args().pid)
