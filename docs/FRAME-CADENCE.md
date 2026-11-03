# Frame cadence and pinned renderer

The play window displays real Minecraft frames under original offline hero pixels.
Measure colorUploads (new source images actually composed), not only native Present
or Minecraft's own FPS counter. The host and source targets are240FPS; actual
values depend on scene and hardware. Report windows are about0.5s and are not
individual frame-time percentiles or a guarantee of a6.67ms maximum frame time.

## 2026-10-16 movement test

45s command sequence: F6 flight, ascend2s, five W/S/A/D loops at1.5s per direction,
with a1200-count yaw turn and return after each loop, then F6 off and land. No
blocks/entities are created. Natural saved world,1920x1080 source and2560x1440
native window. Movement may end a small distance away because collision/timing
and input authority remain real. Source terrain is not reset between runs.

| Run | New composed FPS | Lowest report window | Windows below150 | Held / unmasked |
| --- | ---: | ---: | ---: | ---: |
| bootstrap9 + compositor26 |186.303|143.689|1/85|0/0|
| compositor27 buffer pool |188.890|116.959|1/87|0/0|
| compositor27 + Sodium |194.471|158.915|0/86|0/0|

Both first runs slowed during the first large turn; MC render intervals also
spiked. Pooling alone did not fix that slowdown. Sodium's run passed this bounded
window threshold. Different live starting positions/OS scheduling mean these are
whole-session observations, not a controlled estimate of Sodium's isolated gain.
Private evidence: research/_archive/2026-10/daylight-motion-perf.json, pool27-motion-perf.json,
sodium27-motion-perf.json and corresponding path evidence where recorded.

Compositor27 pools three owned frame vectors. A slot held by latestWorld or the
render thread cannot be reused. Exhaustion skips a source poll; no published
snapshot is overwritten. Original mapping seqlock, generation, age, dimensions,
pose pairing and complete-frame holds remain. sourceReadCpuNs/sourcePolls/
sourcePoolBusy permit inspection; no GPU readback was introduced. CPU/GPU fixtures
cover retained snapshots, bounded exhaustion, reuse, depth/color switches,
concurrent transport, row orientation, mask/warp/state and callback restoration.

## Reproducible renderer dependency

Installed only in guest-passthrough-client/mods, not the user's other profiles.
Official [Sodium](https://modrinth.com/mod/sodium), by CaffeineMC; version
0.8.13+mc1.21.1, Modrinth version SMxNOGZ6, published2026-08-28, Fabric build.
License: Polyform Shield1.0.0. The launcher verifies the exact size/SHA512 and
records its SHA256 in loadedFiles. No network download occurs during play startup.

Install on a migrated machine after stopping the private session:

```powershell
.venv/Scripts/python.exe -X utf8 tools/render_optimization.py --install
```

Without --install the same command only checks. It refuses differing existing
artifacts and renderer conflicts. tools/check_environment.py includes the check.
The exact public download URL/hash are pinned in tools/render_optimization.py;
no jar or proprietary game resources are committed. Existing Fabric0.19.5 and
API0.116.17 meet the embedded dependencies. Real startup log confirms Sodium and
its automatic AMD_GAME_OPTIMIZATION_BROKEN workaround on RX7700XT; no global
AMD driver setting was changed. Frame export, native pose lens and MC full-bright
remain functional in actual native-window screenshots.

## Three-hero attack follow-up on compositor27

Fresh native8212 ran20s per hero with two1.5s primary-fire bursts and reload.
McCree averaged192.559/min164.410FPS; Winston186.843/min147.287 (one of38windows
below150); Genji194.620/min180.934. All had held0/unmasked0. Actual native hero
IDs42/9/29 were checked. All six picker animation frames and three first-person
captures were visually inspected. The Winston dip means the broader150 target
remains pending even though the earlier45s motion sequence passed.

Private evidence: sodium-final-{mccree,winston,genji}-perf.json, picker-a/b and
hands.png, sodium-final-three-heroes.json. Compositor28 then addresses repeated
native buffer descriptor queries using bounded retained identity caching. Its
acceptance result follows; do not treat27's partial pass as a guarantee.

## Compositor28 bounded descriptor cache

Adds64retained identities for non-camera buffers <=1MiB each. This avoids repeated
COM QueryInterface/GetDesc calls without trusting recycled addresses. Retained
references are released with the original callback restoration. Fixture sends
repeated real non-camera Map/Unmap uploads, verifies cache hits, release, exact
foreground/HUD pixels, resize and both first-person/selection restoration.

Fresh native13712 (bootstrap9/body10/weapon8/emission11/Sodium) ran a45s Winston
movement sequence with five additional0.5s fire bursts.192.603FPS,86windows,
minimum168.932FPS, below150=0, held0/unmasked0. Capture file:
research/_archive/2026-10/cache28-winston-motion-fire-perf.json and corresponding path.json.
Buffer observation averaged0.705ms/native frame versus0.723ms in the previous
Winston run. This modest difference is not evidence that caching alone eliminated
the earlier isolated dip. The same-version three-hero check is recorded next.
