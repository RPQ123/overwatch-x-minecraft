package lab.owmcguest.mixin;

import lab.owmcguest.HostMouseCaptureGuard;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.Mouse;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(Mouse.class)
abstract class HostMouseCaptureMixin {
    @Shadow @Final private MinecraftClient client;
    @Inject(method="lockCursor",at=@At("HEAD"),cancellable=true)
    private void owmc$foregroundCapture(CallbackInfo ci){
        if(!HostMouseCaptureGuard.permit(client))ci.cancel();
    }
}
