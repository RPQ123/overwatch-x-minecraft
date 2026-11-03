package lab.owmcguest;

import java.util.UUID;
import com.google.gson.JsonObject;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.util.math.*;
import net.minecraft.world.RaycastContext;
import net.minecraft.util.hit.HitResult;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.sound.*;

/** MC deployment/landing and declared5s/5m/40OW-HP-per-second healing adapter.
 * Drop physics, healing cadence and friendly-target policy are explicit MC rules,
 * not a claim that an original offline server field entity was spawned. */
public final class NativeBioticRuntime {
    public static final long HERO=0x02e000000000006eL;
    public record Deployment(UUID owner,long world,long source,long model,long nativeTick,long wall,Vec3d origin,double duration,double radius,double amount){}
    public record View(UUID owner,long world,long source,long model,long nativeTick,Vec3d at,boolean landed,int remaining,long wall){}
    private static Deployment active;
    private static final NativeBioticLight light=new NativeBioticLight();
    private static Vec3d at;
    private static double velocity;
    private static boolean landed;
    private static int age,remaining;
    private static long lastTick,launches,landings,expired,refused;
    private static double healed;
    public static volatile View view;
    public static volatile String status="{\"active\":false,\"healed\":0}";
    private static boolean matches(MinecraftServer server,Deployment d){
        var p=server.getPlayerManager().getPlayer(d.owner());
        return p!=null&&p.isAlive()&&NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())==d.world()
            &&NativeEliminationRuntime.sessionMatches(d.owner(),d.world(),HERO,d.model(),d.source());
    }
    public static void deploy(MinecraftServer server,Deployment d){
        long now=System.currentTimeMillis();
        if(d==null||now-d.wall()>150||d.wall()>now+50||d.nativeTick()<=lastTick||!matches(server,d)
            ||d.duration()!=5||d.radius()!=5||d.amount()!=40||!Double.isFinite(d.origin().x)||!Double.isFinite(d.origin().y)||!Double.isFinite(d.origin().z)){refused++;return;}
        var p=server.getPlayerManager().getPlayer(d.owner());var world=p.getServerWorld();
        if(d.origin().squaredDistanceTo(p.getPos())>9||!world.isChunkLoaded(BlockPos.ofFloored(d.origin()))){refused++;return;}
        light.clear();active=d;lastTick=d.nativeTick();at=d.origin();velocity=0;landed=false;age=remaining=0;launches++;publish();
    }
    public static void tick(MinecraftServer server){
        var d=active;if(d==null)return;
        if(!matches(server,d)){clear(false);return;}
        var owner=server.getPlayerManager().getPlayer(d.owner());var world=owner.getServerWorld();age++;
        if(!world.isChunkLoaded(BlockPos.ofFloored(at))){clear(false);return;}
        if(!landed){
            velocity=Math.max(-.5,velocity-.04);var next=at.add(0,velocity,0);
            if(!world.isChunkLoaded(BlockPos.ofFloored(next))||age>200||next.y<world.getBottomY()){clear(false);return;}
            var hit=world.raycast(new RaycastContext(at,next,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,owner));
            if(hit.getType()==HitResult.Type.BLOCK){
                if(hit.getSide()!=Direction.UP){clear(false);return;}
                at=hit.getPos().add(0,.025,0);landed=true;remaining=(int)(d.duration()*20);landings++;
                world.playSound(null,at.x,at.y,at.z,SoundEvents.BLOCK_BEACON_ACTIVATE,SoundCategory.PLAYERS,.3f,1.8f);
            }else at=next;
        }else{
            for(var target:world.getPlayers()){
                if(!target.isAlive()||target.isSpectator()||target.getPos().squaredDistanceTo(at)>d.radius()*d.radius())continue;
                // No team implies only self. Ordinary hostile MC mobs are never healed.
                if(target!=owner&&(owner.getScoreboardTeam()==null||!owner.isTeammate(target)))continue;
                var to=target.getPos().add(0,.5,0);
                if(world.raycast(new RaycastContext(at.add(0,.12,0),to,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,owner)).getType()!=HitResult.Type.MISS)continue;
                float before=target.getHealth();target.heal((float)(d.amount()*NativeShotSimulation.HP_SCALE/20));
                double actual=Math.max(0,target.getHealth()-before);healed+=actual;
                // Existing generic native meter owns the only native write.
                if(actual>0)NativeUltimateRuntime.credit(actual);
                if(actual>0&&remaining%10==0)world.spawnParticles(ParticleTypes.HAPPY_VILLAGER,target.getX(),target.getY()+1,target.getZ(),1,.15,.25,.15,0);
            }
            if(--remaining<=0){clear(true);return;}
        }
        // User MC adaptation: actual level-14 light while the owner is in the
        // landed field. Leave/expiry/death/hero/world/session changes restore
        // the owned air cell; healing itself retains the declared 5m/5s rules.
        light.update(world,at,landed&&owner.getPos().squaredDistanceTo(at)<=d.radius()*d.radius(),d.nativeTick());
        publish();
    }
    private static void publish(){
        var d=active;var out=new JsonObject();out.addProperty("active",d!=null);out.addProperty("launches",launches);out.addProperty("landings",landings);out.addProperty("expired",expired);out.addProperty("refused",refused);out.addProperty("healed",healed);out.addProperty("landed",landed);out.addProperty("remainingTicks",remaining);out.addProperty("radius",5);out.addProperty("rateMcHp",4);out.addProperty("adapter","native-cast-volley; MC drop/LOS/friendly policy; declared amount per second");
        out.addProperty("lightActive",light.active());out.addProperty("lightLevel",NativeBioticLight.LEVEL);out.addProperty("lightsPlaced",light.placed);out.addProperty("lightsRemoved",light.removed);out.addProperty("lightEditConflicts",light.conflicts);
        if(d!=null){out.addProperty("nativeTick",d.nativeTick());out.addProperty("x",at.x);out.addProperty("y",at.y);out.addProperty("z",at.z);view=new View(d.owner(),d.world(),d.source(),d.model(),d.nativeTick(),at,landed,remaining,System.currentTimeMillis());}else view=null;
        status=out.toString();
    }
    private static void clear(boolean natural){light.clear();if(natural)expired++;active=null;landed=false;remaining=0;publish();}
    public static void resetSession(){clear(false);lastTick=0;}
}
