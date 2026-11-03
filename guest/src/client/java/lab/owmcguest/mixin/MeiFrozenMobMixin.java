package lab.owmcguest.mixin;

import lab.owmcguest.NativeMeiFreezeRuntime;
import net.minecraft.entity.mob.MobEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Ephemeral integrated-server AI gate; never persists NoAI into entity NBT. */
@Mixin(MobEntity.class)
abstract class MeiFrozenMobMixin {
    @Inject(method="tickNewAi",at=@At("HEAD"),cancellable=true)
    private void owmc$frozenAi(CallbackInfo ci){
        if(NativeMeiFreezeRuntime.frozen((MobEntity)(Object)this)){NativeMeiFreezeRuntime.blockedAi();ci.cancel();}
    }
}
