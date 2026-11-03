# Native attack damage categories

The real MC damage implementation owns creature armor, immunity, teleport and
weak-point rules. NativeDamageTargets previously reused an untagged
native_projectile source for projectile hits, melee, dash, blade and Tesla alike.
Adding IS_PROJECTILE to that shared source would incorrectly make Endermen
immune to melee/Tesla. Leaving it untagged bypassed their projectile response.
The actual mapped MC1.21.1 EndermanEntity.damage bytecode checks IS_PROJECTILE,
then attempts vanilla teleport instead of ordinary HP damage. Local private
inspection: research/_archive/2026-10/enderman-1.21.1-javap.txt; no decompiled game code published.

| Native event | MC damage type | MC category tag |
|---|---|---|
| Projectile or hitscan impact; rocket direct hit | owmcguest:native_projectile | minecraft:is_projectile |
| Quick melee, Genji dash and blade | owmcguest:native_melee | Neither projectile nor explosion |
| Explicit beam protocol mode, currently Tesla | owmcguest:native_beam | Neither projectile nor explosion |
| Rocket/armory splash | owmcguest:native_explosion | minecraft:is_explosion |

All four retain bypasses_cooldown because original native event timing owns the
attack rate. No native damage, falloff, range or cooldown numbers change. Entity
damage still runs through the exact original entity/part.damage, with canonical
parent HP credit and existing source/world/model/replay guards. Beam dispatch is
explicit; do not infer the category from nativeEntity==0, since hitscan also uses
zero. This is category compatibility, not full vanilla projectile-entity,
reflection, shield-direction or every mod's special-source parity. User-cancelled
extra projectile visuals remain disabled; no new MC bullet entities are spawned.

Rocket direct damage resolves BEFORE collecting current splash bounds/exposure.
A direct hit can make an original entity teleport or disappear; collecting first
would apply splash to its stale position. Original current parts/owner dedup,
native rings and terrain/resistance/replay rules remain active.

tools/verify/verify_native_damage_categories.py uses actual original McCree/Winston/
Pharah inputs and a temporary real Enderman (original HP/damage/teleport code,
AI paused/no gravity). Actual source tags and HP loss are observed only for this
owned fixture, bounded32 receipts. Exact tagged orphan recovery and normal
server shutdown/explicit cleanup discard it even after teleport. Profiles must
be backed up first, and the caller lands after the air test. This fixture does
not damage a mob by a synthetic event or change its immunity implementation.

Acceptance must include: real native ray hits without Enderman HP loss, ordinary
near melee damage, explicit non-projectile Tesla/release/replay, rocket teleport
outside splash without stale damage, and ordinary Pharah damage/terrain/replay
regression. Twilight Naga/Hydra source fixtures remain separate server-level
regressions, not native firing at Hydra. Current live IDs/results are in
TAKEOVER.md and MODLOG.md; older successful reports are historical evidence.
