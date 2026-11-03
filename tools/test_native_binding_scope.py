"""Lifecycle race regressions: packets/acknowledgements, no game injection."""
import struct,unittest
from native_binding_scope import decode_scope,current_body,GuestScopeExpired
from launch_passthrough_session import binding_problems

class ScopeTests(unittest.TestCase):
    def packet(self):
        b=bytearray(256);b[:8]=b'OWBODY01'
        for at,v in ((8,1),(12,256),(16,42),(20,7)):struct.pack_into('<I',b,at,v)
        for at,v in ((24,11),(32,12),(64,4),(72,1000),(136,99)):struct.pack_into('<Q',b,at,v)
        return b
    def test_fresh_identity(self):
        self.assertEqual(decode_scope(self.packet(),42,1250)['worldId'],99)
    def test_only_expired_valid_identity_has_typed_gap(self):
        with self.assertRaises(GuestScopeExpired) as error:
            decode_scope(self.packet(),42,1251)
        self.assertEqual(error.exception.age,251)
        self.assertEqual(error.exception.scope['worldId'],99)
        for at,value in ((16,43),(24,0),(32,0),(64,3),(72,1400),(136,0)):
            raw=self.packet();struct.pack_into('<'+('I' if at==16 else 'Q'),raw,at,value)
            try:decode_scope(raw,42,1251)
            except GuestScopeExpired:self.fail('Invalid/future scope classified as retryable')
            except ValueError:pass
            else:self.fail('Invalid scope accepted')
    def test_stale_torn_unready_or_wrong_process_refused(self):
        for at,fmt,value in ((8,'I',2),(16,'I',43),(20,'I',0),(24,'Q',0),(32,'Q',0),(64,'Q',3),(64,'Q',0),(72,'Q',1251),(72,'Q',999),(136,'Q',0)):
            b=self.packet();struct.pack_into('<'+fmt,b,at,value)
            with self.subTest(at=at,value=value),self.assertRaises(ValueError):decode_scope(b,42,1250)
    def test_actual_observer_model_replaces_lagging_diagnostic_only_in_same_acknowledged_scope(self):
        s=decode_scope(self.packet(),42,1000)
        b=dict(s,pid=42,hero=41,modelId=50,worldStable=True)
        e=dict(pid=42,hero=66,modelId=51,enabled=True,failures=0,hostGeneration=12)
        self.assertEqual(current_body(b,e,s,42)['modelId'],51)
        for field in ('sourcePid','guestGeneration','hostGeneration','worldId'):
            old=dict(b);old[field]-=1
            with self.subTest(field=field),self.assertRaises(ValueError):current_body(old,e,s,42)
        b['worldStable']=False
        with self.assertRaises(ValueError):current_body(b,e,s,42)

class AcknowledgementTests(unittest.TestCase):
    def test_torb_requires_actual_core_binding_before_readiness(self):
        expected=dict(hero=0x02e0000000000006,modelId=100,worldId=200,hostGeneration=300)
        combat=dict(locomotion=dict(expected,ready=True),nativeCharge=dict(expected,ready=True,skillsReady=False))
        self.assertIn('Current native skills are not acknowledged',binding_problems(combat,{},expected))
        combat['nativeCharge']['skillsReady']=True
        self.assertEqual(binding_problems(combat,{},expected),[])
    def test_widow_requires_its_current_original_q_binding_before_readiness(self):
        expected=dict(hero=0x02e000000000000a,modelId=100,worldId=200,hostGeneration=300)
        combat=dict(locomotion=dict(expected,ready=True),nativeCharge=dict(expected,ready=True,skillsReady=False))
        self.assertIn('Current native skills are not acknowledged',binding_problems(combat,{},expected))
        combat['nativeCharge']['skillsReady']=True
        self.assertEqual(binding_problems(combat,{},expected),[])
    def test_old_model_world_or_meter_cannot_report_gameplay_ready(self):
        expected=dict(hero=0x02e0000000000042,modelId=100,worldId=200,hostGeneration=300)
        combat=dict(locomotion=dict(expected,ready=True),roll=dict(modelId=100,ready=True),nativeCharge=dict(expected,ready=True))
        light=dict(fixedViewLight=True,viewLightOwned=True,viewLightHero=expected['hero'],viewLightModelId=100,viewLightWorldId=200,viewLightEpoch=4,viewLightVerifiedEpoch=4)
        self.assertEqual(binding_problems(combat,light,expected),[])
        for channel,field in (('locomotion','modelId'),('locomotion','worldId'),('roll','modelId'),('nativeCharge','modelId'),('nativeCharge','worldId'),('nativeCharge','hostGeneration')):
            old=combat[channel][field];combat[channel][field]-=1
            with self.subTest(channel=channel,field=field):self.assertTrue(binding_problems(combat,light,expected))
            combat[channel][field]=old
        light['viewLightVerifiedEpoch']=3;self.assertTrue(binding_problems(combat,light,expected))
    def test_genji_requires_current_dash_scope_instead_of_other_hero_skills(self):
        expected=dict(hero=0x02e0000000000029,modelId=100,worldId=200,hostGeneration=300)
        combat=dict(locomotion=dict(expected,ready=True),dashBinding=dict(expected,ready=True))
        self.assertEqual(binding_problems(combat,{},expected),[])
        combat['dashBinding']['worldId']=199;self.assertTrue(binding_problems(combat,{},expected))
    def test_java_signed_world_and_session_ids_match_the_same_unsigned_wire_bits(self):
        expected=dict(hero=0x02e0000000000042,modelId=100,worldId=0xe000000000000123,hostGeneration=0xd000000000000456)
        signed=dict(expected);signed['worldId']-=1<<64;signed['hostGeneration']-=1<<64
        combat=dict(locomotion=dict(signed,ready=True),roll=dict(modelId=100,ready=True),nativeCharge=dict(signed,ready=True))
        self.assertEqual(binding_problems(combat,{},expected),[])
        combat['nativeCharge']['worldId']-=1;self.assertTrue(binding_problems(combat,{},expected))

if __name__=='__main__':unittest.main()
