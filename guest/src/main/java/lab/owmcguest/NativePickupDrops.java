package lab.owmcguest;

import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.minecraft.server.network.ServerPlayerEntity;

/** The fatal damage source, not a nearby death/assist, owns a passive drop.
 * Hero NPCs are LivingEntities and follow the identical actual-death path. */
final class NativePickupDrops {
    private static boolean initialized;
    static void init(){
        if(initialized)return;initialized=true;
        ServerLivingEntityEvents.AFTER_DEATH.register((victim,source)->{
            if(source.getAttacker() instanceof ServerPlayerEntity killer&&killer!=victim){
                NativeSoulRuntime.killed(killer,victim);NativeTorbjornRuntime.killed(killer,victim);
            }
        });
    }
}
