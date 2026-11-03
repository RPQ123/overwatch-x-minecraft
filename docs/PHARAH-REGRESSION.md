# Pharah explosion, charge and E repair — 2026-10-22

The user's current instruction is **code only while using this PC**. No game
was launched, stopped, focused, injected into or driven. No current profile was
modified. Before edits, source was backed up to
~/.universal-modder/backups/pharah-regression-source-20261022/20261022-194702.zip.
Existing dirty/untracked work, voices, private assets and six native owners remain.

Built source guest SHA256:
b0e9c44ef6797fbe83b47cf16fdbd769e0ef6f43804f77ce5d693268229da4ae.
Installed/running guest still has the earlier locomotion build:
fe2924bdf567b07905eb1c937f6e8bdef3bcec33b5edd3aeee5eb789274767ca.
The read-only audit observed native13744/creation134371425293318036 with six
unique unchanged DLLs. A subsequent live session now exists; the earlier no-game
audit is historical. See research/pharah-regression-20261022/code-final-audit.json.
This build has **no in-game acceptance or deployment**.

## Missing primary explosion

Actual MC1.21.1 source shows that NativeRocketExplosion's extra-boolean overload
was inherited World.createExplosion. It bypassed ServerWorld's overload that
sends ExplosionS2CPacket to nearby clients. It also selected SMOKE for both
particle types. Real server damage/terrain was not proof of client explosion
presentation or sound. Private orange render sprites are a separate effect.

Primary Pharah rockets now call the synced ServerWorld overload **without that
boolean**, using EXPLOSION/EXPLOSION_EMITTER. Custom direct/splash damage still
resolves once; vanilla behavior refuses further entity damage and has zero
knockback. Terrain strength/resistance, drops, protected blocks, loaded-chunk
checks and replay admission are unchanged. No extra fire is enabled.
Barrage retains its own accepted orange impacts/mini-rockets. Other armory
presentation stays on its previous route. This restores the MC explosion style,
not an exported original OW effect graph or pixel-identical reproduction.

RocketExplosionTransportCheck inspects the actual pinned MC dependency with ASM,
finds the declared ServerWorld method creating ExplosionS2CPacket, and verifies
the compiled primary adapter calls its exact descriptor. It also checks the
separate non-primary route remains. This guards the real dependency contract
without inventing a ServerWorld fixture or a game screenshot.

## Charge publication and lost credit

NativeChargeController used Context object reference equality after its reads.
The client replaces that object each20Hz tick: a healthy75ms skill/meter read
could therefore be rejected repeatedly despite identical identity. New
NativeChargeScope compares pid, generation, model, hero, world and reset session.
Both captured/latest samples must remain within150ms; a new publication cannot
extend an old sample's permission. NativeMeterReader's process creation, variable
membership/type and expected-value checks remain at the actual write.

The old meter-null path reset the damage-credit baseline, discarding earned
credit during temporary read/binding failure. NativeChargeBudget now preserves
pending credit only within that verified session and spends it once after an
accepted write. Failed compare/write keeps it for retry; integer fractions are
retained. Active/unknown Q, full meter, changed scope or a reset damage counter
cannot bank old credit for the next ultimate. Existing5 native-points/second
idle policy, native costs and MC damage conversion are preserved. This is not
a faster refill or proof that5 was reverse-engineered from every beta hero.
Genji remains separately owned; body15 notifications and76Visor are unchanged.

Checks reproduce20Hz publication during75ms work; stale/future and all identity
changes; ten seconds of passive charge; damage across unavailable/failed writes;
integer/float values, cost bounds, active Q and resets. Read-only old live Pharah
was observed with a ready meter near full. That does not prove a permanent stall
or verify the new code; the source defects concern intermittent starvation/loss.

## E direction, exposed parts and visual pressure shell

Native script007b/node3/resource010f remains the shot authority, retaining actual
60m/s speed,8m gameplay radius and original12s cooldown. A key cannot create a shot.
The small custom DamageSource(player) hit could add ordinary attacker-directed
LivingEntity knockback before the radial E vector. The new path retains pre-hit
velocity and applies only the declared radial vector after a surviving, unmoved
target's damage reaction. Dead/removed/teleported targets are not pulled back.
Real attribution, armor/immunity and kill feedback remain.

Multipart victims select their strongest exposed part **before** deduplication,
then receive one hit/push per owner. A blocked first part cannot hide another
exposed part. Vanilla explosion exposure replaces the redundant center-only ray;
full cover still has zero exposure. Terrain sampling requires loaded chunks and
bounds part boxes to64m per axis. E does not destroy terrain. Exact OW push
integration/resistances and unusual giant/mod bodies remain uncertified.

The earlier user custom enemy1.5x boost and at most.5MC HP/5OW-equivalent damage
remain; self propulsion retains its scoped impulse/decay. They are custom rules.
[Official July2024 notes](https://overwatch.blizzard.com/en-us/news/patch-notes/live/2024/07/)
describe returning base E to0 explosion damage/8m radius; current perk damage is
not silently substituted into the offline beta/custom adapter.

The [official ability demonstration](https://overwatch.blizzard.com/en-us/heroes/pharah/)
was privately downloaded and its contact sheet actually viewed. It shows a small
flight object and pale violet pressure bubble. The flat cyan square is now
rounded MC-made geometry plus a fading expanding shell and a little residual
cloud. Visual shell lasts.4s/below2m; gameplay radius stays8m. These authored
values are a visual adaptation, not measured original parity or an exported
OW E model. Original animation/cooldown and existing Chinese callouts remain.

PharahConcussiveBursts accepts real loaded E impacts only, deduplicates, bounds
and expires them, and clears on world/player/source/model changes. Projectile
views now carry model identity; primary/Barrage/E reject departed-model views.
Rendering never applies damage or impulse. Particle setting remains ALL.

## Verification and pending acceptance

Final full build/check passed43 Gradle tasks (38 executed/5 up-to-date), including
charge scope/budget, actual-MC explosion transport and E burst lifecycle. Logs:
build-accepted.log and explosion-transport.log. Proper bridge/test_contract.py
passed its Java-backed fixture (http-contract.log). Environment prerequisites,
exact offline executable hash and native compiler passed. No native DLL rebuilt.
These are headless checks, not actual new MC collision/physics/play acceptance.

The first UM contact command failed because ffmpeg was absent from PATH; using
the already installed UM ffmpeg for that command produced official-e-contact.jpg.
Nothing was installed and no UI input was sent. Reference URLs are pinned in
reference-source.json. Private media/game assets stay outside commits.

After the code-only restriction is lifted, verify actual visible primary burst/
audio and single damage/terrain; timed idle/damage charge through Q/End; E front/
behind/partial/full cover and multipart pushes; replay and hero recreation in
Overworld/Nether/End/Twilight; fixture cleanup and all strict restoration gates.
No180FPS, original full E parity, crash-root-cause fix or new live deployment is
claimed. Source/profile/module identities and old runtime observations are in
code-final-audit.json, not a successful live acceptance report.
