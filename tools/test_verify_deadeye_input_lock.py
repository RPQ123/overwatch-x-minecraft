"""Pure byte/acceptance fixtures. Never instantiate the live Suite or input driver."""
import copy
import struct
import unittest
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import Mock, patch
from verify_deadeye_input_lock import DEY1, Suite, HostPoseGap, GuestBodyGap, decode_pose, decode_body, check_locked_rows, angular
from native_binding_scope import GuestScopeExpired
from verify_deadeye_input_lock import client_command


class ClientCoordinatesChecks(unittest.TestCase):
    def test_existing_menu_coordinates_without_resizing(self):
        self.assertEqual(client_command('click 312 1224', (1920, 1080)), 'click 234 918')
        self.assertEqual(client_command('click 1280 1358', (1920, 1080)), 'click 960 1018')
        self.assertEqual(client_command('click 1280 720 right', (2560, 1440)), 'click 1280 720 right')

    def test_native_camera_deltas_and_keys_remain_unscaled(self):
        for cmd in ('rel 220 70', 'key 0x57 down', 'sleep 400', 'mup'):
            self.assertEqual(client_command(cmd, (1920, 1080)), cmd)

    def test_unknown_size_and_outside_reference_refuse_input(self):
        for cmd, size in [('click 1 2', (1600, 900)), ('click 1 2', (2376, 1080)),
                          ('click 2560 720', (1920, 1080))]:
            with self.assertRaises(ValueError):
                client_command(cmd, size)


class WireChecks(unittest.TestCase):
    def test_pose_capability_and_native_angles(self):
        raw = bytearray(4096)
        raw[:8] = b'OWPOSE01'
        for off, value in ((8, 1), (12, 4096), (16, 123), (32, 1), (88, 1), (328, 1), (332, DEY1)):
            struct.pack_into('<I', raw, off, value)
        for off, value in ((24, 99), (64, 2), (72, 80), (80, 1000)):
            struct.pack_into('<Q', raw, off, value)
        struct.pack_into('<9f', raw, 128, 1, 0, 0, 0, 1, 0, 0, 0, 1)
        sample = decode_pose(raw, 123, 1100)
        self.assertEqual((sample['capabilities'], sample['yaw'], sample['pitch']), (DEY1, 180, 0))
        for pid, now in ((124, 1100), (123, 1151), (123, 999)):
            with self.assertRaises(ValueError):
                decode_pose(raw, pid, now)

    def test_body_unsigned_identity_and_control_fields(self):
        raw = bytearray(256)
        raw[:8] = b'OWBODY01'
        for off, value in ((8, 1), (12, 256), (16, 123), (20, 456), (176, DEY1), (180, 1), (184, 789)):
            struct.pack_into('<I', raw, off, value)
        for off, value in ((24, 11), (32, 99), (64, 2), (72, 1000), (136, (1 << 64)-2),
                           (192, 400), (200, 65536), (208, 131072), (216, 990), (224, (1 << 64)-2)):
            struct.pack_into('<Q', raw, off, value)
        sample = decode_body(raw, 123, 1100)
        self.assertEqual(sample['worldId'], (1 << 64)-2)
        self.assertEqual((sample['begin'], sample['model'], sample['observed']), (400, 789, 990))
        raw[176:232] = bytes(56)
        self.assertFalse(decode_body(raw, 123, 1100)['firing'])
        struct.pack_into('<I', raw, 176, 7)
        with self.assertRaises(ValueError):
            decode_body(raw, 123, 1100)


def locked_rows():
    row = dict(wall=1100, nativeModel=789, mcPosition=[1, 2, 3],
               body=dict(magic=DEY1, firing=True, model=789, deadeyeWorld=42, worldId=42,
                         begin=400, script=65536, observed=1000),
               nativeStates={'18': dict(active=True, tick=400, instance=65536), '44': dict(tick=410)},
               pose=dict(yaw=180, pitch=0), player=dict(flying=True))
    return [copy.deepcopy(row) for _ in range(8)]


class AcceptanceChecks(unittest.TestCase):
    def test_no_fire_active_requirement_and_normal_pass(self):
        rows = locked_rows()
        rows[0]['nativeStates']['44']['active'] = False
        check_locked_rows(rows, 789)
        self.assertEqual(angular(179, -179), 2)

    def test_reject_motion_view_and_flight_escape(self):
        changes = [('mcPosition', [1.07, 2, 3]), ('pose', dict(yaw=180.3, pitch=0)),
                   ('pose', dict(yaw=180, pitch=.3)), ('player', dict(flying=False))]
        for key, value in changes:
            with self.subTest(key=key, value=value):
                rows = locked_rows()
                rows[5][key] = value
                with self.assertRaises(ValueError):
                    check_locked_rows(rows, 789)

    def test_reject_old_identity_proof_or_short_trace(self):
        for key, value in (('begin', 399), ('worldId', 43), ('model', 788), ('observed', 949), ('observed', 1101)):
            with self.subTest(key=key):
                rows = locked_rows()
                rows[5]['body'][key] = value
                with self.assertRaises(ValueError):
                    check_locked_rows(rows, 789)
        with self.assertRaises(ValueError):
            check_locked_rows(locked_rows()[:5], 789)


class CleanupChecks(unittest.TestCase):
    def suite(self):
        suite = Suite.__new__(Suite)
        suite.args = SimpleNamespace(pid=123, mc_pid=456)
        suite.model = 789
        suite.result = dict(featurePassed=True, HInterruptPassed=True, cleaned=False)
        suite.driver = Mock()
        suite.driver.foreground.return_value = True
        suite.identity = Mock()
        suite.maps = suite.memory = None
        suite.recordings = []
        suite.mutated = True
        suite.save = Mock()
        return suite

    @patch('verify_deadeye_input_lock.time.sleep')
    @patch('verify_deadeye_input_lock.request')
    @patch('verify_deadeye_input_lock.first_person_ready')
    def test_picker_reentry_cleanup_ack_then_H(self, first_person, request, sleep):
        suite = self.suite()
        events = []
        first_person.side_effect = [False, True, False]
        scope = dict(pose=dict(inputActive=True), body=dict(firing=False),
                     nativeModel=789, locomotion=dict(ready=True, modelId=789))
        picker = dict(pose=dict(inputActive=False), body=dict(firing=False))
        def wait(phase, predicate, *unused, **options):
            row = picker if phase == 'final-picker-after-cleanup' else scope
            self.assertTrue(predicate(row))
            self.assertEqual(options.get('retry_pose_gap', False), phase == 'final-picker-after-cleanup')
            events.append(phase)
            return row
        suite.wait = Mock(side_effect=wait)
        suite.choose = Mock(side_effect=lambda name: events.append('choose-'+name) or dict(modelId=789))
        suite.post = Mock(side_effect=lambda name: events.append('post-'+name))
        suite.driver.send.side_effect = lambda command: events.append(command)
        request.side_effect = [dict(wallBlocks=0, beamTargets={'owned': 20}), dict(wallBlocks=0)]
        suite.close()
        self.assertTrue(suite.result['cleaned'])
        self.assertTrue(suite.result['finalPicker'])
        self.assertEqual(request.call_count, 2, 'HTTP202 alone is not a cleanup acknowledgment')
        self.assertLess(events.index('choose-McCree'), events.index('post-cleanup'))
        self.assertLess(events.index('cleanup-first-person-scope'), events.index('post-cleanup'))
        self.assertLess(events.index('post-cleanup'), events.index('hold 0x48 100'))
        suite.driver.close.assert_called_once()

    @patch('verify_deadeye_input_lock.request')
    @patch('verify_deadeye_input_lock.first_person_ready')
    def test_no_refocus_or_reentry_on_foreground_loss(self, first_person, request):
        suite = self.suite()
        suite.driver.foreground.return_value = False
        suite.choose = Mock()
        suite.post = Mock()
        suite.close()
        self.assertFalse(suite.result['cleaned'])
        self.assertIn('Foreground interference', suite.result['cleanupError'])
        suite.choose.assert_not_called()
        suite.driver.send.assert_not_called()
        request.assert_not_called()
        first_person.assert_not_called()

    @patch('verify_deadeye_input_lock.request')
    @patch('verify_deadeye_input_lock.first_person_ready')
    def test_failed_feature_does_not_replace_native_pawn(self, first_person, request):
        suite = self.suite()
        suite.result['featurePassed'] = False
        suite.choose = Mock()
        suite.post = Mock()
        request.return_value = dict(wallBlocks=0)
        suite.close()
        suite.choose.assert_not_called()
        first_person.assert_not_called()
        self.assertNotIn('finalPicker', suite.result)

    @patch('verify_deadeye_input_lock.time.sleep')
    @patch('verify_deadeye_input_lock.subprocess.Popen')
    def test_record_names_native_video_and_verified_MC_audio(self, popen, sleep):
        suite = self.suite()
        suite.folder = Path('private-fixture-output')
        suite.record('native-lock', 18)
        args = popen.call_args.args[0]
        self.assertEqual(args[args.index('--pid')+1], '456')
        self.assertEqual(args[args.index('--exe')+1], 'GameClientApp.patched.exe')
        self.assertEqual(args[args.index('--seconds')+1], '18')
        self.assertEqual(args[args.index('--fps')+1], '60')
        self.assertEqual(suite.recordings, [('native-lock', popen.return_value)])


class PoseTransitionWaitChecks(unittest.TestCase):
    @patch('verify_deadeye_input_lock.time.sleep')
    def test_body_gap_is_observation_only_and_not_combat_permission(self,sleep):
        suite=Suite.__new__(Suite);suite.result={}
        fresh=dict(pose=dict(inputActive=False))
        suite.snapshot=Mock(side_effect=[GuestBodyGap('age=251ms'),fresh])
        self.assertIs(suite.wait('final-picker',lambda r:True,retry_pose_gap=True),fresh)
        self.assertEqual(len(suite.result['bodyWaitGaps']),1)
        suite.snapshot=Mock(side_effect=GuestBodyGap('age=251ms'))
        with self.assertRaises(GuestBodyGap):suite.wait('combat',lambda r:True)
        self.assertEqual(suite.snapshot.call_count,1)

    @patch('verify_deadeye_input_lock.request',return_value={})
    def test_expired_foreign_identity_cannot_be_retried(self,request):
        suite=Suite.__new__(Suite)
        scope=dict(sourcePid=456,guestGeneration=11,hostGeneration=99,worldId=42)
        suite.result=dict(scope=scope);suite.args=SimpleNamespace(mc_pid=456)
        suite.identity=Mock();suite.driver=Mock();suite.driver.foreground.return_value=True
        suite.maps=Mock()
        suite.maps.read.side_effect=GuestScopeExpired(scope,251)
        with self.assertRaises(GuestBodyGap):suite.snapshot('picker')
        for field in scope:
            bad=dict(scope);bad[field]+=1
            suite.maps.read.side_effect=GuestScopeExpired(bad,251)
            with self.assertRaisesRegex(ValueError,'another source/session/world'):
                suite.snapshot('picker')

    @patch('verify_deadeye_input_lock.time.sleep')
    def test_only_opted_in_transition_waits_for_fresh_pose(self, sleep):
        suite = Suite.__new__(Suite)
        suite.result = {}
        fresh = dict(pose=dict(inputActive=False), body=dict(firing=False))
        suite.snapshot = Mock(side_effect=[HostPoseGap('age=170ms'), fresh])
        row = suite.wait('picker', lambda r: not r['pose']['inputActive'],
                         retry_pose_gap=True)
        self.assertIs(row, fresh)
        self.assertEqual(len(suite.result['poseWaitGaps']), 1)
        self.assertEqual(suite.snapshot.call_count, 2)
        suite.snapshot = Mock(side_effect=HostPoseGap('age=170ms'))
        with self.assertRaises(HostPoseGap):
            suite.wait('actual-firing', lambda r: True)
        self.assertEqual(suite.snapshot.call_count, 1)

    @patch('verify_deadeye_input_lock.time.sleep')
    def test_identity_failure_is_not_retried(self, sleep):
        suite = Suite.__new__(Suite)
        suite.result = {}
        suite.snapshot = Mock(side_effect=ValueError('Source/session changed'))
        with self.assertRaisesRegex(ValueError, 'Source/session changed'):
            suite.wait('picker', lambda r: True, retry_pose_gap=True)
        self.assertEqual(suite.snapshot.call_count, 1)
        sleep.assert_not_called()

    @patch('verify_deadeye_input_lock.time.sleep')
    @patch('verify_deadeye_input_lock.time.monotonic', side_effect=[0, .1, 3.01])
    def test_persistent_gap_keeps_original_deadline(self, monotonic, sleep):
        suite = Suite.__new__(Suite)
        suite.result = {}
        suite.snapshot = Mock(side_effect=HostPoseGap('age=170ms'))
        with self.assertRaisesRegex(ValueError, 'Deadline: picker'):
            suite.wait('picker', lambda r: True, 3, retry_pose_gap=True)
        self.assertEqual(suite.snapshot.call_count, 2)


if __name__ == '__main__':
    unittest.main()
