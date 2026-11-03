# Tracer Blink temporary weapon disappearance — 2026-10-23 investigation

## Accepted42 bounded real-game repair

The main owner normally cold-deployed compositor42; exact current test was
native30976, retained fully modded MC12576, original Overworld lane. SHA256:
`85441d23e6d34000bcb1fc84192f4fe3726800f6dc57b90ed46d2162ac125a63`.
The reader, native inputs and60fps video all completed with exit0; root result
passed/cleaned. Subsequent independent read-only health confirmed actual guest
PID12576 alive20HP while the main owner was conducting the next test, not a
claim that the current hero/flight position still matches the Blink fixture.

`live42/visual-accepted.json` is the manual visual acceptance receipt. Actual
three dense60fps contact sheets were extracted and EACH actually viewed:
`live42/blink1-dense.jpg`, `blink2-dense.jpg`, `blink3-dense.jpg`. Both original
pistols remain visible through all displayed dynamic-camera Blink frames, with
their changing same-frame pose, including approach to the actual MC wall.
No frozen gun pixels or MC stand-in weapons were introduced.

All3223 captured unique first-person ring frames preserved their valid original
hand pair, versus41's108 rejected/3326 preserved. Dynamic-lens42 intervals are:

| Actual frame interval | Captured dynamic frames | Accepted hand draws per frame | Preserved |
| --- | --- | --- | --- |
|12960–12995|36|5|all|
|13309–13313|5|5|all|
|13653–13688|36|5|all|

Native render cadence differed on the second cast; do not rewrite it as36 frames.
The same measured hand projection1.74013..1.98089 is now recognized while world
projection1.30595..1.38181 remains rejected; accepted hand draws stay EXACTLY5,
not an extra world draw. The pure predicate separately rejects those world values.
The mapped host/MC metadata is retained. Exact camera-matrix parity and all-world
presentation are not newly certified by this one bounded run.

Actual Blink starts/captures advanced0→1→2→3 once each. Requested displacements
7.480713/7.479065/7.480469m produced actual7.200000m at the real wall, then
7.479065/7.479065m. Afterwards8 real original pistol events hit a real villager,
20→15.199997HP, damage4.800003MC HP, no rejection. Fixtures were cleaned.

The ring has one117-frame late gap(15093→15211), AFTER all three Blink intervals;
it is retained, not called complete14-second continuous render capture. The raw
root `result.json` retains its initial `visualFixed=false` placeholder unchanged;
actual review is explicitly in the separate manual acceptance receipt. Old41
visual failure is retained. No separately compositor-restored ORIGINAL-native
control was performed, and no persistent fists/crash/full-kit or retail-VFX parity
claim follows. Stop at this accepted scope for the user's requested wrap-up.

## Actual41 diagnosis and42 source candidate

The main owner completed3 real grounded Blinks with native15548 and restored
ordinary primary/cleaned the fixture. Read-only observation and video exited0.
`live41/analysis-full-scripts.json` deduplicates3434 actual ring frames,3326
preserved pairs and108 unpreserved frames, no invalid/resumed/depth-change fault.
The108 form EXACTLY3 groups of36 frames each:

| Actual frame interval | Actual wall interval(ms) | Fullstage candidates | Accepted hands |
| --- | --- | --- | --- |
|134455–134490|1792752133731–1792752133877|15–20 per frame, all lens-rejected|0|
|134832–134867|1792752135310–1792752135457|9 per frame, all lens-rejected|0|
|135209–135244|1792752136906–1792752137052|15–22 per frame, all lens-rejected|0|

All rejected frames still had fullviewport/sixRT/R24 candidates. Their larger
projection value moved through1.74013..1.98089, while the smaller world projection
was1.30595..1.38181. Ordinary preserved frames had larger2.14451/smaller1.42815
and5 accepted hand draws. Actual original Anim35/Wait57 Begin ticks19408/20912/
22432 coincide with the three intervals. Complete original0024 and pistol0016
changes are retained:98/23 events, with actual sampling bounds, not invented
lossless traces. Normal End updates its logger timestamp too; the analyzer now
labels an intervening lost Begin only for End-to-End timestamp changes.

All three60fps dense contact sheets were actually viewed and show both guns
disappearing and returning. Exact video frame-to-wall offset is not independently
certified; do not mislabel an assumed recorder timing origin as an exact join.
Raw detail receipt: `live41/lens-rejection-details.json`.

The main owner explicitly authorized a narrow42 source candidate. Dedicated
`tracer_viewmodel_lens.hpp` recognizes only current native Tracer/first-person,
the observed continuous interval with small margins[1.738,2.005], original packed
perspective/near-plane/16:9/finite/zero off-diagonal checks. Existing recognizers
remain unchanged; the upper boundary overlaps their2.003 lower boundary. It
rejects both measured world intervals, other heroes and selection.

`pose_observer.cpp` now shares ONE `isCurrentViewmodelLens` between world-pose
exclusion and hand capture. The additional branch reads current NativeLocalHero
once per actual render frame and rechecks its controller/model/hero owner; read
failure cancels the scope. No Shift read, guessed duration, native FOV/animation
write, old-frame gun history or extra owner. The main owner will cold-build42;
loaded41 is not overwritten. Candidate fixture source covers9 measured lenses,
1001 continuous points, world/hero/menu/malformed projection and boundary cases.
No42 compilation/deployment/visual acceptance is claimed by this subtask.

Source backup:
`~/.universal-modder/backups/tracer-blink-lens-20261023/20261023-185154/`.

## Follow-up: compositor41 numeric ring is now wired, default OFF

The separate launcher agent wired the existing owner with the previously saved
numeric128-frame ring. Enable only before a normal cold attach by creating
`research/enable-hand-mask-trace.txt`; ordinary play without that file skips the
extra candidate-stage reads. No lens/mask/render rule was widened, and no new
owner/GPU readback/history replay was added. Its6 independent native fixtures
(including the ring) and C++17 syntax check passed, and the main owner built41.
Deployment/current actual enablement and Blink outcomes still require real data.

Actual writer: `native-host/build/world-live-<verified PID>.json`, refreshed about
500ms. Fields are `handMaskTraceEnabled` and `handMaskTrace` rows:
`frame,wall,viewMode,stageCandidates,lensRejected,handDraws,minLens,maxLens,starts,
resumed,depthChanges,before,after,invalid,preserved`. A128-frame ring covers about
711ms at180FPS or533ms at240FPS. Save reports at50–100ms intervals and audit frame
gaps; a single final snapshot cannot cover a long Blink recording.

`observe_blink_weapon_state.py` now also reads existing host/MC mapping HEADER
metadata, before and after each existing logger read. It copies no world pixels.
`analyze_blink_weapon_state.py` deduplicates ring frames by source generation/frame,
joins exact mapped host and MC-acknowledged frames, and bounds observed node2/5/10/
8/35/57 Begin/End changes by their real read interval. Initial rows stay baseline;
lossy finish-only samples do not become invented Begin events. Three pure fixture
tests and both Python syntax checks passed. This is still not a cause/fix proof.

For the main owner, with new verifiedPID and an actual Tracer already selected:

```
.venv/Scripts/python.exe tools/observe_blink_weapon_state.py --pid NEWPID --seconds 14 --output research/tracer-blink-visibility-20261023/live41/observations.json
.venv/Scripts/python.exe tools/analyze_blink_weapon_state.py --input research/tracer-blink-visibility-20261023/live41/observations.json --output research/tracer-blink-visibility-20261023/live41/analysis.json
```

Only the main owner operates inputs/recording: idle1s, three ordinary Shift casts
spaced1.2s, then idle and real primary. Record60fps and retain its timing sidecar.
First compare disappear frames with the exact ring. If the pair stays valid but
weapons disappear, that is not proof the pixels existed in native draw; get a
separate original-native control via strict normal compositor restoration before
changing animation or mask. Keep controls and code changes isolated from the new
Deadeye/Pulse/Pharah acceptance. No unsynchronized simultaneous drivers.

User reports both original weapons disappear briefly on Shift. This is distinct
from the historical persistent fists/no-factory fault. No fix or parity acceptance
is claimed here. No game input/restart/deployment/new callback was performed.

## Actual bounded evidence inspected

`research/_archive/2026-10/tracer-blink-live.mkv` (2026-10-18) and
`research/four-dps-20261023/blink-collision-final/blink.mkv` (2026-10-23)
were decoded at their real30fps. New first80-frame contact sheets under
`research/tracer-blink-visibility-20261023/` were actually viewed. Both show
recurring simultaneous full removal of both weapons for approximately5–6 frames
per Blink, then immediate reappearance. The newer movement/collision/charge
acceptance therefore did not certify transient hand visibility. Those are both
COMPOSED videos, not original-native controls; they do not prove the compositor
caused disappearance. Frame indices and harness elapsed time are not claimed to
share an exact clock correlation.

The real current official [Tracer page](https://overwatch.blizzard.com/zh-cn/heroes/tracer/)
returned200 and its actual Blink video URL was read from HTML. The original CDN
clip `OVERWATCH_WEBSITE_CHARACTER_CAPTURE_TracerBlink_WEB_16x9_1920x1080p30_H264.mp4`
is saved privately as `official-current-blink.mp4`, SHA256
`5435b5788d2faa2102208d5154172e4bb573d2c67b8f82c145c5ae5d8dbbed00`.
It is4.633333s/1920x1080/30fps. Both complete70-frame contact sheets were actually
viewed. In its first-person sequence, weapons remain visible during the blue
stretched Blink trail, including the two observed forward Blinks. Later portions
switch to a third-person hero demonstration; those are not hand-visibility controls.
This is a MODERN official site asset, not authenticated2016 or beta footage.

The official PlayOverwatch [2015-05-27 gameplay preview](https://www.youtube.com/watch?v=zNq4nTA3eMg)
is identified by verified publisher/date and describes an early unedited PC match.
Its frames have NOT been obtained/viewed in this session, so the2015/Beta hand
behavior remains unverified. Do not infer that modern-visible weapons prove the
2015 offline client should behave identically.

## What the code establishes, and what it does not

- `NativeBlinkController`/`NativeBlinkPhase` only transfer the original measured
  teleport and resolve MC collision. They do not hide native guns or request MC
  weapon models. Changing generic movement is not an evidence-based fix here.
- Saved exact native graph0024 has StateBlinkEffect8 and Anim35 with a declared
  `.10000000149` value at field4d475080. Node57 also has `.1s` Wait. The duration
  field alone does not identify a weapon-hide policy. Effect8 has nested effect
  references; no semantically verified hide-first-person field was found.
- Current retail OWLib classes have different field/type hashes/layout and must
  not be used as a2015 native-write schema. No animation/visibility variable was
  patched or disabled.
- `pose_observer.isHand` requires supported projection/fullviewport/six render
  targets/R24 depth. Supported FOV windows are narrow. `observeHands` rejects a
  resumed first-person group after `handAfter`, or a changed depth identity;
  `blendAtHud` then drops the entire current hand mask. Either is a plausible
  mechanism, but no per-frame capture proves one happened during these Blinks.
- Existing `world-live` has only cumulative `unmaskedFrames`, not a reason or
  the exact rejected projection. No root cause follows from those totals.

## Independent diagnostics saved; NOT integrated

`tools/observe_blink_weapon_state.py` reads only existing original logger states
0024/0016 and existing owner's reports, validating exact executable SHA/creation.
It never calls a native evaluator, sends input, focuses a window or attaches a
hook. Existing logger timestamps remain lossy; this is not a pixel comparison.

`native-host/src/hand_mask_trace.hpp` and its independent fixture provide an
optional128-frame numeric ring, disabled by default and NOT wired to the owner.
It records fullstage lens candidates/rejects, starts/resumed groups/depth changes
and actual before/after/invalid/preserve decisions. Immutable atomic snapshots
permit the existing worker to report it. No GPU readback, draw replay, weapon
pixel history or change to mask behavior is included. Fixture source was written
but not compiled/executed here; no production native build was performed.

Minimal owner integration proposal, for a normal future cold deployment:

1. After independent fullviewport/sixRT/R24 checks, report candidate lens[5] and
   the CURRENT existing lens predicate result, without widening it.
2. Record first-group start, resumed-group refusal and depth-identity refusal at
   their existing branches. Record preserve decision at the HUD boundary.
3. Finalize once just before the existing present-reset; include frame/wall/view
   mode and dump the numeric ring through the existing report only. Same owner.
4. In an agreed quiet test, compare those exact frames with native actual Blink
   graph/action and COMPOSED video; separately strict-restore the compositor and
   capture ORIGINAL-native Blink. Preserve all restore checks. The two captures
   must be clearly separated, not mislabeled as simultaneous identical play.

Only after that choose a narrow measured correction: supported original lens,
safe exact-depth grouping, or genuine native visibility lifecycle. Never freeze
or replay weapons from an old world/model/frame to cover the gap. Keep original
Blink animation, charge, collision, actual fire and hands; no MC stand-in guns.
