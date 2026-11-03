package lab.owmcguest.mixin;

import net.minecraft.client.render.LightmapTextureManager;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.ModifyArg;

/** Full brightness applies to MC lighting only; world textures and native hands remain live. */
@Mixin(LightmapTextureManager.class)
abstract class FullBrightMixin {
    @ModifyArg(method="update",at=@At(value="INVOKE",target="Lnet/minecraft/client/texture/NativeImage;setColor(III)V"),index=2)
    private int owmc$fullBright(int original){
        return Boolean.getBoolean("owmc.frameExport")&&Boolean.getBoolean("owmc.fullBright")?0xffffffff:original;
    }
}
