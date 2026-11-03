# Fullscreen render-boundary investigation — 2026-10-24

## 07:55 production lifecycle acceptance

Read NATIVE-DISPLAY-LIFECYCLE.md. The accepted mode is now prepared BEFORE native
renderer creation, retained by a durable exact-identity lease, and original
desktop modes are restored only after normal native exit. Actual full stop and
new native/MC start passed, including real picker clicks and the Bastion cannon
combat/End/ordinary-attack lab. A post-creation mode switch actually failed;
keep that failure. Cold Deadeye H freshness remains separately failed/open.
The originals are backed up; no native renderer DLL or provided inject changed.

## 07:15 correction: visible fullscreen is not a working picker

The earlier normal production restart passed actual strict native close and MC
save, but the old native exit restored both current and registered desktop to
2376x1080/144Hz. New13316 drew real MC/native picker pixels with growing blends,
yet actual hero-card/confirmation clicks did not select a hero. Scaled positions,
the1920 internal-position hypothesis, long dwell, original overlay hiding and
a reversible source-defined availability-byte probe all failed. Availability
was restored; no failure is an accepted mouse-mapping fix.

Reapplying the already accepted1920x1080/144Hz registered display mode restored
original Genji preview on the next click. The same native/MC processes then
passed the complete Deadeye control/End/ordinary-hit/H-interruption/cleanup and
final-picker suite (deadeye-menu-1080-v3). Both videos were actually reviewed.
Current desktop/OW client is1920x1080 again, with a fresh exact original-mode
backup at private known-1080-control-20261024-071157. This is a workaround;
production restart mode retention/reapplication remains pending. Do not resize
the game to2376 just because its picker image can be drawn there.

## Actual resolution, supersedes candidate discussion below

Original compositor42 is retained. Registered desktop1920x1080/144Hz plus original
WindowedFullscreen=1 (exclusive flags0), explicit FullScreenWidth1920/Height1080,
restored visible fusion. Root viewed Genji animation and hands/HUD over actual MC,
moved2.16m, fired24->21 ammo and returned via H to the native animated picker.
Evidence: fullscreen1080-final-audit.json and screenshots. Current display also
uses1080p; original2376x1080 current/registered DEVMODE is fully backed up privately.
This is a real setting change, not only a target or window-size claim.

44 was not accepted. Actual dual/four MRT targets were HDR26 and sRGB GBuffer29,
not a proved original HUD; the format guard refused composition. Candidate
source/DLL/build script were archived privately; original dirty42 source/build
script restored byte-for-byte, DLL unchanged. The offscreen GPU fixture passed
separately from the failed real run. Do not promote44 or rebuild42 from44 source.
Further arbitrary-resolution support is unfinished; working output is1080p.

## Investigation record (failed candidates, retained for evidence)

User requires the original OW window fullscreen. The supplied plugin resets
exclusive-fullscreen state every Present; its accepted DLL remains unchanged.
The original render HWND uses borderless monitor bounds, never a second window.

42 failed visible composition after current monitor/window changes. Source
readiness and module mapping did not establish a visible fused game. Current
monitor is 2376×1080; the historical 2560×1440 client is not this monitor.
An exclusive INI attempt and a 2560×1440 cold control both failed; keep those
failures rather than repeating Alt+Enter or treating window-size metadata as proof.

43 added bounded atomic counters and texture descriptors inside the existing
render owner only. No extra hooks, GPU readbacks or original-script calls.
Actual PID17524 (creation1792793992.9045856) showed:

- swap-chain target2376×1061;
- original scene/HUD color and depth1886×1061;
- 4002 stencil clears,3954 observed non-backbuffer targets;
- world viewport1886×1061, zero captured poses, zero composed frames.

The previous classifier required scene viewport/depth to equal the swap chain.
These actual dimensions prove that this requirement excludes the current native
scene. The native camera constant buffer already supplies exact inverse pixel
dimensions and paired projection/view matrices; those remain mandatory guards.

44 candidate observes a scene only when its viewport and R24G8 depth match those
validated camera constants. It composes at the original stencil-only HUD boundary
only when current-frame camera, color and depth dimensions match. The original
engine retains its later output scaling. First-person six-target/depth-pair
classification, native lens exclusions, MC identity and freshness remain.
Present still holds the last complete final-output frame on a missing boundary.

The debug-banner restoration is skipped across unlike coordinate domains to avoid
copying an unscaled rectangle into the wrong final pixels; full offscreen banner
suppression is not yet accepted. Original HUD/hero names are not broadly hidden.
This limitation must not be concealed as complete visual acceptance.

Further real44 counters onPID10072 showed2/4 bound render targets per stencil
clear, never1. The first single-target guard therefore composed nothing and that
run remains failed. Candidate44 now excludes geometry MRT4/6 while permitting
the observed dual-output stage only with the same current-camera/8-bit-color/depth
guards. The second RTV is not modified. Legacy first-person/selection GPU fixtures
and a separate offscreen128×72 to192×108 dual-RTV/held-frame fixture passed.
An initial offscreen test executable-name mismatch and the earlier over-broad
selection fixture failure are not successes; the latter motivated the MRT guard.

44 remains a candidate until actual pixels, original hero selection, first-person
hands/HUD, movement/attack, resize and restart have passed. Existing baseline42 DLL
is retained privately and has not been overwritten. Tests and real failures are
under research/sprint-20261024/. No all-hero or performance completion is implied.
