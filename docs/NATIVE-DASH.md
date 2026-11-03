# Original Genji Shift into the Minecraft motor

The user's Shift request is implemented as native-confirmed Genji dash execution, with MC movement and collision. It is not a keyboard-derived teleport or repeated button damage.

## Original evidence

The supplied client executes graph `05800000000001db`. Its original MoveTo node 6, TrackTargets node 7 and MovementMod node 10 started at native tick 686736 and finished at 687046 in the recorded run. The original animation and eight-second cooldown were also observed. Reflection identifies MoveTo's `m_speed` as native integer 50 and the dash's ModifyHealth amount as dynamic resource `0d800000000001dc`, whose current value in this separate ability varbag is 30. This differs from the weapon varbag's impact damage 35. Private evidence: `research/native-ability-43764.json` and `research/native-dash-parameters-43764.json`.

`prepare_native_dash.py` checks the exact original process and provided-plugin PDB identity and prepares a private process-creation-bound read request. `NativeAbilityReader` opens only a read/query/synchronize handle. It checks the current camera PID/generation, process creation time, admin/local model identity, original ability graph, varbag and typed numeric objects. Bounded MSVC map lookups read the existing provided-plugin logger; the reader neither installs a hook nor calls original game functions.

## MC effects

The first observation is always a baseline, even if a dash is already running. A later native executing timestamp begins a dash once. Missing/stale reads, a finished node or changed source stop it; a repeated timestamp cannot restart it. The watchdog is 100 ms without a verified refresh, with an additional 750 ms ceiling.

While verified active, the MC client predicts movement at the native speed along the captured native camera direction. Vanilla `Entity.move` sweeps the actual player box against MC collision shapes, and normal movement packets retain integrated-server validation. MC records the actual server path and applies the native amount scaled to MC HP (30 -> 3) to each intersected living entity at most once. A collider ray prevents damage through blocks. The current MC dash contact expansion is a simulation and has not been calibrated against the original TrackTargets volume.

Actual MC37352 recorded four original dash starts, cumulative server path length 41.1833 blocks and no reader error. A 401-sample live record included one later dash adding 14.7717 blocks of actual movement and ending grounded on grass, creative/invulnerable with flight off. User actions occurred during the record; the agent's input attempt was rejected on user-input detection and was not retried. This is observation of real play, not a fixed agent-generated trial. The fixed test villager remained at 20 HP: this run does **not** establish live dash damage or controlled wall acceptance. Evidence: private `research/native-dash-live-proof.json`.

Movement is currently sampled on the 20 Hz MC tick, so native duration quantization can change free-path distance (another observed dash traveled 12.5 blocks). Exact timing/distance calibration, a controlled wall/target test, native kill-reset semantics and hero-recreation recovery remain required. The native HUD/animation/cooldown are retained; ultimate is not yet implemented.
