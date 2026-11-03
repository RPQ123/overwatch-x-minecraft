# Fidelity requirement: complete Minecraft world with original Overwatch presentation

**2026-10-16 evidence update:** the historical unimplemented statements below are
superseded by TAKEOVER.md and NATIVE-HERO-SWITCHING.md. Real two-process play,
native animated selection and Genji/McCree/Winston base attacks against real MC
targets have now been tested. Original attack timing/configuration remains the
source of combat. Compositor26 also owns/restores the original engine frame cap;
actual distinct MC composition has exceeded150 FPS in bounded play tests. This
does not establish all hero abilities, damage/temporary health pools, daylight coupling,
map audio removal or indefinite stutter-free play. Those remain required.

Body10 couples actual MC climb contact to the original animation presentation
state. A recorded 6-block stone-wall climb shows alternating original hands and
return to the shuriken pose; McCree/Winston did not inherit climbing, and Genji
recovered after switching back. This verifies animation and MC collision, not
the adapter's climb speed/height as original native constants. See NATIVE-CLIMB.md.

Creative hero initialization now reads the original HealthPool amounts: Genji
and McCree200, Winston400 normal+100armor. The original HUD and automatic hero
switch initialization were verified; this does not implement damage, regeneration
or temporary ultimate pools. See NATIVE-HERO-HEALTH.md. Body10 also restores the
original grounded predicate, enabling McCree's native roll animation/cooldown.
The original Wait/action state now drives MC roll displacement with its typed
speed/timeout; forward/backward/diagonal6-block movement, wall collision and hero
rebinding have actual evidence. See NATIVE-ROLL.md for scope and limitations.

**Latest route correction:** the user explicitly selected two-process passthrough with OW as visible host and MC as background guest, referencing universal-modder's GTA V example. See PASSTHROUGH.md. The earlier window choice below is historical; original hero fidelity and a complete MC world remain required. The proposed content-port route is not selected. V2/V3 continuous hero-layer replay crashed twice and is retired.

## Current user requirement (2026-10-14)

The user selected the Minecraft window and a complete Minecraft world, then clarified that the result must feel like original Overwatch. Choosing Minecraft as the visible window does not authorize reducing hero fidelity to a recreated HUD and approximate weapon mechanics.

Minecraft owns the actual saved world, chunks, blocks, creatures and world interactions. The desired presentation includes original Overwatch HUD, first-person hero hands and weapons, animation, sound, firing/reload timing and hero abilities. Building uses separate keys; mouse buttons remain hero combat controls. The old Overwatch map must not constrain the playable Minecraft world.

## Evidence and remaining gaps

- The native adapter drew real MC terrain inside the original OW beta and preserved its native hands and HUD. The user verified fixed placement and wall occlusion, and later confirmed the V7 stationary-turning fix. These results do not prove a complete MC world or native combat against MC entities.
- The V8 creative experiment supported block edits and flight, confirmed by the user. V9 used an independently generated MC superflat backend, but the user still reported intermittent disappearing geometry, stutter and floating. The OW movement/collision adapter was approximate. These problems were not proven resolved before switching direction.
- The Minecraft-host combat prototype uses a custom HUD, own item models, Minecraft sounds, approximate ammo/timing/damage and MC projectiles/explosions. It is a functional integration baseline, not original Overwatch presentation or a complete hero implementation.
- The new Minecraft-host launcher created a separate vanilla superflat save, entered it and shut down normally. The build and all six real server GameTests passed after fixing the creative raycast to use the current pose. These tests cover MC damage, collision and block edits; they do not measure Overwatch fidelity. The rebuilt client has not received user acceptance.
- Native OW attack events affecting MC entities have not been verified. Original hands/HUD/animations have not been transferred into the Minecraft renderer. No standalone original hero runtime has been integrated.

## Next feasibility gate

Evaluate whether the offline original beta can supply its native hands/weapon/HUD layers to a Minecraft foreground renderer while Minecraft owns the world. Before expanding recreated heroes, demonstrate one actual original hero visual layer over the full MC world with stable camera alignment and pose/frame synchronization. The existing native scene insertion boundary is not proof that the hands and HUD can be isolated and transferred.

Visual transfer alone is insufficient: actual attack, reload and ability state must be observed and coupled to MC collision, damage and block events. A pasted HUD, static weapon model, recolored MC projectile or a passing server test cannot satisfy that gate. If original runtime reuse fails, a faithful reimplementation remains a separate, much larger route and requires explicit reporting of its missing original behavior; it must not silently replace this requirement.

Do not claim full replica fidelity, successful original-layer compositing, complete map replacement or native hero combat without real runtime evidence.
