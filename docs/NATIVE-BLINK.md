# Original Tracer Blink into Minecraft — 2026-10-18

The original guarded offline client owns Blink activation, the three charges,
recharge timer, animation, HUD and actual teleport vector. The existing body
callback observes that teleport once; MC resolves its player bounding box against
real blocks. No key-derived teleport, guessed7.5m constant, second callback owner
or retail process attachment is used.

## Native evidence and binding

research/tracer-native-motion-oracle.json was measured after restoring the body
writer. Actual native horizontal teleports were about7.48m; the original charge
variable0d8000000000000b changed3 ->2 ->1 ->0, refused an exhausted press and
recovered after the original interval. Native velocity alone did NOT identify
Blink: position teleports while velocity can remain near zero. Do not implement
it as a copied high-speed dash.

tools/prepare_native_blink.py binds original script0580000000000024, nodes5/10,
their declared vector-expression fields and original plugin logger. Their native
type hash is a5f89e3f; no unverified community class name is required. The112-byte
OWBLK001 request contains PID/creation, current admin/controller/model, script/
bag/graph/logger and both node/vtable identities. The worker checks process
creation; the existing owner callback rechecks current ownership and actual graph
membership before observing either action. Ordered-map reads are bounded and
stable. Native activation or cooldown values are never written.

native_blink.hpp admits only a fresh actual action plus a matching observed
horizontal teleport within100ms. Ordinary motion, owner changes, old logger rows,
small/oversized jumps and later Recall movement are refused. Native world and MC
producer-generation changes clear the accumulator. The3D native correction is
used to validate the jump; its horizontal displacement drives MC movement.

## Transport and MC integration

The existing OWFLY001 mapping has mode2 at52 for Blink; mode1 remains Pharah
flight. Blink cumulative displacement is at80; current consumed action tick at120
and native capture count at128. All old source/model/world/seqlock/freshness/own
MC PID guards remain active. No separate callback or shared-mapping owner exists.

NativeBlinkPhase establishes a baseline after an owner/world change, deduplicates
native action/capture counts and never turns several missed, differently directed
teleports into one straight movement. NativeBlinkController uses Entity.move for
actual MC shape collision and preserves ordinary velocity. F6 creative building
flight bypasses this hero movement, as with Pharah. The existing persistent
supervisor prepares the current Blink binding on each Tracer model/world change.

## Actual acceptance and limits

- research/_archive/2026-10/tracer-blink-live-result.json, native4560: passed. Actual requested
  distances7.47949..7.47998m. First two unrestricted MC moves matched; the third
  stopped at the bedrock wall after7.19982m. With no charges a fourth press caused
  no event; after recharge the next native teleport moved MC only0.00098m against
  the same wall. Native/MC each admitted exactly4 teleports. Temporary lab cleaned.
- The10-second native recording/contact sheet was inspected: original Tracer
  hands,150/150HUD, animation and charge indicators over actual MC terrain/wall.
- research/_archive/2026-10/tracer-owner-transition-result.json: Genji ->Tracer ->Pharah ->Tracer
  retained20MC HP, stable feet207, zero native body failures, fresh native capture
  count0 on each new Tracer and no phantom old teleport. Fixture cleaned.
- research/armory-Tracer-4560-result.json: actual primary factory/damage, cover
  and replay checks passed after those transitions. Startup initially confirmed
  Tracer directly, exercising the shared prewarmed observers with this hero.
- Native owner/action/collision-event fixtures and full22-task guest build/check
  passed. These are separate from actual composed-window verification.

Recall, Pulse Bomb, exact native stair/edge/headroom behavior, several missed
teleports during severe stalls and long focus/source-loss acceptance remain open.
Bounded real dimension changes now pass the regression below. This is a verified
Blink increment, not a complete Tracer
kit or a claim that all12 Assault/Defense kits match the original.

Reproduce with tools/verify/verify_native_blink.py --pid <current>. It uses real original
input and a creative-only reversible air lab, records native charges, inspects MC
collision and cleans the temporary platform/wall. Never replay a historical PID.

## Additional dimension/model lifecycle regression

Actual21700 four-dimension/two-activation-per-dimension Blink and post-switch
pistol/replay checks passed on2026-10-19. See BLINK-LIFECYCLE.md for evidence,
backup, harness correction and explicit limits. Production code unchanged.
