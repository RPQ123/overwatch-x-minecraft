package lab.owmcguest;
import java.util.*;
import net.fabricmc.fabric.api.client.rendering.v1.*;
import net.minecraft.block.Blocks;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.*;
import net.minecraft.util.math.*;

/** One expanded terrain plan drives five original meshes, preview and collision. */
final class IceWallRenderer {
    private static long frames,previewFrames;private static String error="";
    static void register(){WorldRenderEvents.AFTER_ENTITIES.register(IceWallRenderer::render);}
    private static boolean current(MinecraftClient c,NativeIceWallRuntime.Scope s,long wall){
        var h=HostPoseReader.INSTANCE.latest();var l=NativeLocomotionController.INSTANCE;long age=System.currentTimeMillis()-wall;
        return c.player!=null&&c.player.isAlive()&&c.world!=null&&c.getServer()!=null&&c.player.getUuid().equals(s.owner())
            &&h!=null&&h.flags()==1&&h.generation()==s.source()&&l.hero()==NativeMeiFreezeRuntime.HERO&&l.modelId()==s.model()
            &&age>=-50&&age<=250&&NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey())==s.world();
    }
    private static void render(WorldRenderContext ctx){
        if(!Boolean.getBoolean("owmc.frameExport")||ctx.matrixStack()==null)return;var c=MinecraftClient.getInstance();
        try{
            var v=NativeIceWallRuntime.view;
            if(v!=null&&current(c,v.scope(),v.wall())){
                var matrices=ctx.matrixStack();var cam=ctx.camera().getPos();var buffers=c.getBufferBuilders().getEntityVertexConsumers();
                for(var support:v.supports()){
                    var at=support.at();matrices.push();matrices.translate(at.getX()-cam.x,at.getY()-cam.y,at.getZ()-cam.z);
                    c.getBlockRenderManager().renderBlockAsEntity(support.state(),matrices,buffers,WorldRenderer.getLightmapCoordinates(c.world,at),OverlayTexture.DEFAULT_UV);matrices.pop();
                }
                pillars(ctx,c,v.plan(),v.pillars(),false,true);frames++;
            }
            var p=NativeIceWallRuntime.previewView;
            if(p!=null&&p.plan()!=null&&current(c,p.scope(),p.wall())){
                pillars(ctx,c,p.plan(),p.plan().pillars(1),true,p.valid());previewFrames++;
            }error="";
        }catch(Exception failure){error=failure.toString();}
    }
    private static void pillars(WorldRenderContext ctx,MinecraftClient c,IceWallGeometry.Plan plan,List<IceWallGeometry.Pillar> pillars,boolean ghost,boolean valid){
        var pack=OriginalMeshPack.get("mei-pillar");if(pack==null)return;var m=ctx.matrixStack();var cam=ctx.camera().getPos();var buffers=c.getBufferBuilders().getEntityVertexConsumers();
        for(var p:pillars){m.push();m.translate(p.x()-cam.x,p.y()-cam.y,p.z()-cam.z);m.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(plan.yaw()));
            m.scale((float)(IceWallGeometry.PILLAR_WIDTH/IceWallGeometry.SOURCE_X),(float)(p.height()/IceWallGeometry.SOURCE_Y),(float)(IceWallGeometry.THICKNESS/IceWallGeometry.SOURCE_Z));
            pack.drawWallSlice(buffers,m.peek(),WorldRenderer.getLightmapCoordinates(c.world,BlockPos.ofFloored(p.x(),p.y()+1,p.z())),(float)plan.sourceMinX(p),(float)plan.sourceMaxX(p),ghost,valid);m.pop();}
    }
    static String diagnostics(){var o=new com.google.gson.JsonObject();o.addProperty("frames",frames);o.addProperty("previewFrames",previewFrames);o.addProperty("model","original0932/2a64");o.addProperty("width",IceWallGeometry.WIDTH);o.addProperty("thickness",IceWallGeometry.THICKNESS);o.addProperty("minecraftIceCore",false);o.addProperty("error",error);return o.toString();}
}
