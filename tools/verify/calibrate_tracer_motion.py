"""Measure original Tracer movement after restoring the existing body owner."""

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
    body=json.loads((ROOT/f'native-host/build/body-sync-{pid}.json').read_text())
    if body.get('enabled') or not body.get('restored'):raise ValueError('Restore body callback first')
    p=ResearchProcess(pid);r=WeaponStates(p);s=r.sample_weapon(False,True)
    admin=r.pointer(p.base+0x17b7f90);table=p.read(r.pointer(admin+16),65536)
    controller=r.entity(table,s['localId']);model=r.entity(table,s['modelId'])
    if r.unpack('<Q',r.component(controller,0x3f)+0x98)[0]!=0x02e0000000000003:raise ValueError('Original Tracer required')
    mover=r.component(model,0x15);script,graph,_=next(k for k in r.graph_cache if k[2]==0x0580000000000024)
    bag=r.pointer(script+0x98);rows=[];start=time.monotonic()
    commands=['focus','sleep 300','key 0x10','sleep 650','key 0x44 down','sleep 100','key 0x10','sleep 300','key 0x44 up','sleep 400','key 0x10','sleep 500','key 0x10','sleep 3500','key 0x10','sleep 600']
    command=subprocess.Popen(['um','win','drive','--proc','GameClientApp.patched.exe',*commands],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        while command.poll() is None or time.monotonic()-start<7:
            if time.monotonic()-start>15:raise RuntimeError('Input deadline')
            if r.unpack('<I',admin+0x220)[0]!=s['localId'] or r.unpack('<I',model+0x94)[0]!=s['modelId']:raise ValueError('Native owner changed')
            rows.append(dict(t=time.monotonic()-start,states=[dict(position=r.unpack('<3f',mover+offset+0x220),velocity=r.unpack('<3f',mover+offset+0x230),gravity=r.unpack('<3f',mover+offset+0x250)) for offset in (0x7e0,0xa50)],variables={v['rid']:v.get('value') for v in r.varbag(bag)}))
            time.sleep(.005)
        stdout,stderr=command.communicate(timeout=1)
        result=dict(pid=pid,bodyRestored=True,input=stdout.decode(errors='replace'),stderr=stderr.decode(errors='replace'),exit=command.returncode,rows=rows)
        path=ROOT/'research/tracer-native-motion-oracle.json';path.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items() if k!='rows'}));print('samples',len(rows))
        previous=None
        for row in rows:
            key=row['variables'].get('0d8000000000000b')
            if key!=previous:print(dict(t=row['t'],charges=key,position=row['states'][0]['position']));previous=key
    finally:
        if command.poll() is None:command.kill()
        p.close()

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--pid',required=True,type=int);main(a.parse_args().pid)
