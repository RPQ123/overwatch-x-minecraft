package lab.owmcguest.mixin;
import lab.owmcguest.WorldFrameExporter;
import net.minecraft.client.render.GameRenderer;
import net.minecraft.client.render.RenderTickCounter;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
@Mixin(GameRenderer.class)
abstract class FinalWorldCaptureMixin {
    @Shadow private boolean renderHand;
    @Unique private boolean owmc$savedHand;
    @Inject(method="renderWorld",at=@At("HEAD"))
    private void owmc$hideSourceHand(RenderTickCounter tick,CallbackInfo ci){
        owmc$savedHand=renderHand;
        if(Boolean.getBoolean("owmc.frameExport"))renderHand=false;
    }
    @Inject(method="renderWorld",at=@At("RETURN"))
    private void owmc$finalWorld(RenderTickCounter tick,CallbackInfo ci){renderHand=owmc$savedHand;}
    // Actual1.21.1 GameRenderer.render composites vanilla entity outlines AFTER
    // renderWorld returns. Exporting at that return silently discarded Sonic
    // silhouettes although the server and vanilla outline pass were active.
    // Stay before GUI/postprocessing, with no second render or fake overlay.
    @Inject(method="render",at=@At(value="INVOKE",target="Lnet/minecraft/client/render/WorldRenderer;drawEntityOutlinesFramebuffer()V",shift=At.Shift.AFTER))
    private void owmc$outlinedWorld(RenderTickCounter tick,boolean tickGame,CallbackInfo ci){WorldFrameExporter.captureFinalWorld();}
}
