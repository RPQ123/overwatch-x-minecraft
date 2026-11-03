# Overwatch beta folder reconnaissance

Date: 2026-10-17

## Target and launch chain

The supplied client is `overwatch-2015/Overwatch Beta 0.8.0.24919`, build
`0.8.0.0.24919`, branch `eu`, product id `prometheus`. `GameClientApp.exe` is a
26.84 MB native x64 Windows GUI executable with a valid Blizzard Entertainment
signature. It is not a managed .NET game client. The scanner's .NET result comes
from the separate `patcher.runtimeconfig.json`, not from the game executable.

`GameClientApp.patched.exe` is an independent same-size copy. Its SHA-256 is
`f73a747b7d63a07402958b2b2c4587125a46ef8e181281669da009d352308e9f`; the
original is `21b761a5b48076728318290ee9d0be6ad1ee36af59e4b7aaefe7b7ac5bf2a68a`.
The patched copy has a hash mismatch by design. The patcher applies ten fixed
byte spans from `research/prometheus/patcher-Program.cs`; the injected loader
resolves and loads `inject.dll`.

The supplied `prometheus-release/` contains the .NET 8 patcher, native
`prometheus.dll`, its MinHook dependency, and a 20 MB `prometheus.pdb`. The PDB
contains matching native symbols for the research layer, including
`state_replicator`, `serialization`, `entity_admin`, `player_spawner`, `statescript`,
`stu_resources`, `stu_explorer`, `management_window`, `viewmodel_write_blocker`
and `window_manager`. The launcher uses the patched copy with its own working
directory; relative CASC/hash paths in the client make the working directory
part of the runtime contract.

## Resource and runtime layers

The client uses Blizzard's CASC layout rather than loose PAK files. Under
`data/casc/` the beta has:

- `data/`: four large `data.000`...`data.003` containers, about 3.58 GiB total,
  plus 17 numeric cache indexes and `shmem`;
- `indices/`: 281 hashed `.index` files, about 80 MiB;
- `config/`: a handful of hashed configuration objects;
- `patch/`: the patch store.

The `offline-lab` copy has matching CASC container hashes, so the lab does not
fork the world content. Only the executable/loader layer is intentionally
separate. The game folder also includes native support libraries for FreeType,
libpng/zlib/brotli/bzip2, RTP/Vivox voice, and error reporting.

Strings and imports identify the following native subsystems: D3D11/DXGI-style
rendering, Audiokinetic Wwise with Vorbis decoding, Blizzard CASC and STU
resources, Statescript graphs, protobuf descriptors, network event systems,
telemetry, and voice. These are useful seams for observation, but they are not
public mod APIs.

## What is interesting

The PDB-backed research layer is the unusual part of this folder. It exposes
symbol names and type information for resource browsing, entity administration,
hero spawning, Statescript inspection, and a WebSocket/state replication path.
The existing local notes recorded 12,762 loaded STU resources and 19 map headers;
that is enough to build a searchable catalogue without extracting the 3.6 GiB
archive wholesale. The same layer names Wwise objects and Vorbis decoders, which
explains why map ambience can be isolated separately from hero presentation.

The executable itself is heavily packed into native sections and dynamically
loads most dependencies. That keeps normal import tables small, but it also
means fixed offsets and byte patches are build-specific. The current research
route is therefore a process-bound, hash-guarded adapter rather than a normal
plugin loader.

## Practical iteration backlog

1. **CASC catalogue first.** Build a read-only index browser that resolves names,
   types, map headers, sound events and model/texture references to CASC IDs.
   Extract only a single verified asset at a time into an external research
   directory. Do not rewrite the archive.
2. **PDB-driven binding.** Resolve the patcher's CodeView GUID/age and the
   provided PDB before using a symbol. Generate a build report for each native
   address and keep a small signature fallback only where the PDB cannot name a
   field. This removes the largest source of breakage when a module is rebuilt.
3. **Lifecycle and hero transitions.** Keep the current session identity guard,
   but add a transition trace containing PID, world generation, hero/model IDs,
   body freshness and controller resets. Use it to test every hero across
   Overworld, Nether and End before adding new abilities.
4. **Native event bridge.** Convert observed Statescript/weapon events into a
   versioned event stream with sequence numbers and timestamps. Minecraft should
   own collision and damage; Overwatch should supply native hands, HUD and
   animation. This is the clean seam for fixing ammo, hit registration and
   cross-dimension resets.
5. **Renderer budget.** Keep D3D11 capture/composition on a bounded frame path,
   expose GPU timing and dropped-frame counters, and make masks/depth resources
   generation-scoped. This is more valuable than raising the nominal FPS cap
   when the guest image or native foreground stalls.
6. **Audio routing.** Observe Wwise event names and map audio banks read-only,
   then add a controlled mute/duck layer for map ambience. The five extracted
   Minecraft tracks can be selected by the guest world without replacing the
   original client archive.
7. **Deterministic regression scenes.** Maintain one saved MC scene with a wall,
   villager, End crystal and portal, and replay the same movement, hero switch,
   shot and dimension sequence. Record native reports, MC combat counters and
   composed frames together.
8. **Packaging.** Continue launching only the isolated, SHA-guarded research
   copy. Keep CASC archives, saves, extracted assets, PDBs and toolchains out of
   commits; commit only adapters, tests and research notes.

## Current conclusion

The folder is a native, data-driven client with a strong research surface but no
stable community loader. The best next investment is metadata and lifecycle
stability: a CASC/PDB catalogue plus deterministic transition traces. Once those
are solid, new heroes, audio choices, map selection and combat events can be
added without widening the fragile byte-patch surface.
