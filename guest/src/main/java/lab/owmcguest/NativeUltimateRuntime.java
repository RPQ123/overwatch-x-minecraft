package lab.owmcguest;

import java.util.LinkedHashSet;
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

/** Original sword tracking events use MC entities and block collision on the server. */
public final class NativeUltimateRuntime {
    public static volatile double chargeCredit;
    public static volatile long swings,hits;
    public static volatile double damageApplied;
    private static final LinkedHashSet<String> seen=new LinkedHashSet<>();
    public static void credit(double actualLoss){if(Double.isFinite(actualLoss)&&actualLoss>0)chargeCredit+=actualLoss/NativeShotSimulation.HP_SCALE;}
    public static void resetSession(){chargeCredit=0;swings=hits=0;damageApplied=0;seen.clear();}
    public static void swing(MinecraftServer server,UUID owner,long worldId,long source,long model,long tick,int node,Vec3d eye,Vec3d forward,Vec3d right,double nativeDamage,long wallMs){
        long now=System.currentTimeMillis();var p=server.getPlayerManager().getPlayer(owner);
        if(p==null||!p.isAlive()||NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())!=worldId||now-wallMs>200||wallMs>now+50||p.getEyePos().squaredDistanceTo(eye)>16||source==0||tick<=0||(node!=57&&node!=58)||nativeDamage!=120
            ||!NativeEliminationRuntime.sessionMatches(owner,worldId,0x02e0000000000029L,model,source))return;
        String key=source+":"+model+":"+node+":"+tick;if(!seen.add(key))return;if(seen.size()>4096)seen.remove(seen.iterator().next());swings++;
        var world=p.getServerWorld();
        // Measured original TrackTargets: local (-2,1.5,4) -> (2,1.5,4), radius 1.
        // Eye-relative vertical alignment follows the same mapping as shuriken.
        var center=eye.add(forward.multiply(4));var a=center.subtract(right.multiply(2));var b=center.add(right.multiply(2));
        var victims=new java.util.HashSet<java.util.UUID>();
        // Sweep back to the player's near plane too. A strip only at the
        // far4m tracking line leaves a dead zone against MC's smaller bodies.
        // Keep the original far/side/radius bounds and the real wall raycast.
        var near=eye.add(forward.multiply(.25));
        var sweep=new Box(a,b).union(new Box(near.subtract(right.multiply(2)),near.add(right.multiply(2)))).expand(1);
        // Narrow phase expands each target by1. Its broad-phase query must
        // expand by the SAME amount, otherwise near targets are discarded
        // before their expanded bounds can intersect the original sword sweep.
        for(var entity:NativeDamageTargets.in(world,p,sweep.expand(1))){
            // Box.raycast returns empty when the segment begins inside an
            // expanded target volume. Use the swept AABB intersection so a
            // nearby target is hit consistently with a farther target.
            if(!entity.getBoundingBox().expand(1).intersects(sweep))continue;
            var target=entity.getBoundingBox().getCenter();var wall=world.raycast(new RaycastContext(eye,target,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
            if(target.subtract(eye).dotProduct(forward)<0&&!entity.getBoundingBox().contains(eye))continue;
            if(wall.getType()!=HitResult.Type.MISS&&eye.squaredDistanceTo(wall.getPos())+1e-5<eye.squaredDistanceTo(target))continue;
            if(!victims.add(NativeDamageTargets.owner(entity).getUuid()))continue;
            var result=NativeDamageTargets.meleeDamage(world,entity,p,nativeDamage*NativeShotSimulation.HP_SCALE);
            if(result.applied()){hits++;damageApplied+=result.healthLost();}
        }
    }
}
