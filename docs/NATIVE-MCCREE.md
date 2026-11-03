# McCree E/Q and player utilities — 2026-10-21

## 2026-10-22 — Cadence, sepia, shot audio and receipt acknowledgement

Read [DEADEYE-PARITY.md](DEADEYE-PARITY.md) for the current body14/request2 route,
the original Wait72(.1333s) target-loop calibration, separate original shot/MC
damage, export-only sepia and private recorded-beta gunshot adapter. Body13's
four-dimension normal run passed, but a650ms IO test exposed an overwritten Begin
and stuck queue. Body14's explicit consumed-sequence acknowledgement actually
passed the same fault (37 IO failures/four distinct deaths/no replay). Preserve
the150ms damage deadline and original logic-thread ownership. Current audit and
latest body14 real regressions are in TAKEOVER.md; do not select body12 merely
because older acceptance paragraphs below mention it. Original postshader,
unique Deadeye sound resource/full muzzle chain/complete server target ordering
are still unverified, despite the now-working adapted presentation.

## 2026-10-21 19:56 — Four dimensions and transport-fault acceptance

Latest selected production modules: compositor40 + logic/body12. Guest SHA256
4559dae89a83141fce4fe644b6d0fa44caf98c6a8521316c307b374ef4b479ce;
body12 SHA2567f459da5cbfad32683a8de3bc3d7a10befae95d789120efc792507ae433e7905.
Native23132 and actual Minecraft5808 are independently supervised. The source/
profile/config backups, all failed tests and actual videos remain under
research/mccree-native-shots-20261021/; no game/extracted/voice data is committed.

**Actual final-four-dimensions/result.json passed all four real dimensions**:
Overworld, Nether, End, Twilight Forest, each Genji->McCree recreation followed by
original E/75-equivalent real damage/2s Slowness potion/exact50% slow/expiry/replay;
native Q lock, individually timed original animations and real MC deaths;
actual charge debit to zero during fire, native End/recovery, ordinary20->13
revolver after1/2/3/wheel input, fullHP and settled current-model light. Overworld
shot six targets including nearby mobs, other dimensions four. F11 is an explicit
full-charge test grant; this test is not natural full-charge acceptance.

The final fixes include two independently reproduced transport defects. Natural
Windows AccessDeniedException on atomic replacement of the request file used to
reset confirmed Q admission through the general exception handler. Presentation
IO now retries separately, keeping the original activation and all150ms damage
freshness/identity requirements. A deliberately held read-only handle denying
delete/rename for650ms reproduced a second defect: native animation End was older
than150ms by the time the request writer recovered, leaving the queue stuck.
Body12 can re-observe/re-acknowledge the same original completed End for a fresh,
exact matching request. It preserves the original animation tick and performs no
new animation, damage or completion-count increment. Changed owner/code/world/
ordinal and changed state still reject. The fixture tests the expired-End refresh.

**transport-contention-v3/result.json passed**:650ms held request,36 actual IO
failures, then four native animations/four individual20HP deaths and normal
recovery/fire, no duplicates. Previous v1/v2 harness/fault failures are retained;
v2 demonstrated the stale-End stall and is not counted as passed. The initial
short final-meter assertion was also corrected: charge really reached zero and
then passive charging resumed during the longer animation wait; the fixture now
checks the actual fire-time debit rather than demanding near-zero after idle.

**chinese-actual/accepted-audio.json passed**: actual MC process audio (f32le48000Hz
stereo, not the video-only MKV) correlates.98768388 with the private Chinese Q clip.
Native shooting video/native-contact.png was inspected: native revolver/hand
animation occurs separately as MC victims die, then ordinary weapon pose returns.
Clip provenance remains the2016 catalogue stated below; earliest2015 or exact
recording date is not certified. No Genji or E voice replacement was made here.

Compositor40 has zero script-notification invocations; body12 shares the original
weapon logic thread. Current23132 render24444 differs from body/weapon13980.
The known native timer pool corruption still has no proven writer/root repair.
28272,17964,23400 survived bounded active tests until explicit normal shutdown;
their strict input/light/frame-cap restoration receipts are retained. Current
23132 actual combat regression passed without a matching crash so far; this is
bounded evidence, not a long-session/no-crash guarantee. The single current
read-only timer observer is live23132; do not stack another reader on this identity.

Remaining original presentation parity: exact native server target ordering,
target-directed aim rotation and complete muzzle/effect/sound event sequence are
not established merely by running original animation69. Keep these limits separate
from the accepted per-shot visible animation/damage/Chinese callout slice.

Final mid-sequence/result.json additionally passed actual world transfer and
Genji selection during a running volley: after changed owner/world settled,
shots stopped, no pending target damage crossed the boundary, and fresh McCree
ordinary20->13/fullHP recovered. Final-audit.json verifies six actual unique
modules, exact current disk hashes, zero owner failures, zero test blocks/pending
shots and no matching current crash report. Actual final-visible_small.png shows
animated McCree picker over real MC Overworld. Independent supervisor2100/12964
remains; no extra callback was installed to leave the games available.

## 2026-10-21 19:45 — Native shot presentation and Chinese audio; regression in progress

The historical audit below described the old batch implementation. Source now
uses the actual supplied `StartStopState` helper (inject RVA7acd0, exact matched
PDB/code) to start original graph022f animation69 / alias0c8000000000019f once
per acquired MC target. Node44 is only the original fire intent. The MC service
admits one shot after an actual native69 Begin receipt, advances after End, and
requests the existing native recovery only after the final animation. Real LOS,
loaded-chunk, owner and range checks run again for every victim. Request160-byte
and receipt88-byte identity/freshness guards reject stale/different sessions.
No custom hand animation, synthetic WeaponVolley or native target is fabricated.
The exact original server target order, aim-to-target rotation and full muzzle/
audio-effect sequence are not established by animation69 alone.

Actual first-sequence/result.json (native17852, compositor39) passed four
separate original animations and four real MC deaths,395/404/389ms apart,
charge debit, replay refusal and ordinary20->13 revolver recovery. Its visible
actual.mkv/contact sheet is retained. That client then crashed with the known
TIMER release signature; do not call that build stable or four-dimension accepted.
Native-only3900 one-shot experiments proved69 playback/End while retaining Q;
starting68 instead caused the empty-native-target loop to end Q. Private probes
restored their swapchain before normal shutdown. They are not startup modules.

Selected compositor40 no longer invokes script notification/animation helpers.
Selected body11 invokes both the unchanged meter Set&Notify and animation helper
on its existing native logic callback, after the original update and fresh stable
guest/hero validation. No second callback is added. Actual28272 measured render
thread27216 versus body/weapon thread21736, establishing that these are different
threads. This fixes a cross-thread ownership concern; it does NOT prove the old
timer's corrupting writer. Actual28272 survived repeated combat/switch tests until
intentional strict stop; all input/light/frame-cap restoration acknowledgements
passed. Its first startup used a stale body10 selector; that failed closed and was
normally restored, then the selector was corrected. Both failure and stop records
are retained. Original DLL38/39/body10 files were not overwritten while mapped.

Regression discovered another actual sequence-loss boundary: in End, three of
four native shots completed, then MC cleared the remaining queue while native Q
was still active. Old150ms read/context gap handling discarded admission. Current
guest0136dabf… retains admission/queue for at most1000ms while paused, but every
damage/receipt still requires a fresh150ms state. Real cancellation/death/model/
world changes clear immediately. The controller no longer consumes a receipt
before server admission; server exact-once logic owns that decision. Status now
records staleHolds/cancelReason. Native17964/MC28624 is cold-retesting this patch;
read actual gap-four-dimensions/result.json before claiming acceptance.

Chinese Q private source is the 2016-06-13 catalogue at
https://www.962.net/patch/103368.html (archive file contains one MP3). The installed
private speech clip is deadeye-zhcn-2016.ogg, SHA256
c9aa7c6c46ec7d3734dceab1a10772d459802f8295b902574bcaeb1dd229ff43.
It is the listed Chinese "午时已到" recording, trimmed without pitch/synthesis.
2016 catalogue date is not proof of recording date or earliest2015 provenance.
Known old English destination migrates with a private backup; unknown user files
fail closed. Five migration fixtures passed. Actual scheduled/playing status has
passed, but actual mixed-output Chinese correlation is still pending. E voice
and Genji Japanese pack remain unchanged; do not claim all voices localized.
Private assets/extracted originals/videos stay out of commits.

Native/body fixture builds,35 guest build tasks,45 supervisor tests,18 strict-stop
tests,5 voice fixtures, environment prerequisites and the proper standalone HTTP
contract entry point passed. Real four-dimension, cancel/hitch and audio results
take precedence over these fixtures. Evidence: research/mccree-native-shots-20261021/.

## 2026-10-21 18:39 - Deadeye implementation audit and claim correction

Read-only current SHA-guarded native30248 resource inspection confirms original
constructed resource058000000000022f is present. Native nodes18 state,27/92
TrackTargets,25/48/50/69 Anim,44 Effect and90 SendGameMessage match the retained
original graph. The current selected model was not McCree; no hero switch/input
was sent. This is original configuration presence, not visible animation playback
acceptance or proof that every referenced animation clip is available.

Current NativeDeadeyeController/Events labels node44 as fire. Its real type is
STUStatescriptActionEffect, NOT a per-target WeaponVolley or projectile factory.
The historical actual-probe Qfire receipt has a node44 change, zero factory
observations and no per-shot native sequence proof. It supports the observed
activation/effect boundary, not a fully restored original multi-shot firing path.
NativeDeadeyeRuntime currently loops over up to six acquired MC targets in one
server invocation and immediately publishes Completion. NativeDeadeyeFinish then
requests original RMB recovery. This explains batched MC deaths. Early recovery
may truncate presentation, but the causal explanation for absent draw/fire
animation requires an isolated frame-by-frame/native-state test; it is not yet
proven. Do not claim the original game lacked Deadeye, that its animation assets
are absent, or that the complete original shooting action is accepted.

MC target acquisition/LOS/damage/lock markers, native meter feedback and bounded
offline completion adaptation are project-authored. Native ability state graph,
original weapon/HUD and available animation/effect machinery are retained. Native
code does not know MC entities without an adapter. English AB5E audio remains
installed, not classic Chinese. Official hero ability reference:
https://overwatch.blizzard.com/en-gb/heroes/cassidy/ . Current native audit receipt:
research/mccree-audit-20261021/native-presence.json . No DLL/JAR/settings/gameplay
changes were made; no assets or animation completeness inferred from node names.


## 2026-10-21 17:25 — Timer-notification identity and exit0 crash evidence

Read NATIVE-TIMER-CRASH.md. Guarded actual-image disassembly now identifies the
three crashes' object as a **TIMER notification**: d14200 selects byte+0x22;
table d14440 maps type1 to d14266, whose d1428b virtual destructor call crashes.
Type8/attribute-change instead maps to d14405. The provided header agrees. The
visible f4f600 detour belongs to the supplied logger, not our d354b0 projectile
factory. This is object-category evidence, **not proof of the corrupting source**;
the native crash remains unfixed. Do not suppress arbitrary timers or blame the
notification/UI/input/GPU path without causal evidence.

Fixed a separate supervisor gap: after supervised gameplay exit, a matching local
error report now produces nativeExitClassification=crash-report plus evidence,
even if nativeExitCode=0. Exact project reporter executable/arguments, actual
redirected Documents, PID/time/Application/size/stable-content checks prevent
misclassification. No report is sent and no crash/restart loop is introduced.
Ten report-identity fixtures and45 supervisor tests pass. Actual historical
38368/26516/13448 files are all recognized with their reporter windows closed;
current30248 has no matching crash report. Picker-only startup exceptions are
still the older path, explicitly not claimed as fully upgraded.

The updated independent supervisor adopted the **same** native30248/MC23340 and
the same six healthy native owners; no game restart, extra injection, callback
owner, gameplay input or test target was introduced. Actual paths/hashes/JAR
b09fe17e… were rechecked; composition/fullHP/full original meter pixels inspected
and125 frames advanced in the final read-only audit (not an FPS guarantee).
The same native process had been alive about52minutes at the final audit; idle
survival is not sustained combat acceptance. Evidence is under
research/native-timer-20261021/ and the earlier notification-lifetime/crash13448/.
Current real supervisor worker16448 adopted via the existing exact-project
stop_supervisor control and normal startup/stage_ready ownership checks.
All potion/charge/HUD/slot/voice/Visor/strict-stop settings/artifacts remain as in
the previous accepted section. Highest next work is timer allocator/queue/release
ownership, originating script/user data and possible reuse/double release.

## 2026-10-21 16:35 — Applied potion survives hero reset; strict stop; crash evidence

This is the latest artifact/acceptance section; earlier sections are historical.
Guest SHA256 `b09fe17e98a78449727b6ff91988f7b2b5a00d1d71693aa21f06b8595b7a4506`; native six DLLs unchanged (compositor38).
Final actual native30248/MC23340, independent
supervisors15792,26100. Current identity,
hashes, actual native pixels and cleanup are in
`research/mccree-polish-20261021/mid-effect-final-audit/final-audit.json`.

Reproduced the previously documented boundary: E hit followed immediately by H /
Genji selection made NativeSessionGuard remove Flashbang's compensation while
vanilla SlownessIII still had8ticks left. Effective target speed changed.25 ->
.274999991 (45% slow), before returning.5. This was a real gameplay defect;
the initial harness also hit a transient diagnostic reset and is retained as a
failed test, not confused with lost native attacks. Guard reset now preserves
already admitted victim effects. MC server ticks own their expiry; server stopping
still calls the full cleanup. No input/admission/native model lifetime guard was
relaxed. Actual accepted E->H/Genji sequence kept exact50% through the remaining
8..1 potion ticks after the guard reset, then restored speed and particles.
Fresh McCree ordinary20->13 shot, full health and current-model light passed.
`mid-effect-accepted/result.json` is the actual receipt. General mod abilities and
victim chunk-unload/potion stacking semantics are not promoted to accepted.

New guest repeated all four dimensions: E actual damage/2s potion/exact slow/
expiry/replay, Q four locks/actual kills/remaining meter debit/native End,
ordinary fire after slot input, full HP and settled actual light all passed in
`mid-effect-four-dimensions/result.json`. Recovered-session Soldier76 core test
also passed: `native-visor-32760-1792571541722132900.json`.
35 guest build tasks,18 stop-report tests,3 session-stop tests,45 supervisor tests,
proper HTTP contract entry point and environment prerequisites passed.

Fixed a stop acceptance race independently of the gameplay patch. An actual32784
report said enabled=false/restored=true while slotInputRestored,viewLightRestored
and nativeFrameLimitRestored were still false: render stop publishes its vtable
result before all releases finish. The old helper could then terminate too early.
`restoration_complete` now requires all three release acknowledgements and
slotInputFilter=false for compositor37+, in both polling and session skip/final
checks. Regression fixture rejects each missing/false flag and wrong PID. Actual
strict32760 stop, preserving MC, completed with all flags true/failures0; fresh
native was cold-started afterwards. No mapped DLL was overwritten or extra owner
installed.32784's earlier incomplete snapshot is not accepted as full restoration.

**Open native crash:** after the four-dimension pass,13448 exited before the next
Visor test could begin, opening this project's BlizzardError reporter. Exit code0
was captured but is NOT a healthy exit: its minidump has execute access violation
0xc0000005, RIP in heap data, caller original native RVA d1428b / return d1428d
(`call [rax]`). Earlier38368 and26516 error logs have the same native call stack.
Private original logs/minidumps and guarded live read-only caller disassembly are
preserved in `crash13448/`; source reports are under
`D:/wendang/Overwatch/Logs/Overwatch/errors`. Error-report windows for exactly these
three project PIDs were closed without sending anything. The original provided
client error handler returns0, so future audits must inspect its reports as well.
The corrupt object's owner/cause is still unproven. Do not assert it is a user,
time limit, input hook, notification call or GPU fault; do not mark sustained
stability solved. The failed first Visor attempt is separate from the later pass.
Highest next priority is identify this native object/lifetime before adding kits.

Final audit: full native200/200/MC20, grounded Overworld/F6OFF, real passive meter
growth, ordinary shot after all top-row/numpad digits/wheels/actual middle click
and no duplicate replay, six actual mapped identities and matching installed/built
JAR, targets/random test mobs/air floors cleaned, native frames advancing and
visible composition inspected. Source settings remain Hollywood/1080p/Low/
8chunks/no shaders/day-night cycle. Private classic voices and real F9 diamond
activation were not changed. Hourly automation now prioritizes native crash
reports and strict restoration, retaining the user2s override and other fixes.

## 2026-10-21 — McCree potion, original charge HUD and slot-input repair

Final cold-start32784/MC26620 passed `mccree-polish-20261021/final-audit.json`:
all top-row/numpad digits, both wheel directions and actual middle-mouse click,
then ordinary20->13shot/replay; real passive charging and native visible60% HUD.
Six actual mapped owner hashes and installed/built JAR agree. Grounded fullHP
Overworld, F6OFF, fixtures cleaned and independent background supervision active.

This section supersedes the older1.2s/compositor34/b295 baseline below. User now
explicitly requests **2 seconds of visible Slowness potion**, a custom duration,
not a claim that the modern official duration changed. Active guest SHA256:
`e67325ca84c08abc528258490f295be74300186457d5cc21ebec7bd926b84892`.
Compositor38 SHA256:
`320a13ba1d4748e6f0a425de1acac5497e8fd3c60c1abe2c29ee37b60fc85a7d`.
Body10/gate9/emission12/bootstrap10/localhero1 remain unchanged.

Real four-dimension Genji->McCree tests passed in
`research/mccree-polish-20261021/lifecycle-final38/result.json`: E75 native-HP
equivalent damage, exact50% effective speed, actual40tick potion with particles,
expiry and replay; Q four real locks, actual fire/kills, meter debit, automatic
native End and immediate20->13 ordinary shot after1/2/3 and both wheel directions;
full native health and independently read current-model camera-relative light.
Read-only light diagnostics initially refused compositor38 because their version
allowlist ended at34; fixed the diagnostic and reran, rather than relaxing light
ownership, hash, map or direction checks. Visor24436-1792568941537642800 passed.

Flashbang now gives actual SlownessIII for40server ticks; an extra modifier
compensates vanilla45% to the requested50%. Potion rendering is vanilla MC.
The impact burst combines FLASH/POOF/ELECTRIC_SPARK/gold dust and a quiet MC
explosion sound; it does not destroy terrain. Canister has silver body/caps,
gold collars, six ribs and a top lever. This is explicitly **MC-made geometry**,
not an exported original mesh. Grenade, native throw, burst, potion particles,
Q circles/skulls and native meter were reviewed in actual native video/contact
sheets. Existing collision/cover/native-event admission remains authoritative.
Arbitrary mod-mob spells are not fully hindered. On caster hero/world reset the
extra compensation is removed; an already applied vanilla potion expires normally,
so exact50% across a mid-effect caster reset is not yet accepted.

Deadeye already earned passive and real-damage charge; its original HUD subscription
was not notified by raw numeric writes. Existing compositor render owner now calls
the original SetValueFromRemote/Set&Notify method, matching the supplied plugin's
CVD_Edit call context. It checks current McCree model/admin/component/varbag,
numeric vtable/GUID/cost/value/membership, exact native function prefix and dirty
flag ownership; no second callback/subscription or replacement HUD overlay.
Int-to-float promotion was a failed candidate and is withdrawn. Original typed
payload writes are preserved. Real native20% and full/skull pixels passed; Q
still follows the documented offline Beta rules, not complete modern Deadeye.

Slot inputs are suppressed only in this exact native OW process's first-person,
foreground, hidden-cursor gameplay. Existing compositor owns individual MinHook
hooks for raw input, key-state queries and **PeekMessage/GetMessage**, plus its
WndProc filter; no adoption of another owner's hook, global uninitialize or
second callback owner. Digits/numpad digits, wheel and middle button are blocked;
movement/fire/skills and visible-cursor menus pass. MC inventory controls remain
in another unhooked process. Earlier low-level Python hooks, UI-unbind macro and
raw/key-state-only routes failed real fire tests and are not production paths.
`smoke38.json` proves real20->13 shots after digit and wheel, not counters alone.
Owned-memory/Win64 MinHook fixtures passed, including message filtering and exact
code restoration. Actual normal stop of24436 confirmed global restored=true,
slotInputRestored=true, failures=0 before cold startup; no mapped DLL overwritten.

F9 now completes all supports/border/flowers before water, then spawns a real
diamond and invokes the installed mod's public validated activation. The diamond
is consumed by the real mod; its real lightning/portal/travel applies. Four active
`twilightforest:twilight_portal` blocks stayed active. Actual native W+jump into
the pool reached Twilight Forest and an ordinary native shot did20->13 there:
`portal-travel.json` includes delayed arrival and the earlier short-wait failure.
The initial pool built while falling had a raised rim; a held jump crossed it.
Do not equate water or direct dimension-switch fixtures with portal entry proof.
Player does not need to throw an extra diamond. F10/F11 behavior unchanged.

Private classic voice selection: McCree AB63 Hold up now / AB5E It's high noon
from The Omnic Talking; Genji OW1/classic1FEDD, not newer059BBD or unused1FEDF.
Genji's archive OGG decodes identically to the previous local recording; the file
wrapper/hash differs. Archive upload dates2023/2026 are not recording dates.
Official2015 gameplay references and a2016 collection were checked; absolute
earliest2015 provenance for all three clean clips is **not established**.
Current actual mixed MC audio correlates E.753/Q.943/Genji.99999998 to the pinned
clips, and the Genji real native Begin schedules exactly one callout. Media stays
private outside commits/JAR; installer/provenance pins retained. See GENJI-VOICE.

35 guest build tasks, native input/meter/light/GPU/restoration fixtures,45 supervisor
tests,17 stop tests,4 light tests, HTTP contract fixture and final environment
prerequisites passed. These fixture results are separate from gameplay above.
Two earlier native processes exited unexpectedly without a captured exit code;
no cause is proven. Keep the failure evidence.24436 ran >11minutes and was then
deliberately stopped through normal recovery (watcher exit15); that controlled
stop is not an unexplained crash. Supervisor now retains a SHA-verified read-only
native handle to record future exit codes. Full sustained/all-hero/performance
acceptance is still open; do not claim every crash,180FPS or modern skill parity
is solved. Failed candidates/logs/videos are retained in the same research folder.
Hollywood/1080p/Low/8chunks/no shaders/day-night cycle and the mod-pinned isolated
Twilight Switch world are unchanged. Current final identity is in final-audit.json;
all earlier PIDs in this document are historical. Hourly automation was updated
to the new2s/potion/input/voice/HUD/portal scope and stays quiet without progress.

The user's latest request explicitly reauthorizes Deadeye, overriding its earlier
cancellation. Reaper experiments remain isolated and disabled. The user selected
modern slow/hinder for E, rather than the classic stun. Keep the two real games,
native hands/animations/HUD and Hollywood lighting route.

## Implemented behavior and version boundary

* E: a real original Flashbang factory launches the MC swept grenade. Modern
  gameplay applies75 OW-equivalent HP (7.5MC HP),50% movement slow for24 server
  ticks (1.2s), and12s native cooldown. A unique temporary movement modifier is
  removed on expiry, death, hero/world reset, without removing other modifiers.
  Real MC collision and a cover ray govern the3m radial effect. No terrain damage.
* Q: a new original022f/18 activation arms the MC target service; original
  targeting27 admits visible loaded targets; original fire action44 requests a
  single volley. Native Q alone, cancellation, expiry and replay do not damage.
  MC checks range/cone, occlusion, actual health and current session again. The
  remaining native half-meter is spent on confirmed fire, closing the missing
  offline-server debit. Normal passive/actual-damage charging remains available.
  After that confirmed volley, a bounded foreground-only adapter sends the
  original RMB recovery once, because the offline server never ends the aiming
  stance itself. It checks current hero/model/world/source/activation and a fresh
  MC completion acknowledgement; it never admits damage. The owned button is
  released on the next client tick or reset. Cancellation/expiry without firing
  does not request this recovery. Ordinary revolver fire is tested after Q.
* Q and E have private original English voice clips. Q uses the normal self/enemy
  call, not a skin/April-Fools/Echo substitute. E uses the classic throw call.
  An admitted original E or a new native Q activation owns playback; key presses
  and journal replay do not. Separate pack preserves the accepted Genji voice.
* E world mesh and Q lock circles/skull are **MC-made presentation**. Native OW
  hands, grenade throw/ultimate animations, weapon model and HUD remain original.
  The new mesh is not advertised as an extracted retail model or exact effect graph.

This is a deliberate mixed-version adapter. Beta E's receipt still proves its
original25HP,30m/s,5s lifetime,7m travel,20gravity and3m ring; the requested modern
75HP/1.2s/50%/12s gameplay policy is separate. Q retains the beta's geometry and
timing:70m/full105-degree tracking,10s local duration,91-node values160/1000 used
for the local charge budget/cap,6-round volley. This is not proof of full modern
retail Deadeye parity, perks, damage reduction, server target sequencing or every
beta health rule. Fresh LOS acquisition resets a lost MC target's budget.

Ordinary MC creatures do not have the OW movement-ability system: the implemented
crowd control is the requested exact slow. Do not claim that arbitrary modded
teleports, spells or every MC mob special ability has been hindered/interrupted.

## Original event route and safeguards

Baseline E entered the original Volley but emitted no factory event: its script
flags408003 were rejected by the old shared gate. Gate9 permits only current
McCree/01e9 to retain the measured extra bit during the existing original Volley
callback. It does not grant that exception to Reaper or other scripts/entities.
No second owner is installed. Emission12 adds the exact037d/ring/amount binding,
source model/world identity, gravity and bounded protocol proof. Its primary
McCree branch now filters02a7 explicitly, so E cannot masquerade as a revolver ray.

Q uses bounded read-only native state/action observation, not the lossless pellet
journal. One Q activation's persistent fire action is consumed at most once and
queued with session/model/world identity. Startup/mid-Q reads establish a
baseline. A read race inside150ms retries without losing the activation; a longer invalid
read interval disarms until a fresh activation. No delayed old fire is replayed
on recovery. This limitation must remain explicit.

All MC targeting, damage, modifier restoration and actual prefab/mob creation run
on the integrated server. Switching hero/dimension invalidates pending work.
The original native meter and F11 writes share a lock. Current-process creation,
typed variable membership, current hero/model, expected value and four-byte
readback/verification remain in force. No retail process is modified.

## F9 / F10 / F11

* F9 builds a real registered Twilight Forest portal5m ahead, with grass/flowers.
  Requires the actual mod, creative mode, loaded Overworld terrain and border/
  height validity. It refuses a missing mod or unsupported dimension.
* F10 creates8 random real AI mobs on nearby loaded safe ground, bounded to80
  attempts. Zombie, husk, skeleton, stray, spider, slime, enderman and pillager are
  selected randomly; no fake particles or remote chunk generation. In unsuitable
  terrain it may create fewer and reports failure if no safe site exists.
* F11 fills the current hero's original typed ultimate meter to its actual cost.
  Genji keeps its existing owner, others use their native meter binding. It does
  not fire Q. Active Genji/McCree ultimates refuse refill until they end.

These keys only respond to the exact foreground native PID with a live gameplay
camera/player. They require release after focus/session changes and trigger once
per press, not repeatedly while held. F6 flight/F7 Nether/F8 End remain available.
MC's own window remains switchable and is not forced on top.

## Assets and sources

Current retail client updated to154504; released OWLib1151 supports154088 and
refused extraction. Official OWLib/TACTLib release/source were checked. No retail
executable, encryption implementation or installed game data was changed. Silent
official website videos and early footage without the requested call were not
substituted as voice. Public original OGG catalog clips are private local assets:

* Deadeye:00000000AB5E.0B2; SHA256
  `8edd442e89e1c583d4c77ec96523bbfe2056e355da90150db7ebe24bc738d2bf`.
* E:00000000AB63.0B2; SHA256
  `293404deb9d8e006991f86122f4892f934d91f060c765d836f73187d064c5452`.

`tools/mccree_voice_assets.py` pins those files and installs a dedicated
`owmc-private-mccree` pack. Full provenance stays under the user's private assets
and resource pack. No copyrighted audio/video, game files or extracted data enter
source control. Do not call this a successful154504 client extraction.

References: [official hero](https://overwatch.blizzard.com/en-us/heroes/cassidy/),
[June2024 E rules](https://overwatch.blizzard.com/en-gb/news/patch-notes/live/2024/06/),
[September2024 damage](https://overwatch.blizzard.com/en-us/news/patch-notes/live/2024/09/),
[November2025 duration](https://overwatch.blizzard.com/en-gb/news/patch-notes/live/2025/11/),
[official original overview](https://www.youtube.com/watch?v=kq4OlEDiCi8),
[voice catalog](https://theomnictalking.altervista.org/en/hero-dialogues/cassidy-x/),
[classic E audio catalog](https://theomnictalking.altervista.org/en/overwatch-classic-eng/).
Later official2026 normal/perk/Stadium/Arcade notes were checked separately;
community-crafted and Stadium changes are not applied as normal E base rules.

## Verification and resumption

Private evidence: `research/mccree-complete-20261021/` includes before/ backups,
failed asset reads/probes, native graph/config records, first actual factory,
four-dimension lifecycle, cover/cancel/expiry/keys and final audio/visible audit.
Use the final audit's exact process/module hashes, never earlier PIDs here.

Guest build/check35tasks, native shared gate/real MinHook restoration fixtures,
45supervisor fixtures,17stop fixtures and proper Java HTTP contract passed.
The first deployed mechanics/render candidate passed E75HP/50%/expiry/replay and
Q multi-target actual damage/full debit in Overworld, Nether, End and Twilight,
with fresh native hero/light/full health. Real foreground F9/F10/F11 holds were
single-fire; cover, cancelled Q and original10s expiry caused no target damage.
Actual MC mixed-output audio matched the private original E/Q clips with
normalized correlations0.853/0.983 (mixed-voice-proof.json). Real native captures
showed the flying MC grenade, target-surface red circles and charged skulls;
completion-locks_small.png is the final visible lock capture. Asset availability
or render counters alone were not used as audible/visible acceptance.

Repeat the isolated actual lifecycle with `.venv/Scripts/python.exe
tools/verify/verify_mccree_lifecycle.py --pid <verifiedPID> --output research/<run>`.
It uses explicit F11 grants, not natural-full-charge proof. Next work should
improve exact grenade mesh/effects and original Q server-rule fidelity without
regressing this playable slice, Visor, Bastion mobility or session switching.

Final tightening found a real End-world regression: immediately resetting on one
inconsistent two-read snapshot discarded Q at its fire boundary. Failed evidence
remains in final-lifecycle/result.json. The repair retries only within the existing
150ms freshness budget and re-baselines after any longer gap; it does not admit
keys or loosen owner/world checks. Final guest087a51e1… cold deployment passed
all four actual dimensions again in final-fixed-lifecycle/result.json. E/Q voices
were scheduled once per successful activation in each dimension and observed by
the real sound manager; the separate mixer/video evidence is listed above.

The subsequent completion-result.json additionally passed native Q End without
manual RMB, no meter refund, and a fresh ordinary revolver hit20->13 immediately
afterward. The final cold deployment is JARb2958826bbacf63b5d2d3764f47f7fb9ff80353fd2fb312fd81bf9217be7f90c.
The first completion-lifecycle receipt retained a light comparison failure taken
during revolver recovery. A subsequent stationary read matched within2e-7; the
verifier now waits for recovery/recoil before comparing its separate snapshots,
without changing the light tolerance or production renderer. See the settled
four-dimension rerun and final-audit.json for final acceptance/current identities.

Final completion-lifecycle-settled/result.json passed all four dimensions. Each
Q fired against real MC targets, ended natively without manual cancellation,
spent its meter without refund, and allowed a fresh20->13ordinary revolver hit.
Native light errors after recovery were below2e-7, full native200/200health held.
The final actual76Visor regression also passed. Final audit36980/37592 confirms
six unique loaded native modules, matching installed/built JAR, no owner failures,
134advancing frames, grounded full-health McCree in Overworld, F6OFF, no temporary
targets/mobs/floors or active skills. F9's real portal is intentionally retained.
The independent wrapper39432/worker37000 keeps both games running after the turn.

Post-deployment maintenance: the old read-only control inspector rejected the
deployed12s E cooldown because it required the original10s in one undifferentiated
tuple. The actual failure is retained in research/control-profile-20261021/.
Inspector schema2 now distinguishes the exact beta projectile/25HP receipt from
the observed12s requested override, retaining all projectile/owner/type guards.
Unexpected values and other heroes cannot inherit this allowance. Five fixtures
and the actual current-model inspection passed; its output reports
mcSkillImplemented=null and mcEffectsVerifiedByThisInspection=false, so parameters
alone cannot misreport an implementation verdict. No DLL/JAR/gameplay changed or
game input was sent. Same six modules/JAR/process creation verified; actual
native pixels remained visible and191frames advanced during the audit sample.
