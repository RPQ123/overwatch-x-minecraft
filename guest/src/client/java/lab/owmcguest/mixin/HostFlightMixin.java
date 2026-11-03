package lab.owmcguest.mixin;

import lab.owmcguest.FlightToggle;
import lab.owmcguest.HostPoseReader;
import lab.owmcguest.GenjiDoubleJump;
import lab.owmcguest.NativeLocomotionController;
import lab.owmcguest.NativeDeadeyeController;
import lab.owmcguest.NativeMotorController;
import net.minecraft.client.network.ClientPlayerEntity;
import net.minecraft.client.network.AbstractClientPlayerEntity;
import net.minecraft.client.world.ClientWorld;
import com.mojang.authlib.GameProfile;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(ClientPlayerEntity.class)
abstract class HostFlightMixin extends AbstractClientPlayerEntity {
    protected HostFlightMixin(ClientWorld world,GameProfile profile){super(world,profile);}
    @Unique private final FlightToggle owmc$flight=new FlightToggle();
    @Unique private final GenjiDoubleJump owmc$doubleJump=new GenjiDoubleJump();
    @Unique private boolean owmc$doubleJumpTriggered;
    @Unique private boolean owmc$enabled(){return Boolean.getBoolean("owmc.frameExport")&&Boolean.getBoolean("owmc.hostMovement");}

    @Inject(method="tickMovement",at=@At("HEAD"))
    private void owmc$disableDoubleJump(CallbackInfo ci){
        // Vanilla's second jump only toggles flight while this countdown is nonzero.
        if(owmc$enabled()) {
            abilityResyncCountdown=0;
            var p=(ClientPlayerEntity)(Object)this;
            var pose=HostPoseReader.INSTANCE.latest();
            boolean active=pose!=null&&pose.inputActive()&&p.isAlive()&&!p.hasVehicle();
            boolean pressed=active&&(pose.movementBits()&16)!=0;
            owmc$doubleJumpTriggered=owmc$doubleJump.tick(
                NativeLocomotionController.INSTANCE.isGenji(),active,p.isOnGround(),pressed);
        } else {
            owmc$doubleJump.reset();owmc$doubleJumpTriggered=false;
        }
    }
    @Inject(method="tickMovement",at=@At("RETURN"))
    private void owmc$flightKey(CallbackInfo ci){
        if(!owmc$enabled())return;
        var p=(ClientPlayerEntity)(Object)this;var pose=HostPoseReader.INSTANCE.latest();
        if(owmc$doubleJumpTriggered&&!p.getAbilities().flying&&!p.hasVehicle()) {
            var velocity=p.getVelocity();p.setVelocity(velocity.x,.42,velocity.z);p.fallDistance=0;
        }
        boolean active=pose!=null&&pose.inputActive()&&p.isAlive()&&!p.hasVehicle();
        boolean toggle=owmc$flight.poll(pose==null?0:pose.generation(),active,pose!=null&&(pose.movementBits()&64)!=0);
        if(toggle&&p.getAbilities().allowFlying&&!NativeDeadeyeController.jumpLocked()
            &&(p.getAbilities().flying||!NativeMotorController.INSTANCE.jumpLocked())){
            p.getAbilities().flying=!p.getAbilities().flying;
            if(p.getAbilities().flying&&p.isOnGround())p.setVelocity(p.getVelocity().x,.42,p.getVelocity().z);
            p.sendAbilitiesUpdate();
        }
    }
}
