package lab.owmcguest;
import java.util.*;
import net.fabricmc.fabric.api.client.rendering.v1.*;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.*;
import net.minecraft.util.math.*;
import org.joml.Quaternionf;
/** Original beta2817 geometry; MC ice tint adapts its native refraction shader. */
final class MeiIcicleRenderer {
    private static MeiIciclePresentation.Scope scope;private static final Map<String,Long> epochs=new HashMap<>();private static long frames,stuckFrames;private static String error="";
    static void register(){WorldRenderEvents.AFTER_ENTITIES.register(MeiIcicleRenderer::render);}
    private static void render(WorldRenderContext ctx){
        var c=MinecraftClient.getInstance();var h=HostPoseReader.INSTANCE.latest();var v=MeiIciclePresentation.view;long now=System.currentTimeMillis();
        if(!Boolean.getBoolean("owmc.frameExport")||ctx.matrixStack()==null||v==null||c.player==null||!c.player.isAlive()||c.world==null||c.getServer()==null||h==null||h.flags()!=1||!h.inputActive()
            ||!v.scope().owner().equals(c.player.getUuid())||v.scope().source().hostGeneration()!=h.generation()||v.scope().source().pid()!=h.pid()||v.scope().model()!=NativeLocomotionController.INSTANCE.modelId()
            ||NativeLocomotionController.INSTANCE.hero()!=MeiIciclePresentation.HERO||v.scope().world()!=NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey())||now-v.wall()>250)return;
        try{
            if(!v.scope().equals(scope)){scope=v.scope();epochs.clear();}if(epochs.size()>2048)epochs.clear();
            var pack=OriginalMeshPack.get("mei-icicle-t6");if(pack==null)return;var m=ctx.matrixStack();var camera=ctx.camera().getPos();var buffers=c.getBufferBuilders().getEntityVertexConsumers();
            for(var f:v.flights()){
                long epoch=epochs.computeIfAbsent(f.id(),id->now);var sample=MeiIciclePresentation.sample(f,now,epoch);if(sample==null)continue;
                boolean stuck=MeiIciclePresentation.stuck(f,now,epoch);float alpha=MeiIciclePresentation.opacity(f,v.tick()+Math.clamp((now-v.wall())/50.,0,1));if(alpha<=0)continue;
                var actual=sample.at();var point=new Vec3d(actual.x(),actual.y(),actual.z());var at=stuck?point:NativeMuzzleOrigins.at(f.id(),point);if(!c.world.isChunkLoaded(BlockPos.ofFloored(at)))continue;
                var d=sample.direction();m.push();m.translate(at.x-camera.x,at.y-camera.y,at.z-camera.z);m.multiply(new Quaternionf().rotationTo(0,0,1,(float)d.x(),(float)d.y(),(float)d.z()));m.scale(1.6f,1.6f,1.6f);
                m.translate(0,-.0348367765,-.2648841143);pack.drawFaded(buffers,m.peek(),LightmapTextureManager.MAX_LIGHT_COORDINATE,.56f,.82f,1,alpha);m.pop();frames++;if(stuck)stuckFrames++;
            }epochs.keySet().retainAll(v.flights().stream().map(MeiIciclePresentation.Flight::id).toList());error="";
        }catch(Exception failure){error=failure.toString();}
    }
    static String diagnostics(){var o=new com.google.gson.JsonObject();o.addProperty("frames",frames);o.addProperty("stuckFrames",stuckFrames);o.addProperty("stuckTicks",MeiIciclePresentation.STUCK_TICKS);o.addProperty("fadeTicks",MeiIciclePresentation.FADE_TICKS);o.addProperty("traced",MeiIciclePresentation.traced);o.addProperty("contacts",MeiIciclePresentation.contacts);o.addProperty("model","original108b/2817");o.addProperty("scale",1.6);o.addProperty("nativeShaderEvaluated",false);o.addProperty("error",error);return o.toString();}
}
