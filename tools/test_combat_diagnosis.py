import unittest
from diagnose_native_combat import classify


class CombatDiagnosisTests(unittest.TestCase):
    def test_no_native_shot_is_distinct_from_missing_guest_visuals(self):
        native={"native-emissions":{"combatReady":True,"accepted":0},"weapon-gate":{"shotCalls":0}}
        self.assertEqual(classify(native,{}),["no-confirmed-native-shot-in-this-session"])
        native["native-emissions"]["accepted"]=3
        self.assertIn("native-events-exist-but-minecraft-has-not-admitted-them",classify(native,{}))
        findings=classify(native,{"admitted":3})
        self.assertEqual(findings,["old-minecraft-build-has-no-projectile-entity-presentation"])

    def test_hitscan_does_not_require_flying_entities(self):
        native={"native-emissions":{"combatReady":True,"accepted":1}}
        self.assertEqual(classify(native,{"admitted":1,"projectileEntitiesSpawned":0,"tracersShown":1}),[])

    def test_removed_substitutes_do_not_claim_original_effects(self):
        native={"native-emissions":{"combatReady":True,"accepted":3}}
        self.assertEqual(classify(native,{"admitted":3,"projectileEntitiesSpawned":0,
            "presentationMode":"original-assets-pending"}),
            ["custom-effects-removed-original-asset-presentation-pending"])
        self.assertEqual(classify(native,{"admitted":3,"projectileEntitiesSpawned":3,
            "presentationMode":"original-genji-model","originalEffectGraph":False}),
            ["original-genji-model-loaded-full-effect-graph-pending"])

    def test_unready_binding_is_reported_even_with_old_counters(self):
        self.assertIn("native-weapon-not-calibrated-or-binding-not-ready",classify(
            {"native-emissions":{"combatReady":False,"accepted":10}},
            {"admitted":10,"projectileEntitiesSpawned":1}))


if __name__=="__main__":
    unittest.main()
