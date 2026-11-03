package lab.owmcguest.mixin;

import lab.owmcguest.HanzoControlController;
import net.minecraft.client.MinecraftClient;
import net.minecraft.entity.LivingEntity;
import net.minecraft.util.math.Vec3d;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** MC 适配：用户要求。Full cast lock includes vertical inertia and creative flight. */
@Mixin(value=LivingEntity.class,priority=1100)
abstract class HanzoQTravelMixin {
    @Inject(method="travel",at=@At("HEAD"),cancellable=true)
    private void owmc$hanzoCastLock(Vec3d input,CallbackInfo ci){
        if((Object)this==MinecraftClient.getInstance().player&&HanzoControlController.holdMotion())ci.cancel();
    }
}
