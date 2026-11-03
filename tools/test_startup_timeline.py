"""Telemetry regressions: clocks, inherited requests and partial log records."""
import json
import os
from pathlib import Path
import tempfile
import time
import threading
import unittest
from unittest.mock import patch

from startup_timeline import GuestStartupLog, StartupTimeline, startup_request, REQUEST_ENV


class TimelineTests(unittest.TestCase):
    def test_parallel_milestones_are_complete_and_atomic(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {REQUEST_ENV: ''}):
            stamp=time.perf_counter_ns()
            timeline=StartupTimeline(Path(folder),{},stamp,stamp)
            workers=[threading.Thread(target=lambda i=i: timeline.mark('parallel_'+str(i))) for i in range(12)]
            for worker in workers:worker.start()
            for worker in workers:worker.join(2)
            data=json.loads(timeline.path.read_text(encoding='utf-8'))
            self.assertEqual(len(data['events']),15)
            self.assertEqual(len({event['name'] for event in data['events']}),15)
            stamps=[event['monotonicNs'] for event in data['events']]
            self.assertEqual(stamps,sorted(stamps))

    def test_request_origin_is_inherited_and_environment_restored(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {REQUEST_ENV: 'previous'}):
            root = Path(folder)
            with startup_request(root) as request:
                entered = time.perf_counter_ns()
                timeline = StartupTimeline(root, {}, entered, entered+1)
                self.assertEqual(timeline.origin, request['requestedNs'])
                self.assertEqual(json.loads(os.environ[REQUEST_ENV])['root'], str(root.resolve()))
            self.assertEqual(os.environ[REQUEST_ENV], 'previous')
            self.assertEqual(timeline.document['events'][0]['elapsedMs'], 0)

    def test_wrong_root_or_expired_origin_cannot_contaminate_a_new_run(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            entered = time.perf_counter_ns()
            for request in (dict(root=str(root/'other'), requestedNs=entered-1),
                            dict(root=str(root), requestedNs=entered-601_000_000_000)):
                with patch.dict(os.environ, {REQUEST_ENV: json.dumps(request)}):
                    timeline = StartupTimeline(root, {}, entered, entered)
                    self.assertEqual(timeline.origin, entered)

    def test_partial_lines_and_repeated_resource_logs_keep_first_milestone(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            stamp = time.perf_counter_ns()
            with patch.dict(os.environ, {REQUEST_ENV: ''}):
                timeline = StartupTimeline(root, {}, stamp, stamp)
            path = root/'launch.log'
            path.write_bytes(b'Loading Minecraft 1.21.1 with Fabric')
            reader = GuestStartupLog(path, timeline)
            reader.poll()
            self.assertNotIn('fabric_loading', [e['name'] for e in timeline.document['events']])
            with path.open('ab') as stream:
                stream.write(b' Loader 0.19.5\n[OWMCStartup] client_initialized\n')
            reader.poll()
            first = next(e.copy() for e in timeline.document['events'] if e['name']=='fabric_loading')
            with path.open('ab') as stream:
                stream.write(b'Loading Minecraft 1.21.1 with Fabric Loader 0.19.5\n')
            reader.poll()
            self.assertEqual(first, next(e for e in timeline.document['events'] if e['name']=='fabric_loading'))
            timeline.finish('failed', error='fixture')
            timeline.finish('hero-selection')
            self.assertEqual(json.loads(timeline.path.read_text(encoding='utf-8'))['status'], 'failed')


if __name__ == '__main__':
    unittest.main()
