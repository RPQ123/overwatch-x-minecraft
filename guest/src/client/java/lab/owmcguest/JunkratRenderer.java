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
            if(pack!=null){var m=ctx.matrixStack();var cam=ctx.camera().getPos();var buffers=client.getBufferBuilders().getEntityVertexConsumers();
                m.push();m.translate(bv.at().x-cam.x,bv.at().y-cam.y+(bv.landed()?.6:0),bv.at().z-cam.z);
                m.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(bv.age()*(bv.landed()?6f:20f)));
                pack.draw(buffers,m.peek(),WorldRenderer.getLightmapCoordinates(client.world,BlockPos.ofFloored(bv.at()).up()));m.pop();frames++;}}
        var wv=NativeIceWallRuntime.view;
        if(wv!=null&&wv.world()==curWorld&&System.currentTimeMillis()-wv.wall()<=250){var pack=OriginalMeshPack.get("mei-pillar");
            if(pack!=null){var m=ctx.matrixStack();var cam=ctx.camera().getPos();var buffers=client.getBufferBuilders().getEntityVertexConsumers();
                for(var at:wv.pillars()){m.push();m.translate(at.x-cam.x,at.y-cam.y,at.z-cam.z);m.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(-wv.yaw()));
                    // 0932 直接引用 2a64 冰柱，高 4.944886 m。1044 是递归资源中的人物，不能当冰柱。
                    float scale=4f/4.944886207580566f; // 原版几何等比匹配现有 4 格 MC 碰撞墙。
                    m.scale(scale,scale*Math.max(.05f,wv.rise()),scale);pack.draw(buffers,m.peek(),WorldRenderer.getLightmapCoordinates(client.world,BlockPos.ofFloored(at).up()));m.pop();frames++;}}}
        var tv=NativeTorbjornRuntime.view;
        if(tv!=null&&tv.world()==curWorld&&System.currentTimeMillis()-tv.wall()<=250){var pack=OriginalMeshPack.get("torb-turret-"+tv.level());
            if(pack!=null){var m=ctx.matrixStack();var cam=ctx.camera().getPos();var buffers=client.getBufferBuilders().getEntityVertexConsumers();
                // 原版炮台 0400000000000143，炮管朝 +Z；按索敌朝向转。
                m.push();m.translate(tv.at().x-cam.x,tv.at().y-cam.y,tv.at().z-cam.z);m.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(-tv.yaw()));
                pack.draw(buffers,m.peek(),WorldRenderer.getLightmapCoordinates(client.world,BlockPos.ofFloored(tv.at()).up()));m.pop();frames++;turretFrames++;}}
        for(var at:NativeTorbjornRuntime.packViews){if(NativeTorbjornRuntime.viewWorld!=curWorld||System.currentTimeMillis()-NativeTorbjornRuntime.viewWall>250)break;var pack=OriginalMeshPack.get("torb-armor");if(pack==null)break;
            var m=ctx.matrixStack();var cam=ctx.camera().getPos();var buffers=client.getBufferBuilders().getEntityVertexConsumers();
            m.push();m.translate(at.x-cam.x,at.y-cam.y,at.z-cam.z);pack.draw(buffers,m.peek(),WorldRenderer.getLightmapCoordinates(client.world,BlockPos.ofFloored(at).up()));m.pop();frames++;}
        var tire=NativeJunkratController.currentTireView();
        if(tire!=null&&tire.world()==curWorld&&System.currentTimeMillis()-tire.wall()<=250){
            var pack=OriginalMeshPack.get("junk-tire");if(pack!=null){var m=ctx.matrixStack();var cam=ctx.camera().getPos();
                m.push();m.translate(tire.at().x-cam.x,tire.at().y-cam.y,tire.at().z-cam.z);m.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(-tire.yaw()));
                pack.draw(client.getBufferBuilders().getEntityVertexConsumers(),m.peek(),WorldRenderer.getLightmapCoordinates(client.world,BlockPos.ofFloored(tire.at()).up()));m.pop();frames++;tireFrames++;}}
        for(var s:NativeTorbjornRuntime.scrapViews){if(s.world()!=curWorld||System.currentTimeMillis()-s.wall()>250)continue;
            var m=ctx.matrixStack();var cam=ctx.camera().getPos();m.push();m.translate(s.at().x-cam.x,s.at().y-cam.y+.12,s.at().z-cam.z);m.scale(.7f,.7f,.7f);
            client.getItemRenderer().renderItem(new net.minecraft.item.ItemStack(net.minecraft.item.Items.IRON_NUGGET),net.minecraft.client.render.model.json.ModelTransformationMode.GROUND,
                WorldRenderer.getLightmapCoordinates(client.world,BlockPos.ofFloored(s.at()).up()),net.minecraft.client.render.OverlayTexture.DEFAULT_UV,m,client.getBufferBuilders().getEntityVertexConsumers(),client.world,0);m.pop();}
        // 世界帧导出在 MC HUD 之前；这里画相机锚定文本，使资源数字进入真正导出的像素。
        if(NativeLocomotionController.INSTANCE.hero()==NativeTorbjornController.HERO){
            var m=ctx.matrixStack();var anchor=new org.joml.Vector3f(.8f,-.43f,-2).rotate(ctx.camera().getRotation());
            m.push();m.translate(anchor.x,anchor.y,anchor.z);m.multiply(ctx.camera().getRotation());m.scale(-.002f,-.002f,.002f);
            client.textRenderer.draw("废料 "+NativeTorbjornRuntime.scrapAmount+"/200  |  护甲包 50",0,0,0xffffc04d,true,m.peek().getPositionMatrix(),
                client.getBufferBuilders().getEntityVertexConsumers(),net.minecraft.client.font.TextRenderer.TextLayerType.SEE_THROUGH,0,0xf000f0);m.pop();scrapHudFrames++;
        }
        if(views.isEmpty())return;
        var buffers=client.getBufferBuilders().getEntityVertexConsumers();var m=ctx.matrixStack();var cam=ctx.camera().getPos();
        for(var v:views){
            if(v.world()!=curWorld||System.currentTimeMillis()-v.wall()>250)continue;
            var pack=OriginalMeshPack.get(switch(v.kind()){case GRENADE->"junk-grenade";case MINE->"junk-mine";case TRAP->"junk-trap";case DEATH_BOMB->"junk-death-bomb";});
            if(pack==null||!client.world.isChunkLoaded(BlockPos.ofFloored(v.at())))continue;
            m.push();m.translate(v.at().x-cam.x,v.at().y-cam.y,v.at().z-cam.z);
            if(v.kind()==NativeJunkratRuntime.Kind.GRENADE){float scale=NativeJunkratGrenadeTuning.RENDER_SCALE;m.scale(scale,scale,scale);}
            if(!v.stuck())m.multiply(RotationAxis.POSITIVE_X.rotationDegrees(v.age()*30f));
            pack.draw(buffers,m.peek(),WorldRenderer.getLightmapCoordinates(client.world,BlockPos.ofFloored(v.at()).up()));
            m.pop();frames++;
        }
    }
}
