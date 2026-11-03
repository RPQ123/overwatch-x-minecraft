# Pharah Barrage: original factory and Wave trajectory — 2026-10-22

## New presentation pass: independent mini-rocket / orange impact / firing loop

The current guest adds PharahBarrageRenderer, PharahBarragePresentation and
PharahBarrageSound. Native emission15/compositor40/body14 and all six native
DLLs are unchanged. Actual native factory admissions still own flight and damage;
the renderer and sounds cannot manufacture a shot or change the curved path.

The Barrage mesh is now an independent MC-made blue/silver mini-rocket with a
gold nose and four fins. It is NOT a newly exported original OW Barrage mesh.
Its authored length is.24m, drawn at.6scale; near-camera solid geometry within2m
is culled while its luminous head remains, avoiding clipped large faces at the
beta's eye-origin factory. It does not reuse the primary rocket's mesh. Primary
rocket mesh, muzzle convergence, material and terrain damage are preserved.
The new private pack recipe is tools/pack_pharah_barrage.py; mesh/texture/audio
outputs and provenance remain under ~/.universal-modder/assets/owmc-pharah-barrage.

Pale soft ribbons sample the same two original Wave trajectories at12segments
over.144seconds. A real server-resolved loaded impact emits a bounded cosmetic
cue: orange original private154088 flame/glow/flare sprites animate for.32seconds
with an initial.07second flash. Additive RGB fades as well as alpha. Barrage skips
vanilla createExplosion after its existing actual direct/splash resolution, so
it no longer creates the large white MC explosion circles or duplicate vanilla
explosion sound/physics. Its terrain remains unchanged. Vanilla victim reactions,
including angry-villager storm-cloud particles in the damage fixture, and the
player's ALL particle setting remain intact. Those target-reaction clouds are
not Barrage smoke or the new mini-rocket mesh; the covered-wall recording avoids
that distraction and shows the orange impact clearly.

One private original gameplay-recording loop starts only with fresh accepted
Barrage factories AND the original firing node. It stops at native firing End,
loss of current source/model/world/player/focus, or220ms without real admissions.
It never starts from Q keydown. NativeSessionGuard clears it on transitions;
server presentation queues are cleared on source/model/world changes. Replay
admission creates no new launch/impact/sound. The loop is automatically ducked
while the actual early Mandarin callout plays, then returns to its lower SFX
level. This is a mixed original recording adaptation, NOT a clean exported
original sound-bank loop or full effect-graph implementation.

Reference correction: the official current Barrage CDN clip has an AAC stream
but every decoded sample is silent. It supplies visuals, not the firing audio.
The old bili-BV1Hs411q779 reference-manifest's hero/video/audio pairing is wrong:
P01 video shows Pharah, P01 audio says McCree's callout, while P02 audio actually
contains Pharah's Mandarin callout (ASR1.22..2.50s). P20 video shows Winston and
cannot be cited as Pharah. The loop uses hash-pinned P02 audio2.72..3.62s with
an80ms circular crossfade after that callout. The2016-06-14 catalogue date does
not prove its recording date. The mixed original game SFX/background remain;
ASR of noisy SFX can hallucinate generic subtitles and is not listening proof.
The unrelated clean early Chinese voice pack is preserved. Do not repeat the
old manifest's visual-attribution claims as verified extraction.

The asset installer preserves unknown user-edited destinations. The known first
test loop98fe351c... is backed up during migration to deterministic bitexact OGG
caa4b4af...; repeated encoding produced identical hashes. Three installer tests
cover idempotence, corrupt source and preservation of modified destinations.
The new server fixture covers admission-only cues, replay, unloaded impacts,
expiry, bounded queues and reset. Full37-task guest build and the proper HTTP
contract entry passed. Source/profile and native identities are pinned separately
in research/pharah-barrage-art-20261022/final-audit.json after delivery.

Private evidence: live1 passed core presentation but the first loud mix FAILED
its separate voice-correlation threshold; live2 lowered the loop but also FAILED
that threshold. These are not final audio acceptance. Final ducked live3 passed
actual90-shot damage/expiry, independent assets/impact counters, single loop
start/End and replay. Its actual MC audio matches the loop at.94896 and Mandarin
at.42116 under the predefined.6/.4 thresholds. This is mixed-audio identification,
not a claim of perfect listening quality. wall-final passed actual cover20HP,
orange impacts, expiry, single sound and replay, with its native contact sheet
actually inspected. The first mid-switch attempt did not obtain a real F11 grant
and is retained as FAILED; the retry holds the20Hz utility edge across ticks and
confirms the native meter before Q, then passed both world and hero interruption.
The final ducked build a3ec52c8... then passed final-four-dimensions on actual
native25412/MC25960: all four dimensions after real Genji->Pharah recreation,
covered and exposed90-shot Qs, cover20HP/exposed0HP, single loop per volley,
native meter debit/End, all flights retired, replay inert, recovered primary20->8,
earned damage charge about127..128 and full200/200 native health. Its separate
final-mid-switch passed world and hero interruptions: old flights/damage/sound
and new impact cues stop, and fresh Pharah/McCree primary works. Test fixtures
were cleaned. The unmodified native oracle remains96checks/zero failures.

Final delivery25412 creationFILETIME134371140459941079 / actual MC25960, supervisor
17060, source/profile JAR a3ec52c8464b3aab1eecb38d1675340b1f7158737b0f83860ecd0fcd68c07f7e.
The actual delivery-picker_small.png was viewed: original animated Pharah,
native HUD/roster over a real nighttime MC Overworld. Day/night remains enabled,
not forced daytime. Player grounded65, full20HP/not flying; particlesALL, no
remaining flights, firing loop stopped (12starts/12stops). All six project modules
are unique and unchanged. Native/source frames advanced168/56 over.6seconds;
this sample is not a minimum-FPS guarantee. Exact audit is final-audit.json.
No matching current error report was found; this does not resolve past crashes.

At this turn's start the supervisor had correctly classified delivery29400 as a
real crash despite exit0. The report/dump is retained in this pass's crash29400/:
native RVA825346, not the historical d1428b TIMER release address. This occurrence
followed delivery; matching an older startup-fault address does NOT prove a
startup-only cause. Neither cause is repaired by these visual/audio changes.
No report is sent. Both prior tested owners23600/23496 were strictly restored
before cold replacement; strict-stops.json confirms all four owner reports,
including compositor global/input/light/frame-cap restoration. Do not treat no
new matching report or idle survival as proof of long-term stability.

## Earlier trajectory pass and retained historical evidence

Selected observer is emission15, with unchanged compositor40/body14. The previous
strictly deferred node2 gap is implemented; node7 remains separately unsupported.
This is the classic offline beta24919 ruleset plus declared MC presentation and
physics adaptations, not all modern Pharah perks or a pixel-identical retail kit.

## What the original client actually provides

Actual script058000000000002b/node2 emits90 resource0400000000000052 factories.
The offline path returns status8/result0 without an initialized projectile. Each
real factory supplies its own origin, direction, timestamp, identity and seed.
Native resolved speed45/lifetime5/range100, direct10 and splash30 are pinned.
Explosion rings are.5/full and1.5/.3000000119. MC keeps the existing10:1 HP scale,
cover/exposure and declared linear ring interpolation. Mini-rockets do not destroy
terrain; the previously accepted primary rocket still does. Creative immunity
remains. The native original Q animation, channel, meter drain and early Mandarin
callout remain; F11 in the lab is an explicit grant, not naturally earned charge.

The earlier unknown855ce717 is CRC32-identified as
STUStatescriptWeaponProjectileMotionWave. Reflected names corroborate startTime,
fadeInDuration, spiralProbability, invertProbability, min/maxPhase, min/maxFrequency
and min/maxMagnitude. Native resolver104633b writes its12 evaluated scalars to
resolved data+20..4c. The two Wave definitions are checked field/type/value by
Python preparation and by the existing native owner; the actual resolved copies
are captured on the original factory thread before their pooled storage expires.

Read-only native code trace10325c5..10325cf copies factory argument+40 into the
projectile's64 seed. Wave update1037b60 reads native RNG table18449f0 at(seed+2..6)
masked3fff. The adapter copies the actual sampled phase/frequency/magnitude/
rotation/spiral parameters, including inverted frequency. No new random direction
or key-triggered projectile is invented. Two original Wave displacements are
added to the real original direction and forward45m/s path. The same pure Java
trajectory drives server5ms swept segments and visible model positions/tangents.
Protocol14+ rejects missing/corrupt Waves, other observers/resources and values.
Emission15 additionally pins the original factory0..89 sequence to the first
actual factory's world, model, host and MC generation. An observed scope change
permanently cancels that episode, even if the player returns; only a fresh
original shot0/tick can arm the next Q. This fixes the actual mid-switch failure
retained in mid-switch/ (emission14 admitted later factories into the new world).
No native timer or running script is arbitrarily stopped. An explicit current
model/hero check also rejects unacknowledged departed-hero
journal entries after a same-world reset. Existing world/source/freshness/ACK and
identity deduplication remain; replay cannot detonate a flight twice.

Scoped calibration uses the existing factory callback, not another owner. After
pinning the original24-byte function prefix, it calls only the original pure Wave
arithmetic on aligned stack-owned temporary flight data and the still-owned
resolved Wave. It never calls a script, timer, allocator or renderer. First16
actual launches x2 Waves x3 ages produce96 comparisons. This is a bounded oracle,
not proof for every possible parameter. The observed maximum error was
2.38419e-7, with zero discrepancies above1e-4. Normal play does not run the oracle.

## Visible projectiles and limits

Actual server-admitted active mini-rockets now render the already private original
retail154088 primary rocket mesh at a smaller scale, with original private flame/
flare sprites and the shared curved trajectory. This is reuse of a primary asset,
NOT a newly exported original Barrage mesh/effect graph. Mini-rockets do not get
the primary launcher's muzzle correction or LMB flash. The MC impact explosion is
still an MC presentation adaptation. Exact original Barrage launch compartments,
impact graph/loop SFX, material and scale parity remain to refine. The primary
mesh/muzzle/light/voice fixes are preserved. MC range retirement uses accumulated
swept distance; the original end-of-range implementation is not independently
certified. Assets stay outside the repository.

The [official current Pharah page](https://overwatch.blizzard.com/en-us/heroes/pharah/)
describes a continuous mini-rocket volley. Its actual official Barrage CDN clip
was fetched from that page and visually inspected in private
research/pharah-completion-20261022/official-reference/. It shows bright orange
heads and thin pale trails; our MC impact smoke is visibly different. Its modern
video does not establish beta flight numbers. No claim of identical pixels or
full modern-server behavior is made. The alternate node7 has a third78aad781
motion plus different damage/rings and stays refused until separately traced.

## Verification and deployment

New native fixture checks actual-seed sampling, native-axis golden displacements
and changed/missing profile refusal. Java checks native-axis golden displacement,
curved swept collision, exact-once blast/replay, old observer/missing Wave/bad
numbers and departed hero/model refusal. Full36-task guest build, native actual
MinHook/lifecycle fixture,19 strict-stop tests,45 supervisor tests and the proper
HTTP contract entry point passed. These fixtures are not visible-play evidence.

Private real evidence: research/pharah-completion-20261022/. Actual native21424,
emission15/guest06eba252... passed four-dimensions-v15: Overworld/Nether/End/
Twilight each after Genji->Pharah recreation, two complete90-shot Qs per dimension,
covered target20HP/exposed target0HP, zero new rejected valid shots, flight expiry,
actual meter debit/End, visible models, replay unchanged, ordinary primary20->8,
and real damage charge credit about127..128 including passive accrual. Each
native model remained full200/200HP. F11 shortens the Q tests; ordinary fire's
credit test does not claim a full natural1500-point charge was earned.

mid-switch-v15 passed actual mid-air world and hero interruption, no residual
flights/new damage and recovered Pharah20->8 / McCree20->13. Tested audit records
85 later native factories refused by the world episode scope,96 arithmetic
oracle checks, zero oracle failures, six unique modules and actual current light.
The normal-stop-v15 result separately verifies all four owners restored, including
compositor input/light/frame-limit, before the final cold delivery launch.

native-resources-result passed actual Shift10-second cooldown/retry, hover fuel
100->0->100, held Space ascent14.81m in the observed hold, health/alive and cleanup.
The private barrage-motion-21424 result passed92 rooted samples with0 movement
range and2.475m recovered ordinary movement. primary-live-result passed original
primary terrain/splash/protected blocks/replay. e-final passed actual non-damaging
movable-target push14.6508m/self2.6562m, one E/cooldown refusal/replay/cleanup under
the declared MC physics (not claimed OW distance). Particles remainALL.

The final actual native video/contact sheet four-dimensions-v15/contact.jpg was
visually inspected: real MC dusk world, original Pharah HUD/launcher recovery,
visible luminous mini-rockets/MC explosions and actual target death. Official
comparison still has visibly different impacts. These are unattended lab checks
and image review, NOT new human user play acceptance or a minimum180FPS guarantee.

Earlier first-live, four-dimensions and final-four-dimensions directories are all
emission14 candidates. first-live preceded the Java handedness correction;
four-dimensions preceded current-model rejection/render-query cleanup. Even the
normal-pass final-four-dimensions candidate FAILED the later mid-switch test.
Do not promote these older results into emission15 transition acceptance. The
failed mid-switch evidence is preserved; the final delivery process/creation,
JAR/DLL hashes, supervisor and visible picker are in final-audit.json.

Native TIMER corruption and separate historical startup crashes remain unresolved;
no matching report or idle survival is not a crash-free/root-cause guarantee.
Stop only using strict restored global/input/light/frame-cap controls. Never
replace a mapped DLL or add another callback owner.

Final delivery29400/MC20936 actually inspected at Pharah native animated picker
over daytime real MC terrain. final-audit.json pins creation/hashes/supervisor,
matching profile JAR,84 native/27 source advancing frames over.6s, particlesALL,
grounded full-health player and no pending test objects. A cold primary20->8
console assertion passed, but its raw snapshots were not persisted after an
audit tool incorrectly requested a nonexistent composed counter. The corrected
audit uses real frames/sourceFrames fields and documents that evidence limitation;
full mechanic raw evidence remains four-dimensions-v15 on tested21424.
