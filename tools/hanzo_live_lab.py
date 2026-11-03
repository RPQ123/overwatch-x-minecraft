"""Hanzo-owned 16m scene receipts; used only by the isolated live verifiers."""
import json
import time
from verify_bastion_cannon import Suite, require

KEY='hanzoCombatLab'


def snapshot(data):
    return dict(lab=data.get(KEY),testError=data.get('testError'),wallBlocks=data.get('wallBlocks'),
                cannonLab=bool(data.get('cannonLab')),targetPresent='targetHealth' in data,
                targetId=data.get('targetId'),targetHealth=data.get('targetHealth'))


def cleanup_contract(state, previous_serial):
    lab=state.get('lab') or {}
    checks=dict(acknowledged=lab.get('cleanupSerial',0)>previous_serial,
                ownedFloorRestored=lab.get('ownedBlocks')==0 and lab.get('lastCleanup',{}).get('pending')==0,
                sceneInactive=not lab.get('active') and not state['cannonLab'],
                genericRestored=state['wallBlocks']==0 and not state['targetPresent'],noCleanupError=not lab.get('error'))
    return dict(passed=all(checks.values()),assertions=checks,failures=[k for k,v in checks.items() if not v])


def wait_cleanup(s, previous_serial, timeout=3):
    deadline=time.monotonic()+timeout;trace=[];stable=0
    while time.monotonic()<deadline:
        state=snapshot(s.data());contract=cleanup_contract(state,previous_serial);trace.append(dict(state=state,contract=contract))
        stable=stable+1 if contract['passed'] else 0
        if stable>=2:return dict(passed=True,state=state,trace=trace)
        time.sleep(.08)
    return dict(passed=False,state=trace[-1]['state'] if trace else {},trace=trace,
                reason='cleanup acknowledgement missing or owned restoration pending; see lastCleanup failures')


def wait_start(s, previous_serial, timeout=4):
    deadline=time.monotonic()+timeout;trace=[];data={}
    while time.monotonic()<deadline:
        data=s.data();state=snapshot(data);trace.append(state);lab=state['lab'] or {}
        fresh=lab.get('startSerial',0)>previous_serial
        if fresh and lab.get('state')=='failed':return dict(passed=False,state=state,trace=trace,reason=str(lab.get('error'))),data
        if fresh and lab.get('active') and lab.get('state')=='ready':
            checks=dict(clear=lab.get('corridorClear') is True,distance=abs(lab.get('targetDistance',0)-16)<.25,
                        target=state['targetId']==lab.get('targetId') and (state['targetHealth'] or 0)>0,
                        noError=not state['testError'] and not lab.get('error'),
                        noTerrainCleared=lab.get('lastStart',{}).get('terrainCleared')==0)
            return dict(passed=all(checks.values()),state=state,trace=trace,assertions=checks,
                        reason='Hanzo ready receipt failed: '+','.join(k for k,v in checks.items() if not v)),data
        time.sleep(.08)
    return dict(passed=False,state=snapshot(data),trace=trace,reason='Hanzo combat start not acknowledged; register hanzo-combat-lab route and hanzoCombatLab diagnostic'),data


def prepare(s, phase):
    data=s.data();require(KEY in data,'Register HanzoCombatLab route/diagnostic/cleanup from handoff-20261027-hanzo.md')
    receipt=dict(phase=phase);s.result.setdefault('labPreparations',[]).append(receipt)
    previous=data[KEY].get('cleanupSerial',0);s.post('cleanup');receipt['cleanup']=wait_cleanup(s,previous)
    require(receipt['cleanup']['passed'],'Hanzo owned cleanup failed: '+json.dumps(receipt['cleanup']['state'],ensure_ascii=False))
    s.aim();previous=s.data()[KEY].get('startSerial',0);s.post('hanzo-combat-lab')
    receipt['start'],data=wait_start(s,previous)
    require(receipt['start']['passed'],'Hanzo safe corridor: '+receipt['start'].get('reason','rejected')+'; '+json.dumps(receipt['start']['state'],ensure_ascii=False))
    return data


class HanzoCombatSuite(Suite):
    def close(self):
        try:
            previous=(self.data().get(KEY) or {}).get('cleanupSerial',0);self.post('cleanup')
            receipt=wait_cleanup(self,previous);self.result['cleanupReceipt']=receipt;self.result['cleaned']=receipt['passed']
            if not receipt['passed']:self.result.update(passed=False,cleanupError=receipt['reason'])
        finally:
            try:self.native.close()
            finally:
                try:self.driver.close()
                finally:self.save()
