package lab.owmcguest.mixin;

import lab.owmcguest.NativeMeiFreezeRuntime;
import net.minecraft.entity.LivingEntity;
import net.minecraft.util.math.Vec3d;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.ModifyVariable;

@Mixin(LivingEntity.class)
abstract class MeiFrozenTravelMixin {
    @ModifyVariable(method="travel",at=@At("HEAD"),argsOnly=true)
    private Vec3d owmc$frozenMovement(Vec3d input){
        var entity=(LivingEntity)(Object)this;
        if(!NativeMeiFreezeRuntime.frozen(entity))return input;
        // Preserve gravity/falling; stop horizontal motion without a saved AI flag.
        var velocity=entity.getVelocity();entity.setVelocity(0,velocity.y,0);entity.setJumping(false);
        NativeMeiFreezeRuntime.blockedTravel();return Vec3d.ZERO;
    }
}
