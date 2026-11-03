# Kyoto first-person light direction — 2026-10-20

## Latest override: Hollywood camera-key rig, compositor33

Read WEAPON-GRAY.md. User released input and chose Hollywood again. Production33
removes the non-Pharah second gamma lift and uses Sun travel coefficients
(0.5,-0.707106781187,-0.5) in actual camera basis instead of overhead(0,-1,0).
Ownership remains the existing render owner/exact12direction bytes with original
picker/stop restoration. Native Sun RGB/materials/reflections remain unchanged.
Actual five-hero28view sheets, rapid pan, unretouched comparison and final forest
view were inspected. Actual picker restoration and McCree/Genji movement/real
damage/replay passed with the cold-input failure/retry limits recorded there.
33 SHA256 f551244c334620b005c19585e91214200493f9b0d435987b74e0cc52e93f0e86.
Current8416/MC27300 is independent Hollywood/McCree gameplay; recheck identities.
No full MC light transport/all-hero/all-angle/performance guarantee. Earlier
overhead/version31/32/code-only descriptions below are historical.

## Latest increment: Hollywood and Kyoto A/B, compositor31

The user released the PC for unattended game tests, superseding the code-only
interval below. Production compositor31 extends the existing camera-relative
direction owner to the separately calibrated Hollywood environment. No second
callback owner, camera rotation, material/RGB/exposure write was added. Exact
SHA256: ed1d50c08cd613f44797a60b0db5da75209f373b50ac32d34acc62d53dfe8c4b.

Hollywood's original direction is (0.1317604184,-0.8386704326,-0.5284610987),
RGB=(3.277166605,3.277166605,3.277166605), derived RGB=(3.003441095,
2.672940969,2.079642296). Only the12 direction bytes change. Kyoto's existing
profile stays unchanged. Wrong-map profiles/unknown scenes are refused. Reports
add fixedViewLight/viewLightMapId; fixedKyotoLight remains scene-specific.

Actual Hollywood14556 baseline40views reproduced strong directional changes.
The reversible12-view causal Sun-only test restored all original values. Native
36912/compositor31 then passed40views each for Genji, McCree, Pharah and Soldier76
(8yaw x5pitch, including +/-85degrees). All four real foreground sheets and the
rapid-pan sheet were inspected; gross directional white/black flips were reduced,
but Hollywood remains visibly darker for some weapons and reflections remain.
Actual picker entry restored the original Hollywood direction. This is not full
MC lighting transport or an all-hero/all-angle guarantee.

Kyoto33032 Genji40views passed and were inspected; a subsequent input stall
stopped that run. Cause is unconfirmed: healthy module reports did not prove
working input. Bounded refocus/minimize/restore attempts did not recover it;
normal restoration/stop and cold restart did. No arbitrary memory repair was
used. Actual9740 with normal UM CLI controls passed12views each for the same four
heroes and a rapid-pan control check. Do not treat failed/partial33032 McCree
captures as passed evidence. Avoid the optional persistent-input experiment for
now. Evidence: research/lighting-ab-20261020/.

Native C++ fixtures,40supervisor/17stop/5map/4light fixtures and the HTTP contract
entry point passed. Guest f4b6d99238240650b56c7fee716fcdd9d166fb1afd9be4cbf6525509e4e6e438
is now deployed by normal cold restart; actual Visor aim acceptance remains open.
All21-hero paired real screenshots completed at fixed yaw/pitch0, same position
and dimension, using actual9740Kyoto and5164Hollywood. Overview and all three
detail pages were visually inspected: matched roster/order, foreground present,
no color edits. Kyoto is warmer; Hollywood more neutral at this fixed view.
Native idle animation varies, especially Torbjorn. They are not all-hero/all-angle
or skill acceptance. Final5164 picker restored actual original Sun, with MC22592
and independent supervisor available. See all-heroes/final-audit.json.

The older version/PID and code-only descriptions below are historical.

Latest user feedback: extreme bright/dark angles remain. On actual29676 the v30
light owner is active and advancing without failures, so acquiring/updating a
direction does not by itself resolve the visual complaint. Reflections/exposure
are still native and were never locked by this implementation. NEXT cold-start
configuration is now Hollywood (bootstrap10 quiet/neutral daylight fallback).
No restart/input was performed after the user requested code-only work. New
map/all-angle pixel acceptance remains pending; do not describe v30 direction
fixtures as satisfying that newer acceptance criterion.

The user reported washed-out native hands/weapons at some viewing angles after
the Kyoto login scene change. Compositor30 now keeps the native main light above
the camera during first-person play. Turning and aiming remain the original OW
camera; MC views, collision, movement and projectile directions are unchanged.
The Kyoto backing scene and bootstrap10 remain selected.

## Actual diagnosis

Actual19784 Genji screenshots at four yaws reproduced strong direction-dependent
brightness. DynamicAmbient0, SinglePointAmbient1 and LocalReflections0 did not
visibly resolve it. All diagnostic settings were restored.

Changing the cached map header's +158 RGB at runtime had no visible effect.
The running native environment has original RGB at +28, derived illumination
RGB at +34 and unit light direction at +40. Temporarily zeroing both RGB triplets
made the native gun/hand dark while MC scenery and HUD stayed normal; changing
only +28 did not. Changing +40 alone visibly changed native weapon lighting.
These were reversible tests at an unchanged actual McCree view, with no input.
All original values were read back after restoration. Do not infer live-light
control merely from a successful cached-header write.

## Ownership and implementation

`native_view_light.hpp` changes only the environment's12-byte direction. It
uses minus the actual world camera's up vector, producing an overhead light
in camera space across yaw and pitch. Original Sun RGB, derived RGB, native
materials, exposure and reflections remain unchanged. This is a fixed lighting
rig, not transport of MC time-of-day, block lighting or shadows into OW.
Small native reflection/idle-animation differences remain; this is not a claim
that every native pixel is identical in all directions.

The verified beta engine class is1589e58; its +78 command-packet pointer is
transient during CPU recording and can be null during GPU callbacks/Present.
Frame-arena offsets also varied across cold starts. Initial fixed-offset and
render-callback-only acquisition attempts therefore failed and are not the
accepted implementation. Current acquisition searches only the calibrated2KiB
Sun-binding neighborhood of an active packet, requiring a unit direction and
the exact environment class158adb8 with unique identity.

The existing compositor worker reads a candidate. The existing render owner
validates the exact Kyoto RGB/derived RGB/original direction before binding,
then checks class, colors and its last owned bytes before each write. No new
thread/callback owner, camera write, gameplay rotation or projectile rotation
is introduced. Missing transient bindings defer lighting without stopping healthy
composition. Picker entry and normal stop restore the original direction.
An external conflicting direction is not silently overwritten.

Native report fields: fixedKyotoLight, viewLightOwned, viewLightRestored,
viewLightUpdates and viewLightPending. An enabled report alone does not prove
lighting was acquired. `verify_native_light_angles.py` checks actual direction
against the camera up vector and retains actual screenshots. The private
read-only diagnostic can resolve the current owner's bound object through the
exact mapped DLL/path/session hash and its own COFF symbol, avoiding transient
packet sampling during screenshot checks. It does not write the owner's state.

Production compositor is `owmc-live-passthrough-v30.dll`, SHA256
42ffbe74953170185243d1317de423f3ebd0e2c13d970e70b9e8eefb34bdb825.
The other five project DLLs and guest JAR are unchanged. v29 remains on disk.
The build script now rejects a loaded target before compiling; this was checked
against the actual running19240. Do not rebuild or overlay a loaded module.

## Tests and evidence

- Native fixture:12 yaw/pitch basis combinations preserve camera-relative
  direction, exact12-byte mutation, original restoration, null transient packet
  after binding, worker-candidate revalidation, shifted arena binding and
  external edits/wrong identities/invalid basis refusal.
- Existing native depth-pair/composition/state/resize/restoration and picker
  fixtures passed;40supervisor,13stop and4private-buffer light fixtures passed.
  The HTTP contract entry point passed.
- Actual19240/MC16824: Genji12views and McCree12views at yaw0/90/180/-90 and
  pitch0/-45/+45 passed actual light/camera checks. Their screenshot sheets were
  inspected. Pharah4yaw views also passed and were inspected.
- Actual Genji/McCree movement1.20/.825m, native fullHP200, real target health
  20->9.5/13, and replay deduplication passed. Test targets/blocks were cleaned.
- Actual picker restoration and final availability are recorded in
  `research/kyoto-fixed-light-20261020/picker-restoration.json` and final-audit.json.
  These do not constitute new all-hero/all-dimension or sustained180FPS acceptance.

Evidence root: `research/kyoto-fixed-light-20261020/`, including original angle
comparison, stationary Sun causal tests, failed acquisition attempts, accepted
v30-genji-r4/v30-mccree-final/v30-pharah-final screenshots/JSON and angle sheets.
Failed r1/r2/r3 attempts are not accepted lighting evidence.

Backup after ordinary save/stop:
`<USERPROFILE>/.universal-modder/backups/kyoto-view-light-v30-20261020/20261020-181755.zip`
(969files,1397.0MB). Earlier task backup remains under kyoto-fixed-light-20261020.

## Runtime issues encountered

Bootstrap report replacement briefly denied a read during the first restart.
`attach_hand_depth_probe.py` and `ensure_bootstrap` now reuse the existing bounded
`read_report` helper.40supervisor and13stop fixtures pass.

Stopping32320 left emission11's verified terminal report in.json.tmp after a
Windows replace-sharing race. Actual original initializer/pellet prefixes and
both ChaseVar callback entries were read and verified, exact process creation
matched, then the unchanged terminal report was promoted. Ordinary stop/save
completed. Evidence: emission-terminal-recovery-32320.json. No callback bytes
were forcibly repaired. General automatic emission terminal recovery is not
implemented by this increment. A build attempted after that incomplete stop was
blocked by Windows' loaded-file lock; the new explicit build preflight prevents
repeating that attempt before compilation. No loaded DLL was overwritten.
