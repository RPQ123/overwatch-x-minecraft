"""Forward Prometheus's local BSON movement stream to the Minecraft diagnostic mod."""
from pathlib import Path
import argparse
import http.client
import json
import math
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/python"))
from bson import BSON
from bson.errors import InvalidBSON
from websockets.sync.client import connect
from websockets.sync.server import serve
from websockets.exceptions import WebSocketException


def decode_message(packet):
    if not isinstance(packet, bytes) or len(packet) > 65536:
        raise ValueError("Expected a BSON binary frame no larger than 64 KiB")
    try:
        message = BSON(packet).decode()
    except InvalidBSON as error:
        raise ValueError("Invalid BSON frame") from error
    if type(message.get("type")) is not int:
        raise ValueError("Message type must be an integer")
    return message


def decode_pose(packet, sequence, *, source="prometheus", player="Server"):
    message = decode_message(packet)
    if message["type"] != 2:
        return None
    identifier = message.get("player_id")
    if not isinstance(identifier, str) or len(identifier) > 128:
        raise ValueError("Invalid position player ID")
    if player is not None and identifier != player:
        return None
    try:
        vector = message["data"]["220"]
        position = {}
        for axis in ("x", "y", "z"):
            value = vector[axis]
            if type(value) not in (int, float) or not math.isfinite(value) or abs(value) > 10_000_000:
                raise ValueError("Invalid raw position coordinate")
            position[axis] = float(value)
    except (KeyError, TypeError, OverflowError) as error:
        raise ValueError("Missing or invalid MovementState position") from error
    return {"schemaVersion": 1, "source": source, "sequence": sequence, "position": position}


def submit_pose(connection, pose):
    connection.request("POST", "/v1/pose", json.dumps(pose, allow_nan=False),
                       {"Content-Type": "application/json"})
    response = connection.getresponse()
    response.read()
    if response.status != 200:
        raise ValueError(f"Minecraft rejected the pose (HTTP {response.status})")


def run_listener(*, ws_port=6969, sink_port=32131, samples=0, test_peer=False,
                 on_ready=None, capture_path=None):
    """Receive one native client at a time without sending application messages to it."""
    count, errors = 0, []
    active = threading.Lock()
    stopped = threading.Event()
    capture = None
    def handler(websocket):
        nonlocal count
        if not active.acquire(blocking=False):
            websocket.close(1013, "One local research client at a time")
            return
        connection = http.client.HTTPConnection("127.0.0.1", sink_port, timeout=2)
        last_wait_report = time.monotonic()
        print(f"Local client connected: {websocket.remote_address}", flush=True)
        try:
            while not stopped.is_set() and (samples == 0 or count < samples):
                try:
                    packet = websocket.recv(timeout=1)
                    pose = decode_pose(packet, count, source="synthetic" if test_peer else "prometheus", player=None)
                except TimeoutError:
                    if time.monotonic() - last_wait_report >= 15:
                        print("No movement frame in 15 seconds; waiting for local gameplay.", flush=True)
                        last_wait_report = time.monotonic()
                    continue
                except ValueError as invalid:
                    print(f"Rejected upstream packet: {invalid}", file=sys.stderr, flush=True)
                    continue
                if pose is None:
                    continue
                last_wait_report = time.monotonic()
                submit_pose(connection, pose)
                count += 1
                # Bounded evidence file; each record remains raw diagnostic telemetry.
                if capture is not None and count <= 200:
                    capture.write(json.dumps(pose, allow_nan=False) + "\n")
                    capture.flush()
                if count == 1 or count % 100 == 0:
                    print(json.dumps({"forwarded": count, **pose}), flush=True)
        except WebSocketException as error:
            print(f"Local client disconnected: {error}", flush=True)
        except (OSError, ValueError, http.client.HTTPException) as error:
            errors.append(error)
            server.shutdown()
        finally:
            connection.close()
            active.release()
        if samples and count >= samples:
            server.shutdown()
    def check_request(connection, request):
        if request.path != "/":
            return connection.respond(404, "Unknown bridge route")
        # IXWebSocket supplies its ws:// loopback URL as Origin automatically.
        origins = request.headers.get_all("Origin")
        native_origin = f"ws://127.0.0.1:{connection.local_address[1]}"
        if origins not in ([], [native_origin]):
            return connection.respond(403, "Unsupported bridge origin")
    try:
        # Restrict origins to the native URL or absent; only bind loopback. Prometheus may not run its
        # receive loop, so don't require application replies or periodic pong replies.
        with serve(handler, "127.0.0.1", ws_port, process_request=check_request,
                   ping_interval=None, open_timeout=3, close_timeout=1,
                   max_size=65536, max_queue=2) as server:
            if capture_path is not None:
                capture = Path(capture_path).open("w", encoding="utf-8")
            port = server.socket.getsockname()[1]
            print(f"Bridge ready at ws://127.0.0.1:{port}/. In Overwatch click Connect Server only.", flush=True)
            if on_ready is not None:
                on_ready(port)
            server.serve_forever()
        if errors:
            raise errors[0]
        return count
    finally:
        stopped.set()
        # Let the current receive/HTTP operation finish before closing its evidence file.
        with active:
            if capture is not None:
                capture.close()


def run_relay(*, ws_port=6969, sink_port=32131, samples=0, player="Server", test_peer=False):
    count = 0
    connection = http.client.HTTPConnection("127.0.0.1", sink_port, timeout=2)
    try:
        # No proxy, remote DNS, accounts or official game services are used.
        with connect(f"ws://127.0.0.1:{ws_port}/", proxy=None, open_timeout=3, close_timeout=2,
                     max_size=65536, max_queue=2) as websocket:
            print("Connected to the local Prometheus stream.", flush=True)
            while samples == 0 or count < samples:
                try:
                    packet = websocket.recv(timeout=15)
                    message = decode_message(packet)
                    if message["type"] == 5:
                        identifier = message.get("player_id")
                        if not isinstance(identifier, str) or not 1 <= len(identifier) <= 128:
                            raise ValueError("Invalid assigned observer ID")
                        websocket.send(BSON.encode({"type": 3, "player_id": identifier, "name": "Minecraft Observer"}))
                        continue
                    pose = decode_pose(packet, count, source="synthetic" if test_peer else "prometheus", player=player)
                except ValueError as invalid:
                    print(f"Rejected upstream packet: {invalid}", file=sys.stderr, flush=True)
                    continue
                if pose is None:
                    continue
                submit_pose(connection, pose)
                count += 1
                if count == 1 or count % 100 == 0:
                    print(json.dumps({"forwarded": count, **pose}), flush=True)
    finally:
        connection.close()
    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=0, help="Stop after this many poses; 0 means until Ctrl+C")
    parser.add_argument("--player", default="Server", help="Upstream player ID to observe")
    parser.add_argument("--ws-port", type=int, default=6969)
    parser.add_argument("--test-peer", action="store_true", help="Label fixture-server data as synthetic")
    parser.add_argument("--listen", action="store_true", help="Provide the local service; Prometheus clicks Connect Server only")
    parser.add_argument("--capture", type=Path, help="Write at most 200 diagnostic poses to this evidence file (listen mode)")
    args = parser.parse_args()
    if args.samples < 0 or not 1 <= args.ws_port <= 65535 or (args.capture and not args.listen):
        parser.error("samples must be nonnegative and the port must be valid")
    try:
        if args.listen:
            run_listener(ws_port=args.ws_port, samples=args.samples, test_peer=args.test_peer,
                         capture_path=args.capture)
        else:
            run_relay(ws_port=args.ws_port, samples=args.samples, player=args.player, test_peer=args.test_peer)
    except KeyboardInterrupt:
        print("Relay stopped.")
    except (OSError, TimeoutError, ValueError, WebSocketException, http.client.HTTPException) as error:
        print(f"Relay unavailable: {error}. Minecraft must run; listen mode requires port 6969 free (don't click Start Server).",
              file=sys.stderr)
        raise SystemExit(1)
