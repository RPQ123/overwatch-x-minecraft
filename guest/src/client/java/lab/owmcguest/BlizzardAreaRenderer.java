package lab.owmcguest;
import net.fabricmc.fabric.api.client.rendering.v1.WorldRenderContext;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.*;
import net.minecraft.util.math.*;
/** A thick, legible boundary at the actual10m freeze radius, not a new range. */
final class BlizzardAreaRenderer {
    static long frames;private static final RenderLayer LAYER=RenderLayer.getLightning();
    static void render(WorldRenderContext ctx,NativeBlizzardRuntime.View view){
        var c=MinecraftClient.getInstance();if(!view.landed()||c.world==null||ctx.matrixStack()==null)return;
        var buffers=c.getBufferBuilders().getEntityVertexConsumers();var vertices=buffers.getBuffer(LAYER);var camera=ctx.camera().getPos();var centre=view.at().add(0,.06,0).subtract(camera);var m=ctx.matrixStack().peek().getPositionMatrix();
        for(int i=0;i<128;i++){double a=i*Math.PI/64,b=(i+1)*Math.PI/64;double pulse=.5+.5*Math.sin(view.age()*.12+i*.05);int alpha=(int)(110+70*pulse);
            for(var p:java.util.List.of(new Vec3d(Math.cos(a)*9.84,0,Math.sin(a)*9.84),new Vec3d(Math.cos(a)*10.16,0,Math.sin(a)*10.16),new Vec3d(Math.cos(b)*10.16,0,Math.sin(b)*10.16),new Vec3d(Math.cos(b)*9.84,0,Math.sin(b)*9.84))){var at=centre.add(p);vertices.vertex(m,(float)at.x,(float)at.y,(float)at.z).color(90,200,255,alpha);}
        }
        buffers.draw(LAYER);frames++;
    }
}
