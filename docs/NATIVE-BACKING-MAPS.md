# Native backing scenes — Kyoto login trial, 2026-10-20

Latest final state: user authorized full operation and another restart. Current
8416/MC27300 independently runs Hollywood with compositor33 camera-key rig and
unit non-Pharah foreground exposure. See WEAPON-GRAY.md for actual visual tests,
restoration/attacks, failed attempts and limits. Code-only notes below revoked;
global nativeMap remains hollywood. Recheck identities on takeover.

Latest override: user subsequently changed back to Hollywood and reported dull
weapon pixels. Actual25584 cold-started Hollywood with unchanged31. User is now
playing and requires CODE ONLY; no more input/restart/deployment until released.
The build-only32 foreground candidate is documented in WEAPON-GRAY.md. This
overrides the Kyoto decision directly below; do not treat map choice as gray-fix
acceptance.

Latest user decision after the full21hero atlas: use kyoto-login globally for
every hero. This supersedes the Hollywood selection in the A/B record below.
Normal Stop/Start applies it; no per-hero map changes or new render owners.

## Latest override: actual two-map test and full beta roster atlas

The user subsequently released the PC for unattended input. Both scenes have
now been cold-started with compositor31; Hollywood has a separately validated
camera-relative Sun profile under the existing render owner. Read the latest
NATIVE-FIXED-LIGHT.md increment. Four main heroes passed40views each on actual
Hollywood36912; Kyoto9740 passed12views each plus rapid-pan control checks.
Normal map-specific ambient color/reflections remain; scene selection alone is
not a complete lighting fix or an FPS guarantee.

Latest task captures all21original beta heroes at yaw/pitch0, same exact MC
position/dimension, with original screenshot colors. Evidence/atlas location:
research/lighting-ab-20261020/all-heroes/. Kyoto9740/MC20408 was stopped through
ordinary restoration/save, then Hollywood5164/MC22592 started independently.
Current configuration is hollywood; recheck actual process IDs on takeover.
This is a first-person appearance comparison, not21complete playable kits or
all21heroes at all angles. Older code-only/version30 statements below are history.

Latest override: user still reports extreme bright/dark view angles. Configuration
now selects Hollywood for the NEXT normal cold start, through existing verified
bootstrap10 quiet/neutral-daylight header handling. The running Kyoto process
has not been interrupted because user requested code-only work while using the
PC. Hollywood visual acceptance is pending; this setting change is not a proven
lighting fix. Read TAKEOVER.md and ITERATION-1-2-3.md before older evidence below.

Latest lighting override: compositor30 now holds the first-person native main light
above the actual camera and restores its original direction for the picker/stop.
Kyoto map headers/resources and bootstrap10 remain unchanged. Reflections stay
native. Read [NATIVE-FIXED-LIGHT.md](NATIVE-FIXED-LIGHT.md); the original trial
lighting/version/PID descriptions below are historical.

The user explicitly requested Kyoto_Login_Scene as the backing scene, expecting
daylight and lower resource use. It is now the configured cold-start default.
Actual world-engine state8 and loaded map0800000000000664 were read from the
SHA-guarded offline client. The visible world remains real Minecraft/Twilight;
this does not replace the two-process route or create a new save.

## Selection and implementation

`passthrough-settings.json` now contains `"nativeMap":"kyoto-login"`.
`tools/native_bootstrap_maps.py` defines the exact whitelist, v10 DLL/request
identity and read-only actual native world-map inspection. `ensure_bootstrap`
passes the selected map to the cold bootstrap; adoption rejects another map,
old version or stale report. The launcher also checks the actual loaded map
before spawning/composing. Changing the key takes effect after normal Stop/Start;
it does not request a hot scene change.

| Key | Map | Treatment |
| --- | --- | --- |
| `kyoto-login` | `0800000000000664`, Maps/LoginScenes/Kyoto_Login_Scene | Original header/resources; no map-constructor hook or lighting/audio header modification |
| `hollywood` | `08000000000002af` | Existing fingerprinted quiet/daylight header adapter retained as fallback |
| `lobby-empty` | `0800000000000223` | Existing experimental empty Lobby; previous lighting failure is not resolved by this increment |

Only these three IDs are accepted. AutomationStressArena remains quarantined.
Kyoto uses its original scene lighting and reflections. Existing compositor
foreground exposure and Pharah color adjustment are unchanged, so this is not
a claim of untouched final native RGB or MC-driven native dynamic lighting.
Kyoto's own ambience is not stripped or claimed silent.

New `owmc-session-bootstrap-v10.dll` was built to a new filename before the
cold Kyoto launch. v9 was preserved. v10 requires exact creation/PID/plugin/
unpacked-loader identity and validates the original loaded map. Hollywood/Lobby
retain their previous header fingerprint/counter gates. Kyoto deliberately
bypasses those map-header modifications. Four continuous adapters remain v29/
body10/gate8/emission11; no loaded DLL was overwritten or second owner added.

v10 SHA256: c8fa92c1a8f5c8f0a5f2e9aa14fe332eba2829b3901ec1da81a5cadff3be47a2.

## Backup and tests

Both games had already exited before this task. Source/settings were preserved
under `research/kyoto-login-20261020/`. Full964file profile backup,1306.2MB:
`<USERPROFILE>/.universal-modder/backups/kyoto-login-20261020/20261020-165607.zip`.
The known Hollywood baseline was cold-launched first, measured, then stopped
through normal callback restoration and MC save. No retail client was attached.

- Native bootstrap policy C++ fixture passed exact whitelist, untouched-Kyoto
  and existing Hollywood/Lobby preparation gates.
-40supervisor,5map/request/adoption,13normal-stop and7cadence fixtures passed;
  HTTP contract entry point and read-only environment check passed.
- Actual29540/MC6840: real Overworld/Nether/End/Twilight transfers with8McCree/
  Genji rows passed model/health rebinding, movement, real native damage and
  replay deduplication. Temporary blocks/targets cleaned.
- Actual Pharah3Space pulses: rise delays59.66/88.80/46.07ms, peak7.90195m/s;
  3native shots/3muzzle flashes, replay unchanged, private visuals error empty,
  fixtures cleaned. Original first-person hand/HUD and actual rocket footage
  inspected; this does not complete modern VFX parity.
- Native Pharah selection foreground/idle animation over the real MC background
  was recorded and its frame sheet inspected. The initially unchosen picker
  did not display a hero until a card was selected; choosing Pharah produced
  the expected original animated model and hero name.

Private evidence root `research/kyoto-login-20261020/`: baseline/Kyoto captures,
`world-hero-switch.json`, `pharah-response.json`, `pharah-primary.mkv`, picker
motion/sheet, source/settings backups and final-audit.json.

## Resource and cadence results

Cold Genji samples used the same MC position(-73.07946,5,-348.94437), yaw/pitch0,
same world/profile/JAR,1080p/OWLow/8chunks/no shaders and the same240caps.

| Native process sample | Hollywood | Kyoto login |
| --- | ---: | ---: |
| Working set | 3,174,752,256bytes | 1,729,462,272bytes |
| Private bytes | 4,921,466,880bytes | 2,998,218,752bytes |

Working set at this cold same-hero sample was45.5% lower. After loading several
heroes/dimensions, the Kyoto native working set grew to2.91GB; the initial saving
must not be described as a fixed maximum or sustained45.5% saving in all play.

The first15second samples measured Hollywood distinct composition107.63fps and
Kyoto90.42fps, but Kyoto lost foreground midway: native cadence paused, then
settled around60fps. That run cannot establish a map-related FPS regression or
improvement. `tools/verify/measure_native_scene.py` now records foreground PID and
excludes intervals whose endpoints are not the native game. A later real Kyoto
Pharah sample had13.92seconds of eligible foreground windows, no excluded pairs,
host228.23fps and distinct composition103.74fps. It was at a different MC
position/hero, so it is a runtime diagnostic, not a controlled A/B advantage.
No180fps or overall frame-time/1%low acceptance is claimed.

## Final available state and fallback

Final verified native29540/MC6840, supervisor wrapper28772/real35968, at original
Pharah picker over Twilight. Source/native frames advance; actual six mapped
project modules/four live owners/failures0, source/build/profile JAR hashes and
actual loaded Kyoto map match. Behind the picker: fullHP200/20, grounded,
F6flightOFF at natural mushroom(57.5,25,12.5), ammo6 and clean fixtures. Final
picker pixels inspected. Recheck current identities rather than reuse these PIDs.

For fallback set nativeMap to `hollywood`, then use normal Stop and Start.
Retain bootstrap10; it still supports the original Hollywood preparation gates.
Do not load another bootstrap/compositor into the running Kyoto process.
