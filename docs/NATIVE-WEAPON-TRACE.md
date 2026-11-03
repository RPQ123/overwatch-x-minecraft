# Native weapon execution investigation

The required route keeps the user's original offline weapon scripts/animations/HUD and translates confirmed native weapon results into MC effects. Native key bits, hand animations, a graph's presence and an integer equal to 24 do not establish a projectile or ammunition authority.

## Evidence established

- The saved real PID 6764 Genji inventory contains script `0580000000000304`, with `STUStatescriptStateWeaponVolley` at node indexes 6 and 31. Both recorded clientOnly/serverOnly values are zero. This does not prove the implementation can emit projectiles in the offline build.
- The optional community type names were read from [OWLib KnownTypes.csv](https://github.com/overtools/OWLib/blob/develop/TankLibHelper/DataPreHashChange/KnownTypes.csv). Each name was accepted only if its lowercase CRC32 equals its hash. All 908 rows matched; 1,090 of 1,568 previously recorded node occurrences now have a resolved type name. Unknown hashes remain unknown.
- Existing provided-plugin `statescript_logger` source already hooks native state entry, finish, action entry and script entry. Its `s_scriptStates` map stores each node's last native tick and finish flag, even without subscribing a UI logger. Exact map/trampoline symbols were resolved from the local provided DLL/PDB with matching CodeView GUID and age. No extra game hook is necessary to read these records.
- The one-hour v7 presentation test finished with 339,383 presents, 339,382 composites, zero failures, zero unblended pose frames, one held startup frame, maximum paired source age 185 ms and normal native pointer restoration. This is sustained idle presentation evidence, not combat or sustained obstacle movement acceptance.

Private evidence remains under ignored `research/`: `native-script-inventory-named.json`, `owlib-prehash-reference/` and `survival-v7-one-hour-proof/restored-report.json`. Original samples are preserved unchanged.

## Read-only investigation tools

```powershell
python tools/inspect_native_scripts.py --annotate research/native-script-inventory.json --type-names research/owlib-prehash-reference/KnownTypes.csv --output research/native-script-inventory-named.json
python tools/observe_native_weapon_states.py --pid ACTUAL_PID --seconds 30 --output research/native-weapon-state-observation.json
```

The observer requires the exact already-running supplied executable, matching loaded provided-plugin DLL/PDB, original model graph and initialized plugin logger. It opens only a query/read process handle. It installs no hook, changes no variable, sends no input, executes no native game call and applies no MC damage. Local controller/model identity is checked before and after each snapshot. Pointer traversal, key ordering, map counts and tree parents are bounded and checked.

Initial records form a baseline and are not new attacks. Subsequent changes retain native tick and finished state. Variable snapshots remain uninterpreted. `projectileEmissionVerified`, `ammoIdentified` and `losslessAttackChannel` remain false. The last-change map can coalesce several transitions between reads, so it cannot serve as the eventual exactly-once projectile transport.

## Next real-client experiment

1. Load the normal original offline world and Genji through the verified original flow. Do not retry hot map unload or the quarantined cold zero-map route.
2. Start a read-only weapon-state observation before generating original left/right/R actions through the supported game UI automation.
3. Correlate the input/hand action with nodes 6/31 and surrounding graph transitions, runtime state implementation presence and weapon-script variable changes. A state-entry observation is still separate from projectile emission.
4. Follow the first missing transition or native volley implementation. Independently validate the emitted projectile, volley cardinality, ammunition changes and reload completion before routing MC damage. Do not fabricate these from button presses or patch an ammo display to look active.

## Verification and remaining limitation

Fifteen offline checks pass: six type-name/annotation guards, five measured map snapshot checks, and four transition-baseline/identity checks. The logger observer itself still needs a real runtime read; fixture tests do not prove live ABI or concurrency acceptance. The native client was absent at this continuation, and automatic execution review rejected the launch command with only `blocked by policy`. No alternate launch path was used. The complete playable goal remains open.

## Ammo output binding reader

The public [pre-hash-change type schema](https://github.com/overtools/OWLib/blob/develop/TankLibHelper/DataPreHashChange/RegisteredSTUTypes.json) declares WeaponVolley field `39D89271`, named `m_out_Ammo` by [KnownFields.csv](https://github.com/overtools/OWLib/blob/develop/TankLibHelper/DataPreHashChange/KnownFields.csv), as an object of `STUConfigVarDynamic`. This supplies a field identity to look up, not a trustworthy native offset or measured beta ammo value.

`native_weapon_binding.py` follows that field using the loaded object's own STU argument metadata. It requires the exact native Volley type, object category and dynamic config type, reads only measured constant-return/LEA-return getter patterns without calling them, checks field alignment/instance size/inheritance bounds, then reads the dynamic output's resource path with a 32-element cap. Unsupported getters/types/absent paths produce an explicit unresolved binding. Neither copying the public schema's offsets nor guessing an integer equal to 24 is used.

The weapon observer now includes these bindings, or their unresolved error, alongside the state trace. Five fixture cases cover both list layouts, missing/wrong fields/types, path bounds, unsupported getter code and inheritance cycles. These are decoder checks; the actual native beta binding and ammo behavior still require a running original client. Fixture resource path `0d80000000000035` is illustrative and is not asserted as the beta ammo variable.

## Actual original-client read, 2026-10-15

User reopened original PID 40552. Normal DP Load -> cold Hollywood -> Demo -> original Genji selection created the local hero without the additional spawner. A 45-second read-only run yielded 1,024 snapshots, zero read failures and 34 node changes. Original left/right animations coincided with WeaponVolley nodes 6/31 entering and finishing at the same native tick. This is execution-entry evidence, not a projectile result.

The actual constraint getter was metadata-backed instead of a constant return. The reader now decodes only that measured load-metadata/hash/OR-category/return sequence without executing it; a regression covers opcode and category changes. The actual original Volley `m_out_Ammo` outputs on both nodes resolve to resource path `0d80000000000035`, whose recorded value remains 24. This establishes the declared output binding, not working ammo consumption. Native volley implementation inspection shows a check of instance execution-flags bit 3 before its firing path, while the recorded instance flags `0x408001` lack that bit. This is a specific next investigation point; no authority flag was patched and no MC damage was generated.

Private evidence: `research/native-weapon-state-40552.json`, `research/native-weapon-bindings-40552.json`, `research/native-script-40552.json`. Six binding checks and four state-transition checks pass. The full combat acceptance remains open.

## Original Genji execution and projectile proof

The bounded `weapon_gate_probe.cpp` owns private copies of only the two original Genji Volley state vtables. It chains the original Begin, Update and Shot callbacks on the native callback thread; execution bit 3 exists only around those original calls and is restored by its owning scope. Nested calls preserve ownership and unrelated native flag changes. No button-derived ammo value, projectile or MC damage is generated. Exact executable, process creation token, graph, local controller/model, both state tables and original callback addresses are checked before attachment. The module has a two-minute ceiling and restores both tables, retaining its code for in-flight calls.

The first two attempts refused execution and restored without any scoped mutation: the original dispatcher changes flags from idle `0x408001` to measured Begin `0x400081`. The third reached the native Shot callback once but refused a later observed Update phase `0x400001`. The fourth accepts only those three measured flag values (plus the nested scoped bit), and completed with zero failures and normal restoration: 3 Begins, 53 Updates, 7 Shot callbacks, 53 owning scopes. A left burst invokes three shots, whereas right spread invokes one shot that emits multiple projectiles; these are not interchangeable damage events.

Actual original HUD and variable output: left reduced ammo 24 -> 21, right reduced 21 -> 18, R completed the original reload to 24, and a second left reduced it to 21. The declared ammo output resource `0d80000000000035` independently read back 21. The read-only projectile component iterator then observed three distinct native entity IDs, all carrying source-model candidate ID 2147485828, with scene positions changing over time. This establishes real native projectile creation for the tested left burst, beyond animation or entry into Shot. The source field still needs full semantic validation for other heroes and ownership cases. Native projectiles currently travel in the virtual native scene and are not yet transferred into MC; no MC damage or ultimate credit is claimed.

Build: `tools/build_weapon_gate.ps1`; bounded attachment: `python tools/attach_hand_depth_probe.py --pid ACTUAL_PID --weapon-gate`. Independent checks prove nested original returns, flag restoration including exceptions and unrelated flag changes, both state-table restoration and preserved vtable prefix in an owned fixture process. Private runtime proof: `research/native-weapon-v4-proof/`, `research/native-weapon-gate-v4-observation-40552.json` and the completed `weapon-gate-40552.json` report. The probe's own `projectileEmissionVerified:false` remains deliberately unasserted: the separate native projectile observation supplies that evidence. Exactly-once emission transport, MC hits/block damage, ultimate and persistent lifecycle remain required.


## Current sustained lab lifecycle

After the completed v4 two-minute probe restored normally, the same guarded weapon behavior is in v5 with an eight-hour ceiling and independent `Local\OWMCWeaponGateStop_PID` event. `tools/stop_passthrough.py --pid PID --weapon` restores only the two weapon state tables. Current compositor v9 and body v5 use the same eight-hour test window; previous render/body callbacks were explicitly stopped and restoration was checked before replacement. These are extended lab sessions, not a verified permanent release.

Actual original PID 40552 remains running with guest PID 43676. In v5, R again restored 21 -> 24 and left again reduced 24 -> 21; 1 Begin, 26 Updates and 3 Shot callbacks were recorded with zero failures. The v9 camera check matched 849 distinct MC images, zero unmatched polls, maximum basis error 7.57e-8 (static direction, not fast-turn acceptance). Full native combat transfer remains the next required slice. Private snapshot: `research/native-weapon-v4-proof/v5-native-ammo.png`.
