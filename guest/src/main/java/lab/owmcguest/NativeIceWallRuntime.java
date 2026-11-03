package lab.owmcguest;

import java.util.*;
import com.google.gson.JsonObject;
import net.minecraft.block.BlockState;
import net.minecraft.block.Blocks;
import net.minecraft.entity.LivingEntity;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvents;
import net.minecraft.util.hit.BlockHitResult;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.math.*;
import net.minecraft.world.RaycastContext;

/** 美 E 冰墙。原版 graph0622：FindGround2（与影步同类，射程字段 35）预览、node19 确认（同影步确认类型 eaee2743）。
 * 原版的地面查询在隐藏的 OW 地图里进行，找不到 MC 地面，所以原版不会执行建墙动作 52/54-57；
 * 这里由 MC 在真实世界找地并建墙。宽 9、高 4、5 秒、逐层升起为 MC 适配值；只占无碰撞的格子，结束原样还原。 */
public final class NativeIceWallRuntime {
    public record Scope(UUID owner,long world,long source,long model){}
    static final double RANGE=35;static final int HALF_WIDTH=4,HEIGHT=4,LIFETIME=100,RISE_TICKS=2;
    private static final class Wall{ServerWorld world;List<BlockPos> columns;int age;float yaw;final LinkedHashMap<BlockPos,BlockState> placed=new LinkedHashMap<>();}
    /** 呈现快照：5 根原版冰柱（实体 0400000000000932）的底部中心、朝向与升起进度 0..1。碰撞用看不见的屏障方块。 */
    public record View(long world,List<Vec3d> pillars,float yaw,float rise,long wall){}
    public static volatile View view;
    private static Wall wall;private static Scope scope;private static boolean previewing;
    private static long previews,builds,refused,blocksPlaced;
    public static volatile String status="{}";

    private static ServerPlayerEntity owner(MinecraftServer server,Scope s){
        var p=s==null?null:server.getPlayerManager().getPlayer(s.owner());
        return p!=null&&p.isAlive()&&NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())==s.world()?p:null;
    }
    /** 真实 MC 地面上的墙基线：视线命中方块的上表面（或其正下方的地面），墙垂直于水平视线。 */
    static List<BlockPos> plan(ServerPlayerEntity p){
        var w=p.getServerWorld();var eye=p.getEyePos();var look=p.getRotationVec(1);
        var hit=w.raycast(new RaycastContext(eye,eye.add(look.multiply(RANGE)),RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
        if(hit.getType()!=HitResult.Type.BLOCK)return null;
        var bh=(BlockHitResult)hit;var base=bh.getSide()==Direction.UP?bh.getBlockPos().up():bh.getBlockPos().offset(bh.getSide());
        for(int i=0;i<4&&w.getBlockState(base.down()).getCollisionShape(w,base.down()).isEmpty();i++)base=base.down();
        var h=new Vec3d(look.x,0,look.z);if(h.lengthSquared()<1e-4)h=new Vec3d(1,0,0);h=h.normalize();
        var side=new Vec3d(-h.z,0,h.x);var cols=new ArrayList<BlockPos>();
        for(int k=-HALF_WIDTH;k<=HALF_WIDTH;k++)cols.add(BlockPos.ofFloored(Vec3d.ofBottomCenter(base).add(side.multiply(k))));
        return cols;
    }
    public static void preview(MinecraftServer server,Scope next,boolean active){
        boolean changed=active!=previewing;if(active&&!previewing)previews++;previewing=active;scope=next;if(changed)publish();
        var p=owner(server,next);if(p==null||!active)return;var cols=plan(p);if(cols==null)return;
        if(p.age%3==0)for(var c:cols)p.getServerWorld().spawnParticles(ParticleTypes.SNOWFLAKE,c.getX()+.5,c.getY()+.1,c.getZ()+.5,1,0,.05,0,0);
    }
    public static void confirm(MinecraftServer server,Scope next){
        scope=next;var p=owner(server,next);if(p==null)return;var cols=plan(p);
        if(cols==null){refused++;publish();return;}
        clear();wall=new Wall();wall.world=p.getServerWorld();wall.columns=cols;wall.yaw=p.getYaw();builds++;
        wall.world.playSound(null,cols.get(HALF_WIDTH),SoundEvents.BLOCK_GLASS_PLACE,SoundCategory.PLAYERS,1.2f,.6f);publish();
    }
    public static void tick(MinecraftServer server){
        if(wall==null)return;var w=wall.world;wall.age++;
        if(wall.age>LIFETIME){clear();publish();return;}
        int layer=(wall.age-1)/RISE_TICKS;
        if(layer<HEIGHT&&(wall.age-1)%RISE_TICKS==0)for(var c:wall.columns){
            var pos=c.up(layer);var st=w.getBlockState(pos);
            if(!w.isChunkLoaded(pos)||!st.getCollisionShape(w,pos).isEmpty()||!st.getFluidState().isEmpty())continue;
            for(var e:w.getEntitiesByClass(LivingEntity.class,new Box(pos),LivingEntity::isAlive)){e.setVelocity(e.getVelocity().add(0,.5,0));e.velocityModified=true;}
            wall.placed.put(pos,st);w.setBlockState(pos,Blocks.BARRIER.getDefaultState());blocksPlaced++;
        }
        var ps=new ArrayList<Vec3d>();for(int k=0;k<wall.columns.size();k+=2)ps.add(Vec3d.ofBottomCenter(wall.columns.get(k)));
        view=new View(NativeWorldIdentity.of(w.getServer(),w.getRegistryKey()),List.copyOf(ps),wall.yaw,Math.min(1f,wall.age/(float)(HEIGHT*RISE_TICKS)),System.currentTimeMillis());
        if(wall.age%10==0)publish();
    }
    public static void clear(){
        if(wall!=null){var w=wall.world;
            for(var e:wall.placed.entrySet())if(w.getBlockState(e.getKey()).isOf(Blocks.BARRIER))w.setBlockState(e.getKey(),e.getValue());
            if(!wall.placed.isEmpty()){var at=wall.placed.keySet().iterator().next();w.playSound(null,at,SoundEvents.BLOCK_GLASS_BREAK,SoundCategory.PLAYERS,1f,.8f);}}
        wall=null;view=null;publish();
    }
    public static void resetSession(){clear();scope=null;previewing=false;publish();}
    private static void publish(){
        var o=new JsonObject();o.addProperty("wall",wall!=null);o.addProperty("previewing",previewing);o.addProperty("previews",previews);o.addProperty("builds",builds);
        o.addProperty("refused",refused);o.addProperty("blocksPlaced",blocksPlaced);o.addProperty("blocksActive",wall==null?0:wall.placed.size());if(wall!=null)o.addProperty("age",wall.age);
        status=o.toString();
    }
}
