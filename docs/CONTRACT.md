# Diagnostic bridge, protocol 1

**Current contract:** the authoritative two-process passthrough ownership, full-world frame layout and integration gates are in [PASSTHROUGH.md](PASSTHROUGH.md). Original OW owns hero presentation and foreground input; real Minecraft owns the world and terrain collision. This document below is the historical diagnostic telemetry channel only; its Minecraft-owned input assumptions do not define the current gameplay route. Receiving OW coordinates in Minecraft does not satisfy the current request.

This first slice receives **raw pose telemetry** inside the real Minecraft client. It does not take control of the player or connect the two renderers. The eventual target remains complete Overwatch gameplay within Minecraft.

Host: Minecraft Java 1.21.1, Fabric Loader 0.19.5, Java 21, Windows x64.
Guest state: original Overwatch Beta 0.8.0.24919 movement state, described by Prometheus's published structures. Read-only process-memory observations have been verified in the supplied runtime; exact supplied DLL/source correspondence is unverified. The optional BSON stream has not yielded authentic movement frames.

## Ownership and coordinates

Minecraft owns player input, physics, camera, collision, entities, health, inventory and saves throughout this slice. Receipt of telemetry changes no game entity or world. Positions are **raw upstream coordinates** with unmeasured units/axes; no Minecraft transform is asserted yet. No damage scaling is defined.

## Channels

- Local HTTP only, bound to `127.0.0.1:32131` in the Minecraft process. UTF-8 JSON, no binary-layout dependence.
- `GET /health`: protocol, host identity and latest raw pose, its local reception age and stale flag.
- `POST /v1/pose`: at most 16 KiB; `schemaVersion` integer 1, `source` exactly `prometheus` or `synthetic`, `sequence` nonnegative integer, `position` finite numeric x/y/z in the range +/-10,000,000. Unknown extra fields are ignored rather than logged or executed.
- Only latest state is retained, so consumers cannot build an unbounded backlog. Snapshot expires after 500 ms without a received update; expiry does not mutate the world. Source/session ordering is deferred until the original upstream adapter is implemented; sequence is diagnostic only in this first slice.
- Responses: 200 accepted/readable; 400 invalid JSON/schema; 404 unknown route; 405 wrong method; 413 oversized body.

## Original upstream seam

Inspected `state_replicator.h`, `state_replicator.cpp`, `serialization.cpp` from saturn-xvi/prometheus main. Original WebSocket port is 6969; messages are BSON. `PositionUpdate` has type 2, `player_id`, and `data`; `data["220"]` contains the x/y/z/w absolute-position vector, and `data["1A0"]` is `command_frame`. This is source evidence, not a captured game packet. A relay must use localhost and label constructed test packets `synthetic`.

The relay now connects to ws://127.0.0.1:6969/ with proxies disabled and at most 64 KiB per message / two queued frames. On `AssignPlayerID` (type 5), it sends the protocol's `JoinInstance` (type 3) with name `Minecraft Observer`. It emits no hero or movement changes. Only the chosen upstream player ID (default `Server`) contributes diagnostic poses. The forwarded sequence is a relay-local counter, not an asserted upstream tick; units/axes remain raw. Source label is `prometheus` for the local upstream stream and explicitly `synthetic` for fixture tests. This label is diagnostic provenance, not cryptographic authentication.

Runtime probe: the supplied native Demo Server listened on 0.0.0.0:6969, but both a WebSocket client and a minimal HTTP Upgrade probe received no handshake response despite TCP connection success. The process also held a connection to itself. This does not establish the underlying cause. The v0.0.1 and main state_replicator.cpp files match.

The optional `Start-Demo-Bridge.cmd` uses `--listen`: the adapter serves only 127.0.0.1:6969, one native client at a time, with a maximum 64 KiB binary message / two queued frames. Only an absent Origin or the exact native ws://127.0.0.1:6969 Origin is accepted; ordinary browser origins and unknown paths are rejected. Start the bridge with the native server disabled, then use only **Connect Server** in the research UI. The native client can send position messages directly after connection; its fresh player ID is empty. The listener validates that ID as a bounded string but does not filter it to `Server`. It sends no BSON application messages, including ID assignment and join requests, to the game. It requires no periodic pong reply because the inspected client path calls synchronous connect without starting a receive thread. Actual supplied-runtime behavior remains a separate verification gate.

Optional `--capture PATH` in listen mode saves at most the first 200 accepted diagnostic poses. No full packet dump or game asset is exported. The receiver still retains only its latest pose. Fixture tests use `--test-peer` and explicitly label their output synthetic.

## Verified read-only backend

The default bridge now uses tools/observe_overwatch.py, with an exact workspace path and patched executable SHA-256 guard. Windows access is PROCESS_QUERY_INFORMATION | PROCESS_VM_READ only. It reads the published GameEntityAdmin pointer, local entity ID, bounded 4,096-slot entity table, controller/model component lists, and Component 0x15's second MovementState. It checks component owners, list bounds, finite coordinate limits, initialized tick and stable admin/local identity. It calls no game function and performs no process-memory write or injection. Invalid/unavailable state stops this diagnostic observer; MC's last snapshot naturally becomes stale.

The original movement tick and x/y/z are observed directly; the HTTP sequence remains observer-local. Source `prometheus` means this adapter's Prometheus-compatible state layout, not proof of WebSocket provenance. Evidence includes explicit `transport=read-only-process-memory`, the original upstream tick, PID/path/hash and whether HTTP forwarding was used. Transport/tick are extra fields that the current MC receiver discards, retaining only its bounded diagnostic snapshot. Source labels are not an authenticated authority mechanism.

The read-only backend forwarded 300 real samples, including changed coordinates, to the existing MC process. A continuous run's health result was current (`stale=false`, receipt age 29 ms). This proves original position data reception; it proves no MC player, camera, rendering, collision, ability or combat behavior.

## Lifecycle and verification

The Fabric client entrypoint starts the listener once. An occupied port disables this diagnostic listener with a clear error; it must not crash Minecraft. The listener stops with its Java process. A disconnected guest leaves a visibly stale diagnostic snapshot; the player's game is unaffected.

Threat boundary: any local process may submit bounded telemetry. This endpoint has no execution, filesystem, account, input or world-control capability. It is a diagnostic interface, not an authenticated control plane.

Verification separates Java/HTTP contract tests, synthetic transport/layout tests, original process-memory observations and optional network packets. Installing the compiled mod requires restarting the MC client. Original telemetry reception is verified; original-runtime motion authority, render, collision and combat tests remain outstanding.


## Current camera-channel extension

The production frame/camera ownership is defined in PASSTHROUGH.md. OWPOSE01 is a local 4096-byte native camera mapping: version at 8, byte size at 12, PID at 16, generation at 24, active at 32, latest history slot at 36, history count 64 at 40. A seqlock at 64 protects frame at 72, Unix milliseconds at 80, provenance flags at 88, viewport at 92/96, lens at 104/108/112, camera-to-world right/up/backward columns at 128, diagnostic native eye at 168, original matrices at 192/256, and 64 history records of 56 bytes starting at 512. History records contain frame, Unix milliseconds, nine basis floats and flags. Flags 1 means original native camera; 2 means isolated synthetic fixture and is refused in production. Native camera poses expire after 500 ms; malformed or inactive poses cause acknowledgement zero and no world teleport.

OWMCFR01's existing descriptor host frame at 16 is now paired with host generation at reserved offset 176. Both must be zero or both nonzero. They identify the pose actually used when the GPU pixels were submitted, including through delayed PBO completion; they never label an older image with a later pose. Producer restart invalidates history from the old generation. All fields are little-endian. The latest native pose is lossy state, not an event queue; the 64-entry history supports image correspondence. MC still owns final position/collision; diagnostic native eye does not grant movement authority.

### Movement intent extension (2026-10-15)

The same pose seqlock covers u32 extension version 1 at 320, u32 key mask at 324 and u32 foreground-active flag at 328. Mask bits 0..5 are forward W, back S, left A, right D, jump Space and sneak Ctrl. Shift remains a native ability key. Unknown versions/bits/active values are refused. An absent extension releases movement. Synthetic camera packets cannot activate movement, even in the pose-test profile. Native messages preserve released short taps for at most 100 ms; held keys remain level state. Focus loss clears the held state and tap leases. MC releases all intent when the native pose is older than 150 ms, earlier than the 500 ms direction timeout.

KeyboardInput's normal movement fields receive intent; vanilla MC computes velocity, gravity, eye height and block collision. Native position never teleports MC. These bits do not represent attacks, damage or ability completion. The original WndProc is chained for every message and restored with the render hooks at the bounded session stop. Native menu gating and full movement/ability presentation synchronization still need work.

### Guest motor result (2026-10-15)

OWMCFR01 reserves header bytes 1536..1791 for an independent 256-byte OWBODY01 record. MC publishes on its client tick, separate from delayed GPU publication. All fields are little-endian: magic at 0, u32 version 1 at 8, size 256 at 12, native PID at 16, MC PID at 20, MC frame-mapping generation at 24, acknowledged native camera generation at 32, u64 seqlock at 64, Unix milliseconds at 72, u32 grounded at 80, reserved zero at 84, three f64 MC feet coordinates at 96, three f32 velocity coordinates in metres/second at 120 (vanilla per-tick velocity times 20). Dead MC players publish no new body result. Odd, incomplete, nonfinite, older-than-250ms, wrong-native-PID or changed source/session records are refused.

The original Genji presentation motor follows this result after its original local-player tick. It uses a virtual native origin (1000,1000,1000) plus displacement from the initial MC feet, outside the old map's geometry. MC remains the sole world-position/collision authority. Only calibrated native movement histories, velocity/gravity/ground fields and eye XYZ are written; tick IDs, pointers and vector W are preserved. The original scene transform setter runs on that native tick, never a worker or D3D callback. Original idle eye height 1.2 is preserved for Genji; visible world camera height is MC's own. This is not a native collision mesh registration or complete wall-climb/dash implementation.

The backwards-compatible extension at 136 is a u64 world identity derived from the normalized local save path and dimension. Legacy zero values cannot authorize guest reconnection. In body adapter v4, a fresh new guest PID/generation can resume only with the same nonzero world identity and unchanged native generation, within the existing displacement bound. The original MC displacement origin is retained; the new process does not reset the map origin. Replacing a save in-place is outside this identity scheme and requires a fresh host session.

`tools/stop_passthrough.py --pid PID --body` restores only the body callback. The renderer uses its existing independent stop. Current compositor v9/body v5 tests have eight-hour ceilings. Body v4 holds the last trusted native presentation position with zero velocity and grounded presentation during missing/stale guest data. This is an explicitly counted presentation hold, not a new MC result or changed MC grounded state. Changed worlds/hosts still stop coupling. Stale/stop paths must not be claimed as a permanently playable release.
