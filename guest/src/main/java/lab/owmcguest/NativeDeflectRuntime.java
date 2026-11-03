package lab.owmcguest;
import java.util.*;
import com.google.gson.JsonObject;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.damage.DamageSource;
import net.minecraft.entity.projectile.*;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.math.*;
import net.minecraft.world.RaycastContext;
import lab.owmcguest.NativeShotProtocol.Vec;

/** MC projectile ownership/velocity adaptation while the original Deflect is active. */
public final class NativeDeflectRuntime {
    private record Phase(UUID owner,long world,long source,long model,long tick,boolean active,Vec3d eye,Vec3d forward,Vec3d right,Vec3d up,List<double[]> boxes,long wall){}
    private record Reflection(UUID owner,long world,long source,long model,long wall){}
    private static Phase phase;
    private static final LinkedHashMap<UUID,Reflection> reflected=new LinkedHashMap<>();
    private static final Map<String,Float> healthBefore=new HashMap<>();
    private static long reflections,hits;private static double healthLost;
    public static volatile String status="{\"active\":false,\"reflections\":0}";
    public static void refresh(UUID owner,long world,long source,long model,long tick,boolean active,Vec3d eye,Vec3d forward,Vec3d right,Vec3d up,List<double[]> boxes,long wall){
        if(!NativeEliminationRuntime.sessionMatches(owner,world,0x02e0000000000029L,model,source)||System.currentTimeMillis()-wall>150||wall>System.currentTimeMillis()+50)return;
        phase=new Phase(owner,world,source,model,tick,active,eye,forward,right,up,boxes,wall);
    }
    private static double[] local(Vec3d vector,Phase p){return new double[]{vector.dotProduct(p.right()),vector.dotProduct(p.up()),vector.dotProduct(p.forward())};}
    public static void tick(MinecraftServer server){
        long now=System.currentTimeMillis();reflected.values().removeIf(v->now-v.wall()>60000);var state=phase;
        var player=state==null?null:server.getPlayerManager().getPlayer(state.owner());
        boolean active=state!=null&&state.active()&&state.tick()>0&&now-state.wall()<=150&&now>=state.wall()-50&&player!=null&&player.isAlive()
            &&NativeEliminationRuntime.sessionMatches(state.owner(),state.world(),0x02e0000000000029L,state.model(),state.source())
            &&NativeWorldIdentity.of(server,player.getWorld().getRegistryKey())==state.world()&&player.getEyePos().squaredDistanceTo(state.eye())<16;
        if(active){
            var world=player.getServerWorld();
            for(var entity:world.getOtherEntities(player,new Box(state.eye(),state.eye()).expand(8),e->e instanceof PersistentProjectileEntity||e instanceof ExplosiveProjectileEntity)){
                var projectile=(ProjectileEntity)entity;var owner=projectile.getOwner();
                if(projectile.isRemoved()||owner==player||(owner!=null&&player.isTeammate(owner))||reflected.containsKey(projectile.getUuid()))continue;
                var start=projectile.getPos();var velocity=projectile.getVelocity();double speed=velocity.length();
                if(!Double.isFinite(speed)||speed<.001||speed>64)continue;
                double hit=NativeDeflectGeometry.hit(local(start.subtract(state.eye()),state),local(velocity,state),state.boxes());if(!Double.isFinite(hit))continue;
                var point=start.add(velocity.multiply(hit));
                var clip=LoadedRayPrefix.clip(new Vec(start.x,start.y,start.z),new Vec(point.x,point.y,point.z),(x,z)->world.isChunkLoaded(new BlockPos(x<<4,0,z<<4)));
                if(!clip.complete())continue;
                var wall=world.raycast(new RaycastContext(start,point,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,player));
                if(wall.getType()!=HitResult.Type.MISS&&start.squaredDistanceTo(wall.getPos())+1e-6<start.squaredDistanceTo(point))continue;
                // Keep this actual vanilla projectile and its damage/speed; no
                // visual-only copy or newly spawned replacement can deal damage.
                projectile.setPosition(point);projectile.setOwner(player);projectile.setVelocity(state.forward().multiply(speed));projectile.velocityDirty=true;
                reflected.put(projectile.getUuid(),new Reflection(state.owner(),state.world(),state.source(),state.model(),now));reflections++;
                if(reflected.size()>4096)reflected.remove(reflected.keySet().iterator().next());
            }
        }
        var out=new JsonObject();out.addProperty("active",active);out.addProperty("nativeTick",state==null?0:state.tick());out.addProperty("reflections",reflections);out.addProperty("hits",hits);out.addProperty("healthLost",healthLost);status=out.toString();
    }
    private static String key(LivingEntity entity,DamageSource source){return source.getSource()==null?"":entity.getUuid()+":"+source.getSource().getUuid();}
    private static ServerPlayerEntity damageOwner(LivingEntity entity,DamageSource source){
        if(source.getSource()==null||!(entity.getWorld() instanceof net.minecraft.server.world.ServerWorld world))return null;
        var ticket=reflected.get(source.getSource().getUuid());if(ticket==null)return null;var p=world.getServer().getPlayerManager().getPlayer(ticket.owner());
        return p!=null&&NativeEliminationRuntime.sessionMatches(ticket.owner(),ticket.world(),0x02e0000000000029L,ticket.model(),ticket.source())?p:null;
    }
    public static void beforeDamage(LivingEntity entity,DamageSource source){
        if(damageOwner(entity,source)==null)return;if(healthBefore.size()>4096)healthBefore.clear();healthBefore.put(key(entity,source),entity.getHealth());
    }
    public static void afterDamage(LivingEntity entity,DamageSource source){
        var p=damageOwner(entity,source);Float before=healthBefore.remove(key(entity,source));if(p==null||before==null)return;
        double lost=Math.max(0,before-entity.getHealth());if(lost<=0)return;hits++;healthLost+=lost;
        NativeUltimateRuntime.credit(lost);NativeEliminationRuntime.damage(p,entity,lost);NativeCombatFeedback.damage(p,entity,lost);
    }
    public static void resetSession(){phase=null;reflected.clear();healthBefore.clear();reflections=hits=0;healthLost=0;status="{\"active\":false,\"reflections\":0}";}
}
