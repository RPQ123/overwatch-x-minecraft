# Soldier76 Tactical Visor — 2026-10-21

Post-change regression: the Bastion Tank movement JARcd5196f7… passed the actual
76 suite again (native21460): passive/damage credit, explicit lab-grant Q/drain,
off-axis hit, cover/replay/End. Receipt:
research/native-visor-21460-1792542441740716700.json. The Visor mechanism below
was not changed; earlier normal-full-charge/four-dimension evidence remains
separate. Current runtime identity/artifact hash is in TAKEOVER.md.

本轮实机复现并修复了76开大后不锁定MC目标的问题。保留原生Q、动画、
准星/HUD、耗能与技能阶段；MC只对已确认的原生步枪子弹执行瞄准适配。
这不等于76整套技能或全部英雄已经完成。最新实际版本/验收见TAKEOVER.md。

## Fault and native evidence

The previously deployed JAR1971e71b… admitted real rifle bullets while native Q
was active and its meter was drained, but the fixed off-axis MC target stayed
at20HP with zero Visor locks. The original failed receipt is
`research/native-visor-33748-1792525437041405900.json`.

`NativeVisorAim.eligible` compared the native factory tick counter with the
statescript logger's millisecond timestamp. These are different counters. One
later same-case trace has native target Begin102544 and factory tick6465;
the old comparison would reject that real bullet. Similar-sized synthetic test
values had concealed the error. New fixtures use unrelated counter magnitudes
and separately reject delayed bullets by their actual creation wall time.

A complete native Q trace also corrected an initial short observation: the
original TrackTargets12 DOES begin, after the windup. The recorded stack begins
at166320, target acquisition at167520, and both end at173520. That is1200ms of
native windup followed by6000ms of acquisition in this trace. No new fixed timer
or substitute early activation was added. The same original15/12 profile and
typed45radius/45angle declarations remain; its binding schema is unchanged.

Private raw trace: `research/hero-skills-implementation-20261021/visor-full-native-q.json`.

## Final behavior

* Only real original Soldier rifle factories03d4 can be corrected. Native ammo,
  spread/firing and damage remain authoritative. Helix, other heroes, replayed
  events and pre-acquisition bullets are excluded.
* Both original ultimate15 and target12 must currently be active, with current
  model ownership and live original geometry. Q input or a full meter alone
  cannot enable tracking.
* A window identity contains host generation, current model, MC world and
  native Begin. Its first observed wall time is captured AFTER reading and
  verifying the native state/configuration. That separates already-created
  bullets from new ones without comparing unrelated clocks.
* End, missing/stale reads, disconnection and replacement clear or invalidate
  the window. Source/model/world/freshness and actual rifle-event identity
  remain checked on the integrated server before aim correction.
* The existing MC target adapter chooses visible attackable targets by aim
  angle, then distance/ID, and raycasts real MC blocks. It keeps the native
  literal radius and the existing cone interpretation. This is an MC adapter,
  not a reimplementation of every native server targeting tie-break or outline.

The acquisition boundary is conservative: a bullet created before the first
verified observation is not retroactively corrected. Exact first-frame latency
parity, every native tie-break, boss/Enderman behavior and the entire76kit are
not established by these tests. MC targets are not injected into OW's native
target-outline system. The original Visor HUD itself remains visible.

## Charge policy and official reference

The current offline adapter retains its explicit5native points/second plus
actual MC damage credit. Native cost, eligibility, Q activation/drain and phase
timing remain original. The feedback policy replaces absent offline server
accounting; it is not claimed as exact official server charge parity.

The official [Overwatch Classic explanation](https://news.blizzard.com/en-gb/article/24146047/a-blast-to-the-past-begins-with-overwatch-classic)
describes Visor as automatic aiming at targets in view. It describes May2016,
not this older Beta's complete parameter table. Actual local native data/state
provides the parameters used here; modern perks and Stadium rules were not
substituted. No new art/audio assets were needed for this fix.

## Tests and private receipts

The first candidate JAR1aea76c3… passed actual inactive miss, active off-axis
damage20->16.599998 for two original17HP bullets, solid-wall exclusion, replay,
native End and post-End charging. The prior script incorrectly required zero
charge during the pre-drain windup; that test was corrected to inspect actual
target acquisition. Its failed receipt is preserved. The successful receipt is
`research/native-visor-11316-1792525933960157400.json`.

The candidate also passed four actual dimensions, each with inactive miss,
active lock, real cover, replay, Q-active replacement into McCree, replacement
back into a fresh Soldier with no old Q, fullHP and scoped weapon light. The
first attempt queried immediately after asynchronous cleanup and falsely
reported a remaining target. That incomplete receipt is retained; cleanup now
waits for the actual server acknowledgement rather than treating HTTP202 as one.

Without an explicit test ultimate grant, seven real20HP targets supplied normal
damage credit to reach the original1500point cost. Actual Q drained to0, locked
the off-axis target and ended with passive charging resumed. The original
Visor HUD/weapon over MC was captured and inspected. This evidence is separate
from the short four-byte lab grants used to shorten the lifecycle regression.

Final code additionally timestamps the boundary after the verified read. Final
deployment/regression receipts are in the `final/` subfolder. Do not conflate
candidate and final hashes or claim those checks before their receipts pass.

Final accepted JAR SHA256:
`c4f57937e63e98c7602cb29a552c486e09dd253f1ac46730310503302e113065`.
Actual26888/MC25228 repeated all four dimension rows and the seven-target
normal-charge/Q cycle. Both final receipts passed/cleaned; the earned cycle
also actually fired after native End and verified no new off-axis damage/lock.
`final-audit.json` verifies loaded JAR identity, all four native modules,
Hollywood, current fullHP/grounded Soldier/F6OFF, cleared targets/blocks,
advancing composed frames and independent supervision. Both final active-Q and
ordinary gameplay captures were inspected. Live off-axis tests use12degrees at
6m; full45m edge, every angle/target type and native target-outline parity are
not established. Range/cone/Helix exclusion guards also have pure fixtures.

Automated checks: full33-task guest build/check, actual Win64 skill/meter
fixtures, independent-clock/window/range/cone fixtures,45supervisor checks and
the HTTP contract fixture pass. These are separate from real gameplay evidence.

Reproduce in the isolated creative Switch world, after checking the exact PID:

```powershell
.venv/Scripts/python.exe tools/verify_native_visor.py --pid <verified-pid>
.venv/Scripts/python.exe tools/verify_visor_lifecycle.py --pid <verified-pid> --output research/visor-validation
.venv/Scripts/python.exe tools/verify_visor_lifecycle.py --pid <verified-pid> --output research/visor-validation --earned-only
```

Production changes are confined to the guest Visor admission/window and charge
controller diagnostics. No loaded native DLL was overwritten, no callback owner
was added, and global Hollywood/compositor34 light/material policy is retained.
McCree Flashbang/Pharah Concussive Blast remain unimplemented MC effects pending
their native event/status/physics calibration; quarantined Reaper experiments
and the separately cancelled Deadeye remain untouched.
