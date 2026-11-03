# World, dimension and hero lifecycle regression — 2026-10-19

User request: investigate/fix hangs when changing worlds or heroes. This remains
the real offline OW + real MC route. No private Wraith/lifetime experiment enabled.

## Fixes

- Native body source loss now holds the last verified position with zero velocity
  and grounded state after a body has been established. Loading/exiting MC no
  longer releases the original actor to fall and die in the old native map.
- A replacement MC source can resume another valid save/dimension under the same
  native host generation. Same-world resumes retain the displacement origin;
  changed-world resumes let the normal world edge rebase it. Wrong host, absent
  identity and out-of-range same-world displacement remain rejected.
- World stability requires two distinct actual body publication sequences. Many
  native callbacks rereading one packet cannot declare a new world stable.
  A source gap or source/generation/world change resets stability. Unready zero
  world IDs are rejected during decoding, before they can disable the body owner.
- Supervisor hero refresh identity now includes MC source PID, guest generation
  and native host generation as well as hero/model/world. Same-hero reloads
  rebind health/abilities after the new source is stable. Reopen monitoring keeps
  a creation-aware psutil process identity, records the actual reopened world and
  refreshes the loaded guest JAR manifest after the previous MC process exits.
- Client disconnect explicitly clears all native session/controller bindings and
  initial creative/respawn state. Reopening the same save with the same player
  UUID and unchanged native hero/model still creates fresh client bindings.
- The opted-in Twilight startup backup prompt guard is per screen instance,
  allowing a second real integrated-server load in the same MC process.

Body reports now include sourcePid/guestGeneration/hostGeneration/sourceAgeMs.
No second callback owner or loaded DLL replacement was used. Body DLL remains
v10 by filename; use loaded hash, not that filename alone, to identify this build.

## Backup and repeatable tests

Normal restoration/stop/save preceded the full profile backup:
`<USERPROFILE>/.universal-modder/backups/world-hero-switch-20261019/20261019-093627.zip`
(808 files, 731.1 MB). Original settings are privately snapshotted in
`research/_archive/2026-10/world-switch-original-settings.json`.

Stress tests used two copies of the existing mod-pinned save, named
`Overwatch Twilight Switch 20261019 A` and `... B`. The original Trial A save was
not used for the dimension/reload stress matrix. Keep the Twilight mod present.

`tools/verify_world_hero_switch.py --pid <verified-offline-pid>` runs four real
dimension transfers, an immediate native McCree selection during each transition,
and subsequent McCree/Genji movement, target damage and duplicate replay checks.
`--reload` tests same-process integrated-server reload, including unchanged-model
quick melee. `--restart-world "Overwatch Twilight Switch ..."` normally saves and
exits MC, lets the independent supervisor reopen it, and keeps OW running.

The server dimension endpoint and reload endpoint require the opted-in Twilight
trial, creative mode, and the exact `Overwatch Twilight Switch ` world-name prefix.
They are disabled on ordinary Trial A. Dimension tests use actual teleport/world
lifecycle into empty air (Nether above roof, End above island), not physical portal
traversal or full ordinary ground play. No synthetic native shots/body were used.

## Actual passing evidence

- Four dimensions (Overworld/Nether/End/Twilight), each McCree + Genji: 8 rows.
  Full declared native HP, real MC20 HP, stable body, actual W movement, McCree
  target20->13, Genji three-shot20->9.5, duplicate replay unchanged/zero rejects.
  `research/world-hero-switch-24424-1792374358459733800.json`.
  Composed Nether/End screenshots inspected; native Genji hands/ammo/HUD retained.
- Same-process/same-save reload: MC18968 and native17472/model2147485755 unchanged.
  Post-reload Genji shots20->9.5 and quick melee20->15. During the sampled source
  gap native HPmin200, Yspan0, max source age1060ms.
  `research/world-hero-switch-17472-1792374972861342500.json`.
- MC process restart, same save: MC18968->5388, OW17472 unchanged, sessionResumes1.
  26 gap samples, native HPmin200, Yspan0.801758, max age19980ms; both heroes'
  actual movement/fire/replay passed.
  `research/world-hero-switch-17472-1792375026354096200.json`.
- MC process restart, different save B->A: MC21112->13416, OW17472 unchanged,
  real world ID3290572199857895851->4318740326124827386. 24 gap samples,
  HPmin200/Yspan0.0048828/max age18695ms; McCree and Genji attacks/movement pass.
  `research/world-hero-switch-17472-1792375272053834700.json`.

These are bounded lifecycle/weapon checks, not all heroes, all portals, full boss
fights or sustained180FPS acceptance. Loading still has an intentional wait;
the native actor survives it and the bindings recover afterward.

## Failed test harness attempts retained

The initial test-only reload endpoint omitted `c.world.disconnect()` before
`c.disconnect()`. The client waited for an integrated server it had not asked to
stop. Test clone MC15336 hung black; native24424 held position/alive200HP with
body failures0. Thread dump and local bytecode inspection establish the wait:
`research/_archive/2026-10/switch-reload-thread-dump.txt`, `research/_archive/2026-10/mc-client-disconnect-javap.txt`.
Normal stop restored native callbacks and ended OW/supervisor. MC normal shutdown
timed out45s; only the exact verified test-clone Java process was then terminated.
`research/_archive/2026-10/switch-reload-recovery.json` records this exceptional recovery. Original
save was untouched. Correct sequence is now `c.world.disconnect();c.disconnect()`;
subsequent same-process reload and all later normal saves/stops succeeded.

An A->B restart report `...17472-1792375131267117500.json` falsely classified the
legitimate new-world virtual-coordinate rebase to1000 as a fall: the body JSON
sample lagged the already-live new MC by its1s report interval. Kept failed report;
sampler now excludes the terminal new-live-source sample from source-gap bounds.
The reverse B->A actual test above passed with both weapons afterward. Earlier
aim/async-cleanup/nullable-player harness failures also remain in ignored research.

## Final ordinary runtime

Restored original settings byte content and selected Trial A. Normal stop before
the final native build; 8 native fixture suites passed, including zero-world-ID
decoding. Guest27-task build/check, Java-fixture HTTP contract, and33 supervisor
Python regressions passed. The final decoder zero-ID guard and supervisor process/
manifest hardening were loaded on the final cold start; dimension stress preceded
those final narrow guards. Final cold-start native Genji shot20->9.5/replay passed:
`research/_archive/2026-10/world-switch-final-native-fire.json`.

Current native7116 / MC24652 / independent supervisor18072, startup
`research/_archive/2026-10/world-switch-final-startup.log`. Settings remain1080p/OWLow/8chunks,
no shaders/day-night/F6flight, same seed. Original animated Genji picker over real
Twilight forest inspected in `research/_archive/2026-10/world-switch-final-picker_small.png`.
Player20HP/alive/onGround/flightOFF at approx(57.500,25,10.898); test targets,
blocks/bosses/probe cleared, mobGriefingtrue. All six actual mapped native DLLs
checked, four owners enabled/failures0, private lifetime/skill/factory probesOFF,
loaded/source/profile hashes match, frames advance, phase/hero/model current.
`research/_archive/2026-10/world-switch-final-status.json` passed. Picker ready=false is expected.
Games and independent background remain available after the agent turn ends.

Next: bounded other-hero lifecycle regression or the cached yellow H prompt;
full Hydra native weak points/progression/full kits/performance remain open.
