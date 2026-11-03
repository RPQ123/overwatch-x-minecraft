"""Read-only capture of user-operated native collision checks; does not drive input."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse
from collections import deque
import json
from pathlib import Path
import time
from observe_overwatch import ROOT, ResearchProcess, PoseReader, PATCHED_SHA256

def capture(pid, seconds, destination):
    process=ResearchProcess(pid)
    reader=PoseReader(process)
    reports=deque(maxlen=1800)
    start=time.monotonic()
    try:
        while time.monotonic()-start<seconds:
            try:
                report=json.loads((ROOT/f"native-host/build/host-{pid}.json").read_text())
                pose=reader.sample()
                reports.append({"elapsed":round(time.monotonic()-start,3),"host":report,"pose":pose})
            except (OSError,ValueError):
                pass # Atomic guest updates and periodic status writes can cross a read.
            time.sleep(.1)
    finally:
        process.close()
        evidence={"pid":pid,"sha256":PATCHED_SHA256,"agentInput":False,"transport":"read-only-process-memory",
                  "synthetic":False,"userVisualConfirmation":None,"samples":list(reports)}
        destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_text(json.dumps(evidence,indent=2),encoding="utf-8")
    if not reports:raise RuntimeError("No genuine host reports/poses captured")
    first,last=reports[0]["host"],reports[-1]["host"]
    summary={key:last.get(key,0)-first.get(key,0) for key in ("collisionTicks","collisionCorrections","collisionFloors","collisionWalls","collisionRejected","collisionWriteFailures")}
    summary["positionSpan"]={axis:round(max(r["pose"]["position"][axis] for r in reports)-min(r["pose"]["position"][axis] for r in reports),6) for axis in "xyz"}
    summary["responsiveCaptureSamples"]=len(reports)
    summary["visualAcceptanceEstablished"]=False
    print(json.dumps(summary))

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid",type=int,required=True)
    parser.add_argument("--seconds",type=int,default=90)
    parser.add_argument("--capture",type=Path,default=ROOT/"research/native-collision-v6.json")
    args=parser.parse_args()
    if args.pid<=0 or not 1<=args.seconds<=180:parser.error("Exact PID and 1..180 seconds required")
    capture(args.pid,args.seconds,args.capture)
