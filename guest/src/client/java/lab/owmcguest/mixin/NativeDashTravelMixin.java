package lab.owmcguest.mixin;

import lab.owmcguest.NativeDashController;
import lab.owmcguest.WallClimbController;
import lab.owmcguest.NativeLocomotionController;
import lab.owmcguest.NativeFlightController;
import lab.owmcguest.NativeBlinkController;
import lab.owmcguest.NativeDeadeyeController;
import net.minecraft.client.MinecraftClient;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.MovementType;
import net.minecraft.util.math.Vec3d;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.ModifyArg;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(LivingEntity.class)
abstract class NativeDashTravelMixin {
    @ModifyArg(method="applyMovementInput",at=@At(value="INVOKE",target="Lnet/minecraft/entity/LivingEntity;move(Lnet/minecraft/entity/MovementType;Lnet/minecraft/util/math/Vec3d;)V"),index=1)
    private Vec3d owmc$baseSpeed(Vec3d movement){
        var client=MinecraftClient.getInstance();
        return (Object)this==client.player?lab.owmcguest.NativeRocketSelfImpulseClient.INSTANCE.vanillaMovement(
            client,NativeLocomotionController.INSTANCE.movement(movement)):movement;
    }
    @Inject(method="travel",at=@At("HEAD"),cancellable=true)
    private void owmc$nativeDash(Vec3d input,CallbackInfo ci){
        if(!Boolean.getBoolean("owmc.frameExport"))return;
        var client=MinecraftClient.getInstance();if((Object)this!=client.player)return;
        if(NativeDeadeyeController.movementLocked()){
            var velocity=client.player.getVelocity();
            client.player.setVelocity(0,client.player.getAbilities().flying?0:velocity.y,0);
        }
        NativeBlinkController.INSTANCE.travel(client);
        if(lab.owmcguest.MercyClient.INSTANCE.travel(client)){ci.cancel();return;}
        if(lab.owmcguest.LucioClient.INSTANCE.travel(client)){ci.cancel();return;}
        if(lab.owmcguest.ReinhardtClient.INSTANCE.travel(client)){ci.cancel();return;}
        if(lab.owmcguest.NativeGrappleController.INSTANCE.travel(client)){ci.cancel();return;}
        if(NativeFlightController.INSTANCE.travel(client)){ci.cancel();return;}
        var push=lab.owmcguest.NativeConcussiveController.INSTANCE.motion(client);
        if(push.lengthSquared()>1e-10)client.player.move(MovementType.SELF,push);
        var motion=NativeDashController.INSTANCE.motion();
        if(motion==null){if(WallClimbController.INSTANCE.travel(client))ci.cancel();return;}
        // Vanilla Entity.move sweeps the actual player bounding box against MC
        // collision shapes. Normal movement packets keep integrated-server validation.
        client.player.setVelocity(Vec3d.ZERO);client.player.move(MovementType.SELF,motion);ci.cancel();
    }
}
