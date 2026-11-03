"""Observe native attack commands and projectile components; no input or writes."""
import argparse
from collections import Counter
import json,math,struct,time
from observe_overwatch import ROOT,ResearchProcess,PoseReader,PATCHED_SHA256

class CombatReader(PoseReader):
    def sample(self):
        admin=self.pointer(self.memory.base+0x17b7f90)
        table=self.memory.read(self.pointer(admin+0x10),65536)
        local_id=self.unpack('<I',admin+0x220)[0];controller=self.entity(table,local_id)
        local=self.component(controller,0x2f)
        current=self.unpack('<H',local+0x147a)[0];copied=self.unpack('<H',local+0x148a)[0]
        info=self.component(controller,0x3f);hero=self.unpack('<Q',info+0x98)[0]
        iterations=self.pointer(admin+0xb0)
        items,count,capacity=self.unpack('<Qii',iterations+0x27*0x18)
        if not 0<=count<=capacity<=4096:raise ValueError('Invalid projectile iterator')
        projectiles=[]
        for item, in struct.iter_unpack('<Q',self.memory.read(items,count*8) if count else b''):
            if self.unpack('<B',item+0x10)[0]!=0x27:raise ValueError('Unexpected projectile component type')
            entity=self.pointer(item+8);entity_id=self.unpack('<I',entity+0x94)[0]
            source_candidate=self.unpack('<I',item+0x18)[0]
            position=None
            try:
                scene=self.component(entity,1);xyz=self.unpack('<3f',scene+0x60)
                if all(math.isfinite(v) and abs(v)<1e6 for v in xyz):position=xyz
            except (OSError,ValueError):pass
            projectiles.append({'entityId':entity_id,'component':item,'ownerCandidate':source_candidate,'scenePosition':position})
        if self.pointer(self.memory.base+0x17b7f90)!=admin or self.unpack('<I',admin+0x220)[0]!=local_id:
            raise ValueError('Original world/player changed during read')
        return {'localId':local_id,'heroResourceId':hero,'currentButtons':current,'copiedButtons':copied,'projectiles':projectiles}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid',type=int,required=True);parser.add_argument('--seconds',type=int,default=180)
    args=parser.parse_args()
    if args.pid<=0 or not 1<=args.seconds<=300:parser.error('Exact PID and 1..300 seconds required')
    process=ResearchProcess(args.pid);reader=CombatReader(process);start=time.monotonic()
    rows=[];total=0;failures=0;previous=None;last_heartbeat=0;commands=Counter();seen=set()
    try:
        while time.monotonic()-start<args.seconds:
            elapsed=time.monotonic()-start
            try:
                sample=reader.sample();total+=1;commands[str(sample['currentButtons'])]+=1
                signature=(sample['currentButtons'],sample['copiedButtons'],tuple((p['entityId'],p['scenePosition']) for p in sample['projectiles']))
                seen.update(p['entityId'] for p in sample['projectiles'])
                if len(rows)<10000 and (signature!=previous or elapsed-last_heartbeat>=1):
                    rows.append({'elapsed':round(elapsed,4),**sample});last_heartbeat=elapsed
                    # Publish incrementally so idle time cannot hide a short attack.
                    destination=ROOT/'research/native-combat-observation.json';temporary=destination.with_suffix('.tmp')
                    temporary.write_text(json.dumps({'playerWrites':False,'agentInput':False,'sha256':PATCHED_SHA256,'samples':rows}),encoding='utf-8');temporary.replace(destination)
                previous=signature
            except (OSError,ValueError):failures+=1
            time.sleep(.01)
    finally:process.close()
    summary={'samples':total,'readFailures':failures,'buttonHistogram':dict(commands),'uniqueProjectileIds':len(seen),
             'nativeAttackOrHitVerified':False,'scenePositionMissingIsNotProofOfNoProjectile':True}
    (ROOT/'research/native-combat-observation-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary))
