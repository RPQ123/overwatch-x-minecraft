package lab.owmcguest.mixin;

import lab.owmcguest.HostPoseReader;
import net.minecraft.client.render.Camera;
import net.minecraft.client.render.GameRenderer;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(GameRenderer.class)
abstract class HostLensMixin {
    @Inject(method="getFov",at=@At("RETURN"),cancellable=true)
    private void owmc$worldLens(Camera camera,float tickDelta,boolean changingFov,CallbackInfoReturnable<Double> result) {
        var pose=HostPoseReader.applied;
        if(pose!=null&&changingFov) result.setReturnValue(Math.toDegrees(2*Math.atan(Math.tan(Math.toRadians(pose.fov())*.5)*1.18)));
    }
}
