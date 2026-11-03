# Pharah rockets and Minecraft terrain — 2026-10-18

Latest2026-10-22: [PHARAH-BARRAGE.md](PHARAH-BARRAGE.md) supersedes older node2
Q-deferred paragraphs below. Emission15 adds actual original Wave mini-rockets
and a first-factory world/session scope after an actual emission14 transition
failure. Original primary/flight/E remain; alternate node7 and complete original
presentation remain explicitly unverified. Final evidence is under
research/pharah-completion-20261022; read each actual result/identity.

## 2026-10-22 — Actual Concussive Blast adapter

Read [PHARAH-CONCUSSIVE.md](PHARAH-CONCUSSIVE.md). Emission13 retains the primary
and adds the exact original E factory; real MC swept collision, cover, non-damage
enemy/self radial impulse and cooldown/replay actually passed four dimensions.
The impulse is explicitly MC physics, not a certified original OW knockback
curve; orb/burst/audio are MC-made. Original primary terrain/splash/protected
blocks/replay passed again. Q remains incomplete on current compound-motion
variants:90 actual native factories were observed but the strict guard admitted
none, and the MC target stayed20HP. Do not promote historical Barrage tests or
this new E implementation to a claim of a fully restored Pharah kit.

Hover/Jump Jet integration and its measured limits are now documented separately
in [NATIVE-FLIGHT.md](NATIVE-FLIGHT.md). Concussive blast and Barrage are pending.

Pharah primary fire now travels through the real MC world, damages creatures and
explodes against terrain. Original offline OW retains its hero, hands, ammo,
animation, firing timing and attack audio. Added projectile models/trails remain
disabled by the user's earlier request; the MC explosion is the newly requested
terrain effect. This does not complete every hero or all Pharah abilities.

## Native evidence and admission

- Hero `02e0000000000008`, primary script `0580000000000023`, Volley node10,
  projectile resource `0400000000000033`. The root script002b contains other
  attacks and must not be mistaken for the primary launcher.
- Actual factory callback: type1, status8, return0, native speed35, lifetime5,
  range100. This offline path does **not** create an initialized native projectile.
  MC supplies the missing flight/collision using the confirmed factory event.
  Button presses and ammo changes are never the attack source.
- Reflected Volley impact gives direct40; its explosion definition gives splash80.
  Two native explosion rings are radius0.5/factor1 and radius2.5/factor0.125.
  The adapter uses linear interpolation between these measured endpoints; the
  exact native interpolation implementation has not been independently traced.
- Preparation verifies declared STU field/type chains, primary graph node,
  literal vtables/values and both ring records. The native callback rechecks
  current owner/model, actual config35/5/100, damage/ring pointers and values,
  native direction, fresh MC body/session/world and generation before publication.
- Journal kind3/flags57 identifies a factory-confirmed rocket. Identity includes
  owner, Volley, native tick, shot and pellet. Guest admission pins its resource,
  numeric calibration and current world. It cannot become a hitscan or beam.

## Minecraft resolution

The server sweeps every flight segment to the first loaded block or creature,
with a100-block travel cap. It retires the flight **before** the explosion callback,
so replay cannot repeat damage or block destruction. Missing/unloaded corridors
retire it without exploding or generating terrain. World/session changes clear
old flights through the existing combat owner guards.

Creature damage uses the existing10:1 OW-to-MC HP conversion. Direct and splash
are combined in one damage operation per victim; dragon parts share their actual
damage owner. Splash uses MC exposure before terrain destruction and the measured
0.5..2.5 radius endpoints. Creative invulnerability remains unchanged.

Terrain uses the vanilla MC explosion, strength2.5, no fire, original blast
resistance, drops, particles and sound. Strength2.5 is an explicit MC terrain
adaptation, not an OW terrain parameter. Vanilla explosion entity damage and
knockback are disabled here because the calibrated damage has already been
applied. Bedrock and other unbreakable blocks are excluded. Neighboring blast
chunks must already be loaded.

Factory diagnostic history retains only256 recent observations, independently
of the acknowledged attack queue, to stay within the guest's524KiB JSON limit.
Diagnostic eviction is not attack loss.

## Verification on this machine

Guest full build/check,35 Python binding/startup tests, the independent Java HTTP
contract entry point and native emission/beam/MinHook restoration fixtures passed.
The native fixture exercises Genji -> McCree -> Pharah -> Genji, rejects wrong
speed/world, deduplicates actual firing identities and restores original hooks.

Real composed-window test in the existing Fresh15C End dimension, native PID6952:

- Native ammo6 ->5; one admitted event, zero rejected events, one explosion.
- Temporary stone wall23 ->22 stone blocks; bedrock and obsidian both intact.
- Nearby villager20 ->14.785919 HP; outside-radius villager remains20.
- Replaying the real batch preserves block counts, explosion count and health.
- An independent direct-hit test on PID21204 gave20 ->8 HP and replay stayed8.
- Inspected real capture/contact sheet shows original Pharah hands/HUD, firing
  animation, the hole and MC explosion particles. Temporary walls/creatures were
  cleaned. No existing terrain/buildings were used as the destructive fixture.

Private evidence: `research/pharah-explosion-live-result.json`,
`research/_archive/2026-10/pharah-explosion-live.mkv`, `research/_archive/2026-10/pharah-explosion-contact.png`,
`research/pharah-direct-{before,after,replay}.json`. These PIDs are test identities,
not current-process claims. Read session-status.json for the live process.

Reproduce after backing up the private profile: choose native Pharah, fly into
loaded empty air, POST `/combat/test/rocket`, then run
`.venv/Scripts/python.exe tools/verify/verify_live_pharah.py --pid <verified-pid>`.
POST `/combat/test/cleanup` afterwards. The fixture refuses occupied blast space;
the script still fires the actual original weapon rather than submitting shots.
