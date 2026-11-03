# Confirmed combat feedback and Deadeye crowd fix — 2026-10-22

This increment addresses the user's six-target Deadeye failure, shared classic
hit/elimination sounds, clearer Deadeye skulls, stronger flashbang presentation,
no jumping during Deadeye, Pharah's stronger enemy push and primary impacts, and
a short blood-like burst on each actually lethal Deadeye shot. Hanzo is paused.
Read TAKEOVER.md for the actual deployment identity; source/build success alone
does not establish installation or real play acceptance.

## Deadeye crowd and lethal markers

The existing lock scan could collect more than six entities, but the volley,
Java presentation request and native presentation owner each limited firing to
six. All three now agree on a bounded64-target limit. Body15 retains the existing
single logic-thread owner, original graph022f/node69/AnimAlias019f, original
Wait72 minimum134ms cadence, sequence acknowledgement and150ms damage freshness.
It does not manufacture a simultaneous group kill or bypass real cover. Requests
for65 targets are rejected;64 is a queue bound, not an unlimited target promise.
Actual64-target/native-duration play has not been certified.

The skull forecast now accounts for vanilla armor/toughness, Resistance,
Protection and absorption before comparing against actual current health.
Charging performs no damage and does not wear equipment. Actual firing still
uses MC's real projectile damage, current loaded collision and cover. Arbitrary
mod-specific immunities, boss phases and shield rules are not fully forecasted.
An invulnerable target must not be presented as a guaranteed kill.

Markers use a filled red head, dark eye/nose sockets and separated teeth with a
thick charging ring. Projection-aware world sizing keeps the skull approximately
38px high at1080p over normal combat distances. The adapted MC sepia pass preserves
saturated red rather than washing out the marker. Neither skull nor sepia is
claimed to be a recovered original OW mesh/shader. Native hands/HUD are retained.

Jump suppression is scoped to the current fresh, admitted native Q, live player,
world/model/source/session. It also blocks creative vertical flight and F6 flight
toggle during Q; ordinary movement/building and post-Q jump remain available.

## Actual hit and elimination receipts

NativeCombatFeedback uses positive actual MC health/absorption loss, not buttons,
animation or a predicted hit. Living damage, reflected projectiles and confirmed
End-crystal destruction enter the shared path for every admitted native hero.
An elimination requires actual health<=0 with a recent<=5s damage contribution.
Despawn/discard/removal alone is not an elimination. Multipart hits/death and
splash cannot duplicate a credited death. Hero/world/source/model transitions
clear pending sounds and contributions; disconnected/old queues cannot replay.
End crystals produce hit feedback, not a living-enemy elimination cue.

The client validates world/owner/model/generation and<=250ms freshness. Hit cues
are limited to one per50ms; kill cues retain their individual shot timing. Queues
and sound tails are bounded. Sound failures are diagnostic and do not change
damage, health, native animations or the frame exporter.

The private pack installer is tools/combat_feedback_assets.py. It checks every
source and existing destination before writing, preserves other enabled packs,
and refuses modified/unknown sound files. It is part of ordinary guest startup.
No game sound is in the JAR or committed source. The public uploader's
[HitSound files](https://github.com/DrAbcOfficial/HitSound) are labeled Overwatch
hit/kill; hit SHA256 e328fa1b16a9dad4caab785691172b1a34b21624b77df2b3e0affd715b45bf6c,
kill SHA25640ef511ec844bc11a77c69a701c7bfbfaafab229da73b31d032f69a7836b89dd.
Official2015 mixed gameplay is corroborating reference only. Its weak mixed-audio
correlation does NOT certify an exact earliest OW1 sound-bank version. Recording
and upload dates are distinct. Preserve this provenance limit in user reports.

## Lethal bursts and flashbang

DeadeyeKillEffects is invoked only by a fresh, individually acknowledged native
shot that actually changes a living victim from positive HP to<=0. It emits short
red fragments and droplets in the shot direction, plus a few impact sparks. No
persistent pools, decal entities or repeated damage are created. The latest
droplets use a Fabric SimpleParticleType, a vanilla atlas sprite, gravity, depth,
short fade and full particle light so they remain readable at night. They are
original MC effects, not extracted OW blood or copied particle-library code.

The previous standard-particle build passed12 actual lethal bursts, but its dark
night appearance was unsatisfactory. The new emissive sprite was cold-installed
and passed live4 on native26572:12 actual lethal bursts, visible short red droplets
in the inspected night-frame crop. It remains a restrained MC blood-like effect,
not a claim of matching OW gore or using an original OW effect asset.

Flashbang uses a bright FLASH, cloud, gold sparks/dust and outward radial sparks
at the one real detonation. Existing original E admission, collision, cover and
75OW-equivalent damage stay intact. The user's custom2-second visible Slowness
potion with exactly50% effective movement remains; current OW/Beta/custom rules
are separate and should not be conflated.

Particle implementations considered: [Lodestone](https://github.com/LodestarMC/Lodestone),
[Veil](https://github.com/FoundryMC/Veil), [Photon](https://github.com/Low-Drag-MC/Photon)
and the [official Fabric particle API](https://github.com/FabricMC/fabric-docs/blob/main/versions/1.21.1/develop/rendering/particles/creating-particles.md).
The existing Fabric engine suffices, without adding another rendering dependency.
MC particles remain ALL at startup and runtime.

## Pharah — explicitly custom enemy impulse and original primary assets

The actual original E factory still supplies event identity/flight/cooldown. Real
MC sweep, cover and exposure remain authoritative. Enemy impulse is multiplied by
1.5; self propulsion retains its accepted baseline. Enemies may take up to.5 MC HP
(5OW equivalent) scaled by exposure/falloff; no self damage is added. This is the
user's custom request, not an assertion about original Beta or current OW damage.
The [official July2024 notes](https://overwatch.blizzard.com/en-us/news/patch-notes/live/2024/07/)
describe a0-damage Concussive Blast, which must remain separately documented.

Primary rockets retain the privately extracted genuine retail154088 primary mesh
and effect sprites. The current154504 client was not successfully extracted and
must not be called a successful newer export. Added primary impact sprites are
scoped, bounded, short-lived and follow actual server impacts; the terrain
explosion avoids the large vanilla white emitter. Existing direct/splash/cover,
protected blocks and independent Barrage gameplay must be regressed in a quiet
actual session. Full original effect-graph identity is not certified.

## Evidence and status

Backups and private evidence: research/combat-feedback-20261022/. Source/profile
backup is referenced by backup.json. No reset, unrelated commit, second callback
owner or overwrite of a mapped native DLL was performed.

* live3/result.json: actual PID744/body15, passed and cleaned. Twelve real targets,
  including armor, Resistance and absorption, all acquired ready markers and died
  in12 separate original-animation shots. Twelve kill sounds and lethal bursts
  were scheduled. Native/server timestamps distinguish individual deaths; replay
  added no burst. Flashbang's damage/potion and ordinary primary recovery passed.
  Actual skull and night-burst frames were viewed. Creative Space was blocked
  during Q and recovered afterward; a grounded-jump acceptance is still separate.
* live1 and live2 remain failures (harness identity misuse; then ordinary-shot
  fixture positioned before a vertical movement). Their partial success does not
  make the full runs passed.
* live2 full-reference mixed-audio correlation FAILED its predefined thresholds.
  Twelve overlapping kill tails are visible in the correlation peaks, but sound
  counters are not clean actual-audio acceptance. An isolated mixed-audio capture
  still needs verification; do not silently lower thresholds or label this passed.
* pharah-live1 FAILED after unexpected Pharah->McCree/input/focus changes. The
  observed target impulse/damage is partial evidence only. Self movement, primary
  impact, protected terrain and complete Pharah regression were not accepted.
  UI actions were stopped when interference was detected.
* Final source build:38 Gradle tasks successful, including feedback/death/marker
  checks. Private installer3 fixtures, native presentation1..64 scheduling,
  proper Java-backed HTTP contract and supervisor/restoration fixtures also pass.
  These are distinct from real-world tests and human play acceptance.
* live4/result.json: selected final JAR/body15 actually repeated the12-target test
  with hero-interference guards, all12 ready/all12 dead/12 shots/12 bursts/no
  replay/primary recovery. Inspected skulls-ready.png and blood-close.png are
  actual composed original-window pixels, not diagnostic illustrations.
* ground-audio/result.json: actual bedrock-grounded Space was suppressed during
  fresh admitted Q, cancel restored ordinary grounded jumping, then three real
  primary shots emitted two hit cues and one kill. Single-kill actual MC48kHz
  mixed-audio reference correlation passed the unchanged thresholds: hit.83782,
  kill.93484. The16kHz downsampled comparison remained below its hit threshold
  and is preserved separately; overlapping live2 remains failed.
* pharah-live2/result.json: actual guarded quiet replay PASSED. Enemy target
  displacement24.977m in the isolated no-gravity fixture, self2.656m unchanged,
  target20->19.52085HP, E replay unchanged. Two original primary rockets killed
  a fresh real target, original mesh/muzzle rendered, actual hit/kill feedback
  advanced, terrain broke and both protected blocks survived. These distances
  measure the MC adaptation, not original OW physics.

Normal stop744 exposed another final-JSON rename race: compositor40's main JSON
remained at an intermediate restored snapshot although its final tmp was complete.
The stop helper now accepts only the exact hash-pinned mapped compositor40 plus a
fresh unchanged complete tmp AND actual read-only terminal proof: finished and
restored flags, inactive owner, released context/swap, all nine original user32
prologues, light release and original frame-limit bytes. Incomplete/changed state
still refuses. Actual744 strict recovery/save/exit passed;22 restoration fixtures
and3 session-stop fixtures passed. Body15 terminal recovery also has its exact
build pin. This is report recovery, not a relaxation of the restoration gates.

four-dimensions-v3/result.json PASSED on native26572: original hero recreation,
E real damage/2-second visible potion/exact50% slow/recovery/replay,12 ready
armored/absorbing targets/12 original per-shot deaths/native cadence/charge
consumption/End, slot-key filter, ordinary primary/full HP/current light passed
in Overworld, Nether, End and Twilight Forest. All fixtures cleaned. The source
profile remains8chunks/no shaders/Hollywood/1080pLow/day-night/particlesALL.
shared-heroes.json additionally PASSED actual Genji and Soldier76 nonlethal hits,
one real death each, shared sound schedules and replay deduplication. Combined
with McCree and Pharah this is four actual hero checks; all21 share the backend,
but this is not an all21-hero gameplay/skill acceptance claim.

The first four-dimensions run FAILED an
outdated<=6-shot harness assertion after acquiring31 real nearby mobs; all four
fixture targets did die, but this is not a full passing run. The current harness
uses a high isolated air corridor and12 armored/absorbing targets per dimension.
four-dimensions-v2 also FAILED: its fixed3-second charge reached11 ready markers;
the armored/Resistant/absorbing twelfth target was correctly not marked lethal
and survived at2.67392HP. This is not evidence of killing a fully ready target.
The passing v3 waited4seconds and required12 actual ready markers and deaths.
mid-sequence/result.json PASSED actual world/H-picker interruption with12-target
queues. No further old shot, lethal burst or shared sound after the changed scope
settled, no pending queue/grade/tails, and fresh ordinary20->13 damage recovered.
World interruption admitted one shot; H-picker transition admitted two before
settlement. It does not prove zero latency at the physical H keypress itself.

Final audit: native26572/creation134371359676399473, MC20808, independent11732;
six unique exact modules, source/profile guest hash a0b3b308...2c5a41f, no manifest
hash mismatch, advancing actual frames, no current matching report. Actual viewed
delivery-picker_small.png shows original animated McCree over daytime real MC.
Player grounded65/full health/no flight; fixtures/pending damage/audio cleaned.
Hollywood1080pLow/8chunks/no shaders/day-night/particlesALL retained. Both games
remain available with the independent supervisor. Full original visual/asset
parity,64-target real-duration play, all21 full kits and original crash causes
remain separate unfinished work. No new report or idle
survival proves neither historical TIMER nor distinct startup crash root fixed.
