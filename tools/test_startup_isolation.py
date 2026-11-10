"""Synthetic audio, process and HWND fixtures for startup isolation and recovery."""
from dataclasses import asdict
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

from modpack.config import OW_SHA256, PackPaths, read_json
from startup_cover import LoadingCancelled
from startup_isolation import JOURNAL, Lease, StartupIsolation, Target, recover_startup_isolation


class Volume:
    def __init__(self, muted=False):
        self.value = muted
        self.writes = []
        self.before_write = lambda: None

    def muted(self):
        return self.value

    def mute(self, value):
        self.before_write()
        self.value = value
        self.writes.append(value)

    def close(self):
        pass


def session(pid, volume, instance_id='session-1', device='device', identifier='stable', single=True):
    return Mock(device=device, process_id=Mock(return_value=(pid, single)),
                identifier=Mock(side_effect=lambda instance=False: instance_id if instance else identifier),
                volume=Mock(return_value=volume))


class Windows:
    def __init__(self):
        self.state = {101: True, 102: False, 201: True}
        self.tags = {}
        self.owners = {101: 10, 102: 10, 201: 20}

    def handles(self, target):
        return [handle for handle, pid in self.owners.items() if target.pid == pid]

    def belongs(self, handle, target):
        return self.owners.get(handle) == target.pid

    def enabled(self, handle):
        return self.state[handle]

    def marker(self, handle):
        return self.tags.get(handle)

    def mark(self, handle, token):
        self.tags[handle] = token

    def unmark(self, handle):
        self.tags.pop(handle)

    def enable(self, handle, enabled):
        self.state[handle] = enabled


class IsolationFixtures(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.paths = PackPaths(self.root, configuration=dict(schemaVersion=1,
            paths={'owExecutable':'game/client.exe','java':'java/java.exe','profile':'guest'}))
        self.ow = Target('ow', 10, 1., str(self.paths.get('owExecutable')))
        self.mc = Target('mc', 20, 2., str(self.paths.get('java').with_name('javaw.exe')))
        self.targets = {10: self.ow, 20: self.mc}
        self.windows = Windows()
        self.journal = self.root/JOURNAL
        self.lease = Lease(self.paths, self.windows)
        identity = patch.object(Target, 'matches', autospec=True,
                                side_effect=lambda target, _: self.targets.get(target.pid) == target)
        identity.start()
        self.addCleanup(identity.stop)

    def test_default_disabled_preserves_explicit_choice(self):
        for raw, expected in (({},False), ({'autoStart':False},False), ({'autoStart':True},True)):
            config = PackPaths(self.root, configuration={'schemaVersion':1, **raw})
            self.assertIs(config.auto_start(), expected)
        with self.assertRaises(ValueError):
            PackPaths(self.root, configuration={'schemaVersion':1,'autoStart':'false'}).auto_start()

    def test_only_two_owned_audio_sessions_change_and_baseline_is_durable_first(self):
        ow, mc, outside, prior_mute = Volume(), Volume(), Volume(), Volume(True)
        def durable():
            self.assertIs(read_json(self.journal)['audio'][0]['muteBefore'], False)
        ow.before_write = durable
        noise = session(89, outside)
        for item in (noise, session(10, ow), session(20, mc, 'session-2'),
                     session(10, prior_mute, 'already-muted')):
            self.lease.visit_audio(item, self.targets, lock=True)
        self.assertEqual((ow.writes, mc.writes, outside.writes, prior_mute.writes), ([True],[True],[],[]))
        noise.volume.assert_not_called()
        self.lease.restore_audio(Mock(sessions=Mock(return_value=())))
        self.assertEqual((ow.writes,mc.writes,prior_mute.value), ([True,False],[True,False],True))
        self.assertFalse(self.journal.exists())

    def test_reused_pid_or_shared_session_does_not_authorize_mute(self):
        volume = Volume()
        item = session(10, volume, single=False)
        with self.assertRaisesRegex(RuntimeError, '多个进程'):
            self.lease.visit_audio(item, self.targets, lock=True)
        self.targets.pop(10)
        self.lease.visit_audio(item, {10:self.ow}, lock=True)
        self.assertEqual(volume.writes, [])
        self.assertFalse(self.journal.exists())

    def p3_window_lease(self):
        for hwnd, target in ((101,self.ow),(201,self.mc)):
            self.lease.input.append(dict(hwnd=hwnd,token=hwnd,target=asdict(target)))
            self.windows.tags[hwnd]=hwnd
            self.windows.state[hwnd]=False
        self.lease.save()

    def test_crash_recovery_restores_exact_instance_and_window_marker(self):
        volume = Volume()
        original = session(10, volume)
        self.lease.visit_audio(original, self.targets, lock=True)
        self.p3_window_lease()
        self.assertFalse(self.windows.enabled(101))
        self.assertFalse(self.windows.enabled(201))
        other = Volume(True)
        replacement = session(10, other, 'reused-pid')
        audio = Mock()
        audio.__enter__ = Mock(return_value=audio)
        audio.__exit__ = Mock()
        audio.sessions.return_value = (replacement, original)
        with patch('startup_isolation.CoreAudio', return_value=audio), \
             patch('startup_isolation.InputWindows', return_value=self.windows):
            recover_startup_isolation(self.paths)
        self.assertEqual((volume.writes,other.writes), ([True,False],[]))
        self.assertEqual(self.windows.state, {101:True,102:False,201:True})
        self.assertFalse(self.windows.tags)
        self.assertFalse(self.journal.exists())

    def test_recovery_leaves_a_reused_window_untouched(self):
        self.p3_window_lease()
        self.windows.tags.pop(101)  # The handle now represents a newly created disabled window.
        Lease(self.paths, self.windows).restore_windows()
        self.assertFalse(self.windows.enabled(101))
        self.assertTrue(self.windows.enabled(201))
        self.assertFalse(self.journal.exists())

    def test_persisted_mute_follows_only_same_profile_endpoint_and_session_id(self):
        self.lease.visit_audio(session(10, Volume()), self.targets, lock=True)
        self.targets.pop(10)
        orphan = Lease(self.paths, self.windows)
        orphan.restore_audio(Mock(sessions=Mock(return_value=())))
        self.assertTrue(self.journal.exists())
        new = Target('ow', 11, 8., self.ow.executable)
        self.targets[11] = new
        inherited, other = Volume(True), Volume(True)
        orphan.visit_audio(session(11, other, 'other-device', device='headset'), self.targets, lock=True)
        orphan.visit_audio(session(11, inherited, 'new-instance'), self.targets, lock=True)
        orphan.restore_audio(Mock(sessions=Mock(return_value=())))
        self.assertEqual((inherited.writes,other.writes), ([False], []))
        self.assertFalse(self.journal.exists())

    def test_every_guard_context_exit_restores_audio_and_leaves_windows_enabled(self):
        for reason in (None, RuntimeError('failed'), TimeoutError('expired'), LoadingCancelled('cancelled')):
            with self.subTest(reason=reason):
                volume = Volume()
                item = session(10, volume)
                audio = Mock()
                audio.__enter__ = Mock(return_value=audio)
                audio.__exit__ = Mock()
                audio.sessions.return_value = (item,)
                gate = StartupIsolation(self.paths)
                gate.targets = dict(self.targets)
                closed = Mock()
                gate.events.append(closed)
                with patch('startup_isolation.CoreAudio', return_value=audio), \
                     patch('startup_isolation.InputWindows', return_value=self.windows):
                    try:
                        with gate:
                            deadline = time.monotonic() + 1
                            while not volume.value:
                                if time.monotonic() >= deadline:
                                    self.fail('fake guard did not apply its lease')
                                time.sleep(.01)
                            self.assertTrue(self.windows.enabled(101))
                            self.assertTrue(self.windows.enabled(201))
                            if reason:
                                raise reason
                    except (RuntimeError, TimeoutError) as error:
                        self.assertIs(error, reason)
                self.assertEqual(volume.writes, [True,False])
                self.assertTrue(self.windows.enabled(101))
                self.assertTrue(self.windows.enabled(201))
                self.assertFalse(self.journal.exists())
                closed.assert_called_once()

    def test_guard_recovers_when_launcher_dies_even_while_supervisor_is_busy(self):
        volume = Volume()
        audio = Mock()
        audio.__enter__ = Mock(return_value=audio)
        audio.__exit__ = Mock()
        audio.sessions.return_value = (session(10, volume),)
        ticket = Mock(state=Mock(return_value='pending'))
        gate = StartupIsolation(self.paths, ticket)
        gate.targets = dict(self.targets)
        closed = Mock()
        gate.events.append(closed)
        with patch('startup_isolation.CoreAudio', return_value=audio), \
             patch('startup_isolation.InputWindows', return_value=self.windows), gate:
            deadline = time.monotonic() + 1
            while not volume.value:
                if time.monotonic() >= deadline:
                    self.fail('fake guard did not mute the owned session')
                time.sleep(.01)
            ticket.state.return_value = 'cancelled'
            gate.wake.set()
            gate.thread.join(1)
            self.assertFalse(gate.thread.is_alive())
            self.assertEqual(volume.writes, [True, False])
            self.assertFalse(self.journal.exists())
            closed.assert_not_called()
        closed.assert_called_once()

    def test_audio_failure_does_not_close_the_native_gate_early(self):
        gate = StartupIsolation(self.paths)
        closed = Mock()
        gate.events.append(closed)
        with patch('startup_isolation.CoreAudio',side_effect=OSError('endpoint unavailable')), gate:
            gate.thread.join(1)
            self.assertFalse(gate.thread.is_alive())
            closed.assert_not_called()
        closed.assert_called_once()

    def test_native_identity_and_event_are_registered_without_suspending_game(self):
        gate = StartupIsolation(self.paths)
        native = Mock(create_time=Mock(return_value=1.))
        child = Mock(pid=10)
        event = Mock()
        with patch('startup_isolation.sha256', return_value=OW_SHA256), \
             patch('startup_isolation.subprocess.Popen', return_value=child) as spawn, \
             patch('startup_isolation.psutil.Process', return_value=native), \
             patch('startup_isolation.native_input_event', event):
            self.assertIs(gate.spawn([self.ow.executable], role='ow'), child)
        self.assertEqual(gate.targets[10], self.ow)
        event.assert_called_once_with(10)
        self.assertNotIn('creationflags',spawn.call_args.kwargs)
        native.resume.assert_not_called()
        child.kill.assert_not_called()


if __name__ == '__main__':
    unittest.main()
