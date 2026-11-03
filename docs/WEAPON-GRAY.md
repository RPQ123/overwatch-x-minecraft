# Weapon gray-veil investigation — 2026-10-20

## 2026-10-21 scoped ownership34 supersedes33 deployment

Read SWITCH-READINESS.md.34 preserves33's native foreground colors/key direction
but scopes/restores/revalidates the Sun after actual hero/model/MC-world changes
and requires a fresh post-transition pose. Current CPU packet checks continue
while owned, with strictly validated same-scene recovery across transient packet
absence. Native RGB/PBR/reflections are preserved. Six heroes plus McCree return,
28actual yaw captures and four-dimension first-shot/light checks passed; the
original-color sheet and picker/gameplay were inspected. No all21/all-angle or
MC day/block light transport claim. Baseline addresses often matched, so a stale
Sun address was a lifecycle risk, not proven to explain every previous screenshot.

## Latest result: deployed33, Hollywood, input released

User subsequently authorized full control and, after closing the games during
testing, explicitly requested reopening and continued comparison. The code-only
restriction below is historical. Final native8416/MC27300 is on Hollywood, with
independent supervision and McCree first-person over real Twilight grass. Native
200HP/MC20HP, grounded/F6OFF, advancing compositions, healthy owners, active test
target/platform cleanup and actual picker Sun restoration are in final-audit.json.

The31 baseline still looked flat at a stable view. Runtime DynamicAmbient0,
SinglePointAmbient1 and LocalReflections0 screenshots did not visibly fix it;
all settings restored. FogEnabled0/ComputeFogEnabled0 individually also showed
no obvious static improvement. Combined fog attempt failed its view guard and
is not accepted evidence. No fog/ambient toggle was made a production setting.

32 removes the second gamma lift but was only a partial improvement. A separate
7direction Sun-only test ran AFTER the existing compositor restored itself and
its supervisor stopped. Remaining native body ownership held position; there
was no second render owner. Those pictures show native-only pixels, NOT MC
fusion. The oblique key separated revolver detail/highlights/shadows more clearly
than a straight overhead rig. All original direction/RGB/derived RGB values
were read back after restoration (sun-rig-native-only/result.json).

33 combines unit foreground exposure with the selected camera-space Sun travel
coefficients (right0.5, up-0.707106781187, backward-0.5). Basis vectors must be
unit and orthogonal; the existing owner still changes only12direction bytes,
checking exact map/class/color/last-owned values, restoring on picker/stop.
Native main/derived RGB, materials and reflections are preserved. Pharah's prior
separate tint policy is unchanged. This is a fixed native studio-style rig;
MC daytime/block light and shadows are not transported into native materials.

SHA256 owmc-live-passthrough-v33.dll:
f551244c334620b005c19585e91214200493f9b0d435987b74e0cc52e93f0e86

tools/native_compositor_version.py now supplies exact33 identity to startup and
attachment/adoption checks. Build default reads that selection; explicit
-NativeForegroundCandidate builds32 and -CameraKeyCandidate builds33. Each
target is checked against mapped modules before compile. Old31/32 files are
preserved. No mapped module was overwritten or overlaid.

## Actual verification of33

- McCree12views (4yaw x3pitch including +/-85), Genji/Pharah/Reaper/Soldier76
  4yaw views each: actual direction checks passed and sheets were inspected.
  Incomplete first Genji/selection attempts are not acceptance; successful
  captures live in v33-mccree/, v33-roster-recheck/ and v33-roster-recheck-2/.
- The before-after image uses actual31/33 fixed MC location/hero/yaw/pitch, with
  original colors. Native idle poses differ slightly. This is improved detail/
  contrast, not a guarantee of identical metallic pixels in every direction.
- Actual8416 rapid yaw/pitch recording passed control checks; its frame sheet
  was inspected without gross whole-weapon white/black flashes. Native picker
  restored the original Sun, then McCree gameplay/key ownership resumed.
- Actual McCree movement/native full200HP, target20->13 and replay13 passed.
  The first Genji cold-switch shot produced no new factory event; it is a failed
  attempt, not passed damage. Reselect/settle retry passed movement/200HP,
  target20->9.5 and replay9.5. No initialization/input-timing fix is claimed.
- Native fixtures add40key-rig yaw/pitch cases, nonorthogonal-basis refusal and
  exact12byte/restoration checks. Actual GPU RGBA swatches, compositor state,
  hidden gameplay/picker callbacks and resize fixtures pass.40supervisor,
  17stop,3native-only-stop policy,4setting,4light and HTTP contract tests pass.
- --keep-minecraft retains only the exact validated guest while normal owner
  restoration/OW termination occurs. Real31/32/33 cold adoption tests kept that
  same guest for A/B. Default Stop still saves/shuts down MC. No broad process
  termination was introduced.

The user closed both processes during the first8416-predecessor smoke; it did
not finish or produce a cleanup receipt. A bounded in-game /fill for the earlier
known-air bedrock lab volume was attempted after reopening, but command feedback
was not observed, so that earlier persisted volume is NOT certified clean.
Subsequent current fixtures have a successful cleanup receipt. Save files are
disposable per user; do not conceal the interrupted run or claim whole-save
cleanup. Current playable region has no active test target/platform.

Full21-hero/all-angle, every dimension/kit and sustained180FPS are not newly
accepted by this increment. Source/profiles/evidence remain private and no
publishing/commits were performed.

The following sections describe the earlier code-only32 proposal.

User rejected the latest Kyoto appearance and requested Hollywood again, then
reported the revolver looked worse/duller after the map change. Actual Hollywood
25584 is running compositor31. No new weapon rendering fix had been deployed
when either user screenshot was taken. Map-specific native ambient/reflections
remain different despite the camera-relative main Sun direction.

## Current input boundary

User is playing and explicitly answered: "我还在玩，先只改代码". Do not send
input, switch heroes, stop/restart games, or deploy the candidate until that
restriction is lifted. A proposed same-view baseline/ambient/reflections test
failed its bounded pose check due to additional movement/hero/fire input. Its
partial angles.json is NOT usable A/B evidence; no render-setting experiment
was entered before that failure. Automatic view restoration was attempted by
the checker before the user gave the code-only answer; no input followed it.

## Build-only candidate32

The deployed31 compositor performs a second gamma operation on already rendered
native foreground RGB: pow(rgb,1/1.15), except Pharah. This lifts dark and middle
values relative to highlights; for example native16/255 becomes23/255. It can
reduce apparent metallic contrast. This is a code-confirmed mechanism and a
testable hypothesis for the gray veil, not a proven complete visual diagnosis.

Build with:

    pwsh -NoProfile -File tools/build_live_passthrough.ps1 -NativeForegroundCandidate

Candidate32 passes exposure1 to the existing foreground shader for non-Pharah
heroes. Unit exposure bypasses pow entirely, retaining original native RGB and
alpha. Pharah's earlier separate tint balance and all scene/Sun ownership,
depth masks, HUD, MC colors and movement remain unchanged. There is no added
contrast/saturation filter. This may reveal darker native shadows; it does not
solve native ambient/reflections by itself.

SHA256 owMC-live-passthrough-v32.dll:
a8b69a931c1bb5fafb73f765bcdd642d77c50dab9df53b5e0d924805a9ede668

The script's default still builds31, with the existing loaded-file rejection.
Candidate mode writes32 separately and the hidden integration fixture loads32.
Launcher/adoption/production manifest still require31 intentionally; ordinary
starts do not silently adopt the untested candidate. Existing loaded31 SHA256
remains ed1d50c08cd613f44797a60b0db5da75209f373b50ac32d34acc62d53dfe8c4b.

## Verification and remaining work

Candidate build passed main-light binding/restoration, native frame-cap ownership,
viewmodel lens, actual WARP GPU composition and hidden gameplay/picker callback
restoration/resize fixtures. New actual shader readbacks verify exact RGBA over
black/deep gray/colored midtone/highlight swatches, both mask positions, and
unchanged guest color/native alpha outside foreground.

No candidate has been loaded into the game and no improved screenshot or visual
acceptance is claimed. Evidence/settings/source backups:
research/weapon-gray-20261020/. Before deployment, wait for the user to release
input. Then compare old31 versus candidate32 at identical hero, world position,
camera and scene through normal restore/Stop/Start, inspecting actual pixels.
If the grayness persists or shadows worsen, investigate native ambient/PBR
with bounded restored setting experiments instead of adding arbitrary filters.
