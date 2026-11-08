package lab.owmcguest;

import com.google.gson.JsonObject;
import java.util.UUID;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.damage.DamageSource;
import net.minecraft.registry.RegistryKey;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.server.MinecraftServer;
import net.minecraft.util.Identifier;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.RaycastContext;

/** Server-side quick melee for the native heroes that have a melee button. */
public final class NativeMeleeRuntime {
    public static final long GENJI=0x02e0000000000029L;
    public static final long MCCREE=0x02e0000000000042L;
    public static final long WINSTON=0x02e0000000000009L;
    private static final java.util.LinkedHashSet<String> seen=new java.util.LinkedHashSet<>();
    public static volatile long accepted,hits,blocked,rejected;
    public static volatile double damageApplied;
    public static volatile String status="{\"accepted\":0,\"hits\":0,\"damageApplied\":0.0,\"blocked\":0,\"rejected\":0}";

    public static boolean supported(long hero){return (hero&~0xffffL)==0x02e0000000000000L&&java.util.Set.of(2L,3L,5L,6L,8L,9L,10L,0x15L,0x29L,0x40L,0x42L,0x65L,0x6eL,0xddL).contains(hero&0xffffL);}
    private static String heroName(long hero){return hero==GENJI?"genji":hero==MCCREE?"mccree":hero==WINSTON?"winston":"unknown";}

    public static void swing(MinecraftServer server,UUID playerId,long expectedWorld,long sourceGeneration,long hero,long model,long tick,long wallMs,Vec3d eye,Vec3d center,double nativeDamage,double radius){
        long now=System.currentTimeMillis();var player=server.getPlayerManager().getPlayer(playerId);
        if(player==null||!player.isAlive()||NativeWorldIdentity.of(server,player.getWorld().getRegistryKey())!=expectedWorld||sourceGeneration==0||!supported(hero)||eye==null||center==null||!Double.isFinite(nativeDamage)||nativeDamage<=0||nativeDamage>1000||radius!=1||tick<=0||now-wallMs>200||wallMs>now+50
            ||!NativeEliminationRuntime.sessionMatches(playerId,expectedWorld,hero,model,sourceGeneration)){rejected++;publish(hero);return;}
        if(player.getEyePos().squaredDistanceTo(eye)>16||!Double.isFinite(center.lengthSquared())||center.squaredDistanceTo(eye)>16){rejected++;publish(hero);return;}
        if(hero==WINSTON&&WinstonServer.INSTANCE.primal(playerId,expectedWorld,sourceGeneration,model))return;
        String identity=sourceGeneration+":"+model+":"+tick;if(!seen.add(identity))return;if(seen.size()>4096)seen.remove(seen.iterator().next());accepted++;
        var world=player.getServerWorld();net.minecraft.entity.Entity best=null;double nearest=Double.POSITIVE_INFINITY;
        for(var entity:NativeDamageTargets.in(world,player,new Box(center,center).expand(radius))){
            var box=entity.getBoundingBox();var point=new Vec3d(Math.clamp(center.x,box.minX,box.maxX),Math.clamp(center.y,box.minY,box.maxY),Math.clamp(center.z,box.minZ,box.maxZ));
            if(center.squaredDistanceTo(point)>radius*radius)continue;double distance=eye.distanceTo(point);
            var wall=world.raycast(new RaycastContext(eye,point,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,player));
            if(wall.getType()!=HitResult.Type.MISS&&eye.squaredDistanceTo(wall.getPos())+1e-5<eye.squaredDistanceTo(point)){blocked++;continue;}
            if(distance<nearest){nearest=distance;best=entity;}
        }
        if(best!=null){var result=NativeDamageTargets.meleeDamage(world,best,player,nativeDamage*NativeShotSimulation.HP_SCALE);if(result.applied()){hits++;damageApplied+=result.healthLost();NativeUltimateRuntime.credit(result.healthLost());}}
        publish(hero);
    }
    private static void publish(long hero){var out=new JsonObject();out.addProperty("hero",heroName(hero));out.addProperty("heroId",hero);out.addProperty("accepted",accepted);out.addProperty("hits",hits);out.addProperty("damageApplied",damageApplied);out.addProperty("blocked",blocked);out.addProperty("rejected",rejected);out.addProperty("source","native TrackTargets");status=out.toString();}
    public static void close(){seen.clear();accepted=hits=blocked=rejected=0;damageApplied=0;publish(0);}
    public static void resetSession(){close();}
}
