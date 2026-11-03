# Pharah E real-world adapter and remaining Q gap — 2026-10-22

Latest code-only repair: read [PHARAH-REGRESSION.md](PHARAH-REGRESSION.md).
E now avoids ordinary hurt knockback contaminating radial push, chooses exposed
multipart victims once and uses an MC-made round orb/pressure shell from inspected
official footage. Prior1.5x enemy/.5MC HP custom rules remain; exact original
physics/model export is not certified. Latest build is not game-tested/deployed;
earlier live receipts do not accept it. Older no-damage/center-ray/square-orb
statements below are historical.

Latest2026-10-22: [PHARAH-BARRAGE.md](PHARAH-BARRAGE.md) supersedes older node2
Q-deferred paragraphs below. Emission15 adds actual original Wave mini-rockets
and a first-factory world/session scope after an actual emission14 transition
failure. Original primary/flight/E remain; alternate node7 and complete original
presentation remain explicitly unverified. Final evidence is under
research/pharah-completion-20261022; read each actual result/identity.

Current emission13 adds the actual Concussive Blast factory to the existing single
native observer. It does not install another hook or manufacture an attack from E.
Native primary rockets, flight/fuel/Jump Jet, animation and Chinese Q remain.

## Source, rules and declared adaptation

The current guarded beta model's script007b/node3 declares resource040000000000010f,
speed60, lifetime5, range100, no gravity, radius8, scale1 and12s cooldown. Its typed
health-modifier receipt amount is1 and knockback inline slots are8/1/1/1. This does
not establish the semantics/units of all knockback slots. Python preparation
checks the real metadata/current owner and exact measured profile. The existing
native factory callback rechecks actual owner/model/script, resource, flight,
radius/scale and receipt amount before publishing effect3. Guest protocol accepts
effect3 only from observer13 and this exact calibrated tuple.

Gameplay deliberately applies no health damage or terrain destruction. The
[official July2024 notes](https://overwatch.blizzard.com/en-us/news/patch-notes/live/2024/07/)
describe returning Concussive Blast to its earlier0-damage/8m-radius behavior.
Those patch notes are a semantic reference, not proof that every beta parameter
or its knockback integration is identical to2024/current OW.

MC sweeps the real projectile corridor to the first loaded collision and retires
the flight before resolving its burst. Actual entity/part ownership, cover rays
and MC exposure determine which living targets receive a radial velocity impulse.
The caster can be pushed as well. This is an explicit MC physics adaptation:
full-exposure unit MC blast impulse, linear radius falloff, normal MC travel for
other mobs, and a scoped self impulse through Pharah's collision-resolving mover
with0.8/tick decay. The exact original OW impulse curve, tank resistance and
self/enemy scaling are still NOT certified. The undocumented1/1/1 is not relabeled
as meters/second. No health event or creative invulnerability bypass is used.

Self cues require current player/world/native model/source, first-person focus
and150ms freshness. Replays deduplicate. Hero/world/focus changes clear residual
movement; no old impulse may enter a new model/world. The original native flight
import no longer erases an admitted MC self push. Creative flight also resolves
the additional displacement with Entity.move. Original native flight physics and
the user's held-Space lift tuning were not replaced.

Presentation is a compact MC-made cyan/silver orb and white cloud burst with MC
audio. It is NOT an exported original OW E mesh/effect. The original native E
animation and HUD cooldown remain native. The tiny flying-orb visual itself has
not been separately certified against official video size/shape.

## Actual acceptance and failures

Private evidence: research/mccree-deadeye-parity-20261021/pharah-e-four-dimensions
passed Overworld, Nether, End and Twilight Forest after actual Genji->Pharah
recreation. Each run admitted exactly one E, blocked an immediate cooldown press,
pushed the real AI-active zero-walk-speed target approximately14.65m and caster
approximately2.656m under the declared MC physics, retained20 target HP, had no
rejected journal events, and replay made no second detonation. Test objects were
cleaned. These distances are the isolated no-gravity test, NOT measured OW values.
Real daylight composed-window contact in pharah-e-live was actually inspected:
native launcher/animation/HUD and visible MC burst/displaced villager coexist.

pharah-final/result.json additionally passed an actual wall impact: the target
behind the wall remained stationary and20HP; E did not pass its effect through
cover. The original primary also passed again under emission13: one terrain
explosion,23->22 temporary stone blocks, two protected blocks intact, splash
target20->14.7859..., outside target20, and replay unchanged.

The initial E test used the old permanently immobile NoAI damage fixture. Self
push1.4229m and one E were observed, but that target did not run vanilla movement.
It was a failed physics test. A harness path error overwrote its full JSON/video
with the later movable-target run; pharah-e-noai-failed-summary.json explicitly
records only console-observed values and that evidence loss. Do not claim its raw
failure recording was retained or that it passed.

## Q is still incomplete

pharah-final actually captured90 native Q factories for resource0052, while the MC
target remained20HP and admitted-shot delta was0. Current nodes2 and7 use two/three
compound motion definitions (types855ce717 and78aad781); the strict simple-gravity
adapter refuses them. Literal profiles separately show node2 direct10+splash30,
rings.5/1.5/.3; node7 direct15+splash30, rings.5/2/.16666. The supplied client has
the attack events and animation; it lacks an initialized projectile entity on
this offline factory path. No straight-line guess was deployed as original Q.

Historical90-shot successful tests on another old model are not current parity
acceptance. Following the user's permission to defer difficult/server-dependent
skills, retain this explicit Q gap. Next work is trace the actual compound motion
implementation, preserve native per-projectile directions/timing, then verify
real MC collision/cover/damage/charge/End and switching before enabling it. Do not
claim that Pharah's full kit or every native server mechanic has been completed.
