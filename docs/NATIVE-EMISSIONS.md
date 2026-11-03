# Original projectile initialization events

The passthrough observes successful original projectile initialization inside the supplied offline Beta 0.8.0.24919. The v4 source now transfers acknowledged events into Minecraft's integrated server for swept block/entity collision and damage. This is a verified Genji increment, not a finished combat bridge.

## Creation and initialization are different boundaries

The original Genji Volley Shot queues a job whose callback is RVA `d455e0`. It calls a precreation pass, and its per-projectile factory at `d354b0` returns a native entity with component 0x27. Those initial entities have owner zero and scene position zero; forwarding them immediately as completed physical projectiles would be premature. A bounded first probe recorded three distinct entities for left burst and three for right spread, but demonstrated that missing initialization.

The later original initializer at `d35c20` receives callback context, native entity and original projectile context. Its core initializer `1032420` assigns component 0x27 owner at +0x18, initial position at +0x40, and actual initial velocity at +0x50. Velocity is the original direction times the native Volley speed, plus original inherited velocity. Capturing after this initializer therefore supplies a completed native physics result. The general scene transform may still remain zero until a later movement stage; it is diagnostic and is not used as the physical origin.

`native_emission_probe.cpp` forwards the original arguments and return unchanged through the supplied, already-loaded MinHook library. It observes only the verified local Genji model and projectile resource `04000000000007ca`, with native model/admin/creation identity checks, a measured unmodified function prefix and a three-minute automatic restoration. It never initializes/uninitializes the shared hook library in the real game and disables only its own target on stop. Original code bytes and any disabled trampoline are preserved appropriately for in-flight calls.

## Event identity and evidence fields

The bounded journal retains at most 512 distinct native entity IDs. Entity IDs include generation; a repeated original entity cannot become a second event. Each retained event also receives a monotonically increasing journal ID. Capacity overflow stops capture explicitly instead of overwriting unconsumed events. Native owner, resource, original tick, shot/pellet indices, actual initial position/direction/velocity and an independent fresh MC body snapshot are recorded. MC source generation, world identity and acknowledged native generation stay attached to that snapshot.

Flags: bit 0 means a fresh matching MC body/world snapshot; bit 1 means native physics position/velocity passed the measured initialization checks; bit 2 means native projectile owner equals the local original model; bit 3 means the native model's feet position was available. The currently reserved status field is zero in the initializer observer and is not asserted as a native return status. Scene position zero is retained only as a diagnostic. The 256-byte encoder is preparation for a transport, not an active MC consumer.

Raw original context/component bytes in local reports are private research evidence. They are not game assets for redistribution. The public mod code/build scripts do not contain captured game data.

## Actual supplied-client results

Original PID40552 and MC PID43676 remained alive. The first factory observer completed with 6 calls/6 retained distinct entities, zero errors, and normal restoration. Left was shot indices 0,1,2 with pellet 0; right was shot 0 with pellet indices 0,1,2 and distinct spread directions.

The completed initializer observer then recorded 27 calls and 27 distinct initialized projectiles, zero filtered/refused events, zero failures and no capacity overflow. Every event had all four evidence flags set and original owner 2147485828. Actual velocity magnitudes ranged 59.99999594..60.00000261, matching the real `m_projectileSpeed` config value 60. Original initializer bytes were independently read back and matched the original prefix after automatic restoration. Source record: private `research/native-emissions-v2-40552.json`.

Some actual attacks occurred while the user was operating the game. When Sky reported user input, the agent did not retry the blocked action. The 27-event run is an observation of real original play, not a claimed fixed script of 27 agent-generated attacks.

## Native damage binding

`WeaponBindingReader.impact_damage` follows the real reflection chain from WeaponVolley to projectile-impact data, `m_modifyHealth`, and `m_amount`. It checks each declared and actual object type and reads the dynamic resource path without executing native configuration getters or evaluators. Both actual Genji nodes 6/31 resolve to `0d800000000001dc`, whose current native integer value is 35. This is the original impact damage amount binding in OW HP units; it is not yet a native-hit or MC-hit result.

The existing ammo reader shares the same bounded dynamic-path decoder. Seven binding tests pass, including the typed damage chain and rejection of a wrong intermediate type. Exact live binding evidence is private `research/native-genji-impact-damage-binding-verified-40552.json`.

## Build, run and next slice

```powershell
./tools/build_native_emission.ps1
python tools/attach_hand_depth_probe.py --pid ORIGINAL_PID --emissions
python tools/stop_passthrough.py --pid ORIGINAL_PID --emissions
```

The loader requires the current verified compositor v9, body v5 and weapon gate v5. Retired modules need current-process restoration records; current callback-owner reports must be fresh and healthy. It refuses to reload the same observer DLL in the same process. A real MinHook fixture process verifies original argument/return preservation, capture after original physics initialization, exact code restoration and a successful subsequent original call. Journal tests verify identity/deduplication, ordering, capacity failure and fixed wire IDs. These are independent checks, separate from actual native runtime evidence.

## Acknowledged transport and actual MC damage, 2026-10-15

The current DLL is `owmc-native-emission-v4.dll`, with an eight-hour lab ceiling. Its atomic JSON journal retains at most 512 unacknowledged events; a separate lifetime set retains native entity identity after ACK (maximum 1,048,576). MC acknowledges only the ordered prefix admitted by its integrated server, using a 32-byte OWACK001 record containing source epoch, prefix and the current MC PID. Wrong epochs/PIDs cannot retire the source. Capacity and future-ACK errors stop capture explicitly.

Request version 2 binds the original weapon script, varbag bucket, resource ID and typed live damage value. Each capture checks that binding and samples the current native amount (35 OW HP) and original lifetime (5 seconds). Flags bit 4 now means this damage binding passed. Current reports require probeVersion 4, all five evidence flags, a fresh heartbeat, native process/epoch/generation identity, matching current MC process/generation/save/dimension and ordered event IDs.

MC maps each native origin relative to native feet into the paired real MC feet, with the difference between MC eye height and the measured original idle eye height (1.2). Original initial velocity remains unchanged; an actual aim comparison measured a dot product approximately 1.0. MC performs swept block and living-entity AABB intersections, resolves the nearest hit, removes the projectile before the damage callback, and maps OW HP to MC HP at 0.1. A custom damage type bypasses vanilla hurt cooldown so the three original pellets can each apply damage. Armor and other normal damage handling remain active. This is a point-projectile hit volume; original projectile meshes/effects and native hit-shape calibration are still outstanding.

Actual original PID43764 / MC29300: 18 native emissions were accepted and acknowledged, with 15 block hits, three entity hits and 8 actual MC HP lost. The victim species was not recorded, so this is not a controlled villager accuracy claim. Replaying the retained real batch three times increased duplicate count by three while entity hits remained three and actual damage remained eight. Evidence is private `research/native-combat-v4-proof/`. Subsequent MC37352 resumed at acknowledged cursor 24 without replaying the old attacks.

A fixed-villager/temporary-wall fixture is available through the localhost test endpoint. Its target stays at its original location; it never follows a shot or later camera turn. Cleanup removes only its own target and restores its recorded blocks. A controlled live wall/villager firing test remains outstanding because coordinate mouse injection changed FPS aim. Synthetic corridor checks are separate evidence and must not be substituted for that live test.

Hero recreation currently invalidates body/weapon/emission bindings. In the observed PID43764 session, these adapters stopped when the user reselected a hero, and the original process subsequently exited. The exact exit cause is unproven. A fresh native process is required by the current loader; do not reload a stopped same-target MinHook observer or ignore the identity errors. Required startup order: enable original Demo, load resources, load a map, enter original Genji, then compositor/body. Initialize both lazy Volley states with real left/right actions before weapon gate and emission attachment. The compositor now refuses attachment before Demo and the actual Genji weapon graph exist.

Pharah, ultimate, complete hero recreation/recovery, original projectile visuals and sustained combat acceptance remain full-goal requirements.
