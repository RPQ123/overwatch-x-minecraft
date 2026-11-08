package lab.owmcguest;
import net.fabricmc.fabric.api.client.rendering.v1.*;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.*;
import net.minecraft.util.math.BlockPos;

/** Victim-specific item heads or actual entity-head geometry/skin. */
final class SoulGlobeRenderer {
    static long frames,models,haloFrames;
    private static final java.util.Map<java.util.UUID,net.minecraft.item.ItemStack> heads=new java.util.HashMap<>();
    private static NativeSoulRuntime.Scope headScope;
    private static net.minecraft.item.ItemStack head(NativeSoulRuntime.Orb orb){
        return heads.computeIfAbsent(orb.victim(),id->{
            var item=switch(orb.head().kind()){
                case WITHER_SKELETON->net.minecraft.item.Items.WITHER_SKELETON_SKULL;
                case ZOMBIE->net.minecraft.item.Items.ZOMBIE_HEAD;
                case CREEPER->net.minecraft.item.Items.CREEPER_HEAD;
                case PIGLIN->net.minecraft.item.Items.PIGLIN_HEAD;
                case DRAGON->net.minecraft.item.Items.DRAGON_HEAD;
                case PLAYER->net.minecraft.item.Items.PLAYER_HEAD;
                default->net.minecraft.item.Items.SKELETON_SKULL;
            };
            var stack=new net.minecraft.item.ItemStack(item);
            if(orb.head().profile()!=null)stack.set(net.minecraft.component.DataComponentTypes.PROFILE,orb.head().profile());
            return stack;
        });
    }
    private static void halo(WorldRenderContext ctx,net.minecraft.util.math.Vec3d at){
        var c=MinecraftClient.getInstance();var buffers=c.getBufferBuilders().getEntityVertexConsumers();var layer=RenderLayer.getLightning();var v=buffers.getBuffer(layer);
        var m=ctx.matrixStack().peek().getPositionMatrix();var center=at.subtract(ctx.camera().getPos());
        var right=new org.joml.Vector3f(1,0,0).rotate(ctx.camera().getRotation());var up=new org.joml.Vector3f(0,1,0).rotate(ctx.camera().getRotation());
        for(int ring=0;ring<2;ring++)for(int i=0;i<32;i++){
            double a=i*Math.PI/16,b=(i+1)*Math.PI/16,inner=ring*SoulHeadVisual.HALO_RADIUS/2,outer=(ring+1)*SoulHeadVisual.HALO_RADIUS/2;
            for(double[] p:new double[][]{{a,inner},{a,outer},{b,outer},{b,inner}}){double x=Math.cos(p[0])*p[1],y=Math.sin(p[0])*p[1];int alpha=p[1]==outer?(ring==1?0:32):ring==0?68:32;
                v.vertex(m,(float)(center.x+right.x*x+up.x*y),(float)(center.y+right.y*x+up.y*y),(float)(center.z+right.z*x+up.z*y)).color(ring==0?125:55,65,255,alpha);}
        }buffers.draw(layer);haloFrames++;
    }
    static com.google.gson.JsonObject diagnostics(){var o=new com.google.gson.JsonObject();o.addProperty("model","victim-head-model-and-skin;unavailable=skeleton_skull;heroNPC=default_player_head");o.addProperty("scale",SoulHeadVisual.scale(SoulHeadVisual.Kind.SKELETON));o.addProperty("haloRadius",SoulHeadVisual.HALO_RADIUS);o.addProperty("externalAssetRequired",false);o.addProperty("fallbackDefault",false);o.addProperty("frames",frames);o.addProperty("models",models);o.addProperty("haloFrames",haloFrames);o.add("entityHeads",SoulEntityHeads.diagnostics());return o;}
    static void register(){WorldRenderEvents.AFTER_ENTITIES.register(ctx->{
        var c=MinecraftClient.getInstance();var h=HostPoseReader.INSTANCE.latest();var s=NativeSoulRuntime.view;
        if(s==null||!s.scope().equals(headScope)){heads.clear();headScope=s==null?null:s.scope();}
        if(s!=null)heads.keySet().retainAll(s.orbs().stream().map(NativeSoulRuntime.Orb::victim).toList());
        SoulEntityHeads.begin(s);
        if(!Boolean.getBoolean("owmc.frameExport")||s==null||s.orbs().isEmpty()||h==null||h.flags()!=1||!h.inputActive()||c.player==null||!c.player.isAlive()||c.world==null||c.getServer()==null||ctx.matrixStack()==null||System.currentTimeMillis()-s.wall()>250
            ||s.scope().source()!=h.generation()||s.scope().model()!=NativeLocomotionController.INSTANCE.modelId()||NativeLocomotionController.INSTANCE.hero()!=NativeReaperRuntime.HERO
            ||s.scope().world()!=NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey())||!s.scope().owner().equals(c.player.getUuid())){SoulEntityHeads.reset();return;}
        var matrices=ctx.matrixStack();var camera=ctx.camera().getPos();var buffers=c.getBufferBuilders().getEntityVertexConsumers();long now=System.currentTimeMillis();
        for(var orb:s.orbs()){
            var at=PickupRenderMotion.at(orb.previous(),orb.position(),s.wall(),now);if(at.squaredDistanceTo(camera)>64*64||!c.world.isChunkLoaded(BlockPos.ofFloored(at)))continue;
            var pose=PickupKinematics.pose(orb.landed(),orb.attracting(),orb.age(),s.wall(),now);
            var center=at.add(0,.2+pose.lift(),0);halo(ctx,center);
            if(orb.head().kind()==SoulHeadVisual.Kind.ENTITY){
                var entityHead=SoulEntityHeads.prepare(orb,c);if(entityHead==null)continue;
                if(!entityHead.fallback()){
                    matrices.push();try{matrices.translate(center.x-camera.x,center.y-camera.y,center.z-camera.z);matrices.multiply(net.minecraft.util.math.RotationAxis.POSITIVE_Y.rotationDegrees((float)pose.yaw()));SoulEntityHeads.draw(entityHead,matrices,buffers);models++;}finally{matrices.pop();}
                    continue;
                }
            }
            matrices.push();try{matrices.translate(center.x-camera.x,center.y-camera.y,center.z-camera.z);matrices.multiply(net.minecraft.util.math.RotationAxis.POSITIVE_Y.rotationDegrees((float)pose.yaw()));float scale=SoulHeadVisual.scale(orb.head().kind());matrices.scale(scale,scale,scale);
                c.getItemRenderer().renderItem(head(orb),net.minecraft.client.render.model.json.ModelTransformationMode.NONE,LightmapTextureManager.MAX_LIGHT_COORDINATE,OverlayTexture.DEFAULT_UV,matrices,buffers,c.world,0);models++;
            }finally{matrices.pop();}
        }
        frames++;
    });}
}
