package lab.owmcguest;

import java.util.HashSet;
import net.fabricmc.fabric.api.client.rendering.v1.WorldRenderEvents;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.RenderLayer;
import net.minecraft.client.render.VertexConsumer;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.RaycastContext;

/** Restored 2026-10-24 silver shell and warm tracer; MC geometry, admitted shots only. */
final class BastionTankRenderer {
    static long glowFrames;
    static String glowError="waiting for tank shell draw";
    private static final HashSet<Long> seen=new HashSet<>();
    private record GlowFrame(Vec3d at,Vec3d direction,double age){}
    private static Object source;private static long world,model;
    private static Vec3d vec(NativeShotProtocol.Vec v){return new Vec3d(v.x(),v.y(),v.z());}
    private static void quad(VertexConsumer v,org.joml.Matrix4f m,Vec3d a,Vec3d b,Vec3d c,Vec3d d,int r,int g,int blue,int alpha){
        for(var p:new Vec3d[]{a,b,c,d})v.vertex(m,(float)p.x,(float)p.y,(float)p.z).color(r,g,blue,alpha);
    }
    private static void ribbon(VertexConsumer v,org.joml.Matrix4f m,Vec3d a,Vec3d b,Vec3d side,double width,int r,int g,int blue,int alpha){
        var s=side.multiply(width);quad(v,m,a.subtract(s),a.add(s),b.add(s),b.subtract(s),r,g,blue,alpha);
    }
    static void register(){WorldRenderEvents.AFTER_ENTITIES.register(ctx->{
        var c=MinecraftClient.getInstance();var h=HostPoseReader.INSTANCE.latest();var s=NativeCombatRuntime.rocketView;
        if(!Boolean.getBoolean("owmc.frameExport")||s==null||h==null||c.player==null||!c.player.isAlive()||c.world==null||c.getServer()==null||ctx.matrixStack()==null
            ||!h.inputActive()||h.flags()!=1||NativeLocomotionController.INSTANCE.hero()!=0x02e0000000000015L||s.model()!=NativeLocomotionController.INSTANCE.modelId()
            ||s.world()!=NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey())||s.source().pid()!=h.pid()||s.source().hostGeneration()!=h.generation()||!s.player().equals(c.player.getUuid())){
            return;
        }
        if(!s.source().equals(source)||s.world()!=world||s.model()!=model){source=s.source();world=s.world();model=s.model();seen.clear();}
        var camera=ctx.camera().getPos();var m=ctx.matrixStack().peek().getPositionMatrix();var buffers=c.getBufferBuilders().getEntityVertexConsumers();
        var layer=RenderLayer.getDebugQuads();var v=buffers.getBuffer(layer);var glows=new java.util.ArrayList<GlowFrame>();boolean drew=false,glowing=false;long now=System.currentTimeMillis();
        for(var shot:s.shots()){
            if(!shot.tankShell())continue;double age=(now-shot.wallMs())/1000.,speed=Math.sqrt(shot.velocity().lengthSquared());
            if(age<0||age>shot.lifetime()||speed<1||age*speed>shot.range())continue;
            var at=vec(BastionTankPresentation.center(shot,age));if(!c.world.isChunkLoaded(BlockPos.ofFloored(at)))continue;
            // A renderer may run between two real server collision ticks. Hide
            // its extrapolation at a nearer block; it cannot cross a wall or
            // create its own impact/damage/sound while waiting for the server.
            var wall=c.world.raycast(new RaycastContext(vec(shot.start()),at,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,c.player));
            if(wall.getType()!=HitResult.Type.MISS)continue;
            var direction=vec(shot.velocity()).normalize();var axis=Math.abs(direction.y)<.9?new Vec3d(0,1,0):new Vec3d(1,0,0);
            var right=direction.crossProduct(axis).normalize();var up=right.crossProduct(direction).normalize();
            var center=at.subtract(camera);var nose=center.add(direction.multiply(BastionTankPresentation.LENGTH*.5));var tail=center.subtract(direction.multiply(BastionTankPresentation.LENGTH*.5));
            // Eight sides make a solid small shell; all geometry is cosmetic.
            for(int i=0;i<8;i++){
                double a=i*Math.PI/4,b=(i+1)*Math.PI/4;var radialA=right.multiply(Math.cos(a)*BastionTankPresentation.RADIUS).add(up.multiply(Math.sin(a)*BastionTankPresentation.RADIUS));
                var radialB=right.multiply(Math.cos(b)*BastionTankPresentation.RADIUS).add(up.multiply(Math.sin(b)*BastionTankPresentation.RADIUS));
                int shade=180+(int)(45*Math.max(0,Math.sin(a)));
                quad(v,m,tail.add(radialA),tail.add(radialB),nose.add(radialB.multiply(.55)),nose.add(radialA.multiply(.55)),shade,shade+5,shade+8,255);
                quad(v,m,nose,nose.add(radialA.multiply(.55)),nose.add(radialB.multiply(.55)),nose,255,195,70,255);
            }
            // Short crossed orange streak, centered on the same native ray.
            var prior=vec(BastionTankPresentation.center(shot,Math.max(0,age-BastionTankPresentation.TRAIL_SECONDS))).subtract(camera);
            ribbon(v,m,tail,prior,right,.047,255,140,35,175);ribbon(v,m,tail,prior,up,.047,255,140,35,175);
            ribbon(v,m,tail,prior,right,.013,255,245,180,240);drew=true;
            // Pharah-style emitting core, sharp star and animated rear flame.
            // This stays behind the same admitted-flight and nearer-wall gates.
            glows.add(new GlowFrame(at,direction,age));
            if(seen.size()>4096)seen.clear();if(seen.add(shot.id()))NativeCombatRuntime.tankShellModelsShown++;
        }
        if(drew){buffers.draw(layer);NativeCombatRuntime.tankShellRenderFrames++;}
        // Finish every solid-shell vertex before switching additive buffers.
        // Immediate may otherwise close the body builder between two shells.
        for(var glow:glows){glowing|=PharahProjectileGlow.draw(ctx,glow.at(),glow.direction(),glow.age());glowError=PharahProjectileGlow.error;}
        if(glowing)glowFrames++;
    });}
}
