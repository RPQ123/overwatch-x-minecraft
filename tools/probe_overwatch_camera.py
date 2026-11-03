"""Read native host camera state from the exact offline research executable."""
import argparse
import json
import math
from pathlib import Path
import struct
import time
from observe_overwatch import PoseReader, ResearchProcess

class HostCameraReader(PoseReader):
    def sample(self):
        admin = self.pointer(self.memory.base + 0x17b7f90)
        iterators = self.pointer(admin + 0xB0)
        pointers, count, capacity = self.unpack("<Qii", iterators + 0x4F * 0x18)
        if not 1 <= count <= capacity <= 256:
            raise ValueError("Native camera component list is unavailable or invalid")
        component = self.pointer(pointers)
        if self.unpack("<B", component + 0x10)[0] != 0x4F:
            raise ValueError("Unexpected native camera component")
        camera = self.pointer(component + 0x40)
        view = self.pointer(camera + 0x260)
        values = struct.unpack("<12f", self.memory.read(view + 0x10, 48))
        if any(not math.isfinite(value) or abs(value) > 10_000_000 for value in values):
            raise ValueError("Native view contains invalid values")
        if self.pointer(self.memory.base + 0x17b7f90) != admin or self.pointer(camera + 0x260) != view:
            raise ValueError("Native world/view changed during observation")
        return {"host": "Overwatch-0.8.0.24919", "transport": "read-only-process-memory",
                "cameraPositionRaw": dict(zip(("x", "y", "z", "w"), values[:4])),
                "cameraRotationRaw": list(values[4:8]), "cameraRollRaw": list(values[8:12]),
                "rotationConventionVerified": False, "projectionVerified": False}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--samples", type=int, default=1)
    parser.add_argument("--interval", type=float, default=.1)
    args = parser.parse_args()
    if not 1 <= args.samples <= 2000 or not .01 <= args.interval <= 1:
        parser.error("Camera capture requires 1..2000 samples and .01..1 second interval")
    process = None
    try:
        process = ResearchProcess(args.pid)
        reader = HostCameraReader(process)
        captures = []
        start = time.monotonic()
        for index in range(args.samples):
            captures.append({"elapsedSeconds": time.monotonic()-start, **reader.sample()})
            if index+1 < args.samples:
                time.sleep(args.interval)
        result = {"pid": args.pid, "executable": str(process.path), **captures[-1]}
        if args.samples > 1:
            result["samples"] = captures
            result["sampleCount"] = len(captures)
            result["positionSpanRaw"] = {axis: max(s["cameraPositionRaw"][axis] for s in captures)
                -min(s["cameraPositionRaw"][axis] for s in captures) for axis in ("x", "y", "z")}
            result["forwardSpanRaw"] = [max(s["cameraRotationRaw"][i] for s in captures)
                -min(s["cameraRotationRaw"][i] for s in captures) for i in range(3)]
        serialized = json.dumps(result, indent=2, allow_nan=False)
        if args.output:
            args.output.write_text(serialized, encoding="utf-8")
        print(json.dumps({k:v for k,v in result.items() if k != "samples"}, indent=2, allow_nan=False))
    except (OSError, ValueError) as error:
        parser.exit(1, f"Camera unavailable: {error}\n")
    finally:
        if process is not None:
            process.close()
