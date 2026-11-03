# Pharah primary presentation and held-Space response — 2026-10-20

This increment keeps the two-process route, original native launcher/animation/
HUD and admitted native rocket events. It does not add a second native callback
owner or replace a loaded DLL. Read current runtime evidence rather than old PIDs.

## Official visual reference

The current [official Pharah page](https://overwatch.blizzard.com/en-us/heroes/pharah/)
embeds the Rocket Launcher demonstration whose filename is
`OVERWATCH_WEBSITE_CHARACTER_CAPTURE_PharahRocketLauncher_WEB_16x9_1920x1080p30_H264.mp4`.
The exact CDN URL and page provenance are in private
`research/pharah-official-reference/source.json`. The official HTML was fetched
directly after the web reader returned403. FFmpeg read the official clip to make
private frame sheets; these were actually inspected. It is a1920x1080/30fps,
4.87second clip, with first-person fire and third-person projectile flight.

The flight image at1.7seconds has a sharp yellow-white central star and a narrow
flame ribbon. A conservative yellow-pixel threshold gives a73x102pixel effect
bounding box, recorded in `measurements.json`. The visible foreground hero is
approximately720pixels tall, but it is at a different depth: this ratio is NOT
an exact physical projectile size. Unknown reference camera/projection and
postprocessing also prevent a claim of identical pixels in our MC scene.

The previous renderer used a dim circular exhaust without the moving star. The
new pass uses the private original star sprite, a brighter core and animated
tail, while retaining the original model. Mesh scale2 is the earlier explicit
user-requested enlargement, not an official world-space measurement. Full native
effect-graph replay, native bloom and exact modern effect fidelity remain open.
The final material pass uses MC's additive `getEyes` layer for light sprites;
ordinary translucent blending compressed the narrow star into a dull orange dot.
This is an adapter material, not the original OW shader.
Real-frame QA rejected the first additive pass: white RGB with alpha-only
intensity produced bright rectangles because the layer does not attenuate RGB
that way. The packer now stores intensity in RGB as well as alpha, including
transparent-white source edges. Two focused material regressions check zero
additive contribution at both opaque-black and transparent-white edges and
preservation of soft intensity/tint. The rejected clip/report have explicit
`pharah-additive-mask-rejected` names; counters passing there did NOT accept
the visible effect.

## Launch alignment

The beta gun is different from the modern website gun. Its actual rest aperture
was inspected in `research/_archive/2026-10/pharah-muzzle-calibration.png`. Use the beta aperture
for placement rather than copying the modern gun's screen coordinate.

The old visual displacement applied a lateral offset while keeping the rocket
at eye depth, which projected the earliest body away from the muzzle. It also
used different displacement scales for flash and rocket. `PharahRocketPresentation`
now supplies both from one projection: normalized aperture(.534,.583), .90m
forward plane, smooth convergence over.16seconds. Farther flight retains the
authoritative native eye ray. Damage, speed35m/s, range and server collision
remain unchanged. The alignment is calibrated for the rest pose; exact animated
bone/recoil tracking is not implemented and must not be claimed.

The muzzle flash only follows an actually admitted shot, including immediate
impact. `NativeShotSimulation.admissions()` retains that fact independently of
ongoing flights. Replay, new native source, hero/player/world transitions clear
or deduplicate the presentation queues. There are no button-created projectiles.

Private original mesh/textures remain under the user's `.universal-modder/assets`;
the packer verifies hashes and does not put game assets in the source/JAR.

## Space response and user-requested faster rise

Actual baseline `research/_archive/2026-10/pharah-response-before.json` measured250–275ms between
the exported Space bit and MC rising. Native graph0580000000000025 node2 was a
Wait with a reflected constant duration of.20000000298seconds. Its actual
Begin→End timing was200ms. `tools/native_hover_response.py` changes only that
constant to0 after verifying SHA-guarded process creation, current Pharah model,
graph resource,37nodes, node type, reflected field, config type/size and old value.
The supervisor reapplies it on new hero/model bindings. No fuel/cooldown/function
or callback changes are made; the original value is restored by process exit.

`NativeHoverLift` now integrates confirmed positive native hover velocity at
MC20Hz instead of amplifying batched native displacement. This removes batching
from the lift multiplier. The explicit user-requested cap is8m/s while Space is
held. No-input/zero native thrust, descent and native Jump Jet retain their
separate path; MC still resolves collision. This is a requested adaptation,
not a claim of modern retail flight physics.

The intermediate pre-enlargement live run35344 passed three rise-delay samples
31.67/45.69/58.93ms and3actual shots/3flashes, replay unchanged. Evidence is
`research/_archive/2026-10/pharah-response-after-before-enlarge.json`. It predates8m/s fixed-step
and the latest visual calibration and cannot accept those later changes.

## Validation and remaining work

The following heartbeat automated the observed body terminal-report recovery in
`tools/stop_passthrough.py`. It checks process freshness, v10 terminal identity,
actual original callback table and absence of another active copied body table,
then promotes only unchanged bytes with bounded retries.13stop fixtures and an
actual active-body rejection check passed. Full real stop-failure reproduction
was not performed again; no running game was interrupted. Details in TAKEOVER.md
and research/heartbeat-20261020-0809/.

Final deployment10364/MC30276, independent wrapper15692/real supervisor29800:
`research/_archive/2026-10/pharah-reference-final-audit.json` passed. Six actual mapped project
DLLs match the expected set, four owners enabled/failures0, source/build/profile
JAR hashes match, frames advanced58 over the audit interval, native hover Wait0.
Fresh identities are required on takeover; these PIDs are historical after exit.

Final response/fire record `research/pharah-response-after.json` passed with
three rise delays57.42/65.91/67.28ms, peak7.90195m/s,3shots/3flashes and replay
unchanged. `research/_archive/2026-10/pharah-primary-final-close.png` and the full recording were
actually inspected: the luminous core/tail are visible, the additive rectangles
are gone, and flight converges from the calibrated muzzle region. This accepts
this visual increment, not exact official VFX parity or all-pose bone alignment.

Fixtures cleared; actual real Twilight transfer back to the natural mushroom at
(57.5,25,12.5) settled with native/MC full HP200/20, ammo6, onGround=true,
F6flightOFF. `research/_archive/2026-10/pharah-reference-final-play.png` was actually inspected:
original native launcher/HUD over real Twilight forest. Both games and the
independent supervisor remain available.1080p/low/8chunks/no shaders/day-night
and the Switch A clone are retained; no new normal-world save was created.

- Build/check:31Gradle tasks passed, including launch projection/near-plane/
  convergence regression, hover checks and combat admission/replay tests.
- HTTP contract entry point passed;2native hover guards and39supervisor tests passed.
- Full profile backup before tests:
  `<USERPROFILE>/.universal-modder/backups/pharah-response-20261020/20261020-142106.zip`.
- Latest actual response/fire test: see `research/pharah-response-after.json`;
  only a passing current record is acceptance for8m/s and3shot/flash correlation.
- Pre-additive current-code flight pass18828: actual rise delays47.73/61.86/
  97.72ms, peak7.90195m/s, three shots/flashes, replay unchanged, clean fixtures.
  Preserved as `research/_archive/2026-10/pharah-response-before-additive.json`.
- Same run ceiling collision passed: maxfeet64.20000 under roof66 with1.8m
  player height, zero horizontal drift; finalfeet61/onGround=true/flightOFF.
  Native resource run passed original Shift10s/retry does not restart, fuel
  100→0→100, and held-Space fuel reaches0 while real ascent occurs. The verifier
  now samples during the hold: sampling only after CLI exit observed9.9 fuel
  already recovered and falsely failed an exact-zero assertion. Both the failed
  post-release report and actual in-hold trace are preserved. This changes the
  test timing, not fuel behavior.
- Same run actual terrain/splash/replay checks passed in
  `research/pharah-explosion-live-result.json`; no new damage constants.
- Native-only reference restored the world compositor normally and captured the
  beta's own muzzle fire. Input then lost foreground and the session exited;
  the MC log shows normal save/stop, not a proven crash. This is reference footage,
  not completed sustained-play acceptance.
- Exact official effect parity, animated muzzle hardpoint tracking, full modern
  Pharah kit and sustained FPS acceptance remain incomplete.

Do not describe a module report or a rendered frame counter as visible acceptance.
Inspect the actual final recording, clean fixtures and leave creative F6 flight
off on safe ground before handing play back to the user.
