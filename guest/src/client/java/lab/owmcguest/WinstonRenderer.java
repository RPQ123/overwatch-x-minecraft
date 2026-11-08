package lab.owmcguest;

import net.fabricmc.fabric.api.client.rendering.v1.WorldRenderEvents;
import net.minecraft.client.MinecraftClient;
import net.minecraft.util.math.Vec3d;
import net.minecraft.util.math.BlockPos;
import org.joml.Vector3f;

/** Owned projector01c2/barrier01c3, no substitute dome or copied game assets. */
final class WinstonRenderer {
    private static boolean registered;
    static void register(){if(registered)return;registered=true;WorldRenderEvents.AFTER_ENTITIES.register(ctx->{
        var c=MinecraftClient.getInstance();var h=HostPoseReader.INSTANCE.latest();var v=WinstonServer.INSTANCE.view;long now=System.currentTimeMillis();
        if(!Boolean.getBoolean("owmc.frameExport")||c.player==null||!c.player.isAlive()||c.world==null||c.getServer()==null||h==null||!h.inputActive()
            ||h.flags()!=1||v==null||now-v.wall()<0||now-v.wall()>200||h.generation()!=v.scope().source()||NativeLocomotionController.INSTANCE.modelId()!=v.scope().model()
            ||NativeLocomotionController.INSTANCE.hero()!=WinstonRules.HERO||!c.player.getUuid().equals(v.scope().owner())
            ||NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey())!=v.scope().world())return;
        if(v.projector()!=null){
            if(OriginalWorldRenderer.mesh(ctx,"winston-projector",v.projector().add(0,.11265,0),null,false,1,1,1,1))WinstonDiagnostics.increment("projectorRenderSubmissions");
            if(v.deployed()){
                if(barrier(ctx,v.projector()))WinstonDiagnostics.increment("barrierRenderSubmissions");
                else WinstonDiagnostics.value("barrierRenderError",OriginalMeshPack.ERRORS.getOrDefault("winston-barrier-w5","mesh submission rejected"));
            }
        }
    });}
    private static boolean barrier(net.fabricmc.fabric.api.client.rendering.v1.WorldRenderContext ctx,Vec3d at){
        var c=MinecraftClient.getInstance();var camera=ctx.camera().getPos();
        if(ctx.matrixStack()==null||at.squaredDistanceTo(camera)>256*256||!c.world.isChunkLoaded(BlockPos.ofFloored(at)))return false;
        var pack=OriginalMeshPack.get("winston-barrier-w5");if(pack==null)return false;
        var m=ctx.matrixStack();m.push();
        try{
            // The owned sphere's equator is sourceY5; keep W1's upper2520 triangles.
            m.translate(at.x-camera.x,at.y-camera.y-5,at.z-camera.z);
            pack.drawWinstonBarrier(c.getBufferBuilders().getEntityVertexConsumers(),m.peek(),
                new Vector3f((float)(camera.x-at.x),(float)(camera.y-at.y+5),(float)(camera.z-at.z)));
            return true;
        }finally{m.pop();}
    }
}
