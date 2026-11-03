"""Prepare a separate Prometheus research copy using the author's loader patch data."""
from pathlib import Path
import hashlib
import json
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "overwatch-2015/Overwatch Beta 0.8.0.24919"
LAB = ROOT / "overwatch-2015/offline-lab"
TOOL = ROOT / "overwatch-2015/prometheus-release"
SOURCE = ROOT / "research/prometheus/patcher-Program.cs"

if __name__ == "__main__":
    exe = ORIGINAL / "GameClientApp.exe"
    before = hashlib.sha256(exe.read_bytes()).hexdigest()
    if LAB.exists():
        raise SystemExit("Offline lab already exists; inspect it before preparing another copy.")
    source = SOURCE.read_text(encoding="utf-8-sig")
    matches = re.findall(r"diffs\.Add\(\((0x[0-9a-fA-F]+), new byte\[\] \{([^}]+)\}\)\);", source)
    if len(matches) != 10:
        raise SystemExit("Unexpected upstream loader patch format; no files changed.")
    patches = [(int(offset, 16), bytes(int(value.strip(), 16) for value in values.split(",") if value.strip()))
               for offset, values in matches]
    data = bytearray(exe.read_bytes())
    if not data.startswith(b"MZ") or any(offset + len(values) > len(data) for offset, values in patches):
        raise SystemExit("Original executable does not fit this loader patch; no files changed.")
    if shutil.disk_usage(ROOT).free < sum(path.stat().st_size for path in ORIGINAL.rglob("*") if path.is_file()) + 100_000_000:
        raise SystemExit("Not enough space for an independent research copy.")
    print("Copying original beta into an independent lab...", flush=True)
    shutil.copytree(ORIGINAL, LAB)
    for file in TOOL.iterdir():
        if file.is_file() and file.suffix.lower() == ".dll":
            shutil.copy2(file, LAB / file.name)
    shutil.copy2(TOOL / "prometheus.dll", LAB / "inject.dll")
    for offset, values in patches:
        data[offset:offset + len(values)] = values
    patched = LAB / "GameClientApp.patched.exe"
    patched.write_bytes(data)
    if hashlib.sha256(exe.read_bytes()).hexdigest() != before:
        raise RuntimeError("Original file unexpectedly changed during preparation")
    report = {"original_sha256": before, "patched_sha256": hashlib.sha256(data).hexdigest(),
              "loader_patch_spans": len(patches), "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              "source_url": "https://github.com/saturn-xvi/prometheus/blob/main/patcher/Program.cs",
              "lab": str(LAB), "original_unchanged": True, "lab_launched": False}
    (ROOT / "research/overwatch-lab-preparation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)
