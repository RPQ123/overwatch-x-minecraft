package lab.owmcguest;

import java.util.HashSet;
import java.util.UUID;
import com.google.gson.JsonObject;
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

/** MC movement and collision determine the traversed damage volume. */
public final class NativeDashRuntime {
    private static UUID owner;
    private static long worldId,source,model,nativeTick,started,deadline,begins,hits;
    private static Vec3d previous;
    private static double amount,distance,applied;
    private static final HashSet<UUID> hit=new HashSet<>();
    public static volatile String status="{}";
    public static void begin(MinecraftServer server,UUID player,long world,long origin,long heroModel,long tick,double nativeAmount){
        var p=server.getPlayerManager().getPlayer(player);
        if(p==null||!p.isAlive()||NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())!=world||!Double.isFinite(nativeAmount)||nativeAmount<=0||nativeAmount>10000)return;
        if(source==origin&&model==heroModel&&tick<=nativeTick)return;
        owner=player;worldId=world;source=origin;model=heroModel;nativeTick=tick;amount=nativeAmount*.1;previous=p.getPos();hit.clear();begins++;started=System.currentTimeMillis();deadline=started+150;
    }
    public static void refresh(UUID player,long origin,long heroModel,long tick,boolean active){
        if(owner==null||!owner.equals(player)||source!=origin||model!=heroModel||tick!=nativeTick)return;
        long until=System.currentTimeMillis()+(active?150:50);
        deadline=active?Math.min(started+750,until):Math.min(deadline,until);
    }
    public static void tick(MinecraftServer server){
        long now=System.currentTimeMillis();var p=owner==null?null:server.getPlayerManager().getPlayer(owner);
        boolean active=p!=null&&p.isAlive()&&now<=deadline&&NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())==worldId;
        JsonObject models=null;
        if(active){
            var world=p.getServerWorld();var current=p.getPos();
            if(previous!=null&&current.squaredDistanceTo(previous)>1e-8&&current.squaredDistanceTo(previous)<=64){
                var a=previous.add(0,.9,0);var b=current.add(0,.9,0);distance+=previous.distanceTo(current);
                GenjiCombatParticles.dash(world,a,b);
                models=OriginalEffectFrames.frame(owner,worldId,source,model,now);
                OriginalEffectFrames.beam(models,"genji-dash-wind",a,b,.45f,.6f);
                for(var e:NativeDamageTargets.in(world,p,new Box(a,b).expand(1.2))){
                    var victimId=NativeDamageTargets.owner(e).getUuid();if(hit.contains(victimId))continue;
                    var box=e.getBoundingBox().expand(.6);var contact=box.contains(a)?java.util.Optional.of(a):box.raycast(a,b);if(contact.isEmpty())continue;
                    var obstruction=world.raycast(new RaycastContext(a,contact.get(),RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
                    if(obstruction.getType()!=HitResult.Type.MISS&&a.squaredDistanceTo(obstruction.getPos())+1e-5<a.squaredDistanceTo(contact.get()))continue;
                    hit.add(victimId);var result=NativeDamageTargets.meleeDamage(world,e,p,amount);if(result.applied()){hits++;applied+=result.healthLost();NativeUltimateRuntime.credit(result.healthLost());}
                }
            }previous=current;
        }else previous=null;
        var out=new JsonObject();out.addProperty("begins",begins);out.addProperty("nativeTick",nativeTick);out.addProperty("active",active);out.addProperty("distance",distance);out.addProperty("entityHits",hits);out.addProperty("damageApplied",applied);out.addProperty("damagePerTarget",amount);if(models!=null)out.add("models",models);status=out.toString();
    }
    public static void close(){owner=null;previous=null;hit.clear();source=0;nativeTick=0;}
    public static void resetSession(){owner=null;worldId=0;source=0;model=0;nativeTick=0;started=0;deadline=0;previous=null;hit.clear();amount=distance=applied=0;begins=hits=0;status="{}";}
}
