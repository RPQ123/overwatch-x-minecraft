package lab.owmcguest.mixin;

import lab.owmcguest.HostPoseReader;
import net.minecraft.client.render.Camera;
import net.minecraft.entity.Entity;
import net.minecraft.world.BlockView;
import org.joml.Quaternionf;
import org.joml.Vector3f;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(Camera.class)
abstract class HostCameraMixin {
    @Shadow @Final private Quaternionf rotation;
    @Shadow @Final private Vector3f horizontalPlane;
    @Shadow @Final private Vector3f verticalPlane;
    @Shadow @Final private Vector3f diagonalPlane;
    @Shadow private float yaw;
    @Shadow private float pitch;

    @Inject(method="update",at=@At("RETURN"))
    private void owmc$hostDirection(BlockView area,Entity focusedEntity,boolean thirdPerson,boolean inverseView,float delta,CallbackInfo ci) {
        HostPoseReader.applied=null;
        if(!Boolean.getBoolean("owmc.frameExport")||!Boolean.getBoolean("owmc.hostPose")||thirdPerson) return;
        var pose=HostPoseReader.INSTANCE.latest();if(pose==null) return;
        // Camera's local axes in the original MC 1.21.1 implementation:
        // forward (0,0,-1), up (0,1,0), left (-1,0,0).
        rotation.set(lab.owmcguest.HanzoControlController.cameraRotation(pose));
        horizontalPlane.set(0,0,-1).rotate(rotation);
        verticalPlane.set(0,1,0).rotate(rotation);
        diagonalPlane.set(-1,0,0).rotate(rotation);
        yaw=(float)Math.toDegrees(Math.atan2(-horizontalPlane.x,horizontalPlane.z));
        pitch=(float)Math.toDegrees(Math.atan2(-horizontalPlane.y,Math.hypot(horizontalPlane.x,horizontalPlane.z)));
        focusedEntity.setYaw(yaw);focusedEntity.setPitch(pitch);focusedEntity.prevYaw=yaw;focusedEntity.prevPitch=pitch;
        HostPoseReader.applied=pose;
    }
}
