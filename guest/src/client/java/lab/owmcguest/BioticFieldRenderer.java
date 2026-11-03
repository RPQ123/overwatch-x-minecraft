package lab.owmcguest;
import net.fabricmc.fabric.api.client.rendering.v1.*;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.*;
import net.minecraft.util.math.*;

/** Original device enlarged 50%. The continuous small pulse/range rings are MC
 * adaptations; NativeBioticRuntime owns actual MC block light and restoration. */
final class BioticFieldRenderer {
    static long frames;
    private static void ring(VertexConsumer v,org.joml.Matrix4f m,float radius,float width,float y,int alpha){
        for(int i=0;i<64;i++)for(int corner=0;corner<4;corner++){
            double a=(i+(corner==1||corner==2?1:0))*Math.PI/32;
            float r=corner>=2?radius-width:radius;
            v.vertex(m,(float)Math.cos(a)*r,y,(float)Math.sin(a)*r).color(255,231,95,alpha);
        }
    }
    static void register(){WorldRenderEvents.AFTER_ENTITIES.register(ctx->{
        var c=MinecraftClient.getInstance();var h=HostPoseReader.INSTANCE.latest();var s=NativeBioticRuntime.view;
        long age=s==null?-1:System.currentTimeMillis()-s.wall();
        if(!Boolean.getBoolean("owmc.frameExport")||s==null||h==null||!h.inputActive()||h.flags()!=1||c.player==null||!c.player.isAlive()||c.world==null||c.getServer()==null
            ||s.source()!=h.generation()||s.model()!=NativeLocomotionController.INSTANCE.modelId()||NativeLocomotionController.INSTANCE.hero()!=NativeBioticRuntime.HERO
            ||s.world()!=NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey())||!s.owner().equals(c.player.getUuid())||age<0||age>250
            ||!c.world.isChunkLoaded(BlockPos.ofFloored(s.at()))||ctx.matrixStack()==null)return;
        boolean drew=OriginalWorldRenderer.mesh(ctx,"soldier-biotic",s.at().add(0,.174975,0),null,false,1.5f,1.5f,1.5f,1);
        if(s.landed()){
            // Native field range/emitter placement was not recovered; retain
            // the existing MC 5m footprint using actual original particle meshes.
            for(int i=0;i<24;i++){
                double a=i*Math.PI/12;var at=s.at().add(Math.cos(a)*5,.04,Math.sin(a)*5);
                drew|=OriginalWorldRenderer.mesh(ctx,"soldier-biotic-field",at,null,true,.18f,.18f,.18f,.45f);
            }
            var matrices=ctx.matrixStack();var camera=ctx.camera().getPos();
            matrices.push();matrices.translate(s.at().x-camera.x,s.at().y-camera.y,s.at().z-camera.z);
            var buffers=c.getBufferBuilders().getEntityVertexConsumers();var layer=RenderLayer.getDebugQuads();var v=buffers.getBuffer(layer);var m=matrices.peek().getPositionMatrix();
            // Small fixed inner circle plus an expanding pulse within the true
            // five-block healing footprint. POSITION_COLOR keeps it luminous;
            // real light emission is independently owned by the server lease.
            ring(v,m,.65f,.045f,.035f,150);ring(v,m,5,.035f,.025f,100);
            float progress=(100-s.remaining())%30/30f;
            ring(v,m,.65f+4.35f*progress,.05f,.04f,(int)(135*(1-progress)));
            matrices.pop();buffers.draw(layer);drew=true;
        }
        if(drew)frames++;
    });}
}

