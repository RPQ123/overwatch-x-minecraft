# Native timer-notification crash investigation — 2026-10-21

## 2026-10-23 — supplied shutdown ABI repaired, TIMER remains open

Read PROVIDED-SHUTDOWN-ABI.md. The provided plugin's exact System slot4 now
returns nullable0 via its existing zero-return implementation, a cold two-byte
data-only correction with unchanged code/PDB/relocation. New DLL SHA c82f8cea…
and private original/manifest are recorded separately. No new callback owner.
19496 after actual skill/four-world play and2424 after a second cold picker
both passed strict restoration, WM_CLOSE/native teardown, observed original
atexit console-pause acknowledgement and actual exit0 with no matching report.
8544's earlier20s timeout remains failed evidence; no force kill passed as close.
27304's real825346 report was another instance of this proven shutdown path.
The source scheduling Loop Exit and the d1428b TIMER corruption writer remain
unproved. Do not merge them or claim long-run crash-free acceptance.

## 2026-10-23 04:20 — shutdown ABI mismatch narrowed, no patch yet

Actual decrypted runtime instructions from fresh23456 are retained in private
crash31364/actual-code-23456.txt.825310 is a pool free:825346 writes the old
free-list head into the supplied allocation.80efa0 loads an object's vtable,
calls slot4(+20) with EDX0, then frees its nonzero RAX result. The exact supplied
PrometheusSystem vtable's slot4 resolves, through matching PE/PDB, to
`deallocate@PrometheusSystem` at plugin38a00: a bare `ret 0`, which leaves RAX
unchanged. This explains how the preceding vtable address can survive as a
return value and be passed to free during shutdown. Its typed PDB signature is
void; the native caller uses a pointer return. Slot dump and names are in
prometheus-vtable.json/prometheus-slot4.txt.

This is evidence for a supplied-interface shutdown ABI mismatch, not evidence
for what scheduled the native main-loop exit, nor a fix for d1428b TIMER reuse.
No allocator, vtable or plugin was changed. Do not patch the shared38a00 stub
(many unrelated void methods alias it), skip arbitrary frees or infer that an
idle recovery has proved stability. Scope any future correction to this exact
verified interface, preserve original deallocation semantics and test shutdown.

## 2026-10-23 — runtime825346 recurrence in31364, distinct from TIMER release

Actual native31364 created2026-10-23 04:04:06.449185 Asia/Shanghai crashed at
04:06:51 while testing Soldier E after hero/dimension recreation. Exit0 was
correctly classified crash-report by the supervisor, and MC was stopped. The
four-dimensions-v3 suite passed only Overworld/Nether, then failed foreground
input because the native process exited. No evidence of human interference.

Exact matching original report/minidump and last status/body/compositor/emission
reports copied to research/biotic-field-20261023/crash31364/. Report module base
0x7ff6ef3d0000, RIP0x7ff6efbf5346 -> RVA0x825346, exception0xc0000005/thread9504.
This matches the earlier960 fault ADDRESS, but happened after2:43 runtime;
neither its same cause nor a relationship to d1428b TIMER pool damage is proved.
RDI0x7ffcef081820 equals supplied inject.dll's PrometheusSystem vtable
(plugin base0x7ffceee10000 + PDB-pinned RVA0x271820). That is a register/symbol
fact, not proof of which object/writer corrupted it. Static EXE bytes did not
give a valid instruction stream at this RVA; do not patch guessed instructions.
Read actual runtime code before interpreting the allocator/call chain.

Exact reporters24908/8208 were verified by path/name and matching31364 report
and closed without sending. New normal recovery launcher logs supervisor-recovery1
under the same research folder. Source/profile guest4dc8bed4 and all6 native DLL
versions are unchanged; no feature blindly disabled and no second owner added.

## 2026-10-21 — distinct startup crash960 retained

A cold launch during the timing work exited before hero selection. Its actual
report/minidump are copied to research/genji-particles-20261021/crash960/ with
identity.json and hashes. Application matches this guarded offline executable,
PID960, report 10-21-26_13.13.49; session lower bound1792588352. Exact process
creation time was unavailable after the picker-start exception; do not invent it.
The exception is native RVA0x825346 (base0x7ff70a1f0000/RIP0x7ff70aa15346),
thread2544, NOT the historical d1428b type1 TIMER release. Report runtime52s.
The current launcher's "Original client exited during hero selection" path still
needs unified creation-aware crash classification. A zero exit or loss of focus
is not proof of a normal exit, user input, GPU fault or timer root cause.
Later29420/23300/27408/3716 were deliberately strictly restored/stopped. Final
21144 completed all21 hero selection swaps and actual Q/E tests; no new matching
report alone is not proof that either crash root cause is fixed. Original six DLLs
were unchanged throughout this work. Do not conflate this distinct startup failure
with the still-unproved old TIMER corruption writer.


## 2026-10-21 20:06 — Candidate state-index mapping; no speculative timer fix

A bounded one-shot read of current23132's immutable constructed resources maps
script0580000000000b3b to24 graph nodes/17 states. Its m_states[0] is graph node1,
STUStatescriptStateBooleanSwitch (not graph node0/Entry). The actual condition is
the dynamic path0d80000000000004 ->0d80000000001793. Thus the30248 recorder's
stateIndex0/userData1 TIMER candidate can be compared with this BooleanSwitch
definition, rather than mistakenly interpreting stateIndex as a graph-node index.
This is current same-build definition evidence, not proof that the captured root
was the crashing object, what that dynamic property means, or which writer
recycled a notification. No state/timer/function was altered or executed.

The supplied STU graph/header m_states list agrees with the measured resource
list; private raw metadata is original-details-23132.json under research/mccree-
native-shots-20261021/. Unsupported reflection getters remain explicitly unknown.
The same one-shot read confirmed Deadeye52 is an Effect action whose two final
words are1/0, versus44's0/0. Those words are not a proven muzzle/sound resource,
and modern OWLib's different field layout was not substituted for beta metadata.
Do not add52 as a guessed per-shot muzzle/sound event on this evidence.

Existing independent23132 reader remains the only bounded background observer;
fresh heartbeat/zero read errors/current exact executable and six module hashes
were checked, without another callback, process restart or gameplay input.
No matching new crash report was found. Idle picker survival is not combat or
root-cause acceptance. Current actual versions remain compositor40/body12 and
guest4559dae8…; TAKEOVER/NATIVE-MCCREE supersede older PID/version paragraphs.

## 2026-10-21 19:45 — New crashes and measured thread separation

30248,12096 and17852 also produced matching execute-access violations at the same
native TIMER-release d1428b call, despite exit0. Private copies are under
research/mccree-native-shots-20261021/crash{PID}/.17852 passed a real sequential
Q before crashing; those feature results do not establish stability.

The30248 read-only recorder completed1855samples/zero read errors. Preserved RDI
maps to candidate script0580000000000b3b, instance-22, current McCree owner,
in its final three seconds. One last-second sample captured a stable native TIMER
root with stateIndex0/userData1; its address was not the crashing object. The
correlation does not identify the corrupting writer, and1Hz is not lossless.

Compositor39 called meter notifications/animation on Present, while body10 was a
separate native logic callback. New compositor40/body11 move both to that existing
logic owner, without disabling charge/animation or adding callbacks. Actual28272
measured render27216, body21736 and weapon21736. This establishes thread separation,
not causation of historical pool reuse. Repeated E/Q/model/dimension combat survived
until intentional normal stop of28272, with all strict restoration flags true.
No-crash observations are bounded and not proof of the allocator's root fix.
Current17964 cold regression/reader status is linked from TAKEOVER.md.

## 2026-10-21 18:20 — Pool-reuse pattern and bounded background identity capture

The native crash is still unfixed. Further actual read-only evidence narrows the
damage pattern. The live TIMER allocator global is at RVA17ab070; its current
pool has elementSize=56 at+0x54 and flags0x31 at+0x38. Its virtual allocate/free
methods are812b80/812c90. In the active flag0x20 path, free writes the current
free-list head into the object's **first qword**, then makes that object the new
head; allocate pops that first qword. These are observed original instructions,
not inferred from the failed on-disk disassembly.

All three crash contexts fit this same56-byte pool lattice:

| Native PID | object minus heap RIP | fake-vtable pointer minus heap RIP |
| --- | --- | --- |
| 13448 | 504 =9slots | 112 =2slots |
| 26516 | 672 =12slots | 112 =2slots |
| 38368 | 392 =7slots | 784 =14slots |

This is consistent with a free-list link being interpreted as a vtable, rather
than an arbitrary code jump. The small dumps lack the full allocator/object
history, so **duplicate release, premature recycling and concurrent reuse remain
hypotheses**, not a proven writer or a repaired bug. All three crashing thread
IDs also match the retained native weapon-gate callback owner thread for that
same process; this does not establish the render thread's identity or exclude
indirect corruption elsewhere. Original code/header/contexts are preserved in
pool-1803.json, historical-registers.json and pool-reuse-evidence.json under
research/native-timer-20261021/.

Added tools/observe_native_timer_lifetime.py, an external reader with only the
existing SHA-verified QUERY/VM_READ handle and matched supplied plugin PE/PDB.
It snapshots that plugin's existing script-state map and the two measured native
instance notification roots; it does not subscribe, hook, inject, call native
functions, traverse a guessed list, send input or touch game state. It records
resource/instance/owner identities plus timer user data/state index when a stable
type1 header is visible. Changed identities are retained with timestamps, so a
future crash's preserved RDI can be compared to **candidate** script identities.
That match is not proof of who wrote the bad pointer. One-Hz snapshots are not a
lossless timer event stream and can miss scripts that live for less than a second.

The independent hidden reader targets exact30248 and has a per-creation mutex,
up-to2hour lifetime,200ms per-snapshot deadline,8192-address history bound with
4versions per address, and four8MiB journal segments (plus one bounded row).
The running output is research/native-timer-20261021/live-30248-1803/. It stops
when that process exits, on its deadline, or when a STOP file exists in that
folder; it does not adopt another PID or restart either game. Before starting
another reader, inspect status.json/heartbeat and its mutex; do not stack readers.
Current measurements:153 script addresses, >250 samples with zero read errors,
roughly5ms reads and >260 stable timer-root observations. The currently observed
idle timers belong to resource0580000000000015, states0/2/8; this is **not** an
attribution of the historical crashes. States0/2 type hash e811ecbb matches the
local OWLib name STUStatescriptStateBooleanSwitch by lowercase CRC32; state8's
e67578c0 remains unnamed. These names alone do not prove timer semantics.

The dump parser is bounded to a16MiB AMD64 minidump, rejects wrong signatures,
stream/context bounds, ambiguous exceptions and non-AMD64 context. Seven fixtures
pass, and all three real stored dumps yield the same registers as the earlier
inspection. Structure references were checked against Microsoft's
[MINIDUMP_EXCEPTION_STREAM](https://learn.microsoft.com/en-us/windows/win32/api/minidumpapiset/ns-minidumpapiset-minidump_exception_stream)
and [AMD64 CONTEXT](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-context).
No new crash, native correction or combat acceptance was manufactured for this
reader. Current native/MC processes and artifacts are unchanged and healthy.

Also repaired mojibake in the saved hourly prompt caused by a previous native
terminal text round trip. Rewrote it via structured Unicode tool arguments,
verified no replacement characters and preserved ACTIVE/hourly/current-thread
settings. Future terminal JSON transport uses ASCII escapes or explicit UTF-8.

The repeated native client exit remains **unfixed**. The current increment
identifies the damaged object's category and fixes a separate supervisor evidence
gap; it does not make an unproven native patch or disable native skills.

## Evidence and object identity

Three supplied-client reports (38368,26516,13448) share the same native call stack.
The13448 minidump contains execute access violation0xc0000005 with RIP in heap
data, not an image-code address. The original caller is RVA d1428b (`call [rax]`),
returning to d1428d. RCX/RBX is the object being released; its virtual target is
invalid. The small dump does not preserve enough of that object/owner to prove
who corrupted it. Keep the original reports/dumps under ignored research.

Read-only disassembly of the SHA-verified actual30248 process resolves the exact
dispatch: original function d14200 reads byte[notification+0x22], bounds it to0..8,
then indexes the nine-RVA table at d14440. Its destinations are:

| Type | Supplied header name | Native release branch RVA |
| --- | --- | --- |
| 0 | LIFETIME | d14229 |
| **1** | **TIMER** | **d14266 (contains the crashing d1428b call)** |
| 2 | EVALEXITS | d142a3 |
| 3 | TRAVERSEFROM | d142e0 |
| 4 | SETVAR | d1431d |
| 5 | SETVARARRAY | d1435a |
| 6 | STOPINST | d14397 |
| 7 | LOGICALBUTTON | d143d0 |
| 8 | ONATTRDEPCHANGE | d14405 |

The supplied Statescript.h independently defines TIMER=1 and the notification
type byte at0x22. Statescript notification allocation assigns these same types;
the shared-manager vtable has Allocate_StatescriptE at0xa0, followed by this
release path at0xa8. The stack's f4f5b0/f4f0b9 path executes then releases a
notification. Thus the crashing branch is **timer notification release**, not
the attribute-change branch. This narrows the investigation; it does not exclude
indirect corruption by another producer or establish a particular mod's guilt.

The detour visible at f4f600 belongs to the **supplied statescript logger** (its
source explicitly hooks TickScript there). It is not our projectile factory;
the latter is at d354b0. Do not misattribute that jump to emission12 or install
another callback owner over the provided logger.

Evidence: research/mccree-polish-20261021/notification-lifetime/original-code.json,
research/native-timer-20261021/audit.json and the earlier crash13448/ originals.
The original binary is encrypted on disk: naive file-byte disassembly produced
garbage and is not accepted. The code/jump-table proof above reads the exact
running SHA-verified offline image, without writes or UI input.

## Supervisor correction

In the observed13448 crash, the client's exception handler returned exit code0
and opened BlizzardError. Zero is not proof of normal termination. The gameplay
supervisor now records nativeExitClassification=crash-report and error plus
nativeCrashEvidence when the corresponding local report is found, regardless
of exit code. No report is submitted or uploaded. No automatic crash/restart loop
was added; no report means process-exit-unclassified, not a proven healthy exit.

tools/native_crash_evidence.py accepts only the exact project ErrorReporting
x86/x64 executable's diagnostic arguments, or the bounded report-name fallback
under Windows' actual redirected Documents folder. It validates native PID,
process/report creation time, bounded stable file contents, assertion marker and
the report's actual Application path against the previously verified target.
Corresponding fresh minidumps are referenced locally. Wrong PID, reused-PID old
files, another executable/reporter, incomplete/oversized files and old dumps are
refused. Current Documents resolves to D:/wendang, not a guessed C: path.

Ten identity fixtures and45 existing supervisor tests pass. The detector also
actually matched all three retained reports after their reporter processes had
closed, and returned no crash evidence for current30248. This is real report
recognition, not a synthetic crash or proof of the native cause. The picker-only
startup exception path is still the older path; this change covers the supervised
gameplay exit and does not claim complete startup-exit classification.

The supervisor was replaced using the existing exact-project stop_supervisor
control and normal adoption. Native30248 and MC23340 stayed alive, and all six
loaded native owner paths/hashes and installed/built guest b09fe17e… stayed the
same. Existing stage_ready checks admitted the current owners, with no extra
injection, callback owner, game restart, test target, or game input. Current native
composition/full McCree health/full original meter pixels were inspected and
frames advanced. This read-only round does not renew the earlier combat tests.

## Next step

Keep highest priority on the timer object's allocator/release lifecycle: identify
its originating script, timer user data, queue ownership and whether it is reused
or released twice. Prefer existing provided logger records and bounded read-only
observation; any instrumentation must retain one callback owner and cold-deploy
new native builds only after full restoration. Do not suppress arbitrary bad
timers or claim stability from an idle session. Retain all accepted gameplay,
2s/50% potion lifetime, slot filtering, HUD notification, classic voice,76Visor
and strict stop fixes while gathering causal evidence.
