package lab.owmcguest.mixin;

import lab.owmcguest.NativeJunkratTireRuntime;
import lab.owmcguest.NativeJunkratController;
import lab.owmcguest.NativeWorldIdentity;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.Camera;
import net.minecraft.entity.Entity;
import net.minecraft.world.BlockView;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** MC 适配相机，只改变真实 MC 世界的拍摄点；原版保留自己的英雄手部/HUD。 */
@Mixin(value=Camera.class,priority=900)
abstract class NativeJunkratCameraMixin {
    @Shadow protected abstract void setPos(double x,double y,double z);
    @Inject(method="update",at=@At("RETURN"))
    private void owmc$tireCamera(BlockView area,Entity focused,boolean thirdPerson,boolean inverse,float delta,CallbackInfo ci){
        if(!Boolean.getBoolean("owmc.frameExport"))return;
        var client=MinecraftClient.getInstance();var v=NativeJunkratController.currentTireView();
        if(v==null||client.world==null||client.getServer()==null||System.currentTimeMillis()-v.wall()>250
            ||NativeWorldIdentity.of(client.getServer(),client.world.getRegistryKey())!=v.world())return;
        setPos(v.at().x,v.at().y+.7,v.at().z);
    }
}
