"""Offline failure-classification regressions for the B15 melee failure."""
import copy
import json
from pathlib import Path
import unittest

from oldgaps_test_policy import WINSTON, melee_progress, timed_native_switch


class MeleeEvidenceCheck(unittest.TestCase):
    def setUp(self):
        self.before = dict(native=dict(hero=WINSTON, modelId=42,
                                      records=[dict(node=13, nativeTick=100, finished=True)]),
                           melee=dict(heroId=WINSTON, accepted=1, hits=0, blocked=1, damageApplied=0),
                           targetHealth=20, sustain=dict(hero=0, nativeTick=0))
        self.after = copy.deepcopy(self.before)

    def new_execution(self):
        self.after['native']['records'][0].update(nativeTick=200, finished=True)

    def test_second_input_without_original_commit(self):
        self.assertEqual(melee_progress(self.before, self.after), 'no-new-native-TrackTargets')

    def test_finished_new_track_is_diagnostic_not_damage_acceptance(self):
        self.new_execution()
        self.assertEqual(melee_progress(self.before, self.after), 'native-TrackTargets-without-client-admission')

    def test_real_admission_without_hit_is_not_open_hit(self):
        self.new_execution()
        self.after['melee']['accepted'] = 2
        self.assertEqual(melee_progress(self.before, self.after), 'accepted-without-target-hit')

    def test_hit_counter_without_real_hp_is_not_damage(self):
        self.new_execution()
        self.after['melee'].update(accepted=2, hits=1, damageApplied=3)
        self.assertEqual(melee_progress(self.before, self.after), 'hit-without-real-HP-damage')

    def test_winston_damage_does_not_require_sustain_owner(self):
        self.new_execution()
        self.after['melee'].update(accepted=2, hits=1, damageApplied=3)
        self.after['targetHealth'] = 17
        self.assertEqual(melee_progress(self.before, self.after), 'actual-MC-damage')

    def test_replaced_model_is_not_a_swing(self):
        self.new_execution()
        self.after['native']['modelId'] = 43
        self.assertEqual(melee_progress(self.before, self.after), 'native-owner-changed')

    def test_b15_really_selected_and_admitted_winston(self):
        root = Path(__file__).resolve().parents[1]
        path = root / 'research/sprint-20261024/integration-live-B15-oldgaps-winston-melee/result.json'
        if not path.exists():
            self.skipTest('private B15 evidence unavailable')
        result = json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(result['bastion']['hero'], WINSTON)
        self.assertTrue(any(row['melee'].get('heroId') == WINSTON and
                            row['melee'].get('accepted') == 1 and row['melee'].get('blocked') == 1
                            for row in result['samples']))
        self.assertTrue(all(row['sustain'].get('hero') == 0 for row in result['samples']))


class TimedSwitchCheck(unittest.TestCase):
    def run_switch(self, blocked=False, delayed=False):
        clock = [0.]
        sent = []
        trace = []

        def send(command):
            sent.append(command)
            clock[0] += .2

        def read():
            mode = 0 if blocked or not sent else 2
            if sent and sent[-1] == 'confirm':
                if delayed:
                    clock[0] = 3.5
                    mode = 1
                else:
                    mode = 1
            return dict(viewMode=mode, hero=42 if mode == 1 else 221, modelId=2 if mode == 1 else 1)

        def pause(seconds):
            clock[0] += seconds

        try:
            row = timed_native_switch(read, send, lambda: None, 'hero', 'confirm', 42, 1, 3, trace,
                                      now=lambda: clock[0], sleep=pause)
            return row, sent, trace
        except ValueError:
            self.last_sent = sent
            raise

    def test_observes_actual_replacement_with_no_post_selection_delay(self):
        row, sent, trace = self.run_switch()
        self.assertEqual(row['modelId'], 2)
        self.assertEqual(sent, ['hold 0x48 150', 'hero', 'confirm'])
        self.assertLess(trace[-1]['observedAt'], 3)

    def test_rejected_H_never_causes_blind_click_or_second_H(self):
        with self.assertRaisesRegex(ValueError, 'deadline'):
            self.run_switch(blocked=True)
        self.assertEqual(self.last_sent, ['hold 0x48 150'])

    def test_late_actual_model_cannot_pass_mid_cryo(self):
        with self.assertRaisesRegex(ValueError, 'deadline'):
            self.run_switch(delayed=True)


if __name__ == '__main__':
    unittest.main()
