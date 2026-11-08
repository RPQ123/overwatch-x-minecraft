package lab.owmcguest;

import net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.WorldRenderContext;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.WorldRenderer;
import net.minecraft.client.render.entity.CaveSpiderEntityRenderer;
import net.minecraft.client.render.entity.EntityRendererFactory;
import net.minecraft.util.math.BlockPos;

/** Vanilla cave-spider model/texture; LivingEntity's synced GENERIC_SCALE applies the 30% size.
 * Before landing, one render-only entity depicts the MC-owned venom ballistic position. */
public final class WidowSpiderRenderer extends CaveSpiderEntityRenderer {
    private static WidowSpiderEntity airborne;

    public WidowSpiderRenderer(EntityRendererFactory.Context context){super(context);}

    static void register(){EntityRendererRegistry.register(WidowSpiderEntity.TYPE,WidowSpiderRenderer::new);}

    static void renderFlying(WorldRenderContext context,NativeVenomRuntime.View view){
        var client=MinecraftClient.getInstance();
        if(client.world==null||context.matrixStack()==null)return;
        if(airborne==null||airborne.getWorld()!=client.world)
            airborne=new WidowSpiderEntity(WidowSpiderEntity.TYPE,client.world);
        var at=view.stuck()?view.at():NativeMuzzleOrigins.at(view.visualId(),view.at());var camera=context.camera().getPos();
        airborne.setPosition(at);airborne.setYaw(view.yaw());airborne.bodyYaw=view.yaw();
        airborne.prevBodyYaw=view.yaw();airborne.age=view.age();
        var buffers=client.getBufferBuilders().getEntityVertexConsumers();
        client.getEntityRenderDispatcher().render(airborne,at.x-camera.x,at.y-camera.y,
            at.z-camera.z,view.yaw(),0,context.matrixStack(),buffers,
            WorldRenderer.getLightmapCoordinates(client.world,BlockPos.ofFloored(at)));
        buffers.draw();
    }
}
