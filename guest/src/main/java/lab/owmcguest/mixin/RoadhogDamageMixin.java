package lab.owmcguest.mixin;

import lab.owmcguest.RoadhogServer;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.damage.DamageSource;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.ModifyVariable;

/** Scoped mitigation before vanilla damage; no second damage call or heal refund. */
@Mixin(LivingEntity.class)
abstract class RoadhogDamageMixin {
    @ModifyVariable(method="damage",at=@At("HEAD"),argsOnly=true,ordinal=0)
    private float owmc$breatherDamage(float amount,DamageSource source,float originalAmount){
        return RoadhogServer.INSTANCE.reduceDamage((LivingEntity)(Object)this,source,amount);
    }
}
