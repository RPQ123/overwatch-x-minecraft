package lab.owmcguest;
import com.google.gson.JsonObject;
import net.fabricmc.fabric.api.client.rendering.v1.WorldRenderContext;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.*;
import net.minecraft.util.math.*;
/** Blue original-event flash and shock waves. Pure geometry, zero gameplay. */
final class PulseBurstRenderer {
    private static final RenderLayer LAYER=RenderLayer.getLightning();private static long frames,flashFrames,waveFrames;private static double maxRadius,lastAge;
    private static void quad(WorldRenderContext ctx,VertexConsumer v,Vec3d a,Vec3d b,Vec3d c,Vec3d d,int alpha){
        var camera=ctx.camera().getPos();var m=ctx.matrixStack().peek().getPositionMatrix();
        for(var p:java.util.List.of(a,b,c,d)){var at=p.subtract(camera);v.vertex(m,(float)at.x,(float)at.y,(float)at.z).color(32,165,255,alpha);}
    }
    private static void ring(WorldRenderContext ctx,VertexConsumer v,Vec3d at,Vec3d x,Vec3d y,double radius,double width,int alpha){
        for(int i=0;i<96;i++){double a=i*Math.PI/48,b=(i+1)*Math.PI/48;var p=x.multiply(Math.cos(a)).add(y.multiply(Math.sin(a)));var q=x.multiply(Math.cos(b)).add(y.multiply(Math.sin(b)));
            quad(ctx,v,at.add(p.multiply(radius-width)),at.add(p.multiply(radius+width)),at.add(q.multiply(radius+width)),at.add(q.multiply(radius-width)),alpha);
        }
    }
    private static void flash(WorldRenderContext ctx,VertexConsumer v,Vec3d at,Vec3d x,Vec3d y,int alpha){
        var camera=ctx.camera().getPos();var m=ctx.matrixStack().peek().getPositionMatrix();var centre=at.subtract(camera);
        for(int i=0;i<64;i++){double a=i*Math.PI/32,b=(i+1)*Math.PI/32;var p=centre.add(x.multiply(Math.cos(a))).add(y.multiply(Math.sin(a)));var q=centre.add(x.multiply(Math.cos(b))).add(y.multiply(Math.sin(b)));
            v.vertex(m,(float)centre.x,(float)centre.y,(float)centre.z).color(145,220,255,alpha);
            v.vertex(m,(float)p.x,(float)p.y,(float)p.z).color(25,110,255,0);
            v.vertex(m,(float)q.x,(float)q.y,(float)q.z).color(25,110,255,0);
            v.vertex(m,(float)centre.x,(float)centre.y,(float)centre.z).color(145,220,255,alpha);
        }
    }
    static void render(WorldRenderContext ctx){
        var c=MinecraftClient.getInstance();var h=HostPoseReader.INSTANCE.latest();var v=PulseBurstPresentation.cue;long now=System.currentTimeMillis();
        if(v==null||h==null||!h.inputActive()||h.flags()!=1||c.world==null||c.player==null||c.getServer()==null||ctx.matrixStack()==null
            ||!v.owner().equals(c.player.getUuid())||v.world()!=NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey())||v.source()!=h.generation()||v.model()!=NativeLocomotionController.INSTANCE.modelId()
            ||NativeLocomotionController.INSTANCE.hero()!=NativePulseRuntime.HERO||now<v.wall()||now-v.wall()>T3VisualTuning.PULSE_WAVE_SECONDS*1000||!c.world.isChunkLoaded(BlockPos.ofFloored(v.at())))return;
        double age=(now-v.wall())/1000.,t=age/T3VisualTuning.PULSE_WAVE_SECONDS,radius=T3VisualTuning.PULSE_WAVE_RADIUS*(1-Math.pow(1-t,3));
        var buffers=c.getBufferBuilders().getEntityVertexConsumers();var out=buffers.getBuffer(LAYER);var at=v.at();
        ring(ctx,out,at,new Vec3d(1,0,0),new Vec3d(0,0,1),radius,.14+.12*(1-t),(int)(210*(1-t)));
        ring(ctx,out,at,new Vec3d(1,0,0),new Vec3d(0,1,0),radius*.75,.10,(int)(140*(1-t)));
        ring(ctx,out,at,new Vec3d(0,0,1),new Vec3d(0,1,0),radius*.75,.10,(int)(140*(1-t)));waveFrames++;
        if(age<T3VisualTuning.PULSE_FLASH_SECONDS){
            double f=age/T3VisualTuning.PULSE_FLASH_SECONDS;var r=new org.joml.Vector3f(1,0,0).rotate(ctx.camera().getRotation());var u=new org.joml.Vector3f(0,1,0).rotate(ctx.camera().getRotation());
            var x=new Vec3d(r.x,r.y,r.z).multiply(3.6*(1-f));var y=new Vec3d(u.x,u.y,u.z).multiply(3.6*(1-f));
            flash(ctx,out,at,x,y,(int)(210*(1-f)));flashFrames++;
        }
        buffers.draw(LAYER);frames++;lastAge=age;maxRadius=Math.max(maxRadius,radius);
    }
    static JsonObject diagnostics(){var o=new JsonObject();o.addProperty("events",PulseBurstPresentation.emitted);o.addProperty("frames",frames);o.addProperty("flashFrames",flashFrames);o.addProperty("waveFrames",waveFrames);o.addProperty("maxRadius",maxRadius);o.addProperty("lastAge",lastAge);return o;}
}
