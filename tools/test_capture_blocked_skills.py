"""Offline fixtures only: no games, process handles, drivers or native writes."""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch, Mock

from analyze_capture import analyze, markdown
from capture_native_graphs import Edges, GraphSampler, cadence, collect
from capture_skill_plan import BY_ID, CASES, HEROES

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('blocked_capture', ROOT/'research/sprint-20261024/capture_blocked_skills.py')
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)


def snapshot(tick=10, active=True, *, model=42, graph=400, node=1, value=0, hero=4):
    graph_key = 'model:100'
    graph_row = dict(role='model', owner=200, instance=256, script='0580000000000266',
                     graph=graph, bag=500, nodePointers=[1000, 1008, 1016])
    return dict(identity=dict(pid=123, created=1, creationFileTime=100, hero=hero,
                              modelId=model, controller=100, model=200),
                graphs={graph_key: graph_row}, records={graph_key+':'+str(node):
                    dict(graphKey=graph_key, instance=256, script=graph_row['script'],
                         node=node, tick=tick, active=active, finished=not active)},
                variables={'entity:model': [dict(rid='0d80000000000004', children=[
                    dict(rid='0d800000000006c7', raw=f'{value:016x}', type=2, value=value)])]},
                healthPools=dict(ownerVerified=True, pools=[dict(kind=0, slot=0, maximum=100, current=80)]))


def fixture_capture(action_id, node, *, background=False, good=True):
    a = snapshot(node=node)
    rows = [dict(phase='baseline', elapsed=0, **a)]
    if background:
        rows.append(dict(phase='baseline', elapsed=.1, **snapshot(11, node=node)))
    rows.append(dict(phase='action', elapsed=.05, **snapshot(12, node=node, value=1)))
    rows.append(dict(phase='action', elapsed=.1, **snapshot(12, False, node=node, value=1)))
    return dict(kind='native-blocked-skill-capture', schemaVersion=1, fixtureOnly=True,
                case=dict(id=action_id), samples=rows, qualityPassed=good,
                nativeSceneAcknowledged=True,
                definitions={'fixture': dict(**a['graphs']['model:100'], identity=a['identity'], nodes=[
                    dict(index=node, hash='4698e4b6', name='SetVar', serverOnly=0,
                         setVarDefinition={'fixture': True})])})


class FakeClock:
    def __init__(self):
        self.now = 0

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class EdgeFixtureTests(unittest.TestCase):
    def test_initial_active_and_unchanged_never_replay(self):
        e = Edges()
        a = snapshot()
        row = e.add(a, 'baseline', 0)
        self.assertTrue(row['baseline'])
        self.assertEqual(row['events'], [])
        self.assertEqual(e.add(a, 'action', .1)['events'], [])

    def test_new_begin_and_same_tick_end(self):
        e = Edges()
        e.add(snapshot(), 'baseline', 0)
        self.assertEqual(e.add(snapshot(11), 'action', .1)['events'][0]['event'], 'Begin')
        end = e.add(snapshot(11, False), 'action', .2)
        self.assertEqual(end['events'][0]['event'], 'End')
        self.assertEqual(e.add(snapshot(11, False), 'action', .3)['events'], [])

    def test_identity_graph_and_bag_changes_rebaseline(self):
        for change in ('model', 'hero', 'controller', 'graph', 'bag', 'nodePointers'):
            with self.subTest(change=change):
                e = Edges()
                e.add(snapshot(), 'baseline', 0)
                a = snapshot(12)
                if change in ('model', 'hero', 'controller'):
                    a['identity'][change] += 1
                else:
                    a['graphs']['model:100'][change] = [999] if change == 'nodePointers' else 999
                row = e.add(a, 'action', .1)
                self.assertTrue(row['baseline'])
                self.assertFalse(row['events'])
                self.assertFalse(row['variableChanges'])

    def test_read_gap_and_tick_rollback_rebaseline(self):
        e = Edges()
        e.add(snapshot(20), 'baseline', 0)
        self.assertEqual(e.add(snapshot(19), 'action', .1)['baselineReason'], 'tick-rollback')
        e.gap()
        self.assertFalse(e.add(snapshot(21), 'action', .2)['events'])
        self.assertTrue(e.add(snapshot(22), 'action', .3)['events'])

    def test_new_graph_is_baseline_and_missing_node_is_unknown(self):
        e = Edges()
        e.add(snapshot(), 'baseline', 0)
        a = snapshot(12)
        a['records'] = {}
        self.assertFalse(e.add(a, 'action', .1)['events'])
        a = snapshot(13)
        row = e.add(a, 'action', .2)
        self.assertTrue(row['events'][0]['firstObserved'])
        self.assertIsNone(row['events'][0]['previous'])

    def test_nested_raw_variable_change_retains_unknown_writer(self):
        e = Edges()
        e.add(snapshot(), 'baseline', 0)
        row = e.add(snapshot(value=1), 'action', .1)
        self.assertFalse(row['events'])
        change = row['variableChanges'][0]
        self.assertTrue(change['path'].endswith('/0d80000000000004/0d800000000006c7'))
        self.assertEqual(change['before']['value'], 0)
        self.assertEqual(change['after']['raw'], '0000000000000001')
        self.assertFalse(change['writerVerified'])


class CollectionFixtureTests(unittest.TestCase):
    def test_bounded_three_seconds_high_frequency_and_failures(self):
        clock = FakeClock()
        class Reader:
            def __init__(self):
                self.n = 0
            def sample(self):
                self.n += 1
                clock.now += .001
                if self.n == 20:
                    raise ValueError('fixture read gap')
                return snapshot(self.n)
        rows = []
        collect(Reader(), 3, 'action', rows, Edges(), clock=clock.clock, sleep=clock.sleep)
        self.assertLessEqual(clock.now, 3.000001)
        self.assertGreater(len(rows), 290)
        self.assertEqual(cadence(rows, 'action')['readFailures'], 1)
        recovery = next(i for i, r in enumerate(rows) if 'readError' in r)+1
        self.assertTrue(rows[recovery]['baseline'])
        self.assertFalse(rows[recovery]['events'])

    def test_slow_reader_reports_actual_rate_instead_of_claiming_100hz(self):
        clock = FakeClock()
        class Reader:
            def sample(self):
                clock.now += .05
                return snapshot()
        rows = []
        collect(Reader(), 3, 'action', rows, Edges(), clock=clock.clock, sleep=clock.sleep)
        self.assertLess(cadence(rows, 'action')['measuredHz'], 21)
        self.assertLessEqual(len(rows), 61)

    def test_guard_failure_is_not_swallowed_as_a_read_failure(self):
        class Reader:
            def sample(self):
                raise AssertionError('must never read')
        def fail():
            raise ValueError('foreground interference')
        with self.assertRaisesRegex(ValueError, 'interference'):
            collect(Reader(), 3, 'action', [], Edges(), guard=fail)

    def test_key_hold_does_not_block_sampler(self):
        class Driver:
            def __init__(self):
                self.log = []
            def send(self, command):
                self.log.append(command)
        class Session:
            driver = Driver()
            guard = lambda self: None
        session, errors, stop = Session(), [], threading.Event()
        thread = threading.Thread(target=capture.perform_actions,
                                  args=(session, [dict(key='E', at=0, seconds=.08)],
                                        time.perf_counter(), stop, errors))
        thread.start()
        samples = 0
        while thread.is_alive():
            samples += 1
            time.sleep(.005)
        thread.join()
        self.assertGreater(samples, 5)
        self.assertEqual(session.driver.log, ['key 0x45 down', 'key 0x45 up'])
        self.assertFalse(errors)

    def test_failed_down_still_attempts_release(self):
        class Session:
            guard = lambda self: None
        class Driver:
            def __init__(self):
                self.log = []
            def send(self, command):
                self.log.append(command)
                if command.endswith('down'):
                    raise ValueError('fixture timeout after send')
        session = Session()
        session.driver = Driver()
        errors = []
        capture.perform_actions(session, [dict(key='Q', at=0, seconds=.12)],
                                time.perf_counter(), threading.Event(), errors)
        self.assertEqual(session.driver.log[-1], 'key 0x51 up')
        self.assertEqual(errors[0]['stage'], 'input')


class NativeReaderFixtureTests(unittest.TestCase):
    def sampler(self):
        sample = snapshot()
        reader = GraphSampler.__new__(GraphSampler)
        reader.process = Mock()
        reader.process.read.return_value = __import__('struct').pack('<qB', 10, 0)
        reader.r = Mock(logger=900, logger_entry=950)
        reader.r.unpack.return_value = (1,)
        reader.r.varbag.return_value = []
        reader.identity = Mock(return_value=sample['identity'])
        reader.inventory = Mock(return_value=(sample['graphs'], {}))
        reader.health = Mock(return_value=sample['healthPools'])
        reader.catalog, reader.current = {}, {}
        return reader

    @staticmethod
    def maps(process, address, key_format):
        return [(256, 800)] if address == 900 else [(1, 10000)]

    def test_verified_read_only_snapshot_and_existing_logger(self):
        reader = self.sampler()
        with patch('native_map_snapshot.snapshot_map', side_effect=self.maps):
            sample = reader.sample()
        self.assertTrue(sample['records']['model:100:1']['active'])
        self.assertEqual(len(reader.catalog), 1)
        reader.process.write.assert_not_called()
        self.assertEqual(reader.inventory.call_count, 2)

    def test_owner_change_discards_the_whole_snapshot(self):
        reader = self.sampler()
        old = snapshot()['identity']
        reader.identity.side_effect = [old, dict(old, modelId=99)]
        with patch('native_map_snapshot.snapshot_map', side_effect=self.maps), self.assertRaisesRegex(ValueError, 'changed'):
            reader.sample()
        self.assertEqual(reader.catalog, {})

    def test_torn_payload_and_missing_logger_are_not_publishable(self):
        reader = self.sampler()
        reader.process.read.side_effect = [b'\x00'*9, b'\x01'+b'\x00'*8]
        with patch('native_map_snapshot.snapshot_map', side_effect=self.maps), self.assertRaisesRegex(ValueError, 'payload changed'):
            reader.sample()
        reader = self.sampler()
        reader.r.unpack.return_value = (0,)
        with self.assertRaisesRegex(ValueError, 'trampoline'):
            reader.sample()


class AnalysisFixtureTests(unittest.TestCase):
    def test_post_only_before_background_and_specificity_requires_comparison(self):
        a = fixture_capture('lucio-song', 1)
        b = fixture_capture('lucio-boop', 2, background=True)
        report = analyze([a, b])
        first = report['candidates'][0]
        self.assertEqual(first['action'], 'lucio-song')
        self.assertTrue(first['postOnly'])
        self.assertTrue(first['uniqueToTestedAction'])
        self.assertFalse(report['candidates'][1]['postOnly'])
        self.assertIsNone(analyze([a])['candidates'][0]['uniqueToTestedAction'])
        self.assertFalse(first['commitVerified'])
        self.assertIn('未认证', markdown(report))

    def test_same_node_in_other_actions_is_not_unique(self):
        report = analyze([fixture_capture('a', 1), fixture_capture('b', 1)])
        self.assertFalse(report['candidates'][0]['uniqueToTestedAction'])
        self.assertEqual(report['candidates'][0]['otherActionsWithEvents'], ['b'])

    def test_recompute_edges_not_trust_forged_events(self):
        fixture = fixture_capture('a', 1)
        fixture['samples'][0]['events'] = [dict(node=999, event='Begin')]
        fixture['samples'][1]['events'] = []
        report = analyze([fixture])
        self.assertEqual(report['candidates'][0]['node'], 1)
        self.assertEqual(report['candidates'][0]['begins'], 1)
        self.assertEqual(report['candidates'][0]['ends'], 1)

    def test_failed_quality_keeps_diagnostic_but_not_eligible(self):
        report = analyze([fixture_capture('a', 1, good=False)])
        self.assertEqual(len(report['rejectedForReview']), 1)
        self.assertFalse(report['candidates'][0]['eligibleForReview'])

    def test_var_writes_are_only_associations_and_health_is_numeric(self):
        report = analyze([fixture_capture('a', 1)])
        row = report['variableChanges'][0]
        self.assertFalse(row['writerVerified'])
        self.assertTrue(row['sameSampleSetVarEvents'])
        self.assertEqual(report['healthPoolChanges'][0]['minTotal'], 80)


class PlanAndGuardFixtureTests(unittest.TestCase):
    def test_prepare_capture_and_analyze_end_to_end_without_native_services(self):
        hero = 0x02e0000000000004
        current = snapshot(hero=hero)
        definitions = fixture_capture('fixture', 1)['definitions']
        definitions['fixture']['identity'] = current['identity']

        class Session:
            def __init__(self, args, folder):
                self.args, self.input_log = args, []
                self.identity = Mock(proof={'fixtureOnly': True})
                self.reader = Mock()
                self.reader.sample.return_value = copy.deepcopy(current)
                self.reader.identity.return_value = current['identity']
                self.reader.definitions.return_value = definitions
            choose = Mock()
            scene = Mock(return_value={'fixtureOnly': True})
            guard = lambda self: None
            close = lambda self: None

        def offline_collect(reader, seconds, phase, rows, edges, **kwargs):
            for n in range(5):
                row = snapshot(10 if phase == 'baseline' else 11+n, hero=hero)
                rows.append(edges.add(row, phase, n*.01))

        with tempfile.TemporaryDirectory() as tmp, patch.object(capture, 'BASE', Path(tmp)), \
                patch.object(capture, 'LiveSession', Session), \
                patch.object(capture, 'backup_proof', return_value={'fixtureOnly': True}), \
                patch.object(capture, 'factory_snapshot', return_value={'fixtureOnly': True}), \
                patch.object(capture, 'collect', side_effect=offline_collect), \
                patch.object(capture, 'perform_actions'), patch('builtins.print'):
            args = argparse.Namespace(case='mercy-unknown-e', output_dir=Path(tmp)/'output',
                                      profile_backup=Path(tmp)/'backup.json', pid=123, created=1,
                                      mc_pid=124, mc_created=1, world='fixture', guest_sha256='fixture',
                                      keep_selected=False, form_from=None)
            capture.prepare(args)
            prepared = args.output_dir/'Mercy-unknown-e.prepare.json'
            self.assertTrue(prepared.exists())
            result = capture.capture(argparse.Namespace(prepared=prepared, native_scene_ready=True,
                                                         baseline_seconds=3, hz=100))
            self.assertTrue(result)
            evidence = capture.load(args.output_dir/'Mercy-unknown-e.json')
            self.assertTrue(evidence['qualityPassed'])
            self.assertFalse(evidence['nativeMemoryWrites'])
            report = analyze([evidence])
            self.assertTrue(report['candidates'])
            self.assertFalse(report['skillCommitVerified'])
            with self.assertRaisesRegex(ValueError, 'already exists'):
                capture.capture(argparse.Namespace(prepared=prepared, native_scene_ready=True))

    def test_full_handoff_matrix_and_action_bounds(self):
        self.assertEqual({c['hero'] for c in CASES}, set(HEROES))
        self.assertEqual(len(CASES), len(BY_ID))
        for c in CASES:
            self.assertTrue(c['nativeScene'])
            self.assertTrue(c['watchHints'])
            for a in c['actions']:
                self.assertIn(a['key'], set(capture.VK)|{'M1', 'M2'})
                self.assertTrue(0 <= a['at'] < a['at']+a['seconds'] <= 2)
        self.assertEqual(len({c['group'] for c in CASES if c['hero'] == 'Reinhardt'}), 4)
        for id in ('mercy-unknown-e', 'dva-postcall-unknown-e', 'junkrat-death-passive',
                   'torbjorn-hammer-repair', 'symmetra-turret', 'symmetra-teleporter'):
            self.assertIn(id, BY_ID)

    def test_charge_read_only_requires_actual_current_model_meter(self):
        a = snapshot()
        with self.assertRaisesRegex(ValueError, 'Q not charged'):
            capture.charge_ready(a)
        a['variables']['entity:model'] = [dict(rid=rid, value=value, type=3)
                                         for rid, value in [('0d80000000000156', 1800), ('0d80000000000152', 1800)]]
        self.assertFalse(capture.charge_ready(a)['nativeMemoryWritten'])
        a['variables']['entity:model'][0]['value'] = 1799
        with self.assertRaises(ValueError):
            capture.charge_ready(a)

    def test_fresh_session_group_and_existing_evidence_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(capture, 'BASE', Path(tmp)):
            args = argparse.Namespace(pid=123, created=1)
            capture.claim_group(args, 'reinhardt-contact')
            capture.claim_group(args, 'reinhardt-contact')
            with self.assertRaisesRegex(ValueError, 'cold start'):
                capture.claim_group(args, 'reinhardt-fire')
            path = Path(tmp)/'evidence.json'
            capture.write(path, {'fixture': True})
            with self.assertRaises(FileExistsError):
                capture.write(path, {'fixture': False})
            self.assertTrue(capture.load(path)['fixture'])

    def test_readonly_modules_and_fixture_import_do_not_open_process(self):
        for path in ('tools/capture_native_graphs.py', 'research/sprint-20261024/capture_blocked_skills.py'):
            source = (ROOT/path).read_text(encoding='utf-8')
            for forbidden in ('WriteProcessMemory', 'CreateRemoteThread', 'grant_for_test',
                              'native_factory_calibration', 'inject_dll'):
                self.assertNotIn(forbidden, source)
        # Authentication/input modules are deliberately deferred until live CLI.
        self.assertNotIn('verify_bastion_cannon', sys.modules)


if __name__ == '__main__':
    unittest.main()
