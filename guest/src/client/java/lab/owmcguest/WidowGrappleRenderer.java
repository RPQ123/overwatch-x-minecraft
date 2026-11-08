package lab.owmcguest;
import net.fabricmc.fabric.api.client.rendering.v1.*;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.*;
import net.minecraft.util.math.*;
import net.minecraft.world.RaycastContext;
import lab.owmcguest.NativeShotProtocol.Vec;
import org.joml.Quaternionf;
/** One left-hand aperture for the original hook/flash and the MC rope. */
final class WidowGrappleRenderer {
    private static long token,source,epoch,frames;private static Vec3d lastOrigin;private static String error="";
    static void register(){WorldRenderEvents.AFTER_ENTITIES.register(WidowGrappleRenderer::render);}
    private static Vec vec(org.joml.Vector3f v){return new Vec(v.x,v.y,v.z);}
    private static void render(WorldRenderContext ctx){
        var c=MinecraftClient.getInstance();var h=HostPoseReader.INSTANCE.latest();var view=NativeGrappleController.view;long now=System.currentTimeMillis();
        if(!Boolean.getBoolean("owmc.frameExport")||ctx.matrixStack()==null||view==null||c.player==null||!c.player.isAlive()||c.world==null||c.getServer()==null||h==null||h.flags()!=1||!h.inputActive()
            ||!view.owner().equals(c.player.getUuid())||view.source()!=h.generation()||view.model()!=NativeLocomotionController.INSTANCE.modelId()||NativeLocomotionController.INSTANCE.hero()!=NativeGrappleController.HERO
            ||view.world()!=NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey())||now-view.wall()>250)return;
        try{
            if(token!=view.token()||source!=view.source()){token=view.token();source=view.source();epoch=now;}
            var rotation=ctx.camera().getRotation();var basis=new MuzzlePresentation.Basis(vec(new org.joml.Vector3f(0,0,-1).rotate(rotation)),vec(new org.joml.Vector3f(1,0,0).rotate(rotation)),vec(new org.joml.Vector3f(0,1,0).rotate(rotation)));
            var offset=GrappleHandOrigin.offset(basis,h.fov(),(double)c.getWindow().getFramebufferWidth()/c.getWindow().getFramebufferHeight());
            var camera=ctx.camera().getPos();var from=camera.add(offset.x(),offset.y(),offset.z());
            var obstruction=c.world.raycast(new RaycastContext(camera,from,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,c.player));
            if(obstruction.getType()!=net.minecraft.util.hit.HitResult.Type.MISS)from=camera.lerp(obstruction.getPos(),.9);
            lastOrigin=from;double phase=Math.clamp((now-epoch)/120.,0,1);var hook=from.lerp(view.anchor(),phase);var d=view.anchor().subtract(from).normalize();
            var m=ctx.matrixStack();var buffers=c.getBufferBuilders().getEntityVertexConsumers();var mesh=OriginalMeshPack.get("widow-hook");
            if(mesh!=null){m.push();m.translate(hook.x-camera.x,hook.y-camera.y,hook.z-camera.z);m.multiply(new Quaternionf().rotationTo(0,0,1,(float)d.x,(float)d.y,(float)d.z));m.translate(0,-.131877512,0);mesh.draw(buffers,m.peek(),LightmapTextureManager.MAX_LIGHT_COORDINATE);m.pop();}
            var a=from.subtract(camera);var b=hook.subtract(camera);var side=d.crossProduct(new Vec3d(0,1,0));if(side.lengthSquared()<1e-8)side=new Vec3d(1,0,0);side=side.normalize().multiply(.009);var up=d.crossProduct(side).normalize().multiply(.009);
            var v=buffers.getBuffer(RenderLayer.getLightning());var mat=m.peek().getPositionMatrix();
            for(int i=0;i<6;i++){double f=i*Math.PI/3,g=(i+1)*Math.PI/3;var p=side.multiply(Math.cos(f)).add(up.multiply(Math.sin(f)));var q=side.multiply(Math.cos(g)).add(up.multiply(Math.sin(g)));
                for(var at:new Vec3d[]{a.add(p),b.add(p),b.add(q),a.add(q)})v.vertex(mat,(float)at.x,(float)at.y,(float)at.z).color(55,45,65,240);}
            if(phase<1){var flash=OriginalMeshPack.get("widow-grapple-flash");if(flash!=null){m.push();m.translate(a.x,a.y,a.z);m.multiply(rotation);m.scale(.25f,.25f,.25f);m.translate(0,-.5,0);flash.draw(buffers,m.peek(),LightmapTextureManager.MAX_LIGHT_COORDINATE);m.pop();}}
            frames++;error="";
        }catch(Exception e){error=e.toString();}
    }
    static String diagnostics(){var o=new com.google.gson.JsonObject();o.addProperty("frames",frames);o.addProperty("origin","left-hand");o.addProperty("pixelCalibrated",false);o.addProperty("error",error);if(lastOrigin!=null)o.add("lastOrigin",new com.google.gson.Gson().toJsonTree(lastOrigin));return o.toString();}
}
