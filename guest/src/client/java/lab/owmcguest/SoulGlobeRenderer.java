package lab.owmcguest;
import net.fabricmc.fabric.api.client.rendering.v1.*;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.*;
import net.minecraft.util.math.BlockPos;

/** A small MC-authored luminous soul crystal; not an exported original mesh. */
final class SoulGlobeRenderer {
    private static void crystal(VertexConsumer v,org.joml.Matrix4f m,float radius,int alpha){
        for(int up:new int[]{-1,1})for(int i=0;i<4;i++){
            float a=(float)(i*Math.PI/2),b=(float)((i+1)*Math.PI/2);
            v.vertex(m,0,up*radius*1.25f,0).color(165,250,255,alpha);
            v.vertex(m,(float)Math.cos(a)*radius,0,(float)Math.sin(a)*radius).color(35,150+i*15,200,alpha);
            v.vertex(m,(float)Math.cos(b)*radius,0,(float)Math.sin(b)*radius).color(45,180,220,alpha);
            v.vertex(m,0,up*radius*1.25f,0).color(165,250,255,alpha);
        }
    }
    static void register(){WorldRenderEvents.AFTER_ENTITIES.register(ctx->{
        var c=MinecraftClient.getInstance();var h=HostPoseReader.INSTANCE.latest();var s=NativeSoulRuntime.view;
        if(s==null||s.orbs().isEmpty()||h==null||c.player==null||c.world==null||c.getServer()==null||ctx.matrixStack()==null||System.currentTimeMillis()-s.wall()>250
            ||s.scope().source()!=h.generation()||s.scope().model()!=NativeLocomotionController.INSTANCE.modelId()||NativeLocomotionController.INSTANCE.hero()!=NativeReaperRuntime.HERO
            ||s.scope().world()!=NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey())||!s.scope().owner().equals(c.player.getUuid()))return;
        var matrices=ctx.matrixStack();var camera=ctx.camera().getPos();var buffers=c.getBufferBuilders().getEntityVertexConsumers();var layer=RenderLayer.getDebugQuads();
        for(var orb:s.orbs()){
            var at=orb.position();if(at.squaredDistanceTo(camera)>64*64||!c.world.isChunkLoaded(BlockPos.ofFloored(at)))continue;
            double t=(System.currentTimeMillis()-orb.born())/1000.;matrices.push();matrices.translate(at.x-camera.x,at.y-camera.y+Math.sin(t*3)*.04,at.z-camera.z);matrices.multiply(new org.joml.Quaternionf().rotateY((float)t));
            var v=buffers.getBuffer(layer);var m=matrices.peek().getPositionMatrix();crystal(v,m,.18f,210);crystal(v,m,.08f,255);matrices.pop();
        }
        buffers.draw(layer);
    });}
}
