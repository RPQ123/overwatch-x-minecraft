package lab.owmcguest;

import java.util.*;
import com.google.gson.JsonObject;
import net.minecraft.entity.LivingEntity;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.util.math.*;
import net.minecraft.world.RaycastContext;
import net.minecraft.util.hit.HitResult;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.sound.*;

/** Classic Reaping: a confirmed real kill creates one physical MC soul globe.
 *50OW HP=5MC HP per official May2016 Classic semantics.15s/1.5m are explicit
 *MC pickup adapters, not an authenticated2015 server extraction. */
public final class NativeSoulRuntime {
    public record Scope(UUID owner,long world,long source,long model){}
    public record Orb(UUID victim,Vec3d position,long born,double velocity,boolean landed){}
    public record View(Scope scope,long wall,List<Orb> orbs){}
    private static Scope scope;private static final LinkedHashMap<UUID,Orb> orbs=new LinkedHashMap<>();
    private static final Set<UUID> seen=new HashSet<>();
    private static long spawned,collected,expired;private static double healed;
    public static volatile View view;public static volatile String status="{\"active\":0}";
    public static void configure(UUID owner,long world,long hero,long model,long source){resetSession();if(hero==NativeReaperRuntime.HERO&&owner!=null)scope=new Scope(owner,world,source,model);}
    private static boolean matches(ServerPlayerEntity p){return scope!=null&&p!=null&&p.isAlive()&&p.getUuid().equals(scope.owner())
        &&NativeWorldIdentity.of(p.getServer(),p.getWorld().getRegistryKey())==scope.world()
        &&NativeEliminationRuntime.sessionMatches(scope.owner(),scope.world(),NativeReaperRuntime.HERO,scope.model(),scope.source());}
    public static void killed(LivingEntity victim){
        if(scope==null||victim.getServer()==null||victim.getHealth()>0)return;
        var p=victim.getServer().getPlayerManager().getPlayer(scope.owner());
        if(!matches(p)||victim.getWorld()!=p.getWorld()||!seen.add(victim.getUuid()))return;
        if(seen.size()>4096){seen.clear();seen.add(victim.getUuid());}
        if(orbs.size()>=32)orbs.remove(orbs.keySet().iterator().next());
        var at=victim.getPos().add(0,.45,0);if(!p.getWorld().isChunkLoaded(BlockPos.ofFloored(at)))return;
        orbs.put(victim.getUuid(),new Orb(victim.getUuid(),at,System.currentTimeMillis(),.06,false));spawned++;publish();
    }
    public static void tick(MinecraftServer server){
        if(scope==null)return;var p=server.getPlayerManager().getPlayer(scope.owner());
        if(!matches(p)){resetSession();return;}var w=p.getServerWorld();long now=System.currentTimeMillis();
        for(var e:new ArrayList<>(orbs.entrySet())){
            var orb=e.getValue();var at=orb.position();
            if(now-orb.born()>15000||!w.isChunkLoaded(BlockPos.ofFloored(at))){orbs.remove(e.getKey());expired++;continue;}
            double v=orb.landed()?0:Math.max(-.5,orb.velocity()-.04);boolean landed=orb.landed();
            if(!landed){var next=at.add(0,v,0);var hit=w.raycast(new RaycastContext(at,next.add(0,-.2,0),RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
                if(hit.getType()==HitResult.Type.BLOCK&&v<0){at=hit.getPos().add(0,.22,0);v=0;landed=true;}else at=next;}
            if(p.getHealth()<p.getMaxHealth()&&p.getPos().add(0,.5,0).squaredDistanceTo(at)<=1.5*1.5){
                float before=p.getHealth();p.heal(5);healed+=p.getHealth()-before;collected++;orbs.remove(e.getKey());
                w.spawnParticles(ParticleTypes.SOUL,at.x,at.y,at.z,12,.15,.2,.15,.03);w.playSound(null,p.getX(),p.getY(),p.getZ(),SoundEvents.PARTICLE_SOUL_ESCAPE,SoundCategory.PLAYERS,.7f,1.2f);
                // Self-healing is not credited as a second Q reward for this kill.
            }else{orbs.put(e.getKey(),new Orb(orb.victim(),at,orb.born(),v,landed));if(p.age%5==0)w.spawnParticles(ParticleTypes.SOUL,at.x,at.y,at.z,1,.06,.05,.06,0);}
        }
        publish();
    }
    private static void publish(){view=scope==null?null:new View(scope,System.currentTimeMillis(),List.copyOf(orbs.values()));var o=new JsonObject();o.addProperty("active",orbs.size());o.addProperty("spawned",spawned);o.addProperty("collected",collected);o.addProperty("expired",expired);o.addProperty("healed",healed);o.addProperty("healMc",5);o.addProperty("pickupRadius",1.5);o.addProperty("lifetimeSeconds",15);status=o.toString();}
    public static void clearForTests(){orbs.clear();seen.clear();publish();}
    public static void resetSession(){scope=null;orbs.clear();seen.clear();publish();}
}
