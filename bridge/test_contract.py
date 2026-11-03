"""Java/HTTP contract checks; these do not claim a real Overwatch or Minecraft run."""
from pathlib import Path
import http.client
import json
import subprocess
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "minecraft-1.21.1"
JDK = GAME / "runtime/java-runtime-delta/windows-x64/java-runtime-delta/bin"
LIBS = [ROOT / "bridge/build/classes",
        GAME / "libraries/net/fabricmc/fabric-loader/0.19.5/fabric-loader-0.19.5.jar",
        GAME / "libraries/com/google/code/gson/gson/2.10.1/gson-2.10.1.jar"]


def request(method, path, body=None):
    connection = http.client.HTTPConnection("127.0.0.1", 32131, timeout=2)
    try:
        connection.request(method, path, body, {"Content-Type": "application/json"})
        response = connection.getresponse()
        return response.status, json.loads(response.read())
    finally:
        connection.close()


class ContractTests(unittest.TestCase):
    def test_pose_and_rejections(self):
        status, initial = request("GET", "/health")
        self.assertEqual(status, 200)
        self.assertTrue(initial["stale"])
        pose = {"schemaVersion": 1, "source": "synthetic", "sequence": 1,
                "position": {"x": 12.5, "y": -3.0, "z": 42.0}}
        self.assertEqual(request("POST", "/v1/pose", json.dumps(pose))[0], 200)
        latest = request("GET", "/health")[1]
        self.assertEqual(latest["latest"], pose)
        self.assertFalse(latest["stale"])
        for change in ({"sequence": -1}, {"sequence": 1.2}, {"schemaVersion": 2},
                       {"source": "pretend_live"}, {"position": {"x": "12", "y": 0, "z": 0}},
                       {"position": {"x": 1e300, "y": 0, "z": 0}}):
            with self.subTest(change=change):
                self.assertEqual(request("POST", "/v1/pose", json.dumps(pose | change))[0], 400)
        self.assertEqual(request("POST", "/v1/pose", "not JSON")[0], 400)
        self.assertEqual(request("POST", "/v1/pose", " " * 16385)[0], 413)
        self.assertEqual(request("GET", "/v1/pose")[0], 405)
        self.assertEqual(request("GET", "/health/unexpected")[0], 404)
        self.assertEqual(request("GET", "/health")[1]["latest"], pose)
        time.sleep(0.6)
        self.assertTrue(request("GET", "/health")[1]["stale"])


if __name__ == "__main__":
    try:
        request("GET", "/health")
    except OSError:
        pass
    else:
        raise SystemExit("Port 32131 is already occupied; leave the existing game/process untouched.")
    probe = ROOT / "bridge/build/ContractProbe.java"
    probe.write_text('class ContractProbe { public static void main(String[] args) throws Exception { '
                     'new lab.owbridge.BridgeClient().onInitializeClient(); Thread.sleep(300000); } }')
    log = (ROOT / "bridge/build/contract-probe.log").open("w")
    process = subprocess.Popen([str(JDK / "java.exe"), "--class-path", ";".join(map(str, LIBS)), str(probe)],
                               stdout=log, stderr=subprocess.STDOUT)
    try:
        for _ in range(100):
            try:
                request("GET", "/health")
                break
            except OSError:
                if process.poll() is not None:
                    raise RuntimeError("Probe failed; inspect bridge/build/contract-probe.log")
                time.sleep(0.1)
        else:
            raise TimeoutError("Diagnostic listener did not start")
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(ContractTests)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
    finally:
        process.terminate()
        process.wait(timeout=5)
        log.close()
    raise SystemExit(0 if result.wasSuccessful() else 1)
