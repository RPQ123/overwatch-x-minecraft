# Native fullscreen display lifecycle — 2026-10-24

## 2026-10-24 10:00: unavailable final readback repair

Old normal Stop26340 again completed native restoration/normal exit but failed
after applying the original display mode when REGISTERED read returnedNone.
Its failed receipt1792806335604026600-30612 is retained; a normal retry completed
desktop restore/MC save before any restart. No forced game termination occurred.

Final restoration readback now retries ONLY unavailable samples within a6second
outer observation deadline (individual WinDisplay reads remain bounded). It
never repeats ChangeDisplaySettings, never treatsNone as success, immediately
rejects a real mismatching mode, and rechecks absence of native processes before
and after both reads. Failure retains the durable receipt; no restart follows.

Actual new normal Stop30220, receipt1792806640150788800-27504, hit this transient:
readbackRetries1, all restoration/normal native close passed, original current+
registered2376x1080/144 restored, actual MC save/exit completed. This is actual
branch evidence, not just an unavailable-read fixture.19 display and19 normal
Stop fixtures passed, including native-start races and bounded failure/refusal.
The active later29556 lease again prepared1920x1080 before native launch.
This fixes an observed final-readback lifecycle path, not TIMER or H publication.

The production launcher now prepares the accepted 1920x1080 mode **before**
creating the original native renderer, binds its durable display receipt to the
exact native PID/creation, and restores the prior desktop only after native
normal exit. The original window remains borderless, not exclusive fullscreen.
No native DLL/JAR, callback owner or provided-plugin ABI was changed here.

## Why startup order matters

The 2376x1080 control drew a real fused picker but actual hero selection failed.
Changing mode after native renderer creation also failed the real compositor
startup (8488, only three owners mapped). Both failures remain in
`research/sprint-20261024/`; they are not evidence of arbitrary-resolution support.
Preparing 1080p before native creation restored real picker interaction,
composition and combat. An earlier observed desktop reversion followed exit;
the later old13316 close did NOT reproduce that reversion. Do not certify its
original cause merely from timing. The launcher now handles either starting mode.

`tools/native_display_mode.py` uses a primary-display lease. Before mutation it
checks the exact offline EXE SHA256, absence of another native process, enumerated
mode and unchanged refresh/bit depth; backs up both current and registered full
DEVMODE bytes with hashes; and writes a durable launch reservation. After native
startup it verifies the original primary-monitor render HWND and binds the exact
process identity. Existing live renderers with mismatched modes require normal
restart; the launcher does not silently resize/reconfigure them mid-game.

Normal Stop reads that same private receipt after ending the supervisor and
normally closing the native process. It restores current and registered modes
and checks readback before saving/stopping MC. A changed user mode, live native
process, foreign receipt or bad backup refuses restoration and restart success.
Already-correct displays are not adopted; an already-restored desktop is a no-op.
UI closure leaves the independent supervisor and its display lease available.

This driver actually returns the 188-byte public prefix through display frequency,
without private data, although the supplied buffer is220 bytes. Both this prefix
and the full layout are recognized; truncated/private layouts refuse mutation.
Special CURRENT/REGISTRY reads refresh the documented index0 enumeration cache,
with bounded observation-only retries across a mode transition. The initial
over-strict layout failure and first restore-readback failure remain recorded.

Microsoft references: [DEVMODEW](https://learn.microsoft.com/en-us/windows/win32/api/wingdi/ns-wingdi-devmodew),
[EnumDisplaySettingsW](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-enumdisplaysettingsw),
[ChangeDisplaySettingsW](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-changedisplaysettingsw).

## Actual acceptance and remaining limits

- Native5428 startup from original2376 desktop acquired1080p before process
  creation and mapped the six original owners. Controlled McCree charge movement,
  firing lock, native End and real ordinary damage passed. The full cold Deadeye
  suite nevertheless FAILED its H-menu freshness deadline; do not mark it passed.
- `display-lifecycle-full-stop-accepted` FAILED at gate11 terminal-report
  observation. Its original native slots were already restored, but its complete
  terminal JSON remained `.json.tmp`; the main JSON still said enabled. The exact
  Windows rename error was not logged. The unchanged v11 source ends its worker
  after that one report write; lack of active presents was not the proven cause.
- New read-only gate11 recovery requires the unique pinned module, exact
  OWGATE05 request PID/creation/admin, no optional entry/tick/lifetime hooks,
  complete success terminal and all three actual original Volley pointers.
  Only then can the existing bounded atomic-promotion helper promote the
  unchanged tmp. A JSON claim alone cannot authorize normal close.
- `display-lifecycle-full-stop-v2` actually PASSED all individual restoration,
  WM_CLOSE/native destructor/precise console acknowledgement/actual exit,
  desktop1920→original2376 for both current/registered, and normal MC save/exit.
  No game was force-terminated. The failed earlier attempt remains failed.
- `display-lifecycle-start4` then actually launched NEW native29520/MC10476,
  reapplied1080p automatically before native creation, and retained six original
  owners. These IDs are historical once replaced; re-read current identity.
- The freshly restarted session passed `display-lifecycle-bastion-smoke`:
  actual Tank03ce factory/direct50+blast140, attenuation/cover, real block
  destruction,48-block travel, model drawing, exact-once replay, Tank charge
  suppression, End natural-charge resumption and ordinary Recon damage. The
  video contact sheet and final original Bastion picker were actually viewed.
  This is one Overworld lab, diagnostic Q grant; not all forms/four dimensions,
  native original knockback calibration or minimum-FPS acceptance.

Fixtures:14 display,6 gate-report,22 report-race,23 normal-close,19 stop,52
supervisor,46 launcher,17 Deadeye harness; correct HTTP contract entry also passed.
Native42/26/11/16/10/1 and guestaf92f746 remain unchanged.

Cold Deadeye H transition is still open: one170ms camera gap and a subsequent
same-identity body gap beyond the ORIGINAL3s observation window caused real test
failures. Damage/identity gates were not widened. The failed scene was separately
cleaned by closing the menu onto the SAME pawn (model unchanged), observing real
cleanup acknowledgement, and returning to the picker; its failed test result was
not rewritten. Investigate the source publication/selection transition rather
than extending stale combat authority or claiming the earlier warm pass is cold
acceptance. TIMER root cause and full hero/Boss-map work remain separate.
