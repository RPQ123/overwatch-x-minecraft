package lab.owmcguest.mixin;

import lab.owmcguest.HanzoSonicReveal;
import net.minecraft.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Local-only MC silhouette from real admitted Sonic factory/collision. */
@Mixin(Entity.class)
abstract class HanzoSonicGlowMixin {
    @Inject(method="isGlowing",at=@At("RETURN"),cancellable=true)
    private void owmc$sonicOutline(CallbackInfoReturnable<Boolean> result){
        if(!result.getReturnValueZ()&&(HanzoSonicReveal.reveals((Entity)(Object)this)||lab.owmcguest.NativeInfraSightController.reveals((Entity)(Object)this)||lab.owmcguest.NativeVenomReveal.reveals((Entity)(Object)this)))result.setReturnValue(true);
    }
    @Inject(method="getTeamColorValue",at=@At("RETURN"),cancellable=true)
    private void owmc$sonicColor(CallbackInfoReturnable<Integer> result){
        if(HanzoSonicReveal.reveals((Entity)(Object)this)||lab.owmcguest.NativeInfraSightController.reveals((Entity)(Object)this))result.setReturnValue(0xff4b4b);
    }
}
