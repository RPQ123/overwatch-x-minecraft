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

/** A fatal, owner-attributed MC hit creates one ephemeral Reaping pickup.
 * The requested50OW heal uses the project's existing HP mapping. */
public final class NativeSoulRuntime {
    public record Scope(UUID owner,long world,long source,long model){}
    public record Head(SoulHeadVisual.Kind kind,net.minecraft.component.type.ProfileComponent profile,SoulVictimAppearance appearance){}
    public record Orb(UUID victim,Head head,Vec3d position,Vec3d previous,long born,double velocity,boolean landed,int age,double magnetSpeed,boolean attracting){}
    public record View(Scope scope,long wall,List<Orb> orbs){}
    private static Scope scope;private static final LinkedHashMap<UUID,Orb> orbs=new LinkedHashMap<>();
    private static final Set<UUID> seen=new HashSet<>();
    private static long spawned,collected,expired,attractionTicks;private static double healed;
    private static final net.minecraft.particle.DustParticleEffect BLUE=new net.minecraft.particle.DustParticleEffect(new org.joml.Vector3f(.15f,.35f,1),.7f),PURPLE=new net.minecraft.particle.DustParticleEffect(new org.joml.Vector3f(.65f,.12f,1),.7f);
    public static volatile View view;public static volatile String status="{\"active\":0}";
    public static void configure(UUID owner,long world,long hero,long model,long source){resetSession();if(hero==NativeReaperRuntime.HERO&&owner!=null)scope=new Scope(owner,world,source,model);}
    private static boolean matches(ServerPlayerEntity p){return scope!=null&&p!=null&&p.isAlive()&&p.getUuid().equals(scope.owner())
        &&NativeWorldIdentity.of(p.getServer(),p.getWorld().getRegistryKey())==scope.world()
        &&NativeEliminationRuntime.sessionMatches(scope.owner(),scope.world(),NativeReaperRuntime.HERO,scope.model(),scope.source());}
    public static void killed(ServerPlayerEntity p,LivingEntity victim){
        if(scope==null||victim.getServer()==null||victim.getHealth()>0||victim==p||victim.isSpectator())return;
        if(!matches(p)||victim.getWorld()!=p.getWorld()||!seen.add(victim.getUuid()))return;
        if(seen.size()>4096){seen.clear();seen.add(victim.getUuid());}
        if(orbs.size()>=32)orbs.remove(orbs.keySet().iterator().next());
        var at=victim.getPos().add(0,.45,0);if(!p.getWorld().isChunkLoaded(BlockPos.ofFloored(at)))return;
        var kind=SoulHeadVisual.kind(net.minecraft.registry.Registries.ENTITY_TYPE.getId(victim.getType()).toString(),victim instanceof net.minecraft.entity.player.PlayerEntity,victim instanceof HeroNpcEntity);
        // Snapshot an existing profile only. NPCs have no MC player skin and use
        // the vanilla default player head; no skin lookup or invented OW texture.
        var profile=victim instanceof net.minecraft.entity.player.PlayerEntity player?new net.minecraft.component.type.ProfileComponent(player.getGameProfile()):null;
        var appearance=kind==SoulHeadVisual.Kind.ENTITY?SoulVictimAppearance.capture(victim):null;
        orbs.put(victim.getUuid(),new Orb(victim.getUuid(),new Head(kind,profile,appearance),at,at,System.currentTimeMillis(),.06,false,0,0,false));spawned++;publish();
    }
    public static void tick(MinecraftServer server){
        if(scope==null)return;var p=server.getPlayerManager().getPlayer(scope.owner());
        if(!matches(p)){resetSession();return;}var w=p.getServerWorld();
        for(var e:new ArrayList<>(orbs.entrySet())){
            var orb=e.getValue();var at=orb.position();int age=orb.age()+1;
            if(age>300||!w.isChunkLoaded(BlockPos.ofFloored(at))){orbs.remove(e.getKey());expired++;continue;}
            var recipient=(orb.landed()||orb.attracting())&&p.getHealth()<p.getMaxHealth()?PickupWorldMotion.nearest(w,p,at,p.getUuid(),candidate->candidate==p):null;
            var motion=PickupWorldMotion.toward(w,p,at,recipient,orb.magnetSpeed());
            double v=orb.velocity();boolean landed=orb.landed();
            if(motion.attracting()){at=motion.at();landed=false;v=0;attractionTicks++;}
            else if(!landed){v=Math.max(-.5,v-.04);var next=at.add(0,v,0);var hit=w.raycast(new RaycastContext(at,next.add(0,-.2,0),RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
                if(hit.getType()==HitResult.Type.BLOCK&&v<0){at=hit.getPos().add(0,.22,0);v=0;landed=true;}else at=next;}
            if(recipient!=null&&PickupWorldMotion.touching(at,p)&&PickupWorldMotion.clear(w,p,at,PickupWorldMotion.target(p))){
                float before=p.getHealth();p.heal((float)(50*NativeShotSimulation.HP_SCALE));double gain=p.getHealth()-before;
                if(gain<=0)continue;healed+=gain;collected++;orbs.remove(e.getKey());
                w.spawnParticles(ParticleTypes.SOUL,at.x,at.y,at.z,12,.15,.2,.15,.03);w.playSound(null,p.getX(),p.getY(),p.getZ(),SoundEvents.PARTICLE_SOUL_ESCAPE,SoundCategory.PLAYERS,.7f,1.2f);
                // Self-healing is not credited as a second Q reward for this kill.
            }else{orbs.put(e.getKey(),new Orb(orb.victim(),orb.head(),at,orb.position(),orb.born(),v,landed,age,motion.speed(),motion.attracting()));
                if(age%3==0)for(int i=0;i<2;i++){double angle=age*.3+i*Math.PI;var point=at.add(Math.cos(angle)*.29,.22+Math.sin(angle*.7)*.12,Math.sin(angle)*.29);w.spawnParticles(i==0?BLUE:PURPLE,point.x,point.y,point.z,1,0,0,0,0);}
                if(motion.attracting()&&age%2==0){var tail=at.lerp(orb.position(),.6);w.spawnParticles(PURPLE,tail.x,tail.y+.2,tail.z,1,.025,.025,.025,0);}
            }
        }
        publish();
    }
    private static void publish(){view=scope==null?null:new View(scope,System.currentTimeMillis(),List.copyOf(orbs.values()));var o=new JsonObject();o.addProperty("active",orbs.size());o.addProperty("spawned",spawned);o.addProperty("collected",collected);o.addProperty("expired",expired);o.addProperty("healed",healed);o.addProperty("healMc",50*NativeShotSimulation.HP_SCALE);o.addProperty("pickupRadius",PickupKinematics.CONTACT);o.addProperty("attractionRadius",PickupKinematics.RADIUS);o.addProperty("attractionTicks",attractionTicks);o.addProperty("lifetimeSeconds",15);status=o.toString();}
    public static void clearForTests(){orbs.clear();seen.clear();publish();}
    public static void resetSession(){scope=null;orbs.clear();seen.clear();publish();}
}
