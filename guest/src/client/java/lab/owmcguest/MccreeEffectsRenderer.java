package lab.owmcguest;

import net.fabricmc.fabric.api.client.rendering.v1.*;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.*;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.util.math.*;
import org.joml.Quaternionf;

/** Original flashbang mesh; lock circles/skull remain MC UI until a native glyph is authenticated. */
final class MccreeEffectsRenderer {
    static long grenadeFrames,lockFrames;
    private static void quad(VertexConsumer v,MatrixStack.Entry m,float x,float y,float xx,float yy,int r,int g,int b,float z){
        point(v,m,x,y,z,r,g,b);point(v,m,xx,y,z,r,g,b);point(v,m,xx,yy,z,r,g,b);point(v,m,x,yy,z,r,g,b);
    }
    private static void polygon(VertexConsumer v,MatrixStack.Entry m,float[][] p,int r,int g,int b,float z){
        for(int i=1;i<p.length-1;i++){
            point(v,m,p[0][0],p[0][1],z,r,g,b);point(v,m,p[i+1][0],p[i+1][1],z,r,g,b);
            point(v,m,p[i][0],p[i][1],z,r,g,b);point(v,m,p[i][0],p[i][1],z,r,g,b);
        }
    }
    private static void ring(VertexConsumer v,MatrixStack.Entry m,float radius,float thickness){
        for(int i=0;i<64;i++){
            double a=i*Math.PI/32,b=(i+1)*Math.PI/32;
            point(v,m,(float)Math.cos(a)*radius,(float)Math.sin(a)*radius,0,255,42,30);
            point(v,m,(float)Math.cos(b)*radius,(float)Math.sin(b)*radius,0,255,42,30);
            point(v,m,(float)Math.cos(b)*(radius-thickness),(float)Math.sin(b)*(radius-thickness),0,255,42,30);
            point(v,m,(float)Math.cos(a)*(radius-thickness),(float)Math.sin(a)*(radius-thickness),0,255,42,30);
        }
    }
    private static void skull(VertexConsumer v,MatrixStack.Entry m){
        float[][] head={{-.82f,.0f},{-.82f,.57f},{-.53f,.96f},{.53f,.96f},{.82f,.57f},{.82f,0},{.49f,-.3f},{-.49f,-.3f}};
        // High contrast filled silhouette, hollow eyes/nose, and separate teeth.
        polygon(v,m,head,255,42,30,.003f);quad(v,m,-.49f,-.86f,.49f,-.12f,255,42,30,.003f);
        polygon(v,m,new float[][]{{-.65f,.41f},{-.14f,.28f},{-.20f,-.02f},{-.56f,.02f}},28,3,2,.005f);
        polygon(v,m,new float[][]{{.14f,.28f},{.65f,.41f},{.56f,.02f},{.20f,-.02f}},28,3,2,.005f);
        polygon(v,m,new float[][]{{0,-.02f},{-.15f,-.32f},{.15f,-.32f}},28,3,2,.005f);
        for(float x:new float[]{-.27f,0,.27f})quad(v,m,x-.035f,-.88f,x+.035f,-.52f,28,3,2,.005f);
    }
    static void register(){WorldRenderEvents.AFTER_ENTITIES.register(MccreeEffectsRenderer::render);}
    private static void point(VertexConsumer v,MatrixStack.Entry m,float x,float y,float z,int r,int g,int b){v.vertex(m.getPositionMatrix(),x,y,z).color(r,g,b,255);}
    private static void line(VertexConsumer v,MatrixStack.Entry m,float x,float y,float xx,float yy){
        float dx=xx-x,dy=yy-y,n=(float)Math.sqrt(dx*dx+dy*dy);if(n<1e-7)return;
        v.vertex(m.getPositionMatrix(),x,y,0).color(255,55,40,255).normal(m,dx/n,dy/n,0);
        v.vertex(m.getPositionMatrix(),xx,yy,0).color(255,55,40,255).normal(m,dx/n,dy/n,0);
    }
    private static void render(WorldRenderContext ctx){
        var client=MinecraftClient.getInstance();var host=HostPoseReader.INSTANCE.latest();
        if(!Boolean.getBoolean("owmc.frameExport")||client.world==null||client.player==null||client.getServer()==null||host==null||!host.inputActive()||NativeLocomotionController.INSTANCE.hero()!=NativeDeadeyeRuntime.HERO)return;
        long world=NativeWorldIdentity.of(client.getServer(),client.world.getRegistryKey()),now=System.currentTimeMillis();
        var matrices=ctx.matrixStack();if(matrices==null)return;var camera=ctx.camera().getPos();var buffers=client.getBufferBuilders().getEntityVertexConsumers();
        var grenades=NativeCombatRuntime.flashbangView;boolean grenadeDrew=false;
        if(grenades!=null&&grenades.world()==world&&grenades.player().equals(client.player.getUuid())&&grenades.source().pid()==host.pid()&&grenades.source().hostGeneration()==host.generation())for(var shot:grenades.shots()){
            double age=(now-shot.wallMs())/1000.;if(age<0||age>.27)continue;
            var at=NativeMuzzleOrigins.at(shot.identity(),new Vec3d(shot.start().x()+shot.velocity().x()*age,shot.start().y()+shot.velocity().y()*age-10*age*age,shot.start().z()+shot.velocity().z()*age));
            if(!client.world.isChunkLoaded(BlockPos.ofFloored(at)))continue;
            var axis=new org.joml.Vector3f(0,1,0).rotate(new Quaternionf().rotationXYZ((float)(age*11),0,(float)(age*6)));
            grenadeDrew|=OriginalWorldRenderer.mesh(ctx,"mccree-flashbang",at,new Vec3d(axis.x,axis.y,axis.z),false,1,1,1,1);
        }
        if(grenadeDrew)grenadeFrames++;
        var locks=NativeDeadeyeRuntime.view;boolean lockDrew=false;
        if(locks==null||locks.world()!=world||locks.model()!=NativeLocomotionController.INSTANCE.modelId()||locks.source()!=host.generation()||!locks.owner().equals(client.player.getUuid())||now-locks.wall()>150)return;
        var lines=RenderLayer.getDebugFilledBox();
        for(var mark:locks.markers()){
            var at=mark.point();matrices.push();matrices.translate(at.x-camera.x,at.y-camera.y,at.z-camera.z);matrices.multiply(ctx.camera().getRotation());
            float unit=(float)DeadeyeMarkerLayout.unit(at.distanceTo(camera),Math.abs(ctx.projectionMatrix().m11()),client.getWindow().getFramebufferHeight());
            matrices.scale(unit,unit,unit);var v=buffers.getBuffer(lines);var m=matrices.peek();
            ring(v,m,(float)DeadeyeMarkerLayout.ring(mark.fraction()),.09f);
            if(mark.fraction()>=1)skull(v,m);
            matrices.pop();lockDrew=true;
        }
        if(lockDrew){buffers.draw(lines);lockFrames++;}
    }
}
