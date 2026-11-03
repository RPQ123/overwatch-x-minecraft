# Soldier76 Helix presentation and actual transport — 2026-10-23

The offline24919 weapon produces ONE native projectile factory for RMB:
resource040000000000072c, speed50m/s, range100. Typed original impact/blast
declarations supply40direct+80splash, radius3 and gravity0. The three missiles
are visual strands around that single authoritative path, never three blasts.
Other Soldier bullets/resource03d4 remain original17HP hitscan. Distance falloff
and headshot parity are still unverified; this increment does not claim them.

## Reference and presentation

The [official Soldier76 page](https://overwatch.blizzard.com/en-us/heroes/soldier-76/)
was fetched directly after the web reader returned403. It embeds the Helix Rockets
demonstration with filename
OVERWATCH_WEBSITE_CHARACTER_CAPTURE_Soldier76HelixRockets_WEB_16x9_1920x1080p30_H264.mp4.
Source HTML and actually inspected private frame sheet are in
research/four-dps-20261023/official-soldier76.html and helix-official.jpg.
The clip shows blue-white spiral trails and a blue impact; its modern gun differs
from this beta gun. It is a visual reference, not a beta numeric oracle.

HelixRocketRenderer draws three small silver/cyan bodies and blue-white winding
ribbons around one admitted NativeShotSimulation flight. HelixPresentation keeps
the three-strand centroid on the unchanged path. Radius.12m,26rad/s and the visual
near-muzzle convergence are authored MC presentation values, not certified native
effect-graph values. Launch basis/FOV is frozen per shot so turning the camera
cannot drag an old launch sideways. Original beta gun/HUD/animation are preserved.
Approximate rest aperture(.565,.575) comes from the actual composed beta frame;
animated bone/recoil attachment and exact original mesh/effect parity remain open.

The renderer requires current real player/source PID/host generation/world/model,
live first-person input and the exact072c resource. Active flights alone produce
bodies; keyboard input creates nothing. New source/world/model clears launch state,
and inactive flights disappear. Only visuals change: no extra damage entity.

## Real missing explosion transport repaired

The previous generic armory route called inherited World.createExplosion with
an extra particles boolean. That overload did not produce ExplosionS2CPacket:
real server damage could occur without the client explosion burst/audio. Soldier
Helix now calls the actual ServerWorld synced overload, retaining explicit damage
once and no terrain destruction. Compact vanilla explosion plus electric sparks
are MC-authored impact feedback, not the official blue shader. Pharah's accepted
synced primary route is preserved; other armory routes were not silently changed.
The bytecode check resolves the actual dependency's packet-producing override.

## Actual bounded acceptance

native19684/MC8848, body25 and guest
8e9bbb8bb9be7757cc926bca3746a9b3ffb46ec7079294f0c88d55e44f4dbe80.
Research helix-live-v1 passed/cleaned: one admitted factory, one blast, target
20->8/12MC damage, one three-strand visual launch across23actual render frames,
replay inert, immediate cooldown press inert, actual covered target20, and
post-skill rifle20->16.599998. Actual recorded contact sheet was inspected;
the winding blue strands and client explosion are visible.48 Gradle tasks passed.
This bounded pass is distinct from full-kit, survival self damage, exported asset
parity and sustained stability. Current identities come from TAKEOVER/session.

Reproduce with .venv/Scripts/python.exe tools/verify/verify_soldier_helix.py --pid CURRENT
--output research/NEW-DIRECTORY, using the fully modded disposable Switch world.
