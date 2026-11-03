# Original Pharah flight into Minecraft — 2026-10-18

2026-10-20 override: user requested faster immediate held-Space rise. The exact
original hover graph's measured.2s Wait is now0 through a creation/model/graph/
field/type guarded four-byte patch, reapplied at hero rebind. Positive original
hover thrust is integrated at MC20Hz with requested8m/s cap; measured7.90195m/s.
This is an explicit adaptation to the earlier original-motion baseline below.
Native fuel/Shift, descent and MC collision remain authoritative. Actual three
Space pulses, ceiling/landing and resource regression passed; details and limits
in [PHARAH-RESPONSE.md](PHARAH-RESPONSE.md).

The original offline Pharah now supplies vertical physics for hover and Jump
Jet. Original scripts0025/0027 retain activation, fuel, acceleration, gravity,
animations, HUD and cooldown. Minecraft resolves the final player bounding box
against its own blocks. F6 creative building flight bypasses this hero channel.
This is a verified flight increment, not complete Pharah or all-hero acceptance.

## Native oracle and ownership

Before integration, restored the body writer using its existing stop control,
then recorded the actual original mover histories with real hover/Shift input.
No second callback owner was installed. Private evidence is
research/pharah-native-flight-oracle.json. The same supplied SHA-guarded research
executable was used; no retail client was attached.

The existing body callback observes the original mover after its native update.
It accumulates displacement relative to the last MC-authoritative position,
retains the original velocity AND separate gravity state, then rebases native
presentation to the actual MC result. Ground/ceiling/side collision feedback
clears only obstructed velocity axes. This avoids copying guessed flight/fuel
numbers or letting the old Hollywood collision own the MC player position.

The supplied offline mover retained horizontal drift after Jump Jet even with
zero input. Initial full-vector imports reproduced that drift. The released
controller imports vertical integration and retains the existing reflected
directional-speed/input adapter horizontally. No-input horizontal drift now
measures0.0. Native horizontal air acceleration/momentum fidelity remains an
explicit calibration item; do not describe the entire movement model as1:1.

## Transport and transitions

Native producer: Local\\OWMCNativeFlight_<pid>,256bytes, OWFLY001/version1.
Fields: PID/model @16/20; host generation/world/MC generation @24/32/40;
MC PID/enabled @48/52; seqlock/wall ms @64/72; cumulative3*f64 @80;
native velocity3*f32 @104; MC grounded @116. The existing MC body packet adds
FLY1 @160, enabled/model/blocked-axis mask @164/168/172. Old consumers ignore it.

The reader checks current native process/generation, model, actual world and
own MC PID, fresh even seqlock, finite bounded numbers and a stable read.
Duplicate motion sequences are not moved again. Models/worlds/creative flight
reset the baseline; missing/stale motion under a valid host pose holds instead
of applying old movement.
Mode1 at52 identifies Pharah; mode2 is the separate original Tracer teleport
stream described in NATIVE-BLINK.md. Their readers reject the other mode.
Native stale guest holding disables the flight producer. Real dimension transfer
and long-duration focus/source-loss flight acceptance remain pending.

## Verification

Actual composed-window evidence (read each result's PID):

- research/pharah-flight-open-result.json: passed; feet78 ->89.53515625,
  max upward1MC block/tick, actual descent,171 ready samples, horizontal drift0.
- research/pharah-flight-ceiling-result.json: latest PID4560 passed after adding
  the independent Blink mode; feet193 ->196.20000005,head stops at roof198,
  172 ready samples and
  horizontal drift0. Temporary
  platform/ceiling restored; both result files record cleaned=true.
- Inspected native recordings and contact sheets. Original Pharah hands/HUD
  remain over actual MC mountains/terrain. Regenerate sheets with um video
  contact and the configured ffmpeg directory on PATH.
- research/pharah-native-resources-result.json: latest PID28968 passed. Actual
  native Shift has its original10-second timer; repeat press leaves the same
  action tick22064 and decreases remaining10 ->8.46498. Holding hover
  commits fuel100 ->0; release restores100. Space also raised actual MC feet
 180 ->182.58984,consumed fuel to0 and left creative flight false.
  No cooldown/fuel values were written by this test. Fixture cleaned.

Meaningful fixtures cover cumulative movement across native frames, world/model
rebasing, teleport rejection, source/model/world/seqlock/stale/nonfinite refusal.
The latest full guest build/check passed22 tasks, including the separate Blink
mode. These tests are distinct from the
actual composed native recordings and do not constitute user play acceptance.

The startup prewarms the existing body/gate/emission owners behind the initial
native picker. The body holds position writes only until the first real gameplay
view, preserving the native selection animation. After the first gameplay write,
retain MC body authority in later menus; suspending it there lets the actor fall
in the old native map. Current camera/ownership proof is shared with the launcher.

Reproduce with tools/verify/verify_pharah_flight.py --pid <current> [--ceiling] and
tools/verify/verify_pharah_native_resources.py --pid <current>. Read current session
status, back up the profile, and use the normal restoration/shutdown controls.
The lab is creative-only, checks all candidate blocks are loaded air, and cleans
its temporary blocks. It does not replace or destroy existing terrain.

Pending Pharah work includes concussive blast, Barrage/charge feedback, exact
horizontal air control and wider dimension/focus regressions. Rocket splash
interpolation and terrain strength limits remain documented in NATIVE-PHARAH.md.
