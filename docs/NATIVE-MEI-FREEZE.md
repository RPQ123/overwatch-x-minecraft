# Mei spray contact freezing — 2026-10-24

This increment is an independently implemented MC reconstruction. The native
Beta24919 still supplies real primary shots, evaluated2.25HP damage,40m/s flight,
5s lifetime and10m range. A keypress cannot create a freeze or a damage event.
Only a successful real MC projectile damage result from that calibrated native
spray may accumulate chill. Icicles and other heroes cannot borrow the effect.

## Version policy and provenance

The freeze/decay timing follows the pinned2018 Minewatch semantic reference,
NOT an authenticated Beta2015/2016 or current retail timing:
[EntityMeiBlast.java](https://github.com/2piradians/Minewatch/blob/ebbc2324c123fcafc81fdc6749cde50ea0dc5e09/src/main/java/twopiradians/minewatch/common/entity/projectile/EntityMeiBlast.java).
Exact SHA25696c1acc2c908c9a1a78897d9606ec612203cfff5b3fd8961fe59b3ddd2da6e41,
Git blob698a83d8f6eccb3bfe00c9825cbdade2317951f5. Private source remains in the
user cache; no original code, sound or art was copied into this increment.

Thirty unique successful contacts reach freeze. Partial accumulation decays
after a ten-server-tick contact gap; frozen state lasts90server ticks(4.5s at
20TPS). Already frozen contacts still damage normally but cannot extend that
freeze. These are explicit2018 reconstruction choices, not original Beta parity.

## MC integration and limitations

- Existing swept block/entity collision, native scope and journal replay guards
  stay in charge of hits. This adds no grant, Begin, native hook or script call.
- The calibrated continuous spray preserves pre-damage velocity when the normal
  MC damage response has not teleported/removed the target. This removes the
  ordinary attacker-directed MC bullet impulse while preserving prior movement.
  Other weapons and real teleport reactions remain unchanged. This is an MC
  adaptation, not proof of original Beta knockback coefficients.
- A bounded per-mob runtime owns only its own temporary speed modifier. It does
  not remove another mod's Slowness potion or change base movement attributes.
  The2018 source's potion replacement/tail is deliberately not copied.
- Chilled mobs get a stepped speed reduction. Frozen mobs have server AI and
  horizontal travel gated temporarily, with vertical gravity retained. This
  stops horizontal knockback as an explicit MC policy. It never writes persistent
  NoAI, invulnerability or NBT flags. Entity saving cannot preserve an AI lock.
- Applied target effects use MC ticks and may finish after the caster changes
  hero/dimension. They do not authorize new old-world attacks. Death/removal/
  world entity unload/end of duration/server stop release this runtime's modifier.
- Initial support is ordinary vanilla mobs only, excluding vanilla bosses and
  vanilla freeze-immune types. Players and mod creatures/Bosses are deferred;
  Twilight shields, weaknesses and phase rules are preserved.
- Snowflakes and glass/ice-like freeze sound are MC-authored presentation, not
  claimed to be exported original OW effects. Original OW weapon/HUD/voice remain.

## Validation status

Accepted guest built=installed SHA256
8c5e7d5bcb7d8694e30d24b12ee52221d2ad03605fcff3938b5f6c1702714a56.
The six native42/26/11/16/10/1 owners did not change. Normal Stop receipts
1792808235120948400-28824 and1792808521493327000-14716 saved/exited both sessions
before cold installation; no loaded DLL/JAR overwrite or second owner.

`research/sprint-20261024/mei-freeze-acceptance.json` indexes five actual
passed/cleaned/video-exit0 runs: live2(Overworld),Nether,End,Twilight and
hero-switch2. They verified real native spray damage, partial stepped slow,
decay/speed restoration, stone-cover no damage/no freeze,30contacts/freeze,
real AI/travel inhibition without NoAI, expiry, actual movement recovery and
icicle damage200->192.5 with no borrowed chill. The frozen velocity probe moved
0m in every run; after expiry it moved1.0444-1.2004m with speed.5 restored.
Ordinary AI remained enabled. Five freezes produced445 actual AI and445travel
gate calls; target effects/owned fixtures were empty at final cleanup.

During actual freeze, selecting Soldier76 retained the already-applied MC
timer, allowed his native rifle to damage the target192.57->189.17, added no
spray chill and did not leave a freeze after expiry. Mei reentry/icicle passed.
Mid-freeze physical portal/world change, mod mobs/players/Boss freezing,
original Beta timing/shape and full Mei remain unaccepted.

Root viewed all four actual frozen-target images, the first recording contact
sheet and final original animated Mei picker over MC Overworld sky. Native
26680/creation1792808578.0166929 and MC29816/1792808561.1781073 are this acceptance's
historical identities only; re-audit next round.1920x1080, independent supervisor
kept. Actual MC20HP/clean fixture/no freeze entry at final-state.json.
54Gradle tasks and the correct HTTP contract/environment check passed.
Pure progress fixtures cover unique/duplicate contacts, exact thresholds,
partial decay, expiry, frozen no-extension, catch-up hits and rearming. They do
not prove actual native hits, collision, visible pixels or AI recovery.

Pre-change private source/config/profile/JAR backup:
`~/.universal-modder/backups/mei-freeze-20261024-101352` (actual-profile subtree).
The disposable Switch-world helper creates an active-AI200HP villager and an
ordinary velocity attempt. It cannot create a freeze, damage or native ability.
The production damage path must supply every accumulated contact.

First real `mei-freeze-live1` remains FAILED/cleaned/video0: partial chill,
decay and cover passed, but the active-AI target drifted out of the fixed native
spray after seven contacts per attempt, so30contacts/freezing were not reached.
The candidate6c874149 JAR is preserved privately. That failure cannot be relabeled
as a freeze or AI recovery pass. The subsequent candidate suppresses only the
ordinary frost damage impulse and was tested separately as live2 and successors.

First hero-switch attempt remains FAILED before switching: its replay assertion
read health/contact counters across the one-tick publication boundary (and could
still have a last travelling shot). This is NOT evidence that replay generated
another real hit. Its recorder's20s cleanup wait was too short for an early
failure in a22s recording; separate-cleanup receipt passed without changing the
failed result. The corrected harness drains real flights and waits350ms after
the last factory before replay baselining, then waits40s for recording and always
closes its handles. Hero-switch2 actually passed; no production timeout, native
permission/freshness or combat deduplication was widened to satisfy the test.

Accepted private source/config/profile/JAR snapshot:
`~/.universal-modder/backups/accepted-mei-freeze-20261024-103054`.
