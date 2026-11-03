"""Bounded live Genji cooldown observation; optional original Shift input."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,struct,subprocess,time
from observe_overwatch import ROOT,ResearchProcess
from observe_native_weapon_states import WeaponStates

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pid',type=int,required=True);parser.add_argument('--fire',action='store_true');args=parser.parse_args()
    p=ResearchProcess(args.pid);rows=[];process=None
    try:
        r=WeaponStates(p);r.sample_weapon();instance,graph,_=next(k for k in r.graph_cache if k[2]==0x05800000000001db)
        defs=r.stu_list(graph+0x60);states=[]
        for state, in struct.iter_unpack('<Q',r.vector(instance+0xa0,8,4096)):
            if state:
                idx=r.unpack('<i',state+0x70)[0];node=r.unpack('<i',defs[idx]+0x68)[0]
                if node==5:states.append(state)
        print('abilityStates',[(hex(s),hex(r.pointer(s)-p.base)) for s in states],flush=True)
        start=time.monotonic()
        if args.fire:process=subprocess.Popen(['um','win','drive','--proc','GameClientApp.patched.exe','focus','key 0x10','sleep 1000','key 0x10'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        while time.monotonic()-start<9:
            sample=r.sample_weapon(all_scripts=True);variables=r.varbag(r.pointer(instance+0x98))
            rows.append(dict(elapsed=time.monotonic()-start,variables=variables,states=[dict(address=s,raw=p.read(s,512).hex()) for s in states],records=[v for v in sample['records'].values() if v['script']=='05800000000001db']))
            time.sleep(.1)
        path=ROOT/'research/genji-cooldown-live.json';path.write_text(json.dumps(rows,indent=2)+'\n');print(path)
        for row in rows[::10]:print(round(row['elapsed'],2),[(v['rid'],v.get('value')) for v in row['variables'] if v['rid'] in ('0d8000000000003d','0d80000000000177','0d800000000001d4')],[(v['node'],v['nativeTick'],v['finished']) for v in row['records'] if v['node'] in(5,6,19)])
    finally:
        if process:print(process.communicate(timeout=2)[0].decode(errors='replace'))
        p.close()

if __name__=='__main__':main()
