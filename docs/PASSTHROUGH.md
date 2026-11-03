# Overwatch host / Minecraft guest: current passthrough contract

The user explicitly selected the two-process passthrough route on 2026-10-14, with the GTA V example as the reference. This supersedes the Minecraft-visible hero experiment and the proposed offline content-port route. Preserve the original Overwatch runtime for hero presentation and behavior; do not replace it with approximate MC weapons/HUD.

Reference: https://github.com/rehan-remade/universal-modder/blob/main/knowledge/games/gta-v/minecraft-passthrough.md and its examples/minecraft-gta5-passthrough code. The GTA example runs MC next to GTA and exchanges frames, controls and events. Its ScriptHookV/ReShade host code is GTA-specific, and its MC 26.3 GPU APIs cannot be copied unchanged into this MC 1.21.1 lab.

## Desired ownership

| System | Owner | Adapter requirement |
|---|---|---|
| Visible window, mouse/keyboard, menus | Original offline OW beta 0.8.0.24919 | Route controls once; suppress fusion while menus/load screens are active |
| Hero hands, weapon animations, native HUD, sound, ability state | Original OW | Preserve native drawing and state; transfer confirmed attack/ability events |
| Complete terrain, chunk generation, blocks, creatures, inventories, saves | Minecraft 1.21.1/Fabric | Run an isolated normal world in the background; export actual world color/depth |
| Collision with MC terrain and final walkable position | Minecraft | One authoritative resolver; render the returned pose with interpolation/prediction, and remove old OW map collision from fused play |
| Look direction | OW | Sample actual world camera, not the different first-person lens; tag it with host frame/request sequence |
| Hero movement/ability intent | OW | Adapt native intent to MC collision; do not let both native map physics and MC position corrections compete |
| MC creature damage and block destruction | MC server | Validate sequenced native attack/projectile events; apply exactly once in the actual MC world |
| Hero health/cooldowns | Native OW state, coupled to MC damage | Explicit conversion and death/respawn synchronization; unverified |

The reference mixes GTA and Minecraft scenery. This project instead needs a full MC scene behind native OW hands/HUD. The old OW map must stop determining visible terrain and collision in fusion mode. That full replacement remains unimplemented; the earlier native cube/patch results do not prove it.

## Channels

- World frames: named shared memory `Local\\OWMCPassthroughFrame`, three slots, odd/even per-slot sequence and final publication. Actual MC world RGBA and depth, captured before MC hands/HUD. Latest completed frame wins; no blocking GPU waits.
- Control/pose: a bounded loopback channel, versioned with host session and sequence. Current framebuffer proof has no host pose consumer; host request sequence is explicitly zero. Pose, input and motor authority are the next slice, not implied by frame export.
- Combat: an ordered bounded event queue, with unique session/event IDs and acknowledgements. Button reads alone do not establish attack, projectile or hit events. This channel is not implemented yet.

The new frame wire magic is `OWMCFR01`, version 1, little-endian. Header: 4096 bytes; 3 descriptors at offset 256, stride 256. Mapping header: magic[8], version u32 @8, header bytes @12, slots @16, max width @20, max height @24, reserved @28, slot byte stride u64 @32, publish counter u64 @40, latest slot i32 @48, source PID u32 @52, generation u64 @56. Slot: seqlock u64 @0, MC frame u64 @8, host request frame u64 @16, dimensions u32 @24/28, near/far/FOV f32 @32/36/40, flags u32 @44 (2 = bottom-up, non-reversed GL depth), camera position f64 @48/56/64, yaw/pitch/roll f32 @72/76/80, first-person u32 @84, capture/publish monotonic ns u64 @88/96, publication Unix ms u64 @104, actual projection matrix 16*f32 @112. Payload: RGBA8 followed by depth f32, each width*height*4 bytes. No MC hand/HUD payload is used in this proof. A changed generation resets consumer state.

Wall-clock ms is used only for freshness; monotonic Java ns and native QPC require an explicit clock correlation before pose-age/reprojection measurements. A source frame carries its own rendered camera/projection. Never attach a newer unrelated pose to older pixels.

## Rendering and lifecycle gates

1. Verify actual MC full-world color/depth and shared-memory integrity independently of OW.
2. Build/test an independent D3D11 compositor with calibrated GL/D3D depth and camera reprojection, plus startup/stale/resize/stop cases.
3. Retain native OW hands/HUD in a measured insertion stage while replacing the world image. Native first-person isolation and complete scene replacement require separate evidence.
4. Synchronize pose and collision authority, then validate walk/jump/turn without old-map barriers, slipping or periodic position correction.
5. Native attack events damage a real MC villager and rockets destroy actual MC blocks, once each, with native animations/HUD intact.

Until gate 2 passes, do not load a new continuous compositor into the user's OW client. GPU creation, copies and rendering must run on the actual render thread; worker threads only publish already-copied CPU data. Never replay native draws to manufacture a hand/HUD layer as the default route. Disconnected/stale sources suppress fusion; native menus remain usable. Restart identities reject old frames and events. New tests use independent profiles and saves.

## Existing evidence / retired experiment

Earlier cube anchoring, original wall occlusion, MC patch geometry and V7 turning stability were user-verified. Later V9 still stuttered/floated and did not replace the host's world.

Three-frame observational OW captures (PID 43152) obtained actual pre-HUD color/depth and final color, restored the callbacks and measured distinct world/first-person lenses. Native hand is already present before HUD, so simply overwriting that stage would erase it.

Continuous native-layer draw replay V2 and V3 each caused a real user-reported crash after two frames. V3's UAV preservation regression passed in WARP, but the real host reported failure and observed no UAVs; this does not prove UAV loss caused the crash. Worker-thread initialization also used the immediate context without render-thread ownership, a confirmed API-contract defect and a crash hypothesis. Full root cause remains unverified. These versions are retired and must not be attached. Source/fixtures are retained as failed research, not a working integration.

The user confirmed native throw/reload animation. The bounded read-only combat observer saw native left/right input bits but no identified projectiles; native hits remain unverified. Offline asset inventory is separate research and is not the selected implementation route.

## Verified full-world guest slice

The new guest entrypoint exports actual MC 1.21.1 color/depth at WorldRenderer return, before MC hands/HUD, through three fenced GL pixel-pack buffers and the versioned Windows mapping. GPU work is confined to the render thread; a daemon publishes completed CPU bytes. GL read framebuffer/buffer and pack state are restored and checked. Duplicate live producers are refused; a dead producer's retained mapping can receive a new generation. The launcher uses guest-passthrough-client and creates/loads its independent vanilla superflat save, with no copied patch, OW process or synthetic OS input.

Validation: guest build passes; the actual Win64 mapping creation/publication/duplicate/shutdown regression runs in Gradle check; eight Python malformed/stale/layout/row/depth tests pass. Real MC runs produced 960x540 frames and original creatures. Two 10-second captures received 173 and 169 distinct fresh frames with zero rejected frames. The final run published 4492 frames, skipped zero captures and passed 10405 GL restoration checks, with no exporter error. A fresh generation was observed on the separately relaunched producer. The test then shut down normally and saved overworld/Nether/End.

Evidence: research/mc-world-frame-proof.json, research/_archive/2026-10/mc-passthrough-health.json, research/_archive/2026-10/mc-passthrough-world.png and guest-passthrough-client/logs/latest.log. These are actual guest-process evidence. They do not prove a native OW compositor, camera synchronization, collision coupling or native combat; host request frame is still zero.

Reproduce this isolated proof:

```powershell
./tools/build_guest.ps1
python bridge/test_world_frames.py
python tools/launch_passthrough_guest.py
# In another terminal, after the background world is ready:
python tools/check_world_frames.py --seconds 10 --capture research/_archive/2026-10/mc-passthrough-world.png
Invoke-RestMethod http://127.0.0.1:32133/shutdown -Method Post
```

This starts only Minecraft. It does not attach an OW module. The old renderer/creative commands are separate historical experiments.

## Independent D3D11 slice, 2026-10-15

`native-host/src/world_frame.hpp` is the native read-only consumer of OWMCFR01. It validates the wire identity/bounds, makes an owned CPU copy, rechecks the slot sequence/generation before upload, rejects stale/invalid depth, and converts bottom-up guest rows to top-down D3D texture rows. A native Win64 mapping fixture exercises odd slots, new generation, expiry and producer removal without creating the production mapping.

`frame_compositor.cpp` owns a separate D3D11 device and immediate context. Every GPU call runs on its owner thread, including initialization. This is an isolated lab renderer, **not a ready host-state adapter**: it does not borrow or restore OW's immediate context. RGBA8 and R32_FLOAT depth are uploaded into independent textures, rendered, and read back for numerical checks. The lab's blocking staging readback is a verification instrument and must not be copied into a per-frame host callback.

The rotation-only target-to-source transform is `P_source * R_target_to_source * inverse(P_target)`. Matrices on the wire are column-major; shader matrices are explicitly row-major and multiply column vectors. GL window depth already ranges from 0 to 1: reconstruct GL clip z with `2*d-1`, transform with the inverse warp, and convert target clip z back to D3D window depth. A value exactly 1 is background/sky and retains depth 1 under rotation; treating it as a finite far-plane point caused a large black sky patch in the first real preview and was fixed. Unsupported source rays produce transparent coverage rather than stretched edge pixels. Rotation still leaves uncovered edges of the old view; this requires a fresh matching source frame or overscan, not a claim of complete camera sync. Translation, disocclusion repair, clock correlation and actual host pose matching remain outstanding.

Verification: WARP tests compare asymmetric color markers and depth endpoints, positive/negative yaw against a CPU oracle, far-background rotation, resize, malformed/stale frames, singular transforms and rejected off-thread GPU use. Hardware tests used two actual MC runs: 345 distinct frames over 20 seconds and, after the sky fix/restart, 171 over 10 seconds. Both had zero rejected frames, exact RGBA roundtrip and maximum depth error 0 at 960x540. The corrected run's upload/draw/readback/pixel-check time averaged 3.86 ms, p95 4.90 ms, max 7.35 ms. This is independent lab timing, not combined-game FPS or host latency. The guest's generation changed on restart; both test worlds stopped normally and saved their dimensions.

Private evidence: `research/d3d-frame-hardware` and `research/d3d-frame-sky-fixed` contain reports and actual screenshots; the corrected directory also retains one original color/depth/projection fixture for future offline regression. `owAttached=false` and `hostPoseConnected=false` remain explicit.

```powershell
./tools/build_frame_compositor.ps1
python tools/launch_passthrough_guest.py
# After the guest has entered its world:
native-host/build/frame-compositor-live.exe 10 research/d3d-frame-proof
Invoke-RestMethod http://127.0.0.1:32133/shutdown -Method Post
```

## Prepared original hand-depth observation, 2026-10-15

The new `hand_depth_probe.cpp` observes three original frames and automatically restores the two vtable pointers. On its second observed frame it copies the actual depth surface before and after the contiguous first-person draw group, then the original pre-HUD/final color. The classifier uses the previously measured **Genji** lens, full viewport, six MRTs and D24S8 resource identity. It neither replays native draws nor creates a replacement native shader/renderer. Texture creation/copy/readback happen only in render callbacks, not its worker. First-person FOV changes, another hero, split draw groups, later world overdraw, transparent effects and menus are unverified: incomplete observations must not become a compositing mask.

An independent WARP scene writes a known half-screen depth change through its real D3D draw call. The probe captured exactly that change, retained original vertex/depth state, verified pointer restoration after three presents, released its references to original resources and allowed a subsequent native ResizeBuffers. Python analysis separately rejects mismatched/truncated resources and proves reused stencil values alone do not classify hands. Both new native builds treat compiler warnings as errors. This is a fixture result; **no real OW hand mask or full-world composition has been verified yet**.

`attach_hand_depth_probe.py` only loads this fixed local observational DLL. It checks the exact offline process path and full executable hash before obtaining loader rights, refuses previous lab probes, keeps the verified process handle through loader-handle acquisition, and bounds the loader/report waits. It does not load retired replay DLLs. A stopped/hidden game with no presents needs to resume to complete the three-frame stop; never retry-load a pending probe.

```powershell
./tools/build_hand_depth_probe.ps1
python tools/test_hand_depth_analysis.py
# Only after the supplied offline client has entered its original Genji map:
python tools/attach_hand_depth_probe.py --pid <fresh-pid>
python tools/analyze_hand_depth.py --pid <fresh-pid>
```

The candidate depth delta stays labeled unverified for moving hands until checked through native throw/reload motion. It is not a replacement for the complete native layer-preservation gate. The first actual idle-frame result and bounded integration proof are recorded below.

## Actual idle hand extraction and one-frame world replacement, 2026-10-15

The user entered the original Genji map. The observational probe ran in PID 30548 for three presents: six original first-person draws, zero failures, original pointers restored, client responding. The before/after depth delta covers 249346 pixels (6.76%) at 2560x1440. Visual inspection on an explicit gray background shows the original arm, fingers and shuriken with the map excluded. The user subsequently **manually** closed and restarted OW as PID 6764; this was confirmed by the user and is not recorded as a crash.

Added a **bounded**, separately named `owmc-world-blend-probe.dll`. It retains the same three-present automatic stop and renders a single mixed frame, the second observed frame only. In its pre-HUD callback it derives a mask from that very frame's original hand-depth pair, accepts only a complete fresh MC mapping snapshot, copies the original native color, and draws MC color wherever the hand mask is false. Native hand RGBA and native background alpha are preserved. OW then draws its own HUD normally. Input, native movement, collision, native attacks and world camera are untouched by this proof; no host pose matching is claimed.

`WorldBlend` creates its resources and records **only its own fullscreen triangle** on an owned deferred D3D11 context, on the actual render callback thread. The immediate context executes that command list with `RestoreContextState=TRUE` as defined by Microsoft's API. This does not replay original native draws. The standalone WARP fixture checks hand/world/alpha pixels plus viewport, topology, RTV and CS-UAV state preservation. The fixture nested inside the actual three-frame observation tests the later HUD pass, original vertex/depth state, vtable restoration and subsequent ResizeBuffers. Both pass with warnings treated as errors.

An earlier state-swap variant of this new blend class passed the standalone fixture but failed the nested observation fixture: the background remained native red instead of guest blue. It was **not attached to OW**. Switching to the owned command list made the same nested pixel/state/HUD fixture pass. Re-entrant draw interception / interface-state switching is a hypothesis; the exact runtime cause of the state-swap variant is not established. This is separate from the retired native replay crashes.

Actual bounded integration in original PID 6764 used real MC PID 45804, generation 5659147328119258277, MC frame 9074. The report shows `frames=3`, six original hand draws, `failures=0`, `restored=true`, `worldBlended=true`, `nativeReplay=false`, `hostPoseConnected=false`. The final original swapchain color contains the MC flat world and creatures, original Genji hand/shuriken, native HP 169/200, ultimate 0%, ammo 24/24 and native skills/UI. The original process remained responding after restoration. MC then shut down normally and saved its dimensions.

Pixel comparison between the original pre-HUD color and mixed color proves **all 248554 observed idle hand pixels have identical RGBA** and every native alpha pixel is retained. 3437846 background pixels changed. The actual final HUD image was captured after OW's own HUD draw; it was not rebuilt by the mod. Private raw/PNG/reports are in `research/native-world-blend-6764`; the earlier idle capture is in `research/native-hand-observation-30548`. The PNG conversion only makes the captured RGB opaque for viewing.

This proves one actual original-client mixed world/hand/HUD frame. It does **not** prove continuous gameplay, moving-hand masks/effects, camera synchronization, MC movement authority or native combat in MC. The window naturally returns to the original map after the bounded stop. The analyzer keeps those general verification flags false, while separately recording `boundedWorldFrameVerified`, `handPixelsExact` and `nativeAlphaExact`.

```powershell
./tools/build_world_blend_probe.ps1
python tools/launch_passthrough_guest.py
# After both games have entered their worlds, using a fresh unhooked original process:
python tools/attach_hand_depth_probe.py --pid <fresh-pid> --world-blend
python tools/analyze_hand_depth.py --pid <fresh-pid>
Invoke-RestMethod http://127.0.0.1:32133/shutdown -Method Post
```

Do not rebuild the blend DLL while that same DLL is loaded, or retry-load a completed/pending module in the same process. This build remains deliberately bounded until pose correlation, render-thread lifecycle, stale/menu gating and moving native hands are verified.

API reference: https://learn.microsoft.com/en-us/windows/win32/api/d3d11/nf-d3d11-id3d11devicecontext-executecommandlist


## Paired original-camera channel, 2026-10-15

A read-only native observer now publishes the original world camera through Local\OWMCHostPose (OWPOSE01, 4096 bytes). It reads CPU-uploaded CB544 slot 9, rejects the known Genji first-person lens, validates the full packed world/inverse matrices and viewport, then publishes one world pose per native frame. Native drawing and movement are unchanged. The observer has a stop event and 120-second ceiling, restores both pointers on the render callback, and refuses active previous lab callbacks. A stopped bounded module can remain loaded only with a current-process restoration record; loading the same DLL twice is refused.

The wire includes a generation, producer PID, active flag, timestamps, seqlock, full orthonormal camera-to-MC basis and 64-frame history. Native view axes map to MC right=-viewX, up=+viewY, backward=-viewZ. Native eye is diagnostic only: it does not teleport or override MC physics. The guest Camera and world FOV mixins use the actual basis, including roll, with 1.18 tangent overscan. A PBO capture retains the exact applied host frame/generation alongside its own pixels. OWMCFR01 descriptor offset 176 now carries host generation; frame and generation must both be zero or both nonzero. Stopped/stale producers clear the guest acknowledgement.

Independent native layout/basis tests and a three-present real D3D observer fixture pass, including native state/pointer restoration and subsequent resize. Java tests check 36 yaw/pitch/roll combinations and invalid/stale/odd/inactive/reflected/synthetic poses. The isolated actual MC test uses its own save and explicitly synthetic flags: four cardinal views see the corresponding physical colored walls; requested 20-degree roll renders 20.0000019 degrees in metadata and 20.00135265 degrees from the wall's geometry pixels. Same-process publisher restart changes generation; expired poses drop acknowledgement. These fixture poses are never accepted by the production guest. Private evidence is research/pose-guest-proof.

Actual original OW PID 6764 published 7261 world poses over 7262 presents with zero failures and restored normally at its time limit. Actual background MC PID 16676 produced 167 distinct matched images in a ten-second verification: each image's acknowledged native history basis agrees with its rendered yaw/pitch/roll to maximum element error 8.69e-8, with zero unmatched polls. The user then turned the native view; native recorded basis changed. The follow-up image verifier began after the bounded publisher expired, so that attempt correctly produced no matched frames. Dynamic during-turn matching is still outstanding; it is not claimed from the earlier static-view proof. Private report: research/native-pose-guest-proof/report.json.

Continuous composition, MC-authoritative movement and native combat remain unverified. Next is a reusable GPU depth-pair compositor, followed by a bounded continuous original-client run with source identity/age and lifecycle gates.


## Continuous GPU slice and dynamic-camera test, 2026-10-15

LiveWorldBlend retains private depth-before/depth-after and color textures, compares R24 depth directly in the pixel shader (stencil excluded), uploads only changed MC frames, and records only its own draw in a deferred context. It retains no original swapchain texture between callbacks. Tests cover exact native hand/alpha, moving masks, texture/upload reuse, native state, resize, wrong thread and source-frame/generation-correlated rotation reprojection. The nested native callback fixture checks native HUD after all three composite frames and automatic restoration. No continuous CPU/GPU depth readback is used.

Actual v1 original PID 6764 completed 7025 mixed frames in two minutes, with zero failures, four private texture allocations and normal callback restoration. v2 extends the lab window to ten minutes with a stop event. An automated actual-client view/throw test produced 1537 distinct matched MC images across large upward/downward turns, maximum basis change 1.99969 and maximum matrix error 3.47e-7, zero unmatched polls. The original hand throw animation and HUD were visible through the real composite. v2 was manually stopped by its event after 18318 presents: 18095 mixed frames, zero failures and restored=true. Evidence is research/native-live-v1-proof and research/native-live-v2-proof.

**Failure observed by user:** v2 still flashed the native map during fast motion. Its log recorded 177 coverage rejects and 45 source rejects. Neither this visual failure nor the original map audio is acceptable as playable completion. The v3 shader now fills missing source rays from the MC image, never original color outside the current hand mask; unmatched/stale frames hold MC rather than exposing the native map, and startup uses a neutral private background. Independent adversarial tests with every ray outside coverage or behind the source camera pass. v3 actual-client motion/source-loss verification remains outstanding. Temporary MC-image hold is not claimed as accurate reprojection.

Original offline weapon test: native throws/reload animation execute but HUD remains 24/24 and ultimate 0%; 3957 read-only samples had zero read failures, left/right bits and zero identified projectile components. A read-only script inventory found 23 model scripts, 59 entity variables and 393 server-only graph nodes. This does not establish the exact missing authority path; no native combat event or ammo fix is claimed.

Empty-scene exploration: a GUID+age match between the provided inject.dll and prometheus.pdb permitted a read-only inventory of 12762 loaded STU resources and 19 map headers. These include AutomationStressArena, tutorial, login scenes and shipped maps; no empty map is established. A normal map-menu-equivalent request from loaded Hollywood to AutomationStressArena reached world-loading state 4 and the original process exited. Existing compositor pointers were restored before the request. This hot-switch route is quarantined. The exact crash cause is unproven. Restoring the provided executable requires its own working directory, otherwise the relative hash library fails to open. Empty scene, original map audio removal, native physics removal and playable weapons remain required work.

Cold-start follow-up: using the original client Map menu from world state 2 with loaded map 0, AutomationStressArena reached world state 8 in PID 14780 and remained responding. It visibly contains a large repeated industrial scene, so it is not an empty map. Selecting Genji before the plugin demo flag was enabled did not create a local entity (local ID stayed 0). The prior hot-switch crash is therefore not proof that the arena asset cannot load. Restored the provided plugin demo flag through its GUID-matched PDB symbol, equivalent to its Demo menu, to resume original local hero spawning. No original map audio removal has been verified.


## Natural survival / grounded input, 2026-10-15

The real background client now defaults to Overwatch Survival World (normal terrain, structures, survival, normal difficulty), preserving the old flat save. A one-time safe grass spawn avoids the original birch-canopy start. Native movement intent enters vanilla MC input without copying original OW position. Actual original-window Space and W tests produced MC jump 71 -> 72.2522 -> 71 with final onGround=true and one short forward step. Full obstacle/ability/death acceptance is not established.

Live v6 completed 26346 presents,26345 composites,zero failures/omitted hand-boundary composites,one held startup frame,max paired source age174ms,then restored native swap/context/WndProc pointers. Current v7 uses the same rendering/input and a one-hour test ceiling; explicit stop is tools/stop_passthrough.py --pid PID. Hand gamma lift1.3 applies only inside the original depth mask; it is not MC dynamic lighting. Missing mask draws MC only; missing boundary holds the previous complete private composition, not original-map color.

Cold zero-map hero initialization exited PID31452 and is quarantined. Current original backing scene is Hollywood; native environment audio and weapon authority remain unsolved. Overall playable goal remains incomplete. Private proof: research/_archive/2026-10/survival-v6-proof and research/_archive/2026-10/survival-native-v6-660.png.
