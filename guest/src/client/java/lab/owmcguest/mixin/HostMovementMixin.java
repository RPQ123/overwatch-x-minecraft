package lab.owmcguest.mixin;

import lab.owmcguest.HostPoseReader;
import lab.owmcguest.NativeDeadeyeController;
import lab.owmcguest.NativeMotorController;
import net.minecraft.client.input.Input;
import net.minecraft.client.input.KeyboardInput;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Intent only: vanilla MC owns velocity, gravity, collision and eye height. */
@Mixin(KeyboardInput.class)
abstract class HostMovementMixin extends Input {
    @Inject(method="tick",at=@At("RETURN"))
    private void owmc$movement(boolean slowDown,float factor,CallbackInfo ci) {
        if(!Boolean.getBoolean("owmc.frameExport")||!Boolean.getBoolean("owmc.hostMovement")) return;
        var pose=HostPoseReader.INSTANCE.latest();
        int bits=pose!=null&&pose.inputActive()?pose.movementBits():0;
        bits=lab.owmcguest.HanzoControlController.movementBits(net.minecraft.client.MinecraftClient.getInstance(),pose,bits);
        if(NativeDeadeyeController.movementLocked()||lab.owmcguest.RoadhogClient.breatherLocked())bits&=~0x7f;
        pressingForward=(bits&1)!=0;pressingBack=(bits&2)!=0;
        pressingLeft=(bits&4)!=0;pressingRight=(bits&8)!=0;
        jumping=(bits&16)!=0&&!NativeDeadeyeController.jumpLocked()&&!NativeMotorController.INSTANCE.jumpLocked();sneaking=(bits&32)!=0;
        movementForward=(pressingForward?1:0)-(pressingBack?1:0);
        movementSideways=(pressingLeft?1:0)-(pressingRight?1:0);
        if(slowDown) {movementForward*=factor;movementSideways*=factor;}
    }
}
