package lab.owmcguest.mixin;

import lab.owmcguest.BackgroundWindowVisibility;
import net.minecraft.client.WindowSettings;
import net.minecraft.client.util.Window;
import org.objectweb.asm.Opcodes;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(Window.class)
abstract class BackgroundWindowMixin {
    @Shadow @Final private long handle;
    @Shadow private boolean fullscreen;
    @Shadow private boolean currentFullscreen;

    // Do not redirect glfwCreateWindow: Sodium already owns that redirect for
    // driver context workarounds. Hints after the reset compose with its owner.
    @Inject(method="<init>",at=@At(value="INVOKE",target="Lorg/lwjgl/glfw/GLFW;glfwDefaultWindowHints()V",shift=At.Shift.AFTER,remap=false))
    private void owmc$prepareInvisibleCreation(CallbackInfo ci) {BackgroundWindowVisibility.prepareCreation();}
    @Redirect(method="<init>",at=@At(value="FIELD",target="Lnet/minecraft/client/WindowSettings;fullscreen:Z",opcode=Opcodes.GETFIELD))
    private static boolean owmc$backgroundWindowed(WindowSettings settings) {
        return BackgroundWindowVisibility.fullscreen(settings.fullscreen);
    }
    @Inject(method="updateWindowRegion",at=@At("HEAD"))
    private void owmc$keepBackgroundWindowed(CallbackInfo ci) {
        if(BackgroundWindowVisibility.concealed()) {fullscreen=false;currentFullscreen=false;}
    }
    @Inject(method="toggleFullscreen",at=@At("HEAD"),cancellable=true)
    private void owmc$deferFullscreen(CallbackInfo ci) {
        if(BackgroundWindowVisibility.concealed())ci.cancel();
    }
    @Inject(method="<init>",at=@At("TAIL"))
    private void owmc$verifyInvisibleCreation(CallbackInfo ci) {BackgroundWindowVisibility.created(handle);}
    @Inject(method={"swapBuffers","setTitle"},at=@At("TAIL"))
    private void owmc$keepInvisibleWhileLoading(CallbackInfo ci) {BackgroundWindowVisibility.enforce(handle);}
}
