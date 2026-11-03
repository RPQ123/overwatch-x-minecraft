package lab.owmcguest;

import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.event.lifecycle.v1.*;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.minecraft.server.network.ServerPlayerEntity;

/** Separate entry point keeps ongoing hero/voice/renderer work isolated. */
public final class SurvivalFeatures implements ModInitializer {
    @Override public void onInitialize(){
        HeroNpcEntity.register();
        if(!Boolean.getBoolean("owmc.frameExport"))return;
        ServerTickEvents.END_SERVER_TICK.register(SurvivalRuntime::tick);
        ServerTickEvents.END_SERVER_TICK.register(HeroSummonRuntime::tick);
        ServerLivingEntityEvents.AFTER_DAMAGE.register((e,s,base,actual,blocked)->{if(e instanceof ServerPlayerEntity p)SurvivalRuntime.damage(p,s,actual);});
        ServerLivingEntityEvents.AFTER_DEATH.register((e,s)->{if(e instanceof ServerPlayerEntity p)SurvivalRuntime.died(p);});
        ServerLifecycleEvents.SERVER_STOPPING.register(s->{HeroSummonRuntime.close();SurvivalLab.close();});
        ServerLifecycleEvents.SERVER_STOPPED.register(s->SurvivalRuntime.close());
    }
}
