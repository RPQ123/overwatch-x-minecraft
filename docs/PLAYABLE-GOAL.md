# Playable passthrough goal

Current runtime is the separate Twilight trial24880/MC21484 (supervisor14768);
Initial-picker guest exit/recovery and gameplay shared recovery now pass
(INITIAL-PICKER-RECOVERY.md). The world/hero lifecycle fix and bounded four-dimension/two-hero, same-process reload,
same/different-save MC restart tests passed; see WORLD-HERO-SWITCH.md. Tracer Blink four-dimension/model-recreation and pistol/replay checks also pass
(BLINK-LIFECYCLE.md), without new production code. Original
Trial A/settings restored and animated picker inspected. These checks do not
establish all-hero/physical-portal/performance acceptance. See TAKEOVER.md
and TWILIGHT-FOREST.md. Actual portal entry, selected hero stability/native
damage in TF, separated direct/explosion semantics, supervised hero switching
and real mod/server multipart fixtures passed. Current Pharah optional armory
extensions remain deferred; validated primary works. Actual Genji shots at real
Naga segments and original dynamic boss-bar pixels now pass a controlled air lab.
Native projectile/melee/Tesla categories and teleport-safe rocket splash now pass
actual Enderman tests, with ordinary weapon/terrain regressions. Hydra native
shots/full boss fights and full hero kits remain open. An hourly thread heartbeat
continues incremental work; do not equate it with completing the historical goal.

Latest scope decision,2026-10-19: user permits postponing difficult or unavailable
server-dependent heroes/skills. Current verified slices and explicit deferrals
are in ASSAULT-DEFENSE.md; current-machine runtime in TAKEOVER.md. Do not treat
this scope reduction as proof of the historical full-goal acceptance below.
Unfinished private Wraith probes are disabled in ordinary play. Normal session
30608/MC30100 passed startup/fire smoke checks and was left on the original
Genji picker over MC; this is separate from sustained full-kit play acceptance.

User explicitly requested a persistent goal on 2026-10-15. The goal remains active until the real two-process build can be played normally. A screenshot is evidence of a rendering slice, not goal completion.

## Acceptance gates

1. Continuous full MC scene behind original OW hands/HUD, native animations retained, smooth turning without scene slip/disappearance, bounded source age and correct image/pose identity. Start/stop/resize/menu/source-loss paths preserve the original client.
2. MC owns walking, gravity, landing and block collision in an independent complete save. The old OW map no longer constrains movement in fusion mode. No periodic competing position correction or floating.
3. Native-confirmed Genji throws damage actual MC creatures, exactly once per projectile/event; native ammo/reload/animations agree with effects. Native Pharah rocket events damage creatures and destroy real MC blocks. Buttons alone are not verified attacks.
4. Hero health, abilities, death/respawn and creative block keys operate consistently. Character/skill coverage must be recorded individually; never silently substitute approximate weapons/HUD for unavailable native behavior.
5. A reproducible launch/stop flow and sustained actual play test, with errors, latency and remaining limitations recorded. Both games stay in the supplied offline lab.

## Verified starting point

Actual MC framebuffer/depth transport and standalone D3D11 verification pass. The original OW client rendered one real MC background frame behind exact original idle Genji hand pixels and native HUD; three-frame automatic restoration succeeded. Source images and native source frame IDs are recorded in PASSTHROUGH.md. Continuous presentation, camera sync, MC movement and native combat are not yet passed.

## Current implementation order

- Versioned native world-camera mapping and paired MC image acknowledgement; test direction/roll/FOV and restart/stale behavior with an independent synthetic host and real MC.
- GPU depth-pair hand mask and reusable world textures; continuous bounded native test with a stop event and source/menu/resize gates, retaining original HUD drawing.
- MC-authoritative motor bridge with movement/ability intent, then native combat-event discovery and server effects.
- Sustained user play, per-hero acceptance and reproducible launcher.

All GPU work stays on the original render thread. Worker threads exchange CPU snapshots only. Retired original draw-replay DLLs stay disabled.

## Current evidence and next blockers, 2026-10-15

Continuous v1/v2 GPU composition and actual dynamic pose correspondence have evidence; the user reports serious native-map flash, so presentation acceptance is still failed. v3 eliminates native-color fallback outside hand pixels in independent GPU tests; actual motion and source-loss acceptance is still required. The original map audio is still present and an actual empty presentation scene is not yet established. A cold-start built-in AutomationStressArena loads but is a repeated industrial geometry scene, not empty; hot-switching to it from the old live world exited the original client and is quarantined.

Original hero hands throw/reload, but ammunition remains 24/24 and no native projectile has been identified. Native weapon authority, damage and ultimate are required fixes, not optional scope. User authorized agent-operated play tests; no further manual gestures are required. Current original process 14780 is responding in the cold-loaded arena, with local hero generation still pending. MC 45944 exports its real independent save normally.

## Natural survival and grounded movement increment, 2026-10-15

The current launcher defaults to an independent `Overwatch Survival World`: normal terrain generator, structures, normal difficulty and survival game mode, preserving the former flat creative save behind `--superflat`. The seed is 20261014. A one-time spawn search chooses nearby open grass instead of the vanilla birch-canopy spawn. MC reports its actual feet/eye position, vertical velocity, flying flags, ground block and onGround state in the local frame health response.

Real run: native PID 660, Minecraft PID 43348, live compositor v6. A Sky-generated Space press in the original window caused actual MC feet Y 71 -> 72.25220334 -> 71; 23 samples were airborne and the final state was grounded on grass. A W press changed MC Z from -309.5 to -309.71014. Flying and allowFlying were false throughout the captured run. Evidence: ignored `research/_archive/2026-10/survival-v6-proof/`, `research/_archive/2026-10/survival-buffered-movement-660.json` and `research/_archive/2026-10/survival-native-v6-660.png`. This establishes jump/landing and a short forward step, not sustained obstacle/ability/death acceptance.

The hand layer has a mild gamma lift (1.3) inside the current native depth-pair mask, retaining native animation, alpha, MC world color and subsequent native HUD. This is presentation correction; MC block/sky light does not yet light the native model. v6 replaces missing-hand frames with the MC world and holds the last complete composed frame if the composition boundary is missed. It records unmasked/held frames separately; it does not claim these are correct newly rendered hand frames.

A cold zero-map experiment with resource packs loaded exited native PID 31452 during original hero spawning. The route is quarantined; setting state 8 does not initialize a working renderer world. The current original scene remains Hollywood underneath the MC replacement, and map audio is not removed. Native weapons still lack confirmed projectile/ammo/ultimate authority. Full goal remains incomplete.

## Latest user direction: natural creative world, 2026-10-15

User explicitly replaced survival damage with creative invulnerability while retaining full MC terrain. The launcher now defaults to creative in the existing natural world save; `--survival` explicitly opts back into damage. Vanilla creative mode grants invulnerability and flight permission, but entry starts with flight off. The old flat save remains opt-in through `--superflat`.

The previous MC player had been killed by a zombie and was stuck on the hidden death screen; reporting feet/onGround alone concealed that condition. Health now reports actual alive/health/invulnerable/screen values. Creative entry recovers that dead player through vanilla respawn and vanilla creative-mode selection. Actual new MC PID 19008 reports health 20, alive=true, invulnerable=true, screen=none, flying=false and grounded grass.

The original PID 40552 was falling below the original map at approximately -30 m/s even while MC was grounded. A separately bounded native presentation-body adapter now receives the actual MC motor result each tick. Static 50-sample observation after the first adapter showed constant native feet Y and vertical speed zero. The first HTTP diagnostic adapter was stopped/restored normally and replaced by direct MC tick publication in reserved shared-frame header space; no third process is required.

Current increment: MC 42756, original 40552, compositor v8, direct body adapter v3. MC remains creative/invulnerable/flight-off. An actual Space press produced MC feet 62 -> 63.25220334 -> 62 and native presentation 999 -> 1000.252197 -> 999, ending grounded with native vertical speed zero. Compositor v8 retains the native lens during held images, disables additional MC camera bob and exports at measured 40 FPS. Actual stationary pause/resume screenshots had pixel-identical scenery through the held-image branch. Full details and limits are in NATIVE-BODY-SYNC.md; combat/abilities/audio/release lifecycle remain incomplete.


## Latest native weapon and reconnect increment

Original Genji execution now has actual ammo/reload/projectile proof: native left 24 -> 21, right 21 -> 18, R -> 24, second left -> 21, with the declared original ammo variable matching. A separate native component observation captured three distinct original projectile entities and their trajectories. The scoped gate executes the original callbacks and restores its bit, without button-derived damage or replacement HUD. Native projectiles have not yet been transferred into MC and no MC damage/ultimate/Pharah acceptance is claimed. See NATIVE-WEAPON-TRACE.md.

A controlled same-save MC restart (11508 -> 43676) resumed body coupling automatically: 1,366 paired samples, 444 guest unavailable/loading samples, one session resume and zero body failures. Native height did not accumulate a fall. Missing guest state now holds the last trusted native presentation, and only the same nonzero world identity/native generation may reconnect. This is a presentation hold; Minecraft retains all movement/collision authority. See NATIVE-BODY-SYNC.md.

Current modules: compositor v9, body v5, weapon gate v5, original PID40552, MC PID43676. Each has an eight-hour lab ceiling and independent restoration. The v9 camera proof matched 849 actual images with zero unmatched polls, but no large-turn acceptance is claimed. Native projectile event transport -> MC collision/damage, ultimate, Pharah, abilities/climbing, old-map audio, HUD health consistency and release lifecycle remain required. The persistent goal stays active.

## Initialized projectile event increment

The original projectile initializer was observed after successful native physics initialization: 27 distinct native projectiles with correct owner, finite native origin/velocity and fresh MC body/world identity, zero capture errors, then independent original-code restoration verification. A precreation probe first established why the earlier factory return was too early: owner and scene transform were still zero. Typed reflection now resolves both original Genji impact damage paths to the current native amount 35, and native velocity magnitude matches the real configured speed 60. See NATIVE-EMISSIONS.md. MC consumption, hits and damage remain unimplemented; the full goal stays active.

## Current damage, day and Shift increment

The v4 acknowledged native event receiver now applies real Genji damage in MC: one actual run recorded 18 accepted/acknowledged original emissions, 15 block hits, three entity hits and eight actual MC HP lost. Replaying the real batch three times produced no additional hits or damage. Current exact behavior and limitations supersede the historical unimplemented-consumer note above; see NATIVE-EMISSIONS.md.

Natural creative mode is retained. The server enforces midday 6000, disables daylight/weather cycles and clears rain/thunder. The full-bright MC lightmap option is enabled by the passthrough launcher; block textures and ordinary directional/AO shading are retained.

Native-confirmed Shift now drives vanilla MC player movement; four actual starts and one 14.7717-block server path ending grounded were observed. Per-target dash damage and wall blocking are implemented but still need controlled live acceptance; see NATIVE-DASH.md. Hero recreation stopped the old adapters and the original process later exited. Recovery is in progress with the same MC save retained. The user additionally requested original Genji Dragonblade/Q; charge, native activation, animation and MC sword damage remain required, not completed.
