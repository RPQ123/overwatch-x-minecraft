"""Inspect the MC diagnostic listener, or send an explicitly synthetic pose."""
import argparse
import http.client
import json
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--sample", action="store_true", help="Send raw test coordinates; this is not live Overwatch data")
args = parser.parse_args()
connection = http.client.HTTPConnection("127.0.0.1", 32131, timeout=2)
try:
    if args.sample:
        sample = {"schemaVersion": 1, "source": "synthetic", "sequence": 1,
                  "position": {"x": 12.5, "y": -3.0, "z": 42.0}}
        connection.request("POST", "/v1/pose", json.dumps(sample), {"Content-Type": "application/json"})
        accepted = connection.getresponse()
        accepted.read()
        if accepted.status != 200:
            raise ValueError(f"Sample rejected (HTTP {accepted.status})")
    connection.request("GET", "/health")
    response = connection.getresponse()
    print(json.dumps(json.loads(response.read()), indent=2))
    if response.status != 200:
        raise SystemExit(1)
except (OSError, ValueError) as error:
    print(f"Bridge unavailable: {error}. Restart Minecraft to load the installed owbridge mod.", file=sys.stderr)
    raise SystemExit(1)
finally:
    connection.close()
