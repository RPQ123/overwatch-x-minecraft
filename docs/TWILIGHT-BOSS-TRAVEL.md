# Twilight Forest boss travel — pinned Fabric 1.21.1

## Scope and status

The 2026-10-23 human request reauthorizes opening the existing Twilight trial,
disabling boss-order restrictions, and using F12 to select a boss destination.
`TwilightBossTravel.java` implements the server half; root owns the F12 client
menu, common integration, compilation, deployment and actual play verification.
The v4 server class passed actual transport to all eight original rooms in
`research/twilight-boss-menu-20261023/eight-v4/result.json`; that first run is
**transport evidence only**. Root subsequently directed the actual native camera
in `eight-v4-camera/` and viewed all eight images, accepting the actual original
room/arena floors. This does not complete every original boss battle or native
attack-recovery gate. A real activated-room revisit failure and its pending
entity-lifecycle correction are recorded below.

The first real F12/Naga attempt is retained as **failed** in
`research/twilight-boss-menu-20261023/naga-first/result.json`: native F12 and1
selected the real request, and the gamerule actually read back disabled, but the
spawner lookup incorrectly reported absence. This is not accepted travel.
The ticket correction subsequently passed actual transport: the original BE
index found Naga's real spawner and all25 owned tickets were released. All seven
other original structures also completed transport with original BE markers and
released tickets in `seven-v2/result.json`. **These are not eight qualified
destinations.** Naga landed in a sealed dirt air pocket atY0; Lich was outside
its real floor, Hydra below its lair surface, Yeti below its cave floor, and Snow
Queen in a packed-ice interlayer. Root actually reviewed these failures. The
floor/connection correction below was deployed as v4 and actually rerun; the
original v2 destinations remain failures, not corrected historical successes.

Travel does not summon replacement bosses, delete dungeons, mark bosses defeated,
grant every advancement, disable original boss shields/phases, or modify the
native OW hero. A failed doorway search leaves the player in place.

## Installed runtime authority

Actual installed file:
`guest-passthrough-client/mods/twilightforest-fabric-1.21.1-4.8.754.jar`

SHA256: `7f4bf512341bda95eeec0343d1233e8ef733ea599f489d60b27db13b2226fb42`.
The archive was read directly: `fabric.mod.json` identifies `twilightforest`
4.8.754, Minecraft `~1.21.1`, Java >=21, loader >=0.17.0 and Fabric API
>=0.116.14+1.21.1. All actual worldgen structure JSON and metadata are preserved
in `research/twilight-boss-travel-20261023/actual-jar.json`.

The official Fabric branch was retrieved online, pinned at source tree commit
`b8363788c3e996c018af360ff038c700a88a92dd`. That current source commit is reference
material, not a claim that the installed release was built from that exact commit.
`sources.json` records the 28 retrieved source URLs and content hashes. Actual
installed class signatures and bytecode were independently recorded in
`javap-spawners.txt`, `javap-entrances.txt`, and `actual-jar-bossrooms.txt`.
`actual-profile-readonly.json` also records actual TOML values and pre-launch
level.dat metadata. The fresh Boss Free save's initial disk gamerule was true;
only the running BooleanRule readback proves unlock.

## Eight implemented main bosses

| F12 number / public ID | Real structure ID | Exact original room class | Real spawner block |
| --- | --- | --- | --- |
| 1 `naga` | `twilightforest:naga_courtyard` | `CourtyardMain` | `twilightforest:naga_boss_spawner` |
| 2 `lich` | `twilightforest:lich_tower` | `LichBossRoom` | `twilightforest:lich_boss_spawner` |
| 3 `minoshroom` | `twilightforest:labyrinth` | `MazeRoomBossComponent` | `twilightforest:minoshroom_boss_spawner` |
| 4 `hydra` | `twilightforest:hydra_lair` | `HydraLairComponent` | `twilightforest:hydra_boss_spawner` |
| 5 `knight_phantom` | `twilightforest:knight_stronghold` | `StrongholdBossRoomComponent` | `twilightforest:knight_phantom_boss_spawner` |
| 6 `ur_ghast` | `twilightforest:dark_tower` | highest `DarkTowerMainComponent` | `twilightforest:ur_ghast_boss_spawner` |
| 7 `alpha_yeti` | `twilightforest:yeti_cave` | `YetiCaveComponent` | `twilightforest:alpha_yeti_boss_spawner` |
| 8 `snow_queen` | `twilightforest:aurora_palace` | `IceTowerBossWingComponent` | `twilightforest:snow_queen_boss_spawner` |

These registry IDs are present in the actual archive's data and blockstates, not
guessed English names. Knight Phantom is the original six-knight encounter,
not six independently summoned bosses. Quest Ram is an optional quest creature,
not one of this main-boss combat catalog's eight entries.

`twilightforest:final_castle` exists as a structure, but its apparent final-boss
spawner is **not a working final boss**. In the pinned installed class,
`FinalBossSpawnerBlockEntity.spawnMyBoss` consists of `iconst_0; ireturn`.
The class references `PLATEAU_BOSS` but never spawns it. The catalog exposes
`finalCastleBossImplemented=false`; it does not add a fake ninth boss or install
an unrelated final-boss addon.

## Progression and original encounter lifecycle

Installed `TFGameRules` bytecode confirms exact name **`tfEnforcedProgression`**,
default true, with the original BooleanRule callback sending
`EnforceProgressionStatusPacket` to players. The server uses its public original
`ENFORCED_PROGRESSION_RULE` supplier, sets the rule false and reads it back across
all server worlds. `progressionDisabled` reflects that actual readback.

Official `ProgressionEvents` gates biome punishment and structural protection on
`LandmarkUtil.isProgressionEnforced`. This is the correct order-lock control;
it does not alter individual bosses' original attack immunity or fight phases.
Lich shield reflection, Hydra head vulnerability, Knight group sequencing and
other original AI remain the installed mod's responsibility.

The Knight stronghold has an additional **physical** trophy pedestal/shield
mechanism. Its real `StrongholdAccessChamberComponent` creates a pedestal and
shield floor; `TrophyPedestalBlock` requires a trophy above even when progression
is false. The ordinary mod neighbor event then removes nearby shields. The human
has authorized activating this original mechanism if needed, strictly at an
actual access piece, with empty space above a real pedestal, and an activation
receipt. Current travel instead targets the actual underground **boss-room**
threshold beyond this prerequisite, so it does not place a trophy or remove
shield blocks. It never pretends the physical pedestal itself is auto-activated.

Original boss spawners, not project replacement entities, activate near players
in non-peaceful difficulty. Some installed subclasses add vertical/range checks;
Knight spawner creates its original six numbered knights. A visited room's
spawner can be consumed. Travel therefore accepts the expected original spawner,
or an already present living original boss of the expected registry type. When
both are absent it explicitly reports a possibly conquered room; it does not
respawn or reset the room covertly.

## Server integration contract

Public entry points:

```java
TwilightBossTravel.tick(server); // END_SERVER_TICK, existing owner
TwilightBossTravel.request(server, playerUuid, bossId, stillAdmitted);
TwilightBossTravel.close(); // optional server-stop cleanup
String snapshot = TwilightBossTravel.status; // immutable JSON string
```

`stillAdmitted` must read only a client-published volatile admission token. It
must not access MinecraftClient or JNA on the server thread. Root's integration
invalidates the token on hero/model/generation change, focus loss, an active
skill, or stale host state. The callback is checked at acceptance, every pending
tick, and immediately before teleport. This also prevents a same-dimension
long-distance teleport from carrying a currently active Q/Recall into a new
position. The 3-argument overload exists for explicit server-only callers and
uses a true predicate; production F12 uses the guarded overload.

Only a living creative player in an explicitly selected singleplayer
`owmc.twilightTrial` save whose name begins `Overwatch Twilight ` is accepted.
The real pinned mod and its real dimension must exist. Server-instance changes
discard pending jobs/future references; disconnect, death, mode or dimension
changes cancel before teleport. Every idle request immediately increments
`requestId`, including requests that fail validation. There is no silent
cooldown. A request while a job is already running attaches to that existing job
and increments observable `busyRequests`; it does not replace or mutate the job.
Client release-to-arm remains necessary to prevent held numeric keys repeating.

Status includes `busy`, `requestId`, `completed`, `busyRequests`, `boss`, `phase`,
`error`, `progressionDisabled`, `structureId`, exact destination/anchor coordinates,
`destinationKind`, original piece class, and an eight-entry catalog. Successful
completion alone increments `completed`. The client should close its menu on
that receipt rather than on keypress or an intermediate locate result.

## Locate, generation and safe floor

The actual Yarn 1.21.1 API was verified both online and using the local named
Minecraft jar. Locate uses `ChunkGenerator.locateStructure` with a direct
`RegistryEntryList` for the one verified structure. Search radii are bounded
8/16/32/64/96/128 with at most one locate invocation per server tick. This bounds
work and separates phases, but a vanilla locate call is synchronous; this is
**not** a promise of zero generation stutter or a hard millisecond limit.

The located point is resolved to a real generated `StructureStart`; only its
actual original boss piece is used. The initial future-based implementation had
an ownership mistake: local Minecraft bytecode proves UNKNOWN tickets expire
after one tick, and `getChunkFutureSyncOnMainThread` pumps tasks until completion
when called on the server thread. Keeping those futures does not keep earlier
chunks resident while later chunks generate. That call was removed here.

The corrected candidate holds a unique job's custom ticket for every requested
chunk. Actual `ChunkTicketManager.addTicket` bytecode computes
`FULL level33 - public radius`, so radius0 is the intended FULL33 lease. At most
two tickets are added each server tick and at most100 exist in the job. Normal
chunk processing advances between ticks. Actual nonblocking `getWorldChunk(x,z)`
is polled until all requested WorldChunks are present. Missing chunks are
reported, never interpreted as an empty spawner index. Success, failure, server
identity reset and close release every job ticket; expiry2600 ticks is a backup
bound. A native POST_TELEPORT short ticket bridges establishment of the arriving
player's ordinary tickets. No permanent forced chunks are created. Total travel
deadline is2400 server ticks. There is no worker-thread ServerWorld access.

The first failed Naga world's strictly saved MCA was read without changing it.
`naga-first-exact.json` records chunk(-16,0), `conquered=0`, CourtyardMain box
[-270,2,-14..-226,12,30], and actual courtyard/spawner template box
[-248,4,8..-248,5,8]. The block entity is `twilightforest:naga_spawner` at
(-248,5,8); its section palette/packed data identifies the block there as
`twilightforest:naga_boss_spawner`. This marker is inside the selected box.
The failure was not an already defeated/missing boss, wrong block ID or
out-of-box marker. This alone does not prove a transient BE-index bug; lost
chunk ownership is the stronger API-supported candidate and is instrumented
with missing chunks, owned tickets, BE counts and resolution data.

Every fallback retains the original-spawner requirement. Naga's actual1×2×1
spawner template and Lich's31×12×31 boss-room template supply verified markers.
Minoshroom/Hydra/Knight/Ur-Ghast/Yeti use source-verified local marker coordinates
and the installed mod's public `getBlockPosWithOffset`, preserving its real
orientation and virtual Y transform. Yeti radius and Dark Tower height are read
from the actual original piece. The last fallback inspects only a real boss-room
box of at most50,000 blocks,512 each tick. It cannot scan an entire dungeon or
invent a marker. `resolutionMethod` distinguishes index, exact template,
original transform, existing original boss and bounded original-block scan.
The original block type must still match before floor search begins.

The first candidate incorrectly searched several blocks down from the marker.
Two air blocks over solid ground proved insufficient: natural pockets and a
palace's thick floor can satisfy that check. This has been replaced with
source-specific **exact walking layers**, derived from the actual room piece,
not from a boss entity's changing Y position:

| Original room | Exact player feet layer | Source / actual failed world comparison |
| --- | --- | --- |
| Naga courtyard | main box minY+2 | actual minY2, marker5: feet4; old feet0 was underground |
| Lich boss room | template box minY+4 | actual template floor smooth_stone at local3, marker local5: feet80; old75 was outside/below |
| Minoshroom | box minY+1 | original room floor local0: feet-23 in current room |
| Hydra lair | box minY | original flat lair floor density: feet0; old-2 was a dirt depression |
| Knight Phantom | box minY+1 | original tomb floor local0: feet-19 in first room |
| Ur-Ghast | main box maxY-4 | highest original5-block floor at height-6, feet at height-5:199 |
| Alpha Yeti | cave box minY | original cave ground layer: feet1; old-1 was below it |
| Snow Queen | minY+(floor(height/10)-1)*10+1 | original10-block floor spacing: feet171; old168 was inside thick ice |

Actual room boxes, old coordinates and expected source layers are summarized in
`source-floor-rules.json`. Lich's palette/blocks, IceTowerWing's floorHeight10,
DarkTowerMain's5-block top floor and the original lair/cave density sources
were read directly; the rules are not one common offset for all heroes/bosses.

Enclosed encounters now prefer **inside the actual boss room at its floor edge**,
honestly labeled `boss-room-edge`; decorative exterior cornices are not preferred
as purported doorways. Starting from walkable cells near the true original marker
with an actual view into the room, a same-layer flood checks real two-air-block /
solid-support connectivity,256 cells per tick and4096 maximum. Enclosed candidates
must belong to that actual component. Each safe candidate also gets a real block
ray into the original room. Only original iron bars/oak fence are ignored for this
visibility test; block state and collision remain unchanged. Thus an intact arena
barrier may remain, while a solid Lich wall, palace interlayer or sealed dirt pocket
cannot stand in for visibility into the encounter.

The actual connected component's own boundary is preferred, not only a strip
inside the large decorative piece box. A read-only check of the real Lich template
found206 potential full-support air cells,100 near-center seeds/connected cells,
and **zero** of those connected cells in the initially proposed bbox-depth0–5
strip; decorative stair rings separate these areas under the strict support rule.
The final frozen candidate therefore includes the actual flood component boundary,
sorted furthest from the original marker, and reports
`connectedFloorBoundaryCells`. This template-only counterexample is not a live
acceptance. Root's earlier v3 build predates this last small boundary
addition. The accepted v4 floor server source SHA256 was
`f7ed223282c29d1849163f853c2fa7b9ea2f67c0cfa24143b1a455ec3c3da80e`; v4 was
cold deployed as guest build `a718a6fe` after all52 Gradle tasks passed. The server
source remained unchanged during the camera investigation below. The later
entity-readiness candidate changes only the consumed-spawner lifecycle, not
these accepted floor rules.

Naga additionally requires sky visibility above the exact courtyard walking layer.
Hydra/Yeti retain their original cave ceilings; sky visibility is deliberately not
required there. Their narrow candidates remain on their own exact original floor
and must see into the actual lair. When a previously visited spawner has been
consumed but its original living boss remains, the original template / mod piece
transform marker remains the fixed room reference; the boss's flying/moving Y
does not move the selected floor.

Some genuine Knight strongholds generated without a boss room. The warm test's
missing-room failure is preserved rather than treated as a successful destination.
Travel can now reject an actual candidate and ask the original locate API for
another: at most8 distinct real structures,17 distinct search centers and the
existing overall deadline. The query center offsets are only bounded search
origins, never proposed teleport coordinates. `seenLocated` prevents repeating
one failed structure; every rejected candidate releases its old tickets before
the next one is considered. `rejectedCandidates` records actual located positions,
piece class counts, reason and owned-ticket release evidence. A missing/consumed
boss or unqualified floor never causes a replacement boss or excavated room.

Every candidate requires world-border containment, loaded terrain, a full solid
support face, two actual air blocks, no supporting fluid or listed contact hazard,
and a collision-free full current player box. It does not excavate a shaft,
replace original floors, or build a landing platform. Search checks at most
384 candidates per tick. The normal ServerPlayer teleport records yaw toward the
real anchor and clears velocity/fall distance. **This server yaw does not rotate
the fusion's actual camera**; production keeps the user's native OW view as
explained below.

Real acceptance must inspect every destination: room threshold vs interior-edge
label, original spawning/AI, no suffocation/roof fall/physical prerequisite,
repeated F12/release semantics, admission cancellation, generation responsiveness,
and native hero/weapon/attack recovery. These remain actual play gates, not
consequences of a passing geometry fixture.

## Activated-room entity loading and revisit correction

The actual request17 in `research/twilight-boss-menu-20261023/final-naga/result.json`
is retained as **failed**. Its original Naga marker had become air after normal
original spawner activation. All25 FULL terrain chunks were held, the real room
scan found no remaining spawner, and the one live-boss lookup was empty. The code
then rejected that original courtyard and began locating another. Native
admission later cancelled; the old generic message does not identify which
admission condition changed. This failure must not be blamed on user input.

The failed run did not record `ServerEntityManager` load state, so it cannot
prove the exact historical pending/moved/absent entity state. Actual Yarn1.21.1
runtime sources nevertheless establish a concrete lifecycle gap:

- `FULL` at level33 maps to entity `TRACKED` and starts the original asynchronous
  entity-file read. An entity-ticking level31 ticket is not required just to
  read and query original stored entities.
- A nonnull `getWorldChunk` proves terrain availability. The separate entity
  data can still be `PENDING`; even a completed read future must pass through
  the original `ServerEntityManager.tick()` loading queue before it is indexed.
- The public exact `ServerWorld.isChunkLoaded(long)` overload delegates to
  `entityManager.isLoaded(long)`, which requires actual status `LOADED`.
  The `BlockPos` terrain overload is not this acknowledgement.
- The v4 code queried the living boss only once, before its22275-block fallback
  scan (about44 bounded ticks), and never rechecked it at the scan's end. A real
  original boss becoming indexed during those ticks could therefore still be
  rejected as absent.

The candidate server SHA256
`245fedb13a7897267cdf392268a617c74dde7633c5e4f94dedae4c2c4500f5b8`
adds `waiting-original-entities` after the original marker checks fail. It keeps
the same owned FULL33 tickets and waits for the real entity-loaded acknowledgement
of each already requested room chunk. It neither upgrades every chunk to ticking
nor expands the chunk budget. Waits are bounded to200 server ticks and the existing
overall deadline; pending entity data times out explicitly, without being called
a conquered room. The actual living original boss is queried after readiness
and again after an exhausted bounded block scan. No boss is spawned or reset,
and no accepted floor, ray, camera or safe-position rule changes.

Evidence reports `entityLoaded`, `entityChunksTotal`, `missingEntityChunks`,
`entityWaitTicks`, `entityWaitPolls`, `entityLoadBudgetTicks`,
`originalBossQueryCount` and `originalBossCount`. All normal failure/retry/reset
paths retain the existing ticket cleanup. Evidence and actual source excerpts
are in `research/twilight-boss-travel-20261023/entity-readiness/`.
The existing `TwilightBossTravelCheck` also exercises the actual vanilla
`ServerEntityManager` with deferred entity data: FULL request, pending future,
completed future before queue consumption, actual LOADED/query visibility,
unload and a fresh read of the same persisted identity on revisit. This fixture
does not create a game boss and is not an in-game revisit acceptance. At this
write the root's unified build and real revisit test are pending.

## Actual rendered-camera limitation and separate verification

The first `eight-v4/result.json` passed eight transports, but its screenshots were
captured without turning the native camera. Root's actual image review found
walls/trees in front of several destinations. That result must not be described
as eight visually accepted boss entrances.

Read-only evidence in
`research/twilight-boss-travel-20261023/eight-v4-render-bearing-audit.json` shows
all eight server destination yaws correctly point from their real landing
coordinates to the fixed original room markers. However, the actual native basis
remained facing almost north. Fresh, seqlock-consistent shared-mapping evidence
in `live26316-camera-readonly.json` identifies native26316, MC20888 and matching
host generation/frame acknowledgements. At the Snow Queen destination the actual
MC render camera eye was `(-464.5,172.62,291.5)`, yaw `179.986526` degrees, while
its server destination yaw was `-45` degrees. These are different orientations;
the actual eye position already matched the v4 destination and recorded source
floor. This orientation evidence alone does not certify the whole encounter.

This follows the existing two-process camera ownership: at the end of each
first-person `Camera.update`,
`guest/src/client/java/lab/owmcguest/mixin/HostCameraMixin.java` replaces the MC
camera quaternion and entity yaw/pitch with the fresh native `HostPoseReader`
rotation. A ServerPlayer teleport's yaw therefore is a target bearing/receipt,
not a promise that the final composed picture faces that bearing. The server's
`viewsOriginalRoom` checks a real block ray from the proposed eye toward the
original room marker, not the user's current native look direction. Its ignored
iron bars/oak fence affect this visibility classification only. A screenshot
facing the opposite direction cannot by itself disprove that marker ray.
Production deliberately preserves the user's native view; no native camera
write, angle override, replay, or extra owner was added during this diagnosis.
The candidate ray eye height is1.60; the actual standing camera is1.62. That2cm
difference cannot explain the measured yaw discrepancies of up to168 degrees.

Root reran the bounded test as
`research/twilight-boss-menu-20261023/eight-v4-camera/`. Only the test tool uses
normal relative mouse input and reads `MCFrames.latest().rotation` to close the
loop toward each target bearing. It does not accept `combat.yaw` as proof of the
rendered view. `result.json` records each `renderedCamera`, actual MC source PID
and acknowledged host frame. All eight transport and rendered-bearing checks
passed, with yaw error below0.07 degrees (required less than2 degrees), and
near-level actual pitch. This is a separate camera-directed rerun, not a
retroactive success for the original unturned screenshots. Root actually viewed
all eight new images and accepted their actual original room/arena floors.
Original encounter behavior and native attack recovery remain separate acceptance
gates; this document does not infer them from that JSON.

## Primary sources

- [Official Fabric repository](https://github.com/TeamTwilight/twilightforest-fabric)
- [Pinned release metadata](https://www.curseforge.com/minecraft/mc-mods/the-twilight-forest/files/9091040)
- [Official rule and packet callback](https://github.com/TeamTwilight/twilightforest-fabric/blob/b8363788c3e996c018af360ff038c700a88a92dd/src/main/java/twilightforest/init/TFGameRules.java)
- [Official structure registry](https://github.com/TeamTwilight/twilightforest-fabric/blob/b8363788c3e996c018af360ff038c700a88a92dd/src/main/java/twilightforest/init/TFStructures.java)
- [Official progression gates](https://github.com/TeamTwilight/twilightforest-fabric/blob/b8363788c3e996c018af360ff038c700a88a92dd/src/main/java/twilightforest/events/ProgressionEvents.java)
- [Original final-boss non-spawning implementation](https://github.com/TeamTwilight/twilightforest-fabric/blob/b8363788c3e996c018af360ff038c700a88a92dd/src/main/java/twilightforest/block/entity/spawner/FinalBossSpawnerBlockEntity.java)
- [Original trophy mechanism](https://github.com/TeamTwilight/twilightforest-fabric/blob/b8363788c3e996c018af360ff038c700a88a92dd/src/main/java/twilightforest/block/TrophyPedestalBlock.java)
- [Yarn 1.21.1 ChunkGenerator](https://maven.fabricmc.net/docs/yarn-1.21.1%2Bbuild.3/net/minecraft/world/gen/chunk/ChunkGenerator.html)
- [Yarn 1.21.1 ServerChunkManager](https://maven.fabricmc.net/docs/yarn-1.21.1%2Bbuild.3/net/minecraft/server/world/ServerChunkManager.html)
- [Yarn 1.21.1 ServerWorld entity-loaded acknowledgement](https://maven.fabricmc.net/docs/yarn-1.21.1%2Bbuild.3/net/minecraft/server/world/ServerWorld.html#isChunkLoaded(long))
- [Yarn 1.21.1 ServerEntityManager](https://maven.fabricmc.net/docs/yarn-1.21.1%2Bbuild.3/net/minecraft/server/world/ServerEntityManager.html)

The legacy official wiki Progression page timed out during this run. Third-party
wiki/search snippets were not used as the authority for current registry IDs,
gamerule spelling, final-boss implementation, or entrance geometry.
