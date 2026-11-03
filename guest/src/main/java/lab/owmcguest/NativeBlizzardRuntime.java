package lab.owmcguest;

import java.util.UUID;
import com.google.gson.JsonObject;
import net.minecraft.entity.mob.MobEntity;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvents;
import net.minecraft.util.hit.BlockHitResult;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.RaycastContext;

/** 美 Q 暴雪。原版 graph064a 的 WeaponVolley10 新 tick 准入一次投掷；原版把无人机交给不存在的服务端，
 * 所以飞行、落地、范围减速/冰冻由 MC 补。原版声明：速度 20 m/s、寿命 20 s；Wait15 字面量 8 作为持续时间
 * （假设，见 NATIVE-MEI-BLIZZARD.md）。半径 10 格、每秒 20 点伤害为 MC 适配值。 */
public final class NativeBlizzardRuntime {
    public record Scope(UUID owner,long world,long source,long model){}
    public record View(UUID owner,long world,Vec3d at,boolean landed,int age,long wall){}
    static final double SPEED=20/20.0,GRAVITY=9.8/400.0,RADIUS=10,NATIVE_DPS=20;
    static final int FLIGHT_TICKS=400,ACTIVE_TICKS=160;
    private static Scope scope;private static Vec3d pos,vel;private static boolean landed;private static int age,activeAge;private static long cast;
    private static long modelsWall;
    private static long casts,lands,contacts,damageTicks;private static double damageApplied;
    public static volatile View view;public static volatile String status="{\"active\":false}";

    private static ServerPlayerEntity owner(MinecraftServer server){
        var p=scope==null?null:server.getPlayerManager().getPlayer(scope.owner());
        return p!=null&&p.isAlive()&&NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())==scope.world()?p:null;
    }
    public static void cast(MinecraftServer server,Scope next){
        scope=next;var p=owner(server);if(p==null){scope=null;return;}
        pos=p.getEyePos().add(p.getRotationVec(1).multiply(.6));vel=p.getRotationVec(1).multiply(SPEED);landed=false;age=0;activeAge=0;cast++;casts++;publish();
    }
    public static void tick(MinecraftServer server){
        if(scope==null)return;var p=owner(server);if(p==null){resetSession();return;}
        var w=p.getServerWorld();age++;modelsWall=System.currentTimeMillis();
        if(!landed){
            var next=pos.add(vel);var hit=w.raycast(new RaycastContext(pos,next,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
            if(hit.getType()==HitResult.Type.BLOCK){pos=((BlockHitResult)hit).getPos().add(Vec3d.of(((BlockHitResult)hit).getSide().getVector()).multiply(.3));landed=true;lands++;
                w.playSound(null,pos.x,pos.y,pos.z,SoundEvents.BLOCK_GLASS_PLACE,SoundCategory.PLAYERS,1f,.7f);}
            else{pos=next;vel=vel.add(0,-GRAVITY,0);w.spawnParticles(ParticleTypes.SNOWFLAKE,pos.x,pos.y,pos.z,2,.05,.05,.05,0);}
            if(!landed&&age>FLIGHT_TICKS){resetSession();return;}
        }else{
            activeAge++;
            if(activeAge>ACTIVE_TICKS){resetSession();return;}
            w.spawnParticles(ParticleTypes.SNOWFLAKE,pos.x,pos.y+1.5,pos.z,40,RADIUS*.55,1.2,RADIUS*.55,.02);
            if(activeAge%5==0)w.spawnParticles(ParticleTypes.WHITE_ASH,pos.x,pos.y+.5,pos.z,30,RADIUS*.5,.4,RADIUS*.5,0);
            boolean damage=activeAge%10==0;
            for(var mob:w.getEntitiesByClass(MobEntity.class,new Box(pos,pos).expand(RADIUS),m->m.isAlive()&&m.getPos().squaredDistanceTo(pos)<=RADIUS*RADIUS)){
                NativeMeiFreezeRuntime.hit(p,scope.world(),scope.model(),scope.source(),"blizzard:"+cast+":"+activeAge,mob);contacts++;
                if(damage){var r=NativeDamageTargets.explosionDamage(w,mob,p,NATIVE_DPS/2*NativeShotSimulation.HP_SCALE);if(r.applied()){damageTicks++;damageApplied+=r.healthLost();}}
            }
        }
        publish();
    }
    private static void publish(){
        view=scope==null||pos==null?null:new View(scope.owner(),scope.world(),pos,landed,landed?activeAge:age,System.currentTimeMillis());
        var o=new JsonObject();o.addProperty("active",scope!=null);o.addProperty("landed",landed&&scope!=null);o.addProperty("casts",casts);o.addProperty("lands",lands);
        o.addProperty("contacts",contacts);o.addProperty("damageTicks",damageTicks);o.addProperty("damageApplied",damageApplied);o.addProperty("radius",RADIUS);
        if(scope!=null&&pos!=null){o.addProperty("x",pos.x);o.addProperty("y",pos.y);o.addProperty("z",pos.z);o.addProperty("activeAge",activeAge);}
        
        // integrator/models: only real state/geometry, never input-derived effects.
if(scope!=null&&pos!=null&&landed&&modelsWall>0){
            var f=OriginalEffectFrames.frame(scope.owner(),scope.world(),scope.source(),scope.model(),modelsWall);
            // MC presentation sampling inside the real active area, not native emitter curves.
            for(int i=0;i<12;i++){double a=i*Math.PI/6+activeAge*.035;
                OriginalEffectFrames.body(f,"mei-blizzard-shard",pos.add(Math.cos(a)*RADIUS*.55,1+(i%3)*.35,Math.sin(a)*RADIUS*.55),new Vec3d(4,4,4),.7f,false);}
            o.add("models",f);
        }
        status=o.toString();
    }
    public static void resetSession(){scope=null;pos=null;vel=null;landed=false;age=activeAge=0;publish();}
    public static void clear(){resetSession();}
}
