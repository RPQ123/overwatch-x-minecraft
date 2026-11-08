package lab.owmcguest;

import java.util.*;
import net.fabricmc.fabric.api.client.rendering.v1.*;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.*;
import net.minecraft.util.math.*;

/** Private original hook, scrap and secondary meshes plus authored chain links.
 * All flight positions follow already accepted MC sweeps, never a visual hit test. */
final class RoadhogRenderer {
    private static final Map<String,Long> epochs=new HashMap<>();private static Object scope;
    static final RoadhogHookPresentation hookOrigin=new RoadhogHookPresentation();
    private static boolean registered;static String error="";
    static long shardFrames,secondaryFrames,hookFrames,chainFrames,fireFrames,trailFrames;
    private static Vec3d clipped(MinecraftClient c,Vec3d from,Vec3d to){
        var hit=c.world.raycast(new net.minecraft.world.RaycastContext(from,to,net.minecraft.world.RaycastContext.ShapeType.COLLIDER,net.minecraft.world.RaycastContext.FluidHandling.NONE,c.player));
        if(hit.getType()!=net.minecraft.util.hit.HitResult.Type.BLOCK)return to;
        var d=to.subtract(from);return d.lengthSquared()<1e-10?from:hit.getPos().subtract(d.normalize().multiply(.02));
    }
    private static void body(WorldRenderContext ctx,VertexConsumerProvider.Immediate buffers,RoadhogProjectileVisuals.Body spec,Vec3d at,Vec3d direction,double age){
        var pack=OriginalMeshPack.get(spec.name());if(pack==null)throw new IllegalStateException("original Roadhog mesh missing: "+spec.name());
        var m=ctx.matrixStack();var cam=ctx.camera().getPos();m.push();
        try{m.translate(at.x-cam.x,at.y-cam.y,at.z-cam.z);
            m.multiply(new org.joml.Quaternionf().rotationTo(0,0,1,(float)direction.x,(float)direction.y,(float)direction.z));
            m.multiply(RotationAxis.POSITIVE_Z.rotation((float)(age*7)));m.scale(spec.scale(),spec.scale(),spec.scale());m.translate(0,-spec.centerY(),0);
            pack.draw(buffers,m.peek(),LightmapTextureManager.MAX_LIGHT_COORDINATE);
        }finally{m.pop();}
    }
    static void register(){if(!registered){registered=true;WorldRenderEvents.AFTER_ENTITIES.register(RoadhogRenderer::render);}}
    private static Vec3d point(NativeShotProtocol.Vec p){return new Vec3d(p.x(),p.y(),p.z());}
    private static boolean current(MinecraftClient c,java.util.UUID owner,long world,long source,long model,long wall){
        var h=HostPoseReader.INSTANCE.latest();long now=System.currentTimeMillis();
        return c.player!=null&&c.player.isAlive()&&c.world!=null&&c.getServer()!=null&&h!=null&&h.flags()==1&&h.inputActive()
            &&owner.equals(c.player.getUuid())&&NativeLocomotionController.INSTANCE.hero()==RoadhogRules.HERO
            &&NativeLocomotionController.INSTANCE.modelId()==model&&h.generation()==source&&now-wall>=-50&&now-wall<=200
            &&NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey())==world;
    }
    private static void render(WorldRenderContext ctx){
        if(!Boolean.getBoolean("owmc.frameExport")||ctx.matrixStack()==null)return;
        var c=MinecraftClient.getInstance();if(c.world==null||c.player==null)return;
        var buffers=c.getBufferBuilders().getEntityVertexConsumers();boolean geometry=false;
        try{
            var view=RoadhogPresentation.view;
            if(view!=null){var s=view.scope();if(current(c,s.owner(),s.world(),s.source().hostGeneration(),s.model(),view.wall())){
                if(!s.equals(scope)){scope=s;epochs.clear();}
                long now=System.currentTimeMillis();
                for(var flight:view.flights()){
                    long epoch=epochs.computeIfAbsent(flight.id(),id->now);var sample=RoadhogPresentation.sample(flight,now,epoch);if(sample==null)continue;
                    var actual=point(sample.at());if(!c.world.isChunkLoaded(BlockPos.ofFloored(actual)))continue;
                    var at=flight.id().contains(":mc-split:")?actual:NativeMuzzleOrigins.firstVisibleTank(flight.id(),actual);var direction=point(sample.direction());
                    var spec=RoadhogProjectileVisuals.body(flight.resource(),flight.id());body(ctx,buffers,spec,at,direction,sample.age());
                    if(flight.resource()==RoadhogRules.SECONDARY)secondaryFrames++;else shardFrames++;
                    // Q's own native factory is a particle-only sprite; keep it
                    // over the same hero's original solid debris adaptation.
                    if(flight.resource()==RoadhogRules.WHOLE_HOG)
                        OriginalWorldRenderer.mesh(ctx,"roadhog-whole-hog",at,null,true,.11f,.11f,.11f,.75f);
                    if(PharahProjectileGlow.draw(ctx,at,direction,sample.age(),spec.fireSize()))fireFrames++;
                    var prior=point(sample.trailFrom());
                    if(!flight.id().contains(":mc-split:"))prior=NativeMuzzleOrigins.at(flight.id(),prior);
                    if(at.squaredDistanceTo(prior)>1e-6&&OriginalWorldRenderer.beam(ctx,"roadhog-scrap",prior,at,.035f,.7f))trailFrames++;
                }
                var alive=new HashSet<String>();for(var f:view.flights())alive.add(f.id());epochs.keySet().retainAll(alive);
            }}
            var hook=RoadhogServer.INSTANCE.hookView;
            if(hook!=null){var s=hook.scope();var host=HostPoseReader.INSTANCE.latest();boolean latched="PULL".equals(hook.stage());
                long source=latched&&host!=null?host.generation():s.source(),model=latched?NativeLocomotionController.INSTANCE.modelId():s.model();
                if(current(c,s.owner(),s.world(),source,model,hook.wall())&&c.world.isChunkLoaded(BlockPos.ofFloored(hook.at()))){
                var camera=ctx.camera();var q=camera.getRotation();var forward=new org.joml.Vector3f(0,0,-1).rotate(q);var right=new org.joml.Vector3f(1,0,0).rotate(q);var up=new org.joml.Vector3f(0,1,0).rotate(q);
                var basis=new MuzzlePresentation.Basis(new NativeShotProtocol.Vec(forward.x,forward.y,forward.z),new NativeShotProtocol.Vec(right.x,right.y,right.z),new NativeShotProtocol.Vec(up.x,up.y,up.z));
                double aspect=(double)c.getWindow().getFramebufferWidth()/c.getWindow().getFramebufferHeight();
                var eye=camera.getPos();var raw=hookOrigin.hand(hook.id(),new NativeShotProtocol.Vec(eye.x,eye.y,eye.z),basis,HostPoseReader.INSTANCE.latest().fov(),aspect,System.currentTimeMillis());
                var hand=clipped(c,eye,point(raw));var hvec=new NativeShotProtocol.Vec(hand.x,hand.y,hand.z);
                var at=point(hookOrigin.position(hook.id(),new NativeShotProtocol.Vec(hook.at().x,hook.at().y,hook.at().z),hvec,new NativeShotProtocol.Vec(eye.x,eye.y,eye.z),hook.stage()));
                if(!"PULL".equals(hook.stage()))at=clipped(c,hand,at);
                if(!OriginalWorldRenderer.zMesh(ctx,"roadhog-hook",at,hook.direction(),.5f))throw new IllegalStateException("original hook mesh missing");
                chain(ctx,buffers,hand,at);geometry=true;hookFrames++;chainFrames++;
            }}
            error="";
        }catch(RuntimeException failure){error=failure.toString();}
        RoadhogPresentation.shardFrames=shardFrames;RoadhogPresentation.secondaryFrames=secondaryFrames;
        RoadhogPresentation.hookFrames=hookFrames;RoadhogPresentation.chainFrames=chainFrames;RoadhogPresentation.renderError=error;
        RoadhogPresentation.fireFrames=fireFrames;RoadhogPresentation.trailFrames=trailFrames;
        if(geometry)buffers.draw(RenderLayer.getLightning());
    }
    /** Alternating closed 3D links, not an untextured straight debug line. */
    private static void chain(WorldRenderContext ctx,VertexConsumerProvider.Immediate buffers,Vec3d from,Vec3d to){
        var delta=to.subtract(from);double length=delta.length();if(length<.05)return;var direction=delta.normalize();
        var side=direction.crossProduct(new Vec3d(0,1,0));if(side.lengthSquared()<1e-8)side=direction.crossProduct(new Vec3d(1,0,0));side=side.normalize();var up=direction.crossProduct(side).normalize();
        int count=Math.min(96,Math.max(1,(int)Math.ceil(length/.19)));double spacing=length/count;
        for(int i=0;i<count;i++){
            var center=from.add(direction.multiply((i+.5)*spacing));var width=(i&1)==0?side:up;
            for(int j=0;j<8;j++){
                double a=j*Math.PI/4,b=(j+1)*Math.PI/4;
                var p=center.add(direction.multiply(Math.cos(a)*spacing*.6)).add(width.multiply(Math.sin(a)*.05));
                var q=center.add(direction.multiply(Math.cos(b)*spacing*.6)).add(width.multiply(Math.sin(b)*.05));
                tube(ctx,buffers,p,q,.011,165,169,174);
            }
        }
    }
    private static void tube(WorldRenderContext ctx,VertexConsumerProvider.Immediate buffers,Vec3d from,Vec3d to,double radius,int r,int g,int b){
        var d=to.subtract(from);if(d.lengthSquared()<1e-10)return;d=d.normalize();var side=d.crossProduct(new Vec3d(0,1,0));if(side.lengthSquared()<1e-8)side=d.crossProduct(new Vec3d(1,0,0));side=side.normalize().multiply(radius);var up=d.crossProduct(side).normalize().multiply(radius);
        var corners=List.of(side.add(up),side.negate().add(up),side.negate().subtract(up),side.subtract(up));var cam=ctx.camera().getPos();var a=from.subtract(cam);var z=to.subtract(cam);
        var v=buffers.getBuffer(RenderLayer.getLightning());var matrix=ctx.matrixStack().peek().getPositionMatrix();
        for(int i=0;i<4;i++)for(var p:List.of(a.add(corners.get(i)),z.add(corners.get(i)),z.add(corners.get((i+1)%4)),a.add(corners.get((i+1)%4))))v.vertex(matrix,(float)p.x,(float)p.y,(float)p.z).color(r,g,b,255);
        for(var p:corners)v.vertex(matrix,(float)(a.x+p.x),(float)(a.y+p.y),(float)(a.z+p.z)).color(r,g,b,255);
        for(int i=3;i>=0;i--){var p=corners.get(i);v.vertex(matrix,(float)(z.x+p.x),(float)(z.y+p.y),(float)(z.z+p.z)).color(r,g,b,255);}
    }
}
