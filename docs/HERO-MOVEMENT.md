# All-hero base movement and native model presentation — 2026-10-22

This work keeps two real games and the original21 beta heroes. OW still draws
its own hands, weapons, animations and HUD. MC still owns the real world, feet,
gravity and swept block collision. It does not replace heroes with MC statues.
Current status must be read from TAKEOVER.md and the private research folder's
code-final-audit.json. No project games/supervisor are running at that audit.
The last live suite is incomplete/failed, and no final live audit was produced.
The user is currently using the PC and requested **code work only**.

## Two reproduced faults

The old motor path imported cumulative native displacement for seven heroes.
Actual Hanzo/Bastion/Mei/Torbjorn/Widowmaker W->S traces kept moving in the old
direction for5–7 MC ticks. Hanzo's backward median was about2.68m/s instead of
the declared4.95. Source game velocity could also remain nonzero after release.
Reaper/Soldier had a special responsive correction; other heroes used a different
route. The old native totals must not be reintroduced as normal walking authority.

The original body received vanilla post-travel friction velocity, about2.33m/s
while actual MC displacement was5.5–6m/s. That did not represent the native-speed
move which had already completed. Original hands/body could retain an incorrect
slow-moving pose. Actual displacement and original pixels are separate checks.

## Original computed speeds, without guessed multipliers

The existing reflected STUCharacterMoverComponent contains six BASE speeds.
The current native runtime component15 contains six COMPUTED speeds at
300/304/308/30c/310/314, including active original modifiers. Read-only actual
disassembly at10b3270..10b32c5 selects forward/back/strafe and crouch values;
105566c/1055693 and105add1/105ade9 are additional original consumers. Private
bounded code evidence and the live Widowmaker speed differential are retained.
No original function is called by this reader and no speed field is patched.

Actual scope observations changed native run5.5->1.925, backward4.95->1.7325,
crouch3->1.05, and scalar1->.35 together. These are the offline beta's values,
not a substituted modern retail table. The user's source remains0.8.0.24919.

Locomotion binding schema2 records the current runtime mover as well as the
reflected base definition. The MC read-only reader checks exact process creation,
host generation, admin/controller/model/hero, definition/vtables, component15
owner and membership of the current model's bounded component list. Computed
values use at most3 double-read attempts, finite, nonnegative and at most3x base.
Zero is valid for a native movement restriction. Bad/stale/replaced data stops
movement and cannot inherit another hero's speeds. /combat reports baseSpeeds
and effectiveSpeeds separately, with speedSource native-computed-directional-limits.

Changing computed fields must not look like a new hero. If all3 pairs differ,
the reader revalidates the process/model/hero/mover owner and membership, returns
no movement speed for this tick, clears diagnostic velocity, and retains only
the still-verified identity. No last-good speed is reused. Coherent reads are
also followed by identity verification. Real scope changes or invalid values
still close the binding. A package-private fixture seam mutates only Win64
self-process test memory between reads; it installs no hook/callback into OW.
Tests prove one-change retry, bounded continuous change without false identity0,
recovery, and actual model/owner changes during the same reads. This code-only
addition passed headless checks and remains pending live validation.

All ordinary heroes now use current input direction and those six computed speeds.
The former motor group no longer requests native flight/motor accumulated motion.
Pharah's real native flight stream and Tracer's real Blink stream retain their
separate routes. MC swimming, lava, vehicles, elytra and the custom F6 flight keep
their existing routes. Bastion retains unique original Recon/Sentry/Tank checks;
unknown/conflicting/transition/Sentry forms remain horizontally locked. Native
slowdown/sprint are not reapplied as an extra guessed boost.

BodyMotionSample exports completed real MC tick displacement for animation.
Collision/release export zero; blocked inputs do not manufacture walking speed.
Player/world/hero/model/source changes, missed ticks and large teleports baseline
instead of creating a velocity spike. Repeated publication in one tick retains
the same sample. Grounded vertical velocity is zero. It never changes MC physics.

## Additional real Bastion defect

The actual initial probe found Sentry still able to perform a1.2522m MC jump;
Mei Cryo did not jump. The final guard reads actual original Sentry/Recon/Tank
states, not Shift or an invented timeout. Sentry/transition cannot trigger MC
jump or enable F6 flight. Existing F6 flight can still be turned off. Recon/Tank
do not acquire this lock. McCree's previously accepted fresh-native-Q jump/flight
restriction remains independent. See root-probe.json and root-fixed.json; a
passing candidate's horizontal test did not prove its rooted jumping was fixed.

The actual root-fixed receipt has no recoveryRise field: the test process had
loaded its script before that recovery check was added. Sentry/Mei restriction
passed, but same-model jump recovery cannot be claimed from this receipt.

## Background cursor ownership after dimension transfer

The original final suite failed at Nether Genji selection. Read-only native
identity remained McCree/fullHP with advancing composed frames; the visible
picker preview did not mean selection had confirmed. Actual GetClipCursor gave
320,180,2240,1260, exactly MC's client rectangle, while OW was foreground with a
2560x1440 client. Clearing the clip in the isolated diagnostic and transferring
MC recreated it. The clipped Genji x218 became x320/McCree, and confirm y1358
became y1260/the hero row. See clip-probe.json and clip-mc-client.json; the failed
selection screenshots were actually inspected. This was a real input defect,
not proof that a current native model or combat initializer was dead.

HostMouseCaptureMixin now gates MC Mouse.lockCursor on exact real Win32 foreground
HWND equality. It is scoped to Windows frameExport+hostMovement fusion; ordinary
MC is unaffected. No native owner, input detour or global cursor-clipping write
was added. The actual96f candidate denied background capture and retained usable
Genji/McCree selection after Nether/End/Twilight transfer. Deliberate MC foreground
capture still requires a live test. The fourth return-to-Overworld selection
failed amid focus changes during PC use; that suite remains failed.

## Models and explicit limits

The21 native first-person models were actually captured during real hero changes.
Resting/carry poses are not missing exported assets merely because a weapon is
low in the frame. Correct motion feedback restores presentation without a new
generated weapon mesh or skeleton. Images/contact sheets need actual review;
a ready flag or successful model pointer is not visible model acceptance.

This is not complete all-skin, third-person, alternate-weapon, transformation or
full-kit support. D.Va currently appears in the actual pilot form with the native
pistol; full Mech creation/ejection/recall/model lifecycle remains unfinished.
The upstream [Prometheus documentation](https://github.com/saturn-xvi/prometheus/blob/main/README.md#3-broken-stuff-and-why-its-broken)
also records D.Va floating and speculates that the Mech is not spawned. That
upstream speculation is not proof of this project's remaining root cause or a
reason to forge a server acknowledgement. The user previously allowed difficult
server-dependent features to be deferred. Quarantined Reaper experiments remain
disabled. No full hero-body mesh, complete server-driven ability or180FPS claim
follows from these base walking checks.

## Evidence discipline and reproduction

Backups are in ~/.universal-modder/backups/all-hero-locomotion-*; backup.json
records source/config UM snapshots and the separate on-disk world/profile ZIP.
The live snapshot excludes session.lock and does not claim to include unsaved
in-memory world changes. Normal stops26572/8204/12508 used strict restoration;
their three strict-stop receipts retain all owner flags. Six native
DLLs were not changed or overwritten; only the guest JAR and Python binding change.

* baseline first stopped when combat-only readiness rejected Junkrat. This is a
  harness failure; presentation/movement can exist while combat remains pending.
* baseline-v2 records21 actual observations, not a passing final acceptance.
  Its unrecentered small platform was eventually exited; Winston/Zarya airborne
  rows cannot certify their independent flat-ground movement. Final runs use
  explicit creative-only locomotion-origin on the same reversible fixture.
* Candidate live-v1 has21 passing BASE walking traces and20 ordinary MC jumps.
  Its overall result remains FAILED: Pharah's actual .5539m short-Space native
  hover was wrongly compared with an ordinary MC .7..1.5m jump. core-walk-acceptance
  explicitly accepts only its base walking slice, preserving the whole-run failure.
* Candidate modifiers passed actual Soldier sprint8.25, Widow scope1.925, Hanzo
  drawing3.30 and Bastion/Mei horizontal restrictions. Candidate pharah-response
  passed actual real-fuel Space pulses,7.90m/s peak,58–74ms observed rise delay,
  three original primary emissions/muzzle flashes and replay. These are bounded
  observations and distinct from the final rooted-jump deployment.
* Final39-task build/check includes Win64 computed-speed identity/value fixtures
  and actual-displacement/collision/teleport/scope checks. Proper Java-backed HTTP
  contract and45 supervisor fixtures passed. Fixtures are not actual game play.
* final-all21/result.json passed/cleaned on4c/native12508:21 heroes' base walks,
  reverse/release/strafe/ground/body-speed and20 ordinary jumps. The full native
  contact sheet was viewed. final-modifiers and final-pharah separately passed.
  root-fixed passed zero Sentry jump/F6 and Mei root; recovery was not tested.
* Top-level final-suite.json remains FAILED at the first world selection. It
  cannot accept a world movement/attack matrix. cursor-final/final-suite.json
  also remains FAILED, with only3 completed cursor/Genji/McCree transfer rows.
  Fourth-world focus/selection failed; all21 and world attack phases never ran.
* Latest native25864 exited0 and MC12036 was then stopped by the supervisor.
  cursor-final/exit-observed.json records process-exit-unclassified with no
  matched report. User confirmed PC use, not a manual close. Cause remains
  unproven; absence of a report is not no-crash evidence. Interrupted cleanup
  was not accepted. No project games/supervisor were running at the code audit.
* Final built source fe2924bd... contains bounded coherent-read protection;
  profile remains96f7ec3e... and was not modified after the code-only reply.
  Full39-task build, proper HTTP contract and environment checks passed. No
  new game acceptance applies to this last build. code-final-audit.json pins
  both hashes and the6 unchanged native modules; there is no final-audit.json.

Run tools/verify_hero_locomotion.py --pid <current-verified-pid> --output
research/<new-private-folder> --jump only in the backed-up full-mod Switch lab.
It uses protected real OW input, unique actual MC body ticks, native health/model
checks and real composed-window captures. Pharah is separately tested by
tools/verify_pharah_response.py because Space is native flight. No human play
acceptance, crash-root-cause repair, all-hero full-kit or original asset parity
is implied. Historical TIMER and startup825346 crash sources remain unproven.
