package lab.owmcguest;

import net.fabricmc.fabric.api.client.rendering.v1.*;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.*;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.util.math.*;

/** Restored 2026-10-24 cyan orb/pressure shell, enlarged 25% (MC adaptation). */
final class PharahConcussiveRenderer {
    static long frames;
    private static final float[] SPHERE=sphere();
    private static float[] sphere(){
        var points=new float[8*24*4*3];int at=0;
        for(int lat=0;lat<8;lat++)for(int lon=0;lon<24;lon++)for(int corner=0;corner<4;corner++){
            double a=-Math.PI/2+(lat+(corner>=2?1:0))*Math.PI/8;
            double b=(lon+(corner==1||corner==2?1:0))*2*Math.PI/24;
            points[at++]=(float)(Math.cos(a)*Math.cos(b));points[at++]=(float)Math.sin(a);points[at++]=(float)(Math.cos(a)*Math.sin(b));
        }
        return points;
    }
    private static void shell(WorldRenderContext ctx,VertexConsumer vertices,MatrixStack matrices,Vec3d at,float radius,int r,int g,int b,int alpha){
        var camera=ctx.camera().getPos();matrices.push();matrices.translate(at.x-camera.x,at.y-camera.y,at.z-camera.z);
        matrices.multiply(ctx.camera().getRotation());matrices.scale(radius,radius,radius);var entry=matrices.peek();
        for(int i=0;i<SPHERE.length;i+=3){
            int a=(int)(alpha*(.12+.88*(1-Math.abs(SPHERE[i+2]))));
            vertices.vertex(entry.getPositionMatrix(),SPHERE[i],SPHERE[i+1],SPHERE[i+2]).color(r,g,b,a);
        }
        matrices.pop();
    }
    static void register(){WorldRenderEvents.AFTER_ENTITIES.register(ctx->{
        var c=MinecraftClient.getInstance();var host=HostPoseReader.INSTANCE.latest();var view=NativeCombatRuntime.concussiveView;
        if(!Boolean.getBoolean("owmc.frameExport")||c.player==null||!c.player.isAlive()||c.world==null||c.getServer()==null||host==null||!host.inputActive()||host.flags()!=1||view==null
            ||NativeLocomotionController.INSTANCE.hero()!=NativeConcussiveRuntime.HERO||view.model()!=NativeLocomotionController.INSTANCE.modelId()
            ||view.world()!=NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey())||view.source().pid()!=host.pid()
            ||view.source().hostGeneration()!=host.generation()||!view.player().equals(c.player.getUuid()))return;
        var matrices=ctx.matrixStack();if(matrices==null)return;
        var buffers=c.getBufferBuilders().getEntityVertexConsumers();var layer=RenderLayer.getDebugQuads();boolean drew=false;long now=System.currentTimeMillis();
        for(var shot:view.shots()){
            double age=(now-shot.wallMs())/1000.;if(age<0||age>shot.lifetime())continue;
            var at=NativeMuzzleOrigins.at(shot.identity(),new Vec3d(shot.start().x()+shot.velocity().x()*age,shot.start().y()+shot.velocity().y()*age,shot.start().z()+shot.velocity().z()*age));
            if(!c.world.isChunkLoaded(BlockPos.ofFloored(at)))continue;
            // Exact admitted trajectory; drawing cannot manufacture a shot.
            shell(ctx,buffers.getBuffer(layer),matrices,at,.14375f,90,205,255,180);
            shell(ctx,buffers.getBuffer(layer),matrices,at,.08125f,225,245,255,220);drew=true;
        }
        var bursts=PharahConcussiveBursts.view;
        if(bursts!=null&&bursts.world()==view.world()&&bursts.model()==view.model()&&bursts.source().equals(view.source())&&bursts.player().equals(view.player()))for(var burst:bursts.bursts()){
            double age=(now-burst.wallMs())/1000.;float radius=(float)(1.25*PharahConcussiveBursts.radius(age)),opacity=(float)PharahConcussiveBursts.opacity(age);
            if(radius<=0||opacity<=0)continue;var p=burst.point();var at=new Vec3d(p.x(),p.y(),p.z());
            if(!c.world.isChunkLoaded(BlockPos.ofFloored(at)))continue;
            // Official footage shows a pale violet pressure bubble, not a
            // fireball. Its visual shell is smaller than the8m gameplay radius.
            shell(ctx,buffers.getBuffer(layer),matrices,at,radius,168,175,255,(int)(100*opacity));
            shell(ctx,buffers.getBuffer(layer),matrices,at,radius*.86f,205,220,255,(int)(28*opacity));drew=true;
        }
        if(drew){buffers.draw(layer);frames++;}
    });}
}
