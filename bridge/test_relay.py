"""Synthetic protocol tests; fixtures are not captured Overwatch gameplay."""
from pathlib import Path
import json
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/python")]
from bson import BSON
from tools.relay_prometheus import decode_pose, run_relay, run_listener
from websockets.sync.client import connect
from websockets.exceptions import ConnectionClosed, InvalidStatus
from websockets.sync.server import serve


class RelayTests(unittest.TestCase):
    def packet(self, **changes):
        original = {"type": 2, "player_id": "Server", "data": {"220": {"x": 12.5, "y": -3, "z": 42, "w": 1}}}
        return BSON.encode(original | changes)

    def test_position_source_shape(self):
        result = decode_pose(self.packet(), 7, source="synthetic")
        self.assertEqual(result, {"schemaVersion": 1, "source": "synthetic", "sequence": 7,
                                 "position": {"x": 12.5, "y": -3.0, "z": 42.0}})

    def test_other_messages_and_players_are_ignored(self):
        self.assertIsNone(decode_pose(BSON.encode({"type": 1, "player_id": "Server"}), 0))
        self.assertIsNone(decode_pose(self.packet(player_id="Observer"), 0))

    def test_malformed_position_rejected(self):
        for value in (float("nan"), float("inf"), 1e100, True, "12", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                decode_pose(self.packet(data={"220": {"x": value, "y": 0, "z": 0}}), 0)
        for packet in (b"bad bson", self.packet(data={}), self.packet(type=True)):
            with self.subTest(packet=packet), self.assertRaises(ValueError):
                decode_pose(packet, 0)

    def test_text_and_oversized_frames_rejected(self):
        for packet in ("not a binary frame", b"x" * 65537):
            with self.assertRaises(ValueError):
                decode_pose(packet, 0)

    def test_reverse_listener_accepts_fresh_client_and_rejects_bad_data(self):
        poses, result, ready = [], [], threading.Event()
        class Receiver(BaseHTTPRequestHandler):
            def do_POST(self):
                poses.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
                self.send_response(200)
                self.end_headers()
            def log_message(self, *args):
                pass
        sink = HTTPServer(("127.0.0.1", 0), Receiver)
        threading.Thread(target=sink.serve_forever, daemon=True).start()
        address = []
        def listening(port):
            address.append(port)
            ready.set()
        def run():
            result.append(run_listener(ws_port=0, sink_port=sink.server_port, samples=1,
                                       test_peer=True, on_ready=listening))
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        try:
            self.assertTrue(ready.wait(3))
            url = f"ws://127.0.0.1:{address[0]}"
            with self.assertRaises(InvalidStatus):
                connect(url + "/", origin="https://example.org", proxy=None)
            with self.assertRaises(InvalidStatus):
                connect(url + "/wrong", proxy=None)
            with connect(url + "/", origin=url, proxy=None, close_timeout=1) as websocket:
                # A fresh Prometheus client has an empty ID; no game-side ID assignment is needed.
                websocket.send(b"bad bson")
                websocket.send(self.packet(player_id=""))
                # Listener must never send gameplay/JoinInstance/AssignPlayerID messages.
                with self.assertRaises((TimeoutError, ConnectionClosed)):
                    websocket.recv(timeout=.2)
            thread.join(timeout=3)
            self.assertFalse(thread.is_alive())
            self.assertEqual(result, [1])
            self.assertEqual(len(poses), 1)
            self.assertEqual(poses[0]["source"], "synthetic")
            self.assertEqual(poses[0]["position"], {"x": 12.5, "y": -3.0, "z": 42.0})
        finally:
            sink.shutdown()
            sink.server_close()

    def test_local_bson_handshake_to_http(self):
        poses, joins = [], []
        class Receiver(BaseHTTPRequestHandler):
            def do_POST(self):
                poses.append((self.path, json.loads(self.rfile.read(int(self.headers["Content-Length"])))))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"received":true}')
            def log_message(self, *args):
                pass
        sink = HTTPServer(("127.0.0.1", 0), Receiver)
        sink_thread = threading.Thread(target=sink.serve_forever, daemon=True)
        sink_thread.start()
        def upstream(websocket):
            websocket.send(BSON.encode({"type": 5, "player_id": "observer-1"}))
            joins.append(BSON(websocket.recv(timeout=3)).decode())
            websocket.send(self.packet())
        try:
            with serve(upstream, "127.0.0.1", 0) as server:
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                count = run_relay(ws_port=server.socket.getsockname()[1], sink_port=sink.server_port,
                                  samples=1, test_peer=True)
            self.assertEqual(count, 1)
            self.assertEqual(joins, [{"type": 3, "player_id": "observer-1", "name": "Minecraft Observer"}])
            self.assertEqual(poses[0][0], "/v1/pose")
            self.assertEqual(poses[0][1]["source"], "synthetic")
            self.assertEqual(poses[0][1]["position"], {"x": 12.5, "y": -3.0, "z": 42.0})
        finally:
            sink.shutdown()
            sink.server_close()
            sink_thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
