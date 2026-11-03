# Native Genji climbing over Minecraft

**Body10 update:** the presentation state now also receives the MC-derived air
and ground bits, using the same mask as the two mover states. TrackMovement's
output108/variable1a1 means AIRBORNE (flags&0x0c), and output110/variable0221
means GROUNDED (its inverse). Older notes calling1a1 grounded were incorrect.
Body9 had retained native falling in the presentation copy, blocking grounded
skills despite standing in MC. Body10 fixes this without changing skill gates.
Climbing retains flag80 plus an air bit, so it cannot falsely report grounded.
Native6760 high-wall video climb10-platform-contact.mkv confirms alternating
hands and6block maximum rise remain functional. Repeated-climb15s:189.93distinct
FPS,29report windows minimum170.87, held0/unmasked0 (body10-climb-perf.json).

Body9 preserves the original animation graph while Minecraft resolves actual
wall and ceiling collision. Real offline client25048 climbed a temporary stone
wall by6blocks with alternating original left/right hands, then returned to its
shuriken pose. Evidence: research/_archive/2026-10/climb9-platform-contact.mkv, .json and
-sheet.png. The test is recorded game output, not synthetic animation frames.

## Animation contract

The original TrackMovement state (graph05800000000001c7/node42, update10aa870)
sets dynamic04b4 only when movement flags198 contain80 and WallMove mode8c is
2..4. Its context getter d14af0 uses component12's presentation state atA060;
writing only component15's simulation states does not reach this predicate.
Genji graph0580000000000157/node20 then starts original animation node40,
alias0c800000000000a0. No animation callback, asset or graph is replaced.

The body-v1 reserved area carries optional CLM2 magic324d4c43 at144, active at148
and unsigned native model identity at152. Active packets require airborne MC
state and a nonzero model. MC sends contact only for the same current player
tick and verified Genji model. Native additionally matches hero29 and current
model identity; stale packets clear climbing while holding the last safe body.
Legacy emission consumers ignore this reserved extension.

After the original movement tick, body9 applies flag80/mode2 to the two mover
states and the current presentation state. The presentation write changes only
that bit and byte, preserving unrelated flags, positions, profile IDs and history.
Mode and flag clear on exit. Every field is preflighted and rolled back after
an injected write failure; all16 ground/14 air failure positions are covered.
All pointers are rebound and owner-checked when the native hero changes.

## Actual checks and limits

- Native25048/MC: one climb20motor ticks,6blocks; original4b4 and Anim40 enter
  and exit. Actual video confirms alternating hands, recovery and collision.
- Four further held/released cycles:19.59native seconds,189.42distinct composed
  FPS;38report windows, minimum169.88, none below150; held0/unmasked0. This is
  bounded cadence evidence, not per-frame minimums or all-world guarantees.
- McCree and Winston W+Space against the same wall left native climbTicks at304
  and MC starts/ticks unchanged. Returning to Genji climbed again with no restart.
  Evidence climb9-mccree-isolation.json, -winston-isolation.json and
  climb9-genji-return.*. Flying with wall contact reports no active climbing;
  climb9-flight-isolation.json is a post-action snapshot, not a full input trace.
- Fixture endpoint POST combat/test/climb-wall validates an entire3x8air-only
  wall and, while flying,5x5air-only landing platform. It refuses occupied sites.
  Cleanup restored all49temporary blocks (wallBlocks0), removed no existing
  terrain, and the ordinary save was saved through normal shutdown.
- All body/guest builds and20launcher checks passed. Native callback owners
  restored normally on tested shutdowns; no old body7/8 owner is reused.

Motor speed.30block/tick,6block rise and30tick budget remain adapter settings.
The separate native mantle field m_climbSpeed=7.5 is not proven to be sustained
wall-climb speed. Do not infer surface normals from native XYZ70: that earlier
candidate did not trigger animation. WallClimbController reports contact intent
as nativeAnimationRequested, not a fabricated live native animation verdict.

During cold startup from still water, locomotion readiness had retained an old
camera error because applyMovementInput is bypassed by water travel. The reader
now refreshes once per player tick through the ordinary client tick, including
water, cancelled climb travel and idle states. Movement shares the same cache.
Final cold native23620 reached ready=true at the identical stationary water
position without movement input (climb9-water-cold-ready.json). After moving to
a leaf platform,15s yielded193.74distinct FPS,28windows minimum178.29 and
held0/unmasked0 (climb9-final-cold-perf.json).
