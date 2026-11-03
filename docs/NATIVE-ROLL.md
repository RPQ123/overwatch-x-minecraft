# McCree native roll into the Minecraft motor

The original offline McCree graph05800000000001f0 controls activation, cooldown,
animation and reload. Its node4 Wait begins and ends the MC roll; keyboard edges
never start a roll themselves. The existing native logger is observed read-only.

## Configuration and direction

`prepare_native_roll.py` validates the current hero/model/script and the reflected
movement actions8/11, their exact expression bytecode, owner inputs and speed
variable path. Script-local0670 currently supplies15 metres/second. Node4's
typed m_timeout supplies0.400000006seconds. The expected unobstructed distance
is therefore6 MC blocks, with a distance ceiling to prevent an extra client tick.

Action11 uses normalized horizontal original forward. Action8 uses normalized
forward*throttle.y-left*throttle.x. The adapter correlates the selected native
action's timestamp with the Wait Begin, then latches the original camera direction
and directional input from the existing host intent channel. It does not call
the native expression evaluator or read its resulting movement vector. Very short
direction changes between native action and MC polling have not been separately
verified; unsupported/missing directional input cancels instead of guessing.

`NativeRollReader` checks process creation time, current local/model/reference,
hero ID, graph/bag and script-owner chain, numeric types and bounded values.
Nested logger maps and state payloads are read twice where needed. Original End
timestamps cannot start another roll. A stale reader, owner change or reconnect
rebases the phase; an already active historical roll cannot be replayed.

MC keeps vanilla vertical gravity and Entity.move block collision. The dry-land
horizontal movement hook consumes the original speed at20ticks/second. Flight,
vehicle and fluid travel do not use this roll override. Genji's dash/climb reader
is separate and has not been broadened to McCree. Water-specific roll behavior,
moving-platform cases and extreme tick stalls remain unverified.

## Actual evidence

Native16892 with MC17092 and modules7/1/26/10/8/10:

- Forward fallback, backward input and diagonal input each moved6.0000blocks
  during the roll interval. Normal walking before the held-key tests is excluded.
  The diagonal vector was(4.24164,-4.24364), length6; original action8 was observed.
- Approaching a three-block wall stopped after0.8900blocks, preserving MC height
  and collision. Two extra Shift taps inside cooldown produced no additional Begin.
- Switching to Winston invalidated the roll reader without movement; switching
  back created a new model binding and the next native roll worked automatically.
- Actual recording/contact sheet shows original revolver holster/recovery and
  native cooldown over the MC test lane. Private evidence is
  research/mccree-roll-motor-{open,wall,back,diagonal}.*, mccree-roll-return.*,
  mccree-roll-motor-summary.json and mccree-roll-winston-isolation.json.
- 20s performance:187.26distinct composed FPS,38report windows minimum172.15,
  below150=0, held0/unmasked0. This is bounded cadence, not individual-frame lows
  or an indefinite guarantee. Evidence mccree-roll-motor-perf.json.

The air-only test lane created340temporary stone blocks after checking the
whole volume. They were all restored to air; no original terrain was replaced.
MC returned to natural birch leaves at(-538.6987373,73,-363.4625002), flightfalse,
health20, before normal callback restoration and save. Backup:
<USERPROFILE>/.universal-modder/backups/owmc-roll/20261016-074126.zip
(75files,44,214,173compressed bytes). Evidence mccree-roll-cleanup.json.

NativeRollCheck tests lifecycle, stale data, reconnect, End, distance ceiling and
diagonal speed. NativeRollReaderCheck performs actual Win64 self-process reads
of owned fixtures, testing map/action correlation, owner/creation/numeric guards
and reconnect. These fixtures are separate from actual game evidence above.

## Startup correction

Changing to McCree before the initial Genji-only readiness check finished used
to terminate the launcher after20seconds. Startup now enters the persistent
supervision loop immediately after connecting verified adapters and retries
current-hero bindings there. Missing Genji-only channels on another hero still
report ready=false; they no longer kill supervision or prevent subsequent hero
changes. This does not claim those missing abilities are implemented.

Direct McCree cold selection then exposed two older Genji-only startup gates:
the Python body precheck required only graph0304, and emission10's worker
required Genji projectile07ca even though its live rebind path supported all
three heroes. The body check now validates the supported hero/base weapon and
component owners, allowing additional skill graphs (McCree also has01e9).
Emission11 shares the exact hero/resource-pair validator between initial startup
and rebind. Invalid initial requests report a restored, non-active failure.
No opcode/callback or emission wire layout changes were required; the guest's
accepted producer version is now11. Build/lifecycle fixtures retain original
callback restoration and test all valid and crossed hero/resource pairs.

Fresh19536 selected McCree first, loaded emission11 and automatically bound
roll/base health/locomotion; its supervisor stayed alive beyond the former20s
timeout. Two original shots hit a real MC test villager20->6 (two70HP native
events mapped to7MC HP each), with HUD ammo6->4. After landing, the first roll
ran against natural leaf collision and restored original ammo4->6, HUD cooldown8.
The target was removed and no test blocks were created. Final-source phase reset
was present in this run. Evidence emission11-mccree-first-selection.json,
emission11-mccree-live-hit.json, roll-final-source-cold-check.json and
mccree-roll-ammo-{before,after}_small.png. Normal stop restored all callbacks and
saved MC before the next cold test.

Fresh15736 selected Winston first on emission11, initialized500HP and kept
supervision running. A600ms native beam reduced the actual MC target20->16.351988,
with31intervals, one Begin/End and no observer failures. Switching to Genji then
delivered three original35HP projectiles to a fresh target20->9.5 and restored
all current Genji channel readiness. Targets were removed and flight disabled.
Evidence emission11-winston-first-selection.json, emission11-winston-live-hit.json,
emission11-genji-live-hit.json and roll-emission11-final-ready.json.
