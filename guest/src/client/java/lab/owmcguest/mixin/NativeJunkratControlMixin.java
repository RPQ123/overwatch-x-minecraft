package lab.owmcguest.mixin;

import lab.owmcguest.NativeJunkratController;
import net.minecraft.client.MinecraftClient;
import net.minecraft.entity.LivingEntity;
import net.minecraft.util.math.Vec3d;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** 已经认证的轮胎拥有移动输入时，MC 英雄本体留在原地。 */
@Mixin(value=LivingEntity.class,priority=1100)
abstract class NativeJunkratControlMixin {
    @Inject(method="travel",at=@At("HEAD"),cancellable=true)
    private void owmc$tireOwnsInput(Vec3d input,CallbackInfo ci){
        if(Boolean.getBoolean("owmc.frameExport")&&(Object)this==MinecraftClient.getInstance().player&&NativeJunkratController.movementLocked()){
            ((LivingEntity)(Object)this).setVelocity(Vec3d.ZERO);ci.cancel();
        }
    }
}
