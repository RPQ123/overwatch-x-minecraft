# Genji cosmetic effects — 2026-10-21

## 2026-10-21T22:11 — synchronized animation cosmetic v3, final combined JAR

User reported that white sword FX appeared after the slash. Server damage tracking
57/58 starts100..160ms after the actual original sword animations47/48; emitting
cosmetics on damage also incurred a server/client round trip. The cosmetic now
reads actual47/48 Begin in the provided native logger, queues at most16 bounded
SwordVisual events with native source/model/world/session/tick identity, and emits
local real MC particles at WorldRenderEvents.START. Existing150ms freshness,
monotonic high water and reset/owner guards apply. No Q/LMB-key-derived slashes.
Damage remains on its original57/58 tracking path; it was NOT advanced.

Verified animation47/48: original StateAnim type7fb4bf64; config field f9045e7a
declared basebfd9aadd, actual AnimAlias configee7800e7; aliases0c8000000000003f
and0c80000000000039. Native recovery69/70 was an incorrect first candidate:
it occurs about600ms after hit. Its failed timing candidate is retained as
timing-rejected-recovery.json/.mkv and must never be promoted to acceptance.

Corrected timing-only run native23300 passed42.71/28.37ms, copied to
research/genji-particles-20261021/timing-before-roster.json. Final combined
21-voice JAR in native21144/MC29288 passed [15.86, 27.97]ms from
observed47/48 Begin to MC cosmetic, BOTH before57/58 tracking. Actual target
20->8->0, exactly two cosmetic events, ALL particles and cleanup. Receipt:
timing-result.json passed=true/cleaned=true. Actual captures retained.
One read-only map-identity transient was rejected/retried as a whole snapshot;
it was not a write, fabricated event or acceptance of an invalid snapshot.

Current style white-layered-sweep-v3-animation: three white SWEEP_ATTACK and small
ELECTRIC_SPARK accents, no green MC dust. Original native blade material stays
original green. Shift sparse CLOUD travel wake unchanged from accepted v2.
Current combined JAR SHA256 e0d9998247222ef06d43f6e2ac91e1a45c8c36307573e8b8bf078dd84dd311ce. All21 voice selection and both Genji Q
language variants actually passed, separately from the combat/timing receipt.
36 Gradle tasks and HTTP contract passed. Four-dimension full Genji combat was not
rerun in this slice; previous white Shift and basic damage acceptance stays historical.


## Final white build, actual controlled acceptance

After input was idle193s, a new bounded run in native6848/MC12968 passed:
first native sword event emitted10 cosmetic particles and target20->8;
second emitted10 and target8->0. No dash preceded the harness's Shift.
Actual Shift traversed7 segments and emitted35 sparse cloud particles.
Idle snapshots were identical; McCree selection did not replay either effect;
ALL persisted. Back to Genji. Cleanup was confirmed after the queued server
cleanup completed (the harness's immediate first read was too early).
Receipt: research/genji-particles-20261021/live-result.json, passed=true and
cleaned=true. Actual white-contact.jpg was inspected: real native sword/MC
village/target red damage response, white sweep and small pale sparks, no green
MC dust. The native OW blade itself remains its original green material.
Installed JAR SHA2567803b009c103a64291ac0b5cea4959544b3deb6b902269fc1816ec8e2766ec39.
Earlier two failures below remain failures; this supersedes their pending single-
dimension/hero-switch gate, not the broader four-dimension/full-kit goal.
Additional empty-view two-swing recording white-open-view.mkv and inspected
white-open-contact.jpg clearly show layered white crescents without the close
target obscuring them. Final audit again verified6 unique native modules, matching
installed JAR, ALL, advancing composed frames and no matching current crash report.
Final original Genji animated picker was inspected; independent supervisor remains.

Latest user direction supersedes the initial green-dust experiment: remove green
particles, retain the liked vanilla sweep and make the sword presentation richer.
Keep Minecraft particles at ALL, including the performance graphics preset.

`GenjiCombatParticles` now emits three staggered **white SWEEP_ATTACK** particles
and seven small ELECTRIC_SPARK particles per admitted Dragonblade swing. Both
native tracking nodes57/58 use opposite lateral offsets. Every sword location
is checked against actual MC block collision before emission. There are no
colored DustParticleEffect instances. Actual Shift travel gets a sparse vanilla
CLOUD wake (one point per0.5m, at most16 points per bounded movement segment).
These are user-requested MC effects, not claimed original OW asset exports.

Effects run on the integrated server thread after existing native identity,
freshness, world/model and duplicate checks. Sword effects follow the real native
tracking event, even when the swing misses an entity. Dash effects follow actual
bounded MC displacement during an admitted native dash, not W or Shift keypresses.
No additional timers, native hooks, damage paths or charge writers were added.

`launch_passthrough_guest.prepare` persists particles:0 for all launch presets.
`WorldFrameExporter` enforces ParticlesMode.ALL each client tick, so video settings
or later performance preparation cannot leave potion/combat particles minimized.
The local combat diagnostic exposes particleMode and cumulative genjiParticles
event/particle counters. Cosmetic counters intentionally survive hero resets;
they cannot admit or replay combat. Style is white-layered-sweep-v2.

## Evidence and limits

Source/options/settings/JAR backup is in research/genji-particles-20261021/.
Usable profile/config/mod/private-pack/current-world backup:
`~/.universal-modder/backups/genji-particles-20261021/selected-1792585776/profile.zip`.
The earlier unrestricted profile archive attempt was terminated while processing
old profile backups; its incomplete archive is not a usable restore snapshot.
The initial guest4559dae8 and green-build a54de14e are retained privately.

35 Gradle build/check tasks passed for both the first and final white build;
the standalone bridge/test_contract.py Java/HTTP entry point passed. Existing
combat/ultimate/dash lifecycle fixtures passed. Native DLLs remain unchanged.
Both cold deployments used the existing strict normal restoration/stop controls.

Actual first green-build frame capture visibly contains the native Genji sword,
real MC world and MC sweep/green arc (sword-contact.jpg, failed-first.mkv).
Actual client diagnostic reported particleMode ALL. The user confirmed that the
sweep looked good and explicitly rejected green dust; final code removes it.

Neither failed-second-result.json nor failed-first-result.json is a passed controlled
damage regression: first sampled before the event completed; the second observed
seven native dash travel segments BEFORE the harness sent Shift, extra attack/
model changes and target17 rather than expected8. UI input was stopped instead
of accepting these results or attributing their cause without evidence. Temporary
targets/blocks were cleaned. The final white build subsequently passed the
bounded run at the top. Separate four-dimension/full-kit acceptance is not claimed
by this cosmetic increment. Do not promote green-build screenshots or compilation
into white play evidence.

Keep the all-hero early Chinese voice task active; see EARLY-CHINESE-VOICE.md.
