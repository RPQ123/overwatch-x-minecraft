package lab.owmcguest;

import net.fabricmc.fabric.api.client.rendering.v1.*;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.WorldRenderer;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.RotationAxis;

/** 狂鼠榴弹/震荡地雷/捕兽夹：在 MC 自有的投射物位置绘制原版 24919 网格（OriginalMeshPack）。飞行中旋转为呈现用。 */
final class JunkratRenderer {
    static long frames,tireFrames,turretFrames,scrapHudFrames;
    static void register(){WorldRenderEvents.AFTER_ENTITIES.register(JunkratRenderer::render);}
    private static void render(WorldRenderContext ctx){
        if(!Boolean.getBoolean("owmc.frameExport"))return;
        var client=MinecraftClient.getInstance();var views=NativeJunkratRuntime.views;
        if(client.world==null||ctx.matrixStack()==null)return;
        var bv=NativeBlizzardRuntime.view;
        long curWorld=client.getServer()==null?0:NativeWorldIdentity.of(client.getServer(),client.world.getRegistryKey());
        if(bv!=null&&bv.world()==curWorld&&System.currentTimeMillis()-bv.wall()<=250){var pack=OriginalMeshPack.get("mei-drone");
            if(bv.landed())BlizzardAreaRenderer.render(ctx,bv);
            if(pack!=null){var m=ctx.matrixStack();var cam=ctx.camera().getPos();var buffers=client.getBufferBuilders().getEntityVertexConsumers();
                var shown=bv.landed()?bv.at():NativeMuzzleOrigins.at(bv.visualId(),bv.at());
                m.push();m.translate(shown.x-cam.x,shown.y-cam.y+(bv.landed()?.6:0),shown.z-cam.z);
                m.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(bv.age()*(bv.landed()?6f:20f)));
                m.scale(T3VisualTuning.BLIZZARD_DRONE_SCALE,T3VisualTuning.BLIZZARD_DRONE_SCALE,T3VisualTuning.BLIZZARD_DRONE_SCALE);
                pack.draw(buffers,m.peek(),WorldRenderer.getLightmapCoordinates(client.world,BlockPos.ofFloored(bv.at()).up()));m.pop();frames++;}}
        // Torbjorn meshes and tracking now share the scoped TorbjornRenderer;
        // do not submit a duplicate turret/pack from this renderer.
        var tire=NativeJunkratController.currentTireView();
        if(tire!=null&&tire.world()==curWorld&&System.currentTimeMillis()-tire.wall()<=250){
            var pack=OriginalMeshPack.get("junk-tire");if(pack!=null){var m=ctx.matrixStack();var cam=ctx.camera().getPos();
                m.push();m.translate(tire.at().x-cam.x,tire.at().y-cam.y,tire.at().z-cam.z);m.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(-tire.yaw()));
                pack.draw(client.getBufferBuilders().getEntityVertexConsumers(),m.peek(),WorldRenderer.getLightmapCoordinates(client.world,BlockPos.ofFloored(tire.at()).up()));m.pop();frames++;tireFrames++;}}
        // 世界帧导出在 MC HUD 之前；这里画相机锚定文本，使资源数字进入真正导出的像素。
        if(NativeLocomotionController.INSTANCE.hero()==NativeTorbjornController.HERO){
            var m=ctx.matrixStack();var anchor=new org.joml.Vector3f(.8f,-.43f,-2).rotate(ctx.camera().getRotation());
            m.push();m.translate(anchor.x,anchor.y,anchor.z);m.multiply(ctx.camera().getRotation());m.scale(-.002f,-.002f,.002f);
            client.textRenderer.draw(NativeTorbjornRuntime.nativeScrapAvailable?"废料 "+NativeTorbjornRuntime.scrapAmount+"/200  |  护甲包 50":"废料：等待原生资源",0,0,0xffffc04d,true,m.peek().getPositionMatrix(),
                client.getBufferBuilders().getEntityVertexConsumers(),net.minecraft.client.font.TextRenderer.TextLayerType.SEE_THROUGH,0,0xf000f0);m.pop();scrapHudFrames++;
        }
        if(views.isEmpty())return;
        var buffers=client.getBufferBuilders().getEntityVertexConsumers();var m=ctx.matrixStack();var cam=ctx.camera().getPos();
        for(var v:views){
            if(v.world()!=curWorld||System.currentTimeMillis()-v.wall()>250)continue;
            var pack=OriginalMeshPack.get(switch(v.kind()){case GRENADE->"junk-grenade";case MINE->"junk-mine";case TRAP->"junk-trap";case DEATH_BOMB->"junk-death-bomb";});
            if(pack==null||!client.world.isChunkLoaded(BlockPos.ofFloored(v.at())))continue;
            var shown=v.stuck()||v.kind()==NativeJunkratRuntime.Kind.DEATH_BOMB?v.at():NativeMuzzleOrigins.at(v.visualId(),v.at());
            m.push();m.translate(shown.x-cam.x,shown.y-cam.y,shown.z-cam.z);
            if(v.kind()==NativeJunkratRuntime.Kind.GRENADE){float scale=NativeJunkratGrenadeTuning.RENDER_SCALE;m.scale(scale,scale,scale);}
            if(!v.stuck())m.multiply(RotationAxis.POSITIVE_X.rotationDegrees(v.age()*30f));
            pack.draw(buffers,m.peek(),WorldRenderer.getLightmapCoordinates(client.world,BlockPos.ofFloored(v.at()).up()));
            m.pop();frames++;
        }
    }
}
