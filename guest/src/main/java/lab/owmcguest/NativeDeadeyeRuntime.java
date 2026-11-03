package lab.owmcguest;

import java.util.*;
import com.google.gson.JsonObject;
import net.minecraft.server.MinecraftServer;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.math.*;
import net.minecraft.world.RaycastContext;

/** MC target service for the native beta Deadeye activation and confirmed fire action. */
public final class NativeDeadeyeRuntime {
    public static final long HERO=0x02e0000000000042L;
    public static final int MAX_TARGETS=64;
    public record Frame(UUID owner,long world,long source,long model,long begin,long wall,boolean active,boolean tracking,boolean fire,double radius,double angle,double rate,double cap,double duration,Vec3d eye,Vec3d forward){}
    private record Lock(int id,Vec3d point,double damage){}
    public record Marker(Vec3d point,double fraction){}
    public record View(UUID owner,long world,long source,long model,long wall,List<Marker> markers){}
    public static volatile View view;
    public record Completion(UUID owner,long world,long source,long model,long begin,long wall){}
    public static volatile Completion completion;
    public record Presentation(UUID owner,long world,long source,long model,long begin,long sequence,int ordinal){}
    public static volatile Presentation presentation;
    public static volatile long presentationAcknowledged;
    public record Receipt(long source,long world,long model,long begin,long sequence,int ordinal,int phase,long wall,long nativeTick){}
    public record ShotCue(UUID owner,long source,long world,long model,long begin,long sequence,int ordinal,long wall,long nativeTick){}
    private static final java.util.concurrent.ArrayBlockingQueue<ShotCue> shotCues=new java.util.concurrent.ArrayBlockingQueue<>(16);
    public static ShotCue pollShotCue(){return shotCues.poll();}
    private static final List<Lock> volley=new ArrayList<>();private static int nextShot;private static long sequence;private static boolean shotApplied;
    private static final com.google.gson.JsonArray shotReceipts=new com.google.gson.JsonArray();
    private static Frame frame;private static long activation,model,world,source,lastTick=-1,startedWall;
    private static boolean fired,pendingFire;private static final Map<UUID,Lock> locks=new LinkedHashMap<>();
    public static long activations,shots,hits,staleHolds;public static double healthLost;
    private static String cancelReason="";
    public static volatile String status="{}";
    public static void refresh(Frame f){
        long now=System.currentTimeMillis();
        if(f==null||now-f.wall()>150||f.wall()>now+50||!NativeEliminationRuntime.sessionMatches(f.owner(),f.world(),HERO,f.model(),f.source()))return;
        if(f.source()!=source||f.model()!=model||f.world()!=world||f.begin()!=activation){
            locks.clear();volley.clear();presentation=null;presentationAcknowledged=0;shotApplied=false;nextShot=0;activation=f.begin();source=f.source();model=f.model();world=f.world();fired=pendingFire=false;lastTick=-1;startedWall=now;
            if(f.active())activations++;
        }
        pendingFire|=f.fire();frame=f;
    }
    public static void tick(MinecraftServer server){
        var f=frame;long now=System.currentTimeMillis();var p=f==null?null:server.getPlayerManager().getPlayer(f.owner());
        boolean identity=f!=null&&f.active()&&p!=null&&p.isAlive()
            &&NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())==f.world()
            &&NativeEliminationRuntime.sessionMatches(f.owner(),f.world(),HERO,f.model(),f.source())&&now-startedWall<=(long)((f.duration()+1)*1000);
        // Preserve an admitted sequence across a bounded reader/client hitch.
        // No targeting, damage, receipt admission or charge accrues on stale
        // frames. Actual cancellation/world/model/death changes clear at once.
        if(identity&&now-f.wall()>150&&now-f.wall()<=1000){staleHolds++;view=null;lastTick=-1;publish(false);return;}
        boolean valid=identity&&now-f.wall()<=150&&now>=f.wall()-50;
        if(!valid){cancelReason=!identity?"inactive-or-owner-change":"frame-deadline";locks.clear();volley.clear();presentation=null;view=null;lastTick=-1;publish(false);return;}
        cancelReason="";
        long tick=Integer.toUnsignedLong(server.getTicks());double dt=lastTick<0||tick!=lastTick+1?0:.05;lastTick=tick;
        var w=p.getServerWorld();var fresh=new LinkedHashMap<UUID,Lock>();
        if(f.tracking()&&!fired){
            for(var entity:NativeDamageTargets.in(w,p,new Box(f.eye(),f.eye()).expand(f.radius()))){
                if(!w.isChunkLoaded(entity.getBlockPos()))continue;
                var target=entity.getBoundingBox().getCenter();var delta=target.subtract(f.eye());double distance=delta.length();
                if(distance<1e-6||distance>f.radius()||delta.dotProduct(f.forward())/distance<Math.cos(Math.toRadians(f.angle()/2)))continue;
                var wallHit=w.raycast(new RaycastContext(f.eye(),target,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
                if(wallHit.getType()!=HitResult.Type.MISS&&f.eye().squaredDistanceTo(wallHit.getPos())+1e-5<delta.lengthSquared())continue;
                var owner=NativeDamageTargets.owner(entity);var old=locks.get(owner.getUuid());
                double damage=Math.min(f.cap(),(old==null?0:old.damage())+f.rate()*dt);
                fresh.putIfAbsent(owner.getUuid(),new Lock(entity.getId(),target,damage));if(fresh.size()>=MAX_TARGETS)break;
            }
        }
        locks.clear();locks.putAll(fresh);
        if(pendingFire&&!fired){
            fired=true;pendingFire=false;
            volley.clear();volley.addAll(locks.values());nextShot=0;shotApplied=false;
            locks.clear();requestNext(f,now);
        }
        var markers=new ArrayList<Marker>();
        for(var lock:locks.values()){
            var part=NativeDamageTargets.resolve(w,lock.id());if(part==null)continue;var entity=NativeDamageTargets.owner(part);
            double hp=entity instanceof net.minecraft.entity.LivingEntity living?living.getHealth():1;
            // The marker belongs on the visible surface. At the box center,
            // depth testing hid a correctly drawn marker inside the mob.
            var surface=entity.getBoundingBox().raycast(f.eye(),lock.point()).orElse(lock.point());
            var towardEye=f.eye().subtract(surface).normalize();
            double predicted=NativeDamageTargets.projectileHealthEstimate(w,part,p,lock.damage()*NativeShotSimulation.HP_SCALE);
            markers.add(new Marker(surface.add(towardEye.multiply(.04)),Math.clamp(predicted/Math.max(.1,hp),0,1)));
        }
        view=!fired?new View(f.owner(),f.world(),f.source(),f.model(),now,List.copyOf(markers)):null;publish(true);
    }
    private static void requestNext(Frame f,long now){
        if(nextShot>=volley.size()){presentation=null;completion=new Completion(f.owner(),f.world(),f.source(),f.model(),f.begin(),now);return;}
        presentation=new Presentation(f.owner(),f.world(),f.source(),f.model(),f.begin(),++sequence,nextShot+1);
    }
    /** Only an acknowledged original animation can release one MC shot. */
    public static void receipt(MinecraftServer server,Receipt receipt){
        var request=presentation;var f=frame;long now=System.currentTimeMillis();
        if(request==null||f==null||receipt.sequence()!=request.sequence()||receipt.ordinal()!=request.ordinal()||receipt.model()!=model||receipt.world()!=world||receipt.source()!=source||receipt.begin()!=activation
            ||receipt.wall()>now+50||now-receipt.wall()>150||now-f.wall()>150||!f.active()||!NativeEliminationRuntime.sessionMatches(f.owner(),world,HERO,model,source))return;
        var player=server.getPlayerManager().getPlayer(f.owner());if(player==null||!player.isAlive()||NativeWorldIdentity.of(server,player.getWorld().getRegistryKey())!=world)return;
        if(receipt.phase()==1&&!shotApplied){
            shotApplied=true;presentationAcknowledged=receipt.sequence();shots++;var lock=volley.get(nextShot);var w=player.getServerWorld();var entity=NativeDamageTargets.resolve(w,lock.id());double lost=0;
            if(entity!=null&&entity.isAlive()&&w.isChunkLoaded(entity.getBlockPos())&&lock.damage()>0){
                var eye=player.getEyePos();var target=entity.getBoundingBox().getCenter();
                var obstruction=w.raycast(new RaycastContext(eye,target,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,player));
                if(eye.squaredDistanceTo(target)<=f.radius()*f.radius()&&(obstruction.getType()==HitResult.Type.MISS||eye.squaredDistanceTo(obstruction.getPos())+1e-5>=eye.squaredDistanceTo(target))){
                    var victim=NativeDamageTargets.owner(entity);double before=victim instanceof net.minecraft.entity.LivingEntity living?living.getHealth():0;
                    var result=NativeDamageTargets.projectileDamage(w,entity,player,lock.damage()*NativeShotSimulation.HP_SCALE);
                    if(result.applied()){hits++;healthLost+=result.healthLost();lost=result.healthLost();}
                    if(before>0&&result.healthLost()>0&&victim instanceof net.minecraft.entity.LivingEntity living&&living.getHealth()<=0)
                        DeadeyeKillEffects.lethal(w,living,eye);
                }
            }
            var row=new JsonObject();row.addProperty("sequence",receipt.sequence());row.addProperty("ordinal",receipt.ordinal());row.addProperty("entityId",lock.id());row.addProperty("nativeTick",receipt.nativeTick());row.addProperty("serverTick",server.getTicks());row.addProperty("wall",now);row.addProperty("healthLost",lost);shotReceipts.add(row);while(shotReceipts.size()>32)shotReceipts.remove(0);
            shotCues.offer(new ShotCue(f.owner(),source,world,model,activation,receipt.sequence(),receipt.ordinal(),now,receipt.nativeTick()));
            // Queue the next target immediately after this confirmed shot.
            // The original logic owner enforces Wait72's native cadence; only
            // the final shot waits for its natural animation End/recovery.
            if(nextShot+1<volley.size()){nextShot++;shotApplied=false;requestNext(f,now);}
        }else if(receipt.phase()==2&&shotApplied){nextShot++;shotApplied=false;requestNext(f,now);}
        else if(receipt.phase()==3){presentation=null;volley.clear();completion=new Completion(f.owner(),world,source,model,activation,now);}
        publish(true);
    }
    private static void publish(boolean active){var o=new JsonObject();o.addProperty("active",active);o.addProperty("activation",activation);o.addProperty("fired",fired);o.addProperty("locks",locks.size());o.addProperty("readyLocks",view==null?0:view.markers().stream().filter(m->m.fraction()>=1).count());o.addProperty("maxTargets",MAX_TARGETS);o.addProperty("volleySize",volley.size());o.addProperty("activations",activations);o.addProperty("shots",shots);o.addProperty("hits",hits);o.addProperty("healthLost",healthLost);o.addProperty("pendingShots",Math.max(0,volley.size()-nextShot));o.addProperty("staleHolds",staleHolds);o.addProperty("cancelReason",cancelReason);o.add("shotReceipts",shotReceipts.deepCopy());status=o.toString();}
    public static void resetSession(){completion=null;presentation=null;presentationAcknowledged=0;volley.clear();shotCues.clear();shotApplied=false;nextShot=0;frame=null;view=null;locks.clear();activation=model=world=source=startedWall=0;lastTick=-1;fired=pendingFire=false;publish(false);}
}
