# Original base locomotion — beta 0.8.0.24919

Latest 2026-10-22: read [HERO-MOVEMENT.md](HERO-MOVEMENT.md) and the first
TAKEOVER section. Schema2 reads all heroes' current computed directional limits
as well as reflected base definitions; ordinary walking no longer imports the
cumulative motor displacement or the Reaper/Soldier-only inferred speed boost.
Actual completed MC tick displacement now feeds native animation. Bounded coherent
reads preserve a verified identity during a modifier transition but reject real
model/owner changes. Final code-only build has no new live acceptance; earlier
21-hero base-walking acceptance and the interrupted cursor/world suite are distinct.
The user is using this PC: code work only until this constraint is lifted.

The following sections are historical evidence, not the latest runtime route.
In particular, base-only modifier limits, friction-damped body velocity and
initial-Genji-only setup statements below have been superseded.

2026-10-20 historical: Reaper/Soldier76 used current input direction and native
base speeds with native boost retained. See [GENJI-VOICE.md](GENJI-VOICE.md).

Read-only reflection resolves the current model's loaded STUEntityDefinition,
its m_componentMap, and STUCharacterMoverComponent (CRC32 C6EC49E5). The field
names below reproduce the actual metadata hashes; field primitives are validated
as f32 through the native constraint getter. No approximate public-game table is
used and no native functions are called by the reader.

| Field | Hash | Genji | McCree / Winston |
|---|---|---:|---:|
| m_speedRunForward | A77DAFCE | 6 | 5.5 |
| m_speedRunBackward | 2AC3A673 | 5.4 | 4.95 |
| m_speedRunStrafe | 85F126DF | 6 | 5.5 |
| m_speedCrouchForward | DFC6730D | 3 | 3 |
| m_speedCrouchBackward | 28D68EA5 | 3 | 3 |
| m_speedCrouchStrafe | 39E44797 | 3 | 3 |

The Python binder verifies exact offline process hash, reflected types, map bounds,
field hashes and field constraints. The guest opens a read-only process handle and
revalidates process creation, admin/local/controller-reference/model/hero/template
identity and finite speed bounds before using the six live values. New hero
identities cannot reuse the previous binding. Startup health requires this reader
ready. Current launcher only completes combat setup for the initial Genji. Body6
and compositor23 now have real McCree/Winston visible-movement evidence, and the
launcher refreshes locomotion after their native model changes. Their MC combat
is still incomplete; see NATIVE-HERO-SWITCHING.md.

MC applies those directional speeds to the horizontal vector passed into vanilla
Entity.move, preserving vertical physics and swept block collision. Input is
normalized before applying directional speeds, preventing a forward-diagonal
boost. F6 flight, swimming, lava, vehicles and elytra retain their MC movement.
Native dash and the wall climb adapter retain their separate swept movement.
Native acceleration, air-control details, slow effects and backwards-diagonal
semantics still require original-motion comparison; this is base speed fidelity.
Native presentation body velocity still uses MC post-travel velocity, which is
friction-damped; actual feet displacement is authoritative. Aligning that velocity
for animation/interpolation remains a follow-up.

Actual Genji/MC flat-world run (native376) measured median per-tick distances:
forward .3, backward .27000000477, strafe .3, forward-diagonal .3, crouch .15 blocks.
At the actual 20Hz MC tick these are 6,5.4,6,6,3 blocks/s. Each direction had40-41
moving tick samples, grounded throughout, flyingfalse. No user-play acceptance or
native air-control equivalence is claimed. Evidence: research/native-locomotion-mc-live.json.
Win64 self-process fixture tests validate hero changes, NaN rejection and recovery;
all guest checks and build passed.

## Native hero switching research

After restoring all four adapters, original H opens animated hero selection.
Actual H -> McCree -> confirm -> H -> Winston -> confirm recreated BOTH controller
and model IDs. Generic body/weapon observers must rebind, not retain old addresses.
Native first-person weapon images: research/_archive/2026-10/mccree-native-firstperson.png and
winston-native-firstperson.png. These are native-only calibration, not fusion.

McCree hero002E...0042: weapon script0580...01D2, Volley nodes33/38, flags00408001,
original dynamic ammo path0D80...0035. Actual click kept6->6: the gate is needed.
Winston hero002E...0009, model0400...01C0: weapon script0580...00FE, Volley node10,
beam effect nodes125/127/143, flags00C08001. Its native maximum health still shows
200 from the supplied spawner, so original hero-specific health initialization
must also be fixed. Do not present either hero as completed combat support.

Full inventories and three live native speed profiles are private research files.
Next: generic verified per-hero scope for native Volley execution, real emission
semantics for hitscan/beam, dynamic body+ability rebind on original H selection,
hero-specific health and viewmodel lens checks, and MC damage tests per hero.
