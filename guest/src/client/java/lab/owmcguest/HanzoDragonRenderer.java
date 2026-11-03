package lab.owmcguest;

import net.fabricmc.fabric.api.client.rendering.v1.WorldRenderContext;
import net.fabricmc.fabric.api.client.rendering.v1.WorldRenderEvents;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.WorldRenderer;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Vec3d;
import org.joml.Matrix3f;
import org.joml.Quaternionf;
import org.joml.Vector3f;

/** 原版24919完整龙网格0ee9（龙头/身/尾一体），不是粒子替身。
 * 原版颜色/发光参数与骨骼权重；骨骼行进波、缠绕路径和生长裁切为MC适配，未播放原版动画片段。
 * frames/draws只证明提交绘制；实际合成像素与原版攻击仍须Claude实测。 */
public final class HanzoDragonRenderer {
    public static volatile long frames,dragonDraws,arrowFrames,errors;
    public static volatile long skinDraws,skinFallbackDraws;
    public static volatile int lastSwimBones;
    public static final String animationMode="native-bind-skeleton/UNORM8-weights + MC-procedural-swim";
    public static volatile String error="";
    private static boolean registered;
    private static long hostFrame=-1,hostWall;
    // ow_model_submeshes recentered the original model to its bottom/center.
    private static final double SOURCE_Y_SHIFT=2.643839120864868;
    private static final float HEAD_AT_PACK_Z=20.33017254f;

    private HanzoDragonRenderer(){}
    public static void register(){
        if(registered)return;
        registered=true;WorldRenderEvents.AFTER_ENTITIES.register(HanzoDragonRenderer::render);
    }
    private static void render(WorldRenderContext ctx){
        if(!Boolean.getBoolean("owmc.frameExport"))return;
        var client=MinecraftClient.getInstance();var h=HostPoseReader.INSTANCE.latest();
        if(client.world==null||client.player==null||!client.player.isAlive()||client.getServer()==null
            ||client.isPaused()||ctx.matrixStack()==null||h==null||h.flags()!=1||!h.inputActive()
            ||NativeLocomotionController.INSTANCE.hero()!=NativeHanzoSkillController.HERO)return;
        long wall=System.currentTimeMillis();
        if(hostFrame!=h.frame()){hostFrame=h.frame();hostWall=wall;}
        if(wall-hostWall>150)return;
        long world=NativeWorldIdentity.of(client.getServer(),client.world.getRegistryKey());
        long model=NativeLocomotionController.INSTANCE.modelId(),now=System.nanoTime();
        var matrices=ctx.matrixStack();var camera=ctx.camera().getPos();
        var buffers=client.getBufferBuilders().getEntityVertexConsumers();
        boolean drew=false,failed=false;
        for(var v:NativeHanzoSkillRuntime.dragonViews){
            var scope=v.scope();long elapsed=now-v.sampledNanos();
            if(elapsed<0||elapsed>250_000_000L||scope.world()!=world||scope.source()!=h.generation()
                ||scope.model()!=model||!scope.owner().equals(client.player.getUuid()))continue;
            double alpha=Math.max(0,Math.min(1,elapsed/50_000_000.0));
            var at=v.previous().lerp(v.at(),alpha);var direction=v.direction();
            if(!client.world.isChunkLoaded(BlockPos.ofFloored(at))||direction.lengthSquared()<1e-8)continue;
            boolean dragon=v.released()&&v.travelled()>0;
            var pack=OriginalMeshPack.get(dragon?"hanzo-dragon-blue":"hanzo-dragon-arrow");
            if(pack==null){errors++;error="Missing verified pack: "+(dragon?"hanzo-dragon-blue":"hanzo-dragon-arrow");failed=true;continue;}
            matrices.push();
            try{
                matrices.translate(at.x-camera.x,at.y-camera.y,at.z-camera.z);
                var right=new Vec3d(0,1,0).crossProduct(direction);
                if(right.lengthSquared()<1e-6)right=new Vec3d(1,0,0);
                right=right.normalize();var up=direction.crossProduct(right).normalize();
                matrices.multiply(new Quaternionf().setFromNormalized(new Matrix3f(
                    (float)right.x,(float)right.y,(float)right.z,(float)up.x,(float)up.y,(float)up.z,
                    (float)direction.x,(float)direction.y,(float)direction.z)));
                if(!dragon){
                    pack.draw(buffers,matrices.peek(),WorldRenderer.getLightmapCoordinates(client.world,BlockPos.ofFloored(at)));
                    arrowFrames++;drew=true;continue;
                }
                double age=v.age()-1+alpha;
                double length=Math.max(0,v.travelled()-NativeHanzoSkillRuntime.DRAGON_SPEED*(1-alpha));
                double radius=NativeHanzoSkillRuntime.DRAGON_COIL_RADIUS;
                double wave=NativeHanzoSkillRuntime.DRAGON_ANGULAR_SPEED/NativeHanzoSkillRuntime.DRAGON_SPEED;
                for(int twin=0;twin<2;twin++){
                    double phase=age*NativeHanzoSkillRuntime.DRAGON_ANGULAR_SPEED+twin*Math.PI;
                    int bones=pack.boneCount();lastSwimBones=bones;
                    var bind=new Vector3f[bones];var offset=new Vector3f[bones];var rotation=new Quaternionf[bones];
                    for(int bone=0;bone<bones;bone++){
                        bind[bone]=pack.boneBindPosition(bone);
                        var sample=HanzoDragonSwim.sample(bind[bone].z-HEAD_AT_PACK_Z,age*HanzoDragonSwim.PHASE_PER_TICK+twin*Math.PI);
                        offset[bone]=new Vector3f((float)sample.x(),(float)sample.y(),0);
                        var tangent=new Vector3f((float)sample.slopeX(),(float)sample.slopeY(),1).normalize();
                        rotation[bone]=new Quaternionf().rotationTo(new Vector3f(0,0,1),tangent);
                    }
                    boolean skinned=pack.drawSkinnedEffect(buffers,matrices.peek(),(bone,p,n)->{
                        p.sub(bind[bone]).rotate(rotation[bone]).add(bind[bone]).add(offset[bone]);
                        n.rotate(rotation[bone]);
                    },(p,n)->{
                        double z=p.z-HEAD_AT_PACK_Z;
                        double angle=phase+z*wave,sin=Math.sin(angle),cos=Math.cos(angle);
                        p.set((float)(p.x+radius*cos),(float)(p.y-SOURCE_Y_SHIFT+radius*sin),(float)z);
                        // Inverse transpose of the axial sine deformation.
                        n.z+=(float)(radius*wave*(sin*n.x-cos*n.y));n.normalize();
                    },(float)(HEAD_AT_PACK_Z-length));
                    if(skinned)skinDraws++;else skinFallbackDraws++;
                    dragonDraws++;
                }
                drew=true;
            }catch(RuntimeException ex){errors++;error=ex.toString();failed=true;}
            finally{matrices.pop();}
        }
        if(drew){frames++;if(!failed)error="";}
    }
}
