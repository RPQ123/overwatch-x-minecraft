# Initial hero picker and Minecraft source recovery — 2026-10-19

This heartbeat fixes a startup lifecycle gap identified by source inspection:
`wait_for_selection` previously only filled native health and waited for the first
confirmation. Minecraft restart supervision began afterward. A guest exit before
that first confirmation could therefore leave the initial picker without a new
source until manual intervention. The old behavior was established from code,
not claimed as a fresh old-build live reproduction.

## Changes

GuestRecovery owns one creation-aware psutil MC identity, current guest metadata
and the existing three-restart budget, shared by initial selection and gameplay.
No second supervisor, native owner, callback or process injection was introduced.
Initial picker now publishes its manifest/health/phase while waiting and normally
reopens a stopped guest without confirming a hero. Reopened world/source and the
actual copied guest JAR hash update together. Entering gameplay retains that same
restart budget and correct loaded JAR hash. A creation-aware native identity also
prevents the picker loop following a reused OW PID. A confirmation during recovery
cannot carry the obsolete stop error into full supervision (fixture checked).
Initial picker readiness remains false; it does not imply attack/kit acceptance.

Only Python launcher/shutdown/test tooling changed. Native/guest binaries and
ability/balance code were unchanged. No native or Java rebuild/HTTP contract rerun
was needed for these Python changes. Existing private Wraith/lifetime experiments
remain OFF. Tools/verify_initial_picker_recovery.py is the new repeatable real test;
it refuses ordinary saves and requires a separate Switch clone before first hero
confirmation. It normally saves/exits MC through the existing shutdown endpoint.

## Backup and actual initial-picker test

Initial native24440/MC3164 was healthy, with six actual mapped native project DLLs
and four healthy owners; read-only environment checks passed on Python3.13.13 and
the exact SHA256-guarded offline executable. Normal restore/stop/save before full
profile backup:
`<USERPROFILE>/.universal-modder/backups/initial-picker-recovery-20261019/20261019-111247.zip`
(920 files,895.0MB). Original settings snapshot:
research/_archive/2026-10/initial-picker-original-settings.json. Stress tests use mod-pinned
Overwatch Twilight Switch 20261019 A/B; original Trial A save is not used for them.

research/initial-picker-recovery-2592-1792379711416554000.json passed:
- OW2592 and native model2147485759 unchanged. Previewed the original Genji card
  without confirming gameplay. MC32128 normally saved/exited, reopened as3884.
- After recovery the initial picker remains active, readyfalse/stateNone, no error,
  body writes0 before/after, current source/world/generation stable and new real
  MC image generation composited. The updated manifest matches the profile JAR.
- 28 loading samples retain native200HP. The original animated Genji over actual
  Twilight forest was inspected in the -after_small.png screenshot.
- First actual confirmation afterward entered full supervision. Real W input moves
  MC0.786786m; original Genji3 shots take target20->9.5, replay unchanged, zero
  rejects. Temporary target/blocks cleaned. No synthetic shot/body packets used.

## Actual gameplay regression, same supervisor and unchanged OW

research/world-hero-switch-2592-1792379757738505900.json passed:
MC3884->30956 while switching clone A->B; world ID4318740326124827386 ->
3290572199857895851. Same OW2592. Shared guestRecovery count is2 (initial-picker
recovery was1), body sessionResumes2. The restart budget was not reset at gameplay.
24 stale-source gap samples retain native HPmin200, Yspan0.0048828125, max source
age18827ms. Post-reopen McCree target20->13/movement0.703062m and Genji20->9.5/
movement0.786786m pass actual fire/replay. Both old and new saves keep their mod.
These are controlled creative air tests, not physical portal/full-kit acceptance.

39 launcher fixture tests passed (6 new recovery/identity/status cases), plus
3 bounded shutdown-read fixtures. Real source recovery tests passed as above.
No general all-hero, long-play, boss/progression or sustained180FPS claim.

## Additional normal-stop file-read race

During one preliminary final startup, normal stop for exact native32556 restored
emission/gate/body, then PermissionError13 reading world-live-32556.json interrupted
its last restoration stage. This is consistent with a brief Windows report-file
sharing/replace race; its precise lock origin was not instrumented.

stop_passthrough.read_report now retries only report read/parse failures8 times
at30ms intervals, used by both stage restoration polling and session shutdown.
Persistent failures still propagate; restoration is never presumed or bypassed.
Fixtures force transient sharing/partial-JSON failures, a persistent bounded failure
and an immediate stable read. Rerunning the existing normal stop after this fix
restored the remaining owner and saved MC successfully. No forced process exit.
research/_archive/2026-10/initial-picker-stop-race.json records the exception and all4 restored
owner reports. The final cold supervisor was restarted after the last source edit.

## Final ordinary runtime

Original settings restored byte-for-byte and original Twilight Trial A reopened.
Current native24880 / MC21484 / independent supervisor14768. Startup:
research/_archive/2026-10/initial-picker-final-startup.log. Confirmed Genji once to apply OWLow and
initialize full current hero supervision, then H back to animated picker. Actual
composed image inspected: research/_archive/2026-10/initial-picker-final-picker_small.png.

Player20HP/alive/onGround/flightOFF approx(57.500,25,10.898), native200HP. Settings
remain1080p/OWLow/8chunks/no shaders/day-night/F6flight/same seed. Exactly six
expected project DLL paths mapped, four owners healthy, private probesOFF, loaded/
build/profile hashes match, frames advancing, current phase/hero/model, no error/
warning, no test targets/blocks/boss/probe, mobGriefingtrue.
research/_archive/2026-10/initial-picker-final-status.json passed and records launcher source hash.
Games and independent background stay available after the agent turn.

Next: cached yellow H prompt or another bounded hero/source lifecycle slice.
Blink long source-loss/Recall/bomb, Pharah wider flight transitions, full Hydra
native weak points/progression/full kits and sustained180FPS remain open.
