# Hero/world initialization and scoped lighting — 2026-10-21

This increment preserves the two real processes and the global Hollywood scene.
It addresses first attacks/skills after replacement and weapon light ownership.
Private evidence and source/profile snapshots: `research/switch-readiness-20261021/`.
Do not treat historical PIDs or unfinished probe output as acceptance.

## Reproduced defects and changes

1. The old supervisor discovered replacement from a roughly one-second body JSON
   diagnostic and polled every two seconds. Four actual Genji/McCree changes
   produced original factory calls (3/1/3/1) while combat binding was still false;
   all four real MC targets retained20HP. `baseline-original.json` retains this
   failure, rather than a reselect-and-retry success.
2. Supervision could exit on a Windows sharing violation while atomically
   replacing `session-status.json`. A reader stress run reproduced the exception
   and the subsequent loss of automatic rebinding. Bounded publication retries
   now keep gameplay supervision alive; persistent telemetry sharing failure
   skips that publication and retries later, rather than terminating the owner.
3. A departed Genji model/script can remain allocated with intact IDs/admin.
   NativeAbilityReader checked those old objects but omitted the current
   controller's reference to the model. Dash and Dragonblade now require v2
   requests and verify current controller/reference/hero/graph ownership. A real
   Win64 fixture retains the old model unchanged, replaces only the reference,
   and proves rejection/reconnection. No historical Begin is promoted to a new
   skill. Primary and first-Shift initialization now precede optional melee.
4. Meter preparation failures were swallowed and could be cached as successful
   initialization. They now remain retryable. Readiness checks compare actual
   hero/model/world/session acknowledgements for movement, applicable skills,
   meter and light. Java signed-long world/session JSON and unsigned wire IDs
   are compared by the same64bits, including high-bit world IDs found in real
   Overworld/Nether/End transfers. Unsupported kits are not declared complete.
5. The old light owner had no hero/world lifetime and stopped checking the
   current CPU packet after acquisition. Compositor34 scopes the same render
   owner's light by actual hero/model, MC source/generation/world and a fresh
   post-transition pose. It restores old ownership on transition and rejects
   worker candidates from a departed epoch. This closes an ownership gap; the
   earlier baseline did NOT prove that a different Sun address caused every
   gray screenshot (three measured addresses matched and one was ambiguous).

## Low-latency supervision without weakening scope guards

`native_binding_scope.py` opens the existing frame mapping READ ONLY. It checks
the256byte body packet's format, host PID, source/session/world, even seqlock and
250ms freshness. Its scope must match the native body's stable acknowledgement.
Only then does the current emission observer's20ms hero/model replace lagging
body JSON model data for preparation. A transfer in progress cannot initialize
the departed hero/world. Discovery polls50ms; large HTTP/status snapshots run4Hz.
Failed preparation backs off250ms for that identity while a new identity can
proceed immediately. Same-model repair never repeatedly refills health, even
when a later skill preparation failed after the initial fill.

PE/PDB parsing reuses exact immutable file CONTENT, not timestamps or guessed
addresses. Loaded module inventory, absolute plugin path/uniqueness and PE/PDB
GUID/age checks remain. Unrelated Windows DLL paths no longer undergo expensive
filesystem resolution on every channel preparation. A local measurement was
about132ms before versus31ms for a repeated content-verified lookup afterwards;
this is a lookup timing, not an FPS claim.

## Compositor34 ownership policy

Hollywood remains `08000000000002af`. The calibrated camera-key coefficients
remain `(0.5,-0.707106781187,-0.5)`. Native RGB/derived RGB, materials, reflections,
the foreground exposure policy and Pharah's earlier tint policy are unchanged.
Only the existing owner's12Sun-direction bytes are written/restored. No new
callback owner, replay layer or loaded-DLL overwrite is introduced.

The worker continues read-only CPU-packet sampling even while bound. A different
validated candidate restores the old object before acquiring the new one.
The scene's Sun is not a per-hero object. During a transient missing packet, a
previously packet-verified object from the unchanged OW scene may be reacquired
only after exact original class/color/direction and new pose/scope validation.
This avoids seconds of unlit weapon while the transient packet is absent.
It never authorizes another map or relaxes last-owned-byte restoration guards.

Reports distinguish `viewLightVerifiedEpoch` (successful current scoped
class/color/pose/write validation) from `viewLightPacketEpoch` (a fresh CPU packet
actually confirmed that object in this epoch). Do not conflate them. Missing or
ambiguous transient packets are recorded honestly; actual Sun readback and
camera-space direction are also checked in the live tests.

## Deployment and bounded acceptance

Selected compositor: `tools/native_compositor_version.py`, VERSION34.

* `owmc-live-passthrough-v34.dll` SHA256
  `25c910f5a159648e8a46858bd8a1c9b1424eaa3ddeec17f99328244049433fad`.
* `guest/build/libs/owmc-guest-0.1.0.jar` SHA256
  `1971e71b186382514de3625505b9963d66be9d13ca252a45ac636cccfb034f1f`.
  The first full initialization/skill run used `c5944ee2beae0c1d31da0b77bcabc1c063847b1d6d18a4ead0b90fee6d72effd`;
  the final JAR adds the sword near-volume repair and explicit geometry fixtures.
* Body10/gate8/emission11/bootstrap10/localhero1 remain unchanged. Normal
  restoration/stop and cold startup were used for deployment. The selected
  executable remains guarded by its exact documented SHA256.

`tools/verify_switch_readiness.py` fires in the SAME input batch as selection,
900ms after confirmation, with no supervisor-ready wait/reselect before the
shot. The stationary target is placed along the known native reset direction
before selection. Each shot checks actual factory counts, real target HP,
replay deduplication, native full health and current light readback. Skills use
the first held150ms Shift1700ms after confirmation, preserving native startup
input gating. Tests place only reversible air floors/targets in the opted-in
isolated Switch world; the source/profile backups do not clone disposable saves.

`final-four-dimensions/result.json` PASSED: four actual dimension edges through
Overworld/Nether/End/Twilight, with a real hero replacement during each transfer,
8first shots and8first Shift activations. Genji targets20->9.5, McCree20->13;
replays unchanged, native heroes200/200. All four rolls moved6m. Dash admitted
one real Begin and moved in each dimension; native damage-path distance varied
5..17.5m in this probe (the post-action3D displacement also includes falling off
the small test floor). This validates activation/initialization, NOT exact full
dash timing/distance in every case. Three further traced replacements each
reported one Begin/15m and no read errors during the active phase. Keep this
timing detail open instead of claiming perfect skill equivalence.

Earlier probes remain in separate folders. The300ms probe produced NO original
factory call, so it is not a lost emitted shot. Some900ms Shift probes likewise
produced no native cooldown/activation and are not accepted skill tests. A
different real failed probe DID show native cooldown8 with MC begins0; that
failure drove the ownership/order correction above. An intermediate light-only
probe incorrectly required a fresh transient CPU packet within4s even though
the cached, guarded light was already active; the final reports separate those
two kinds of evidence. `final-fast12.json` contains only10completed rows before
a fixture assertion, despite its historical filename; do not count it as12.

Automated checks:45supervisor,6scope/ack,2content-cache,17report/stop,3native-only
stop,4render-setting,4light,4state,11weapon-binding tests; full33-task guest
Gradle build/checks including retained-old-model Win64 reads; native light epoch,
camera-key/restoration, GPU blend and hidden gameplay/picker/resize fixtures;
HTTP contract via `bridge/test_contract.py` all passed. Fixture passes are not
substitutes for the real tests and original pixels above.

Automation `mc` remains PAUSED. Existing deferred
kits, quarantined Reaper experiments, all-hero exact timing, MC-to-OW material
light transport, dungeon progression and sustained180FPS are not accepted here.

## Additional completed live receipts

* `roster/result.json`: six different heroes plus a second McCree return,
  seven real attack/replay checks and28actual yaw captures. Genji9.5HP,
  McCree13HP, Pharah8HP, Reaper13.699997HP, Soldier76=16.599998HP,
  Winston17.407993HP. The original-color angle sheet was visually inspected;
  no gross whole-weapon white/black flips appeared. Native reflections/idle
  poses retain small differences. This is six heroes/four yaw views, not all21.
* `research/world-hero-switch-36252-1792522810750654000.json`: same-process
  integrated-world reload, source PID unchanged, full native HP throughout,
  Genji movement/real damage/replay and same-model melee passed.
* `research/world-hero-switch-36252-1792522856603972400.json`: full MC process
  shutdown and independent supervisor recovery, old native body held during
  the source gap, sessionResumes increased, McCree/Genji attacks passed. No
  manual reattachment or second callback owner was needed.
* `extra-skills.json` on final33748: original Q and default callout really
  activated, original swing hit a2m target20->8, idle did not hit again.
  Explicit typed4byte ultimate grant is recorded; this is activation, not
  natural full-charge acceptance. Pharah held Space0.5s gained2.192749m and
  the current native flight channel recovered. Soldier76 walked2.2m at
  native5.5m/s, then actual sprint reached8.25m/s/4.69917m in the input probe.
* `blade-near-before.json` retains a real regression: native swing1 but the2m
  target stayed20HP. The old broad-phase query omitted candidates whose
  expanded bounds intersected the sword. Its strip only at the far4m tracking
  line also left a near dead zone against smaller MC bodies. The final adapter
  extends the same sweep back to the near plane, preserves far/side/radius,
  rejects targets behind the eye and keeps actual MC wall occlusion.
  `blade-geometry.json`: original Q/swing at1m,2m,4m each20->8 exactly once;
  7m and a2m target behind a real wall each remained20. Five actual cases
  passed, with explicit lab grants and all temporary blocks/targets cleaned.
* `final-jar-four-dimensions/result.json`: after that final JAR deployment,
  four actual dimension edges and8fresh Genji/McCree shots/fullHP/current-light
  checks passed again, no reselect before first shot, replay unchanged.
* `milestone-audit.json`: final33748/MC36272, standalone supervisor38260/11548,
  Hollywood, McCree200/200 and MC20HP on natural brown-mushroom terrain/F6OFF,
  no active test target/blocks. Actual animated picker restored the exact
  original Sun bytes; returning gameplay reacquired the scoped key. Picker
  and gameplay images were inspected. Recheck identities before any next work.

User subsequently requested hero-order skill completion, first McCree Flashbang
and Pharah Concussive Blast. That is a NEW increment after this verified
baseline. Official research and original graph calibration must precede adding
MC effects; do not count research or existing native animation as a finished skill.
