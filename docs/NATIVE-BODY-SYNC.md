# MC authority and original hero presentation

The user requested a normal Minecraft world in creative mode, invulnerability and original OW hands/HUD without a constantly falling native character. This remains two real processes. Native weapons/ammo/ultimate are separate required unfinished work.

## Ownership and current build

- Minecraft owns terrain, final feet position, velocity, gravity, block contacts and creative abilities. The existing natural save is preserved; `tools/launch_passthrough_guest.py` defaults to creative, with flight off at entry. `--survival` explicitly enables normal damage again; `--superflat` reopens the previous flat test world.
- Original OW receives the real MC motor result through OWBODY01 inside the shared frame header. The native adapter runs after the original local-player tick, follows MC displacement in an empty virtual native coordinates region, and supplies matching grounded/airborne presentation fields. It does not move Minecraft or simulate its terrain.
- Original eye/model fields are updated together through the measured scene setter. The adapter preserves original tick IDs, pointers, rotations and vector W, preflights each field and attempts rollback on any failed write. Hero/model/host/world changes stop coupling; v4 explicitly permits a fresh same-world guest restart.
- The original native renderer still owns hands, materials, animations and HUD. Current compositor v8 preserves its native lens even when the MC image must be held. Extra MC camera bob is disabled because the original native camera already supplies presentation motion. Native block/sky relighting, complete abilities and native map audio removal remain unfinished.

Wire offsets, units and freshness rules are in [CONTRACT.md](CONTRACT.md). Builds:

```powershell
./tools/build_guest.ps1
./tools/build_guest_body.ps1
./tools/build_live_passthrough.ps1
python tools/launch_passthrough_guest.py
python tools/attach_hand_depth_probe.py --pid ORIGINAL_PID --live-passthrough
python tools/attach_hand_depth_probe.py --pid ORIGINAL_PID --body-sync
```

Use the already-running exact supplied offline client, normal resource/map/Demo/Genji selection and only one of each current adapter per process. Do not hot-unload maps or reuse retired draw replay. `stop_passthrough.py --pid ORIGINAL_PID --body` restores the movement callback; without `--body` it restores the compositor/WndProc. Versioned restoration records keep stopped older modules distinguishable from the current active module. Current compositor v9 and body v5 have eight-hour test ceilings and explicit independent stop events; this remains a lab lifecycle.

## Bugs measured and corrected

The earlier background MC player had been killed by a zombie. Its hidden death screen still rendered the world, while the limited status reported feet/onGround but not health. MC now reports alive/health/invulnerable/screen, and creative entry recovers that dead player through vanilla respawn and creative-mode selection.

Separately, the native character was falling below the old map at approximately -30 m/s while MC stood on grass. The first bounded body adapter stopped that idle fall; 50 read-only samples had constant native height and zero vertical speed. Its callback restored normally. A temporary HTTP diagnostic producer was replaced by direct MC tick publication; no third process is needed. The next direct adapter completed 32,778 native writes, zero rejected body samples and zero failures, with 52 airborne ticks, then restored normally before loading the current version.

On the user's walking/blocks-changing report, a real 40-second trace contained 651 MC image frames. A forward tap moved the MC camera approximately 0.426 blocks with unchanged direction; the world origin did not reset. There were two presentation defects: identity warp on stale/history-missing images exposed the guest's 79.13-degree overscan instead of retaining the native 70-degree crop, and MC's independent walking bob was not represented in the native paired pose. The current implementation retains the lens crop during image hold, disables MC bob and raises capture cadence from the measured approximately 16 image FPS to actual approximately 40 image FPS.

## Current actual evidence

The initial proof used original PID 40552, background MC PID 42756, compositor v8 and body adapter v3. The actual MC reported creative-natural, health 20, alive=true, invulnerable=true, flying=false and cameraBobbing=false. A 35-second camera check matched 1,207 distinct real MC images with zero unmatched polls and maximum basis error 1.03e-7; this run does not claim large-angle turning acceptance.

The real export was deliberately paused and resumed while the original client stayed running. The held-image branch was reached (1,389 source rejects in the paused native report). The fixed stone-wall ROI [80,80,950,600] in original-window screenshots was pixel-identical before pause, during pause and after resume: zero changed pixels and mean channel error zero. This establishes stable hold/resume scale at a stationary view, not translation reprojection or arbitrary fast movement acceptance. Private proof: `research/_archive/2026-10/creative-v8-proof/`, source-rate samples in `research/_archive/2026-10/creative-v8-source-rate.json`.

An original-window Space press was captured across both real processes: MC feet Y 62 -> 63.25220334 -> 62, 23 observed airborne samples, native presentation Y 999 -> 1000.252197 -> 999, ending with native vertical speed zero and MC grounded on grass. MC health remained 20, invulnerability true and flight false. This is an actual normal jump/landing check, not native wall-climbing or a full obstacle-course test. Private trace: `research/_archive/2026-10/creative-v8-proof/jump-confirmed.json`.

Fixture checks cover packet identity/age/finite values/sequence, virtual origin and jump/ground flags, every injected field-write failure rollback and preserved W. D3D tests cover native hand masks/state/lifecycle plus equal paired/held lens crop. The full guest build and its camera/mapping checks pass. Full native wall-climb/dash, native combat effects/ammo/ultimate, old map audio and long session lifecycle still require work.

## Same-world restart repair

MC PID 42756 was absent at the next continuation. The renderer retained its final frame. Starting the same save restored live rendering, but v3 correctly stopped on the changed source generation; native body presentation then reverted to its old map physics. This was a second route to the falling/swaying symptom.

Body v4 retains the last trusted native position during missing guest data, with zero velocity and explicitly counted grounded presentation. This does not write to Minecraft. It accepts a fresh guest process only for the same nonzero save-path/dimension identity and original host generation, retaining the same MC displacement origin. Different worlds/hosts, legacy zero identity and displacement beyond the existing bound are refused. Before attaching v4, the helper verified the retired v3 movement table against all three original native callbacks; it did not ignore an active callback based only on a report.

Real save/shutdown/restart: MC 11508 -> 43676, native 40552 unchanged, v4 remained loaded. A 65-second trace contained 1,366 paired samples including 444 unavailable/loading guest samples. Native Y stayed within 999.995117..1000 and read vertical speed within -0.279297..0, including the small original-tick-before-correction window. There was no accumulated fall. The adapter reported 1 successful session resume, 1,903 held ticks and zero failures. Reconnected MC retained health20, invulnerability, flight off and creative mode. Private evidence: `research/body-v4-reconnect-40552.json` and `research/_archive/2026-10/body-v4-reconnect-summary.json`. This is a single controlled same-save restart, not arbitrary world switching or long-session acceptance.
