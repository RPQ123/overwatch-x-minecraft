"""纯离线等待/朝向策略回归，不连接游戏，不发送真实按键。"""
import copy
from types import SimpleNamespace
import unittest
from voice_aim import aim_readiness,settle_aim

JUNK=0x02e0000000000065
PHARAH=0x02e0000000000008


def state(hero=JUNK,model=123,name='Junkrat'):
    return dict(yaw=180,pitch=0,locomotion=dict(ready=True,hero=hero,modelId=model,worldId=41),
                heroVoice=dict(hero=name.lower()),
                junkrat=dict(signals=dict(ready=True,hero=hero,model=model,world=41,source=99,trap=dict(ready=True,tick=1))))


def native(hero=JUNK,model=123):
    return dict(hero=hero,modelId=model,hostGeneration=99,combatReady=False,armoryVariants=4,enabled=True,restored=False)


class Clock:
    def __init__(self):self.now=0.
    def monotonic(self):return self.now
    def sleep(self,seconds):self.now+=seconds


class Suite:
    def __init__(self,clock,read):
        self.clock=clock;self.read=read;self.voice_selected='Junkrat';self.saved=0;self.commands=[]
        self.result=dict(bastion=dict(hero=JUNK,modelId=123));self.driver=SimpleNamespace(send=self.send)
    def data(self):return self.read()
    def send(self,command):self.commands.append((self.clock.now,command))
    def save(self):self.saved+=1


class VoiceAimTests(unittest.TestCase):
    def test_independent_trap_does_not_require_primary_combat_ready(self):
        ready,sample=aim_readiness(state(),native(),JUNK,123,'Junkrat')
        self.assertTrue(ready);self.assertEqual(sample['path'],'junkrat-trap')
        self.assertFalse(sample['native']['combatReady'])
    def test_wrong_hero_model_world_and_trap_must_fail(self):
        for key,value in [('hero',PHARAH),('model',999),('world',42),('source',0)]:
            c=state();c['junkrat']['signals'][key]=value
            self.assertFalse(aim_readiness(c,native(),JUNK,123,'Junkrat')[0],key)
        c=state();c['junkrat']['signals']['trap']['ready']=False
        self.assertFalse(aim_readiness(c,native(),JUNK,123,'Junkrat')[0])
    def test_primary_pharah_still_requires_emission_readiness(self):
        c=state(PHARAH,name='Pharah');n=native(PHARAH)
        self.assertFalse(aim_readiness(c,n,PHARAH,123,'Pharah')[0])
        n['combatReady']=True
        self.assertTrue(aim_readiness(c,n,PHARAH,123,'Pharah')[0])
        n['restored']=True
        self.assertFalse(aim_readiness(c,n,PHARAH,123,'Pharah')[0])
    def test_settle_after_nine_seconds_is_accepted_and_recorded(self):
        clock=Clock()
        def read():
            c=state();c['locomotion']['ready']=clock.now>=9;return c
        s=Suite(clock,read);settle_aim(s,native,clock=clock)
        row=s.result['aimDiagnostics'][-1]
        self.assertTrue(row['passed']);self.assertGreaterEqual(row['elapsed'],9.5);self.assertLess(row['elapsed'],25)
        self.assertEqual(s.commands,[])
    def test_timeout_identifies_hero_and_failed_predicate(self):
        clock=Clock();c=state();c['junkrat']['signals']['trap']['ready']=False;s=Suite(clock,lambda:c)
        with self.assertRaisesRegex(ValueError,'Junkrat'):
            settle_aim(s,native,timeout=1,clock=clock)
        self.assertIn('trapReady',s.result['aimTimeout']['failed']);self.assertEqual(s.commands,[])
        self.assertIn('error',s.result['aimDiagnostics'][-1])
    def test_orientation_is_corrected_only_after_stability(self):
        clock=Clock();c=state();c['yaw']=170;c['pitch']=5;s=Suite(clock,lambda:copy.deepcopy(c))
        def send(command):
            s.commands.append((clock.now,command));c.update(yaw=180,pitch=0)
        s.driver.send=send;settle_aim(s,native,clock=clock)
        self.assertEqual(s.commands[0][1],'rel 100 -50');self.assertGreaterEqual(s.commands[0][0],.35)
        self.assertTrue(s.result['aimDiagnostics'][-1]['passed'])
    def test_world_change_restarts_stability(self):
        clock=Clock()
        def read():
            c=state()
            if clock.now>=.3:c['locomotion']['worldId']=c['junkrat']['signals']['world']=42
            return c
        s=Suite(clock,read);settle_aim(s,native,clock=clock)
        self.assertGreaterEqual(s.result['aimDiagnostics'][-1]['elapsed'],.8)


if __name__=='__main__':unittest.main()
