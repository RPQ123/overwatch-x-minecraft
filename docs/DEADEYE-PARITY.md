# Deadeye cadence, export grade and per-shot audio — 2026-10-22

This is the original offline beta + real Minecraft passthrough, not a replacement
OW hero implementation. Native heroes, hands, HUD and animations remain native.

## What was wrong

The former adapter waited for each node69 animation's approximately330ms End
before requesting the next target. File exchange added further delay. Read-only
inspection of the actual guarded client's graph022f instead finds the original
target loop71 -> Wait72(.1333000064 seconds) ->73 ->66. The animation envelope and
the server target-loop interval are different quantities.

The native Deadeye postprocessing did not grade the separately exported MC world,
and manually entering original animation69 did not establish a complete native
gunshot/muzzle event chain. These were genuine presentation gaps.

## Current implementation and boundaries

* The server requests the next target after one admitted original animation Begin,
  instead of awaiting the previous animation End. The existing native logic owner
  validates actual Wait72, model, script, graph, Q Begin, code and world before
  restarting original node69/AnimAlias019f. A134ms wall-clock lower bound honors
  the authored interval. Native simulation timestamps are16ms quantized; real
  normal tests report128/144ms steps. Only the final shot awaits natural recovery.
* Every target is damaged separately on its own fresh native Begin receipt. The
 150ms damage freshness rule, actual MC collision/cover, identity and replay
  guards remain. Existing server target-order approximation and six-target cap
  are NOT certified as the original full server targeting implementation.
* Body14/request version2 adds an explicit MC acknowledged-sequence field. Native
  Begin cannot be overwritten by End until that exact MC shot is acknowledged.
  Its original wall time is never refreshed to invent fresh damage. A missing
  consumer acknowledgement times out after1s to cancellation/recovery, not damage.
  Same-scope fresh End re-acknowledgement still avoids replaying animations.
* MC background gets one GPU sepia pass only while a fresh scoped native McCree Q
  is active in first person. The0.4s entrance follows the authored graph's chase
  duration. Original MC framebuffer/depth and native hands/HUD are untouched;
  picker, scope loss, hero/world change and Q End clear the grade. This is an
  explicitly adapted sepia presentation, NOT a recovered original OW shader or
  pixel-identical vignette/tonemapping. Cosmetic shader failure falls back to
  ordinary world export, without disabling combat or the full frame exporter.
* One private original-beta Peacekeeper recording plays per admitted shot. Its
  source is an actual single native primary shot on22512, with hash-pinned OGG
  conversion and a50ms tail fade. It is NOT certified as the unique Deadeye sound
  asset. No key press alone plays a shot; sounds are scoped/deduplicated and old
  tails stop on session reset. Classic Mandarin Q and all21 accepted selection
  callouts remain intact. The website's candidate revolver clip did not match
  beta audio adequately and was not deployed.

Original reference videos are private under ~/.universal-modder/assets/owmc-mccree.
The2015 [official ability overview](https://www.youtube.com/watch?v=kq4OlEDiCi8)
and the [official hero page](https://overwatch.blizzard.com/en-us/heroes/cassidy/)
are references; the2022 official Deadeye demo shows sepia, but has silent audio.
The attempted unconstrained image-fit grade is retained as rejected research;
production uses an explicitly positive-coefficient sepia adapter.

## Real tests and failures

Final selected body14 + guest49ac34c2... also actually passed all four dimensions
under final-four-dimensions-v14. Mid-sequence-v14 used a persistent protected
driver to interrupt this faster sequence: both a real world transfer and opening
H after the first shot produced no additional old shot, no pending queue, no
remaining grade and ordinary20->13 fire after reselection. pharah-e-v14 passed
again. normal-stop-v14 proves real strict restoration before the final cold
delivery launch; TAKEOVER/final-audit identify the current picker session.

Evidence lives in research/mccree-deadeye-parity-20261021. Before changes, profile,
settings and sources were backed up under the private UM backup folder referenced
by backup.json. No source reset, unrelated commit, game/voice asset publication,
second callback owner or loaded DLL overwrite was performed.

Body13 + guest26c8ca58... passed final-four-dimensions-v2: Overworld, Nether, End
and Twilight Forest, Genji->McCree each time, E real75-equivalent damage/2s potion
slow/exact50% speed/recovery/replay; four individual20HP Q deaths, native cadence,
four sound schedules, sepia entrance/clear, actual meter debit to0 then native
End/passive recharge,1/2/3/wheel filter, ordinary revolver20->13, fullHP and current
model light checks. The earlier four-dimension run hit the End build-height limit
in its lab setup and is retained as a failed harness run, not a gameplay pass.

live-accepted contains actual native video and MC mixed audio: four UNIQUE shot
matches, correlations approximately.53..68. Observed mixed-audio delays107..149ms
include game audio scheduling/mixer/capture latency; zero-latency audio is not
claimed. A broad first analyzer could match one loud shot twice and was corrected
to disjoint ordered windows. Shots and recording are separate evidence types.

The first body13 transport-contention run is a real failure: after650ms file
sharing contention, the second native Begin was overwritten by End before MC
admission, leaving three targets alive. Body14 adds the explicit acknowledgement
above. transport-contention-v2 actually passed on29540:650ms held file,37 real
AccessDeniedExceptions, four individual20HP deaths, four original starts/Ends,
no replay and ordinary fire recovery. The one intentional hitch is measured
separately from normal cadence; the test does not relax production freshness.

The first candidate startup also had a version-label mismatch (DLL13 reported12).
It was stopped/restored before rebuilding with matching metadata. Terminal JSON
rename races were recovered only with exact loaded DLL hash + current terminal
packet + read-back proof of the original native callback table. Stop tooling now
supports pinned body13/14 and emission13, and still refuses partial compositor
input/light/frame-limit restoration. These are not native crash-root-cause fixes.

## Remaining work

Confirm the final body14 current-session audit and latest real regressions in
TAKEOVER.md. Exact original full target ordering, aim-at-target rotation, all
muzzle events, unique Deadeye sound resource and original postprocessing remain
unverified. Native TIMER pool corruption and distinct startup825346 failure have
no proven root-cause repair; no new error report is not crash-free certification.
