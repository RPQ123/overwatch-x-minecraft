# Widowmaker Infra-Sight: native phase, MC creature outlines

## Implementation and source scope

The actual current offline Beta24919 graph0067 was observed in
`research/sprint-20261024/widow-infra-calibration1`. Original nodes6(animation),
13(effect),10(timer) and18(ultimate windup) are typed and bound to the exact
current owner/model/graph. Animation6's declared duration is the original
integer15; the current duration variable237 was also15. Those values came from
this client, not a guessed modern balance table. The observer installed no
callback and made no native script calls. The Q lab grant is diagnostic only.

[Blizzard's Classic retrospective](https://news.blizzard.com/en-gb/article/24146047/a-blast-to-the-past-begins-with-overwatch-classic)
and [official hero page](https://overwatch.blizzard.com/en-us/heroes/widowmaker/)
describe the original enemy-location reveal. Retail perks and modern balance
are separate from this2015 Beta and the explicit MC adaptation below.

Native hands, animation, red screen/visor overlay, HUD, meter consumption and
ordinary weapon remain original. MC's real outline compositor highlights real
loaded living nonplayer creatures through blocks. This single-player policy
includes animals/villagers/Boss roots; it is NOT an authenticated OW server team
or invisibility rule. No chunks/entities are loaded/spawned to reveal them, no
damage/weakness/armor/phase is bypassed and no global glowing flag/scoreboard team
is changed. It reuses the local Sonic outline query and post-outline frame
capture. MC's original terrain/collision/rendering remain authoritative.

Fresh native animation/effect/timer state is required. Attaching to an already
active Q is only a baseline, never a synthetic Begin. Repeated snapshots cannot
extend the fifteen-second presentation cap. Native End, missing/expired source,
menus/focus loss, death or hero/world/model/session changes remove the view.
After losing admission it will not silently join the old still-running Q.
That conservative non-rejoin policy is explicit, not full menu-pause parity.
Original150ms source/view freshness and500ms camera bounds were not widened.

The charge adapter now reads original Widow windup/animation/effect/timer
phases. It suppresses both time and damage credit throughout Q/unknown binding,
then resumes only fresh idle credit after End. Other heroes retain their prior
policy. Generic meter writes still use the existing original logic-thread
owner; no second writer/callback or render-thread script call was added.

## Actual validation

Accepted guest860dd3c730487c3f2bd630ac67d4675146fec00285737f6e86621f81e87121b6
is cold installed after normal restore/exit/save. Six native42/26/11/16/10/1
unchanged. `research/sprint-20261024/widow-infra-acceptance.json` indexes six
actual Q passes and two shared-code regressions, each passed/cleaned/video0.
The first live1 failure remains separate. Source/build/installed identities
and final real runtime audit are recorded there, not inferred from old PIDs.

Four actual expiry runs passed/cleaned/video0: live2(Overworld),Nether,End,
Twilight. Real stone-covered target remained20HP, real red outline appeared,
and was gone after End. The observed sampled view span in the first run was
14.937s; whole native phase cleanup was observed about15.7s after first view.
Do not equate those two observation endpoints with an exact15.000s timing test.
Active original meter stayed0; idle natural credit resumed afterward. Native
ordinary fire afterward20->17.400002 in each world.

Actual hero-interrupt and Twilight->Overworld-interrupt runs passed/cleaned/
video0. During Q a real rifle hit damaged20->17.400002 while meter remained0.
Selecting76 cleared old vision; new Widow did not replay it, and her ordinary
fire still worked. World handoff removed old reveal rather than joining the
departed world's Q. This is Infra-Sight's bounded lifecycle, not the full Widow
kit, physical portals, death/revival or all hero completion.

First live1 FAILED before Q: the new Python binding branch referenced a name
shadowed by a local import in another branch, raising UnboundLocalError and
ending supervision. Both games remained alive. Its logs/result stay failed.
The read-only binding uses its own import alias now; direct current binding
passed. Supervision was restarted against the same verified six owners/processes
using the existing connect-stage checks, without re-injection or game restart.
New live2 actually passed. No old failure was rewritten.

Pure fixtures verify baseline/Begin/End, repeated/future/stale data, scope changes,
and charge admission/suppression.55Gradle tasks,52supervisor fixtures,8binding
acknowledgement fixtures and the
correct HTTP contract passed. They do not replace visible native/MC acceptance.
No third-party source/art/audio imported. Pre-change private backup:
`~/.universal-modder/backups/widow-infra-20261024-104646`.

Actual Sonic regression still showed the red silhouette through real stone,
ordinary arrows20->7.5, correct expiry/replay and ordinary recovery; root viewed
its new image. Actual Mei regression retained partial chill/freeze, wall cover,
AI/travel stop/expiry/restoration, replay and icicle recovery, with its image
also viewed. These are one-world shared-code regressions, not new four-world
acceptance of every older skill.

The production supervisor now also refuses ready when Widow's current original
skill acknowledgement is absent. Its Python-only restart/adoption(supervisor3)
preserved the exact same two games and six callback owners; no game restart or
second injection. Final helper actually reentered Widow, verified new original
skill/meter/movement/composition readiness, cleaned, and returned to the original
animated Widow picker over real Overworld sky. Root viewed that frame.
Final historical native14644/creation1792810237.9891343,MC31492/
1792810220.3256333, supervisor31144/child; re-audit before further inputs.
Actual MC20HP, no test targets/wall/freeze/reveal at final-state.json.
Accepted source/config/profile/JAR snapshot:
`~/.universal-modder/backups/accepted-widow-infra-20261024-110826`.

Remaining Widow items include grapple/venom lifecycle and fuller voice/target
semantics. H pose publication gap and original TIMER corruption remain OPEN;
this increment is not their root-cause fix.
