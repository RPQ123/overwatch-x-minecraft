# Tracer Pulse Bomb — native calibration only — 2026-10-21

Pulse Bomb is **not implemented in Minecraft**. This increment identifies the
actual beta throw and its typed configuration without turning a button, latest
logger row or cosmetic entity into a synthetic attack. The accepted guest JAR
and six native DLLs are unchanged. Recall's separate attack-lock limitation in
[NATIVE-RECALL.md](NATIVE-RECALL.md) remains open; no Recall E was used here.

## Official reference and version boundary

Blizzard's [Overwatch Classic article](https://news.blizzard.com/en-gb/article/24146047/a-blast-to-the-past-begins-with-overwatch-classic)
describes Pulse Bomb as sticky and explicitly targets the May2016 launch1.0
rules. It is a semantic reference, not an exact numeric oracle for our older
offline0.8.0.24919. The following values come from this client's reflected
declarations; they are not modern balance values or measured MC trajectories.

## Current-model declarations

`tools/inspect_native_pulse_bomb.py` uses the existing exact-SHA read-only
ResearchProcess, current controller/reference/model ownership, the unique graph,
reflected field types, bounded arrays and a second owner check after reading.
It executes no evaluator and installs no callback, input handler or binding.
Its CLI only writes private research JSON. A Soldier model is explicitly rejected.

| Declaration | Beta value |
|---|---|
| Hero |02e0000000000003|
| Pulse Bomb graph / node count |0580000000000034 /45|
| Original Volley node / projectile |1 /0400000000000045|
| Speed / lifetime / range |15 /5 /100|
| Gravity motion type / declared gravity |c2b6ce4b /30|
| Explosion health modifier |400|
| Direct impact health modifier |5|
| Explosion radius/scale pairs |2/1 and4/0.2|
| Anonymous explosion fieldb3aef067 |1|
| SetVar2 |entity variable156→0|

Do not nameb3aef067 a verified contact fuse merely because its literal is1.
Attachment eligibility, enemy/self/terrain policy, fuse start/reset semantics,
in-flight timeout behavior, occlusion and the exact ring interpolation still
need an independent native oracle. The gravity literal is an integer; the
generic armory's float-only gravity calibration must not silently substitute20.

## Actual native Q observation

The current SHA-guarded OW39520/MC25228 was audited with the six mapped module
paths and hashes before testing. Profiles/settings/source and guest JAR were
backed up privately. Original Tracer was selected through H/picker. A guarded
explicit four-byte **lab charge grant** filled its actual900-point meter; this
was not a natural-full-charge acceptance run. Original Q then executed graph34,
Volley1 and SetVar2. The meter drained and resumed ordinary passive earning.

The original factory callback was observed twice for the **same**
owner/volley/tick/shot/pellet/projectile identity: status1 then8, both result0,
type1, speed15/lifetime5/range100. These are not two bombs. The diagnostic field
`evaluatedDamage=0` does not mean a zero-damage native bomb: this resource has no
production armory spec, so that diagnostic evaluator was not invoked. The typed
400/5 modifiers above come from a separate read-only declaration path.

A bounded entity census observed five transient new entities, all with no
statescript component. This does not establish a functional native collision,
sticky target or explosion. The existing scoped factory diagnostics are lossy
calibration snapshots and remain unsuitable as the production attack channel.
The resource was not added to PRIMARY_RESOURCES, and no guessed fuse, fake
damage or timer-based Q bomb was enabled in MC.

After Q, actual native pistol input still damaged a real20HP MC target to
15.199997. This confirms ordinary pistol recovery for this Q attempt; it does
not repair Recall or prove an implemented bomb. Original replacement to76 then
damaged a fresh20HP target to16.599998, with current native light scope verified.
The inspector rejected that actual76 model as intended.

## Cleanup, evidence and next work

Private receipts: `research/pulse-bomb-20261021/` contains `before-audit.json`,
`graphs.json`, `typed-profile.json`, `q-probe.json`, `final-audit.json`, backups
and the bounded probe scripts. No game data is committed or published.
All test targets/blocks and the diagnostic flag were cleared. Final76 is native
200/200, MC20, grounded Overworld, F6OFF. Actual composed native weapon/HUD over
MC terrain was captured and inspected. The existing center H prompt remains
visible. A56-frame advance over the sampled interval proves transport activity,
not a sustained FPS guarantee. The supervisor briefly reports an expected
binding transition during replacement; a subsequent settled snapshot is ready
with no warnings and the current model. Wrapper35352/worker39876 remain
independent, with OW39520/MC25228 unchanged.

Before enabling this skill, establish the sticky/contact/fuse and blast policies,
then extend the existing acknowledged callback journal with a versioned spec and
MC attachment simulation. Test native identity deduplication, entity/block
attachment, moving targets, blast cover/self damage, invalid targets, expiry,
hero replacement and world/generation invalidation. A whitelist-only change to
the current generic projectile path would explode on contact and cannot claim
sticky parity. This harder physics slice is explicitly deferred under the
user's allowance; the next picker-order feasible investigation is Bastion Tank.

```powershell
.venv/Scripts/python.exe tools/inspect_native_pulse_bomb.py --pid VERIFIED_TRACER_PID --output research/pulse-profile.json
```
