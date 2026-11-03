# Tracer Recall - current native/MC implementation

## 2026-10-23 current acceptance

The former attack-lock attempts below are historical failures, superseded by
body19. Read NATIVE-TRACER-KIT.md. recall-sixth, recall-repeat and
research/tracer-kit-20261023/four-dimensions-v1/result.json actually PASSED:
real3-second history rewind4.2m/0m error,2->20MC HP, original magazine30->40,
original root31 End then state1 completion after real MC disposition, and
actual post-Recall primary damage. All4 dimensions passed fresh hero binding.
The earlier variable/timer guards remain withdrawn; this is a new scoped
existing-logic-owner handshake. Mid-cast low-health world interruption is still
a separate pending regression; do not infer full parity from the fixture.

## Historical 2026-10-21 failure record


**Recall is currently unavailable as an MC skill. Pressing original E can also
leave the native Tracer unable to fire.** Ordinary original hero replacement
recovers it. Two attempted availability guards failed real tests and were fully
withdrawn. Do not call this a repaired Recall or a working quarantine. Current
accepted gameplay artifacts remain the Visor JARc4f57937… and original six DLLs.

## Official semantics and actual version

The [official Classic article](https://news.blizzard.com/en-gb/article/24146047/a-blast-to-the-past-begins-with-overwatch-classic)
describes Recall as returning to a previous location and health, and Pulse Bomb
as sticky. It explicitly concerns May2016 launch1.0. It does not establish exact
rules for our older0.8.0.24919. Current
[official Tracer information](https://overwatch.blizzard.com/en-us/heroes/tracer/)
also contains modern perks/Stadium rules, which must not be substituted here.
No modern overhealth/allied-healing perk was implemented or assumed.

## Current-client declarations

The new `tools/inspect_native_recall.py` is strictly read-only and writes only
private research JSON. It checks current controller/reference/model ownership,
the unique1a graph, reflected types, exact dynamic destinations/resource links
and owner again after the read. It publishes no gameplay binding or native hook.

```powershell
.venv/Scripts/python.exe tools/inspect_native_recall.py --pid VERIFIED_TRACER_PID --output research/recall-profile.json
```

| Declaration | Actual value |
|---|---|
| Recall script / node count |058000000000001a /48|
| Node1, type7211cf70, fielda9157cbb |3.0|
| Node1 fields53222441 /05aaa790 /d970b2d6 |0.1 /0.1 /0|
| SetVar15 → variable0d800…d7 |0.9|
| SetVar16 → variable0d800…1d8 |12|
| ChaseVar14 fields5d05b699 /fc7bc05c /924cebfa |1 /0 /0.375|
| Dataflow12 /13 references |0480000000000023 /0480000000000030|

Node1's legacy type and the exact meanings of those anonymous fields are not
fully identified. Do not label0.1 a verified history-sampling interval, equate
the0.9 variable with every immunity/skill phase, or create an MC3second rewind
solely because the number3 appears. Native health/ammo history, safe destination,
cover/collision, interruption and cross-world history policy remain open.

## Actual failure evidence

Exact SHA256-guarded OW26888/MC25228 was initially healthy. Original E entered
node27 Stack and nodes4/9/12/13/14/19/31. The ChaseVar14 End was375ms after
Begin; animation9 End was900ms after Begin. Other observed states did not exit
in the bounded trace. A recreated native model reproduced first activation
followed by no second activation after waiting more than the declared12seconds.
Actual injured MC health stayed2 rather than healing; cleanup restored20.

A reversible grounded platform probe had over3seconds of stationary history,
then actual W movement: MC Z12.5→16.7. E did not return MC to the old location.
That particular attempt followed the earlier native activation and produced no
new Recall state entries; it demonstrates the repeat failure, not a fresh
first-activation trajectory oracle. Raw trace retains this distinction.

Most significantly, after a fresh original E, a real empty-space MC target
remained20HP and native primary did not produce admitted damage. This was
reproduced and saved under `unprotected-pre-fire.json` and
`unprotected-failure.json`. A later baseline-only A/B on fresh native39520
removed the ambiguity: before E, the real target20→15.199997; after a confirmed
first E, a new healthy target stayed20 and admitted bullets203→203. Both input
commands succeeded. Full before/after native/MC/state receipts are in
`unprotected-ab.json`. Original hero replacement restored ordinary play.
The exact cause of the incomplete native history/dataflow path is still open;
do not claim a specific missing server routine or blame the body adapter without
an independent oracle. The failure is real even though that root cause is not.

## Failed guards — not shipped

1. Script variable3d was set to12 through its reflected Ability28 dynamic
   declaration. A short E/primary/Blink smoke passed: target20→15.199997 and
   actual Blink7.479492m. Longer same-process/world tests failed. This variable
   is a declaration and is **not** an established availability latch. Changing
   it does not reliably stop Recall. Do not reinstate this candidate.
2. The actual runtime Ability state was separately located through graph
   definition membership: unique node28, runtime index18 in the observed model,
   exact vtableRVA15d7c98 and script ownership. A real Genji Shift independently
   confirmed the same class/counter layout, with counter0→8; no force-finish or
   Genji reset function was called. A temporary3600second timer override used
   the previously measured counter-setter fields150/144/146. It also failed a
   cold-process real E test. The number3600 was an explicit attempted quarantine
   policy, never a claimed original cooldown. That candidate is withdrawn too.

The variable candidate passed only two Overworld rows before failure; it did
**not** pass the four-dimension gate. The runtime candidate passed zero complete
rows. Early short smokes and unit tests do not supersede these failures. One
initial supervisor attempt also rejected a wrong metadata field declaration;
that failure and correction were preserved rather than presented as gameplay
success. Normal-stop restoration of the temporary runtime fields was observed,
but restoration success did not establish a working input guard.

All guard imports, binding/stop integration and added guard tests were removed
from ordinary tools. Launch/stop/refresh-test files match their pre-heartbeat
backups byte-for-byte. Failed source/test/harness candidates remain private
under `research/tracer-recall-20261021/failed-runtime-*` and
`native_recall_quarantine-variable-candidate.py`. They are not supported launch
commands. No Reaper experiment or cancelled McCree ultimate was restored.

## Receipts, recovery and next step

Private folder: `research/tracer-recall-20261021/`. Key receipts include
`typed-profile.json`, `e-action.json`, `repeat-probe.json`, `motion-probe.json`,
`unprotected-pre-fire.json`, `unprotected-failure.json`, `guarded-smoke.json`,
`unprotected-ab.json`,
`lifecycle-variable-guard-failed.json`, `runtime-lifecycle.json`,
`row-failure-*.json`, `native-cooling-state-oracle.json`, and
`normal-stop-restored.json`. Source/settings/profile/JAR backups are in before/.
Only the read-only inspector is retained as a new ordinary tool.

The experimental native processes were stopped through the existing callback
restoration flow. A fresh native process was launched with the unchanged guest
and original native DLLs; the independent supervisor runs the restored baseline
source. Final39520/MC25228 and supervisor35352/39876 were audited, native76
200/200/MC20 grounded, no test objects/guard present, visible composed frame
inspected. Post-recovery actual76 Visor suite passed (Q used an explicit lab
grant; passive/damage credit was also tested). A final fresh-model rifle/light
smoke passed. Receipts: restored-smoke.json, final-audit.json, final-grounded.png
and research/native-visor-39520-1792536352064540000.json.45supervisor/3stop fixtures
and the proper HTTP contract entry point passed. See TAKEOVER.md for identities.

Until a proper native input/history lifecycle fix is independently verified,
avoid Tracer E in ordinary play; changing hero recovers a triggered lock. Keep
the accepted Blink and pistol implementation. Do not force-finish this graph
using the quarantined Reaper helper or a guessed animation-duration timer.
Investigate the original input/notification and history completion path in an
isolated test; if still unavailable, advance to a feasible next skill such as
Pulse Bomb calibration while documenting this explicit Recall limitation.
