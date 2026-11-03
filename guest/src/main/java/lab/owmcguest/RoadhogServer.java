package lab.owmcguest;

import com.google.gson.JsonObject;
import java.util.*;
import net.minecraft.entity.Entity;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.MovementType;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.RaycastContext;

/** Offline 24919 Roadhog, HERO-BRIEFS-NEW8-20261025 §5.
 * Native factories supply every pellet and its direction; node37 is ONE Q stream.
 * Declarations: pellet9/80m/s/5s, secondary parent50/60m/s/.15s, Q pellet7/range100,
 * Take a Breather amount300. All HP conversion uses HP_SCALE.
 * MC adaptation values: straight flight (gravity NOT declared), eye-origin mapping,
 * no falloff/headshot bonus, Q ray collision (speed/lifetime unknown), knockback .12,
 * hook40m/s/range20/radius.3, pull1m/tick/stop2m/timeout20ticks, no hook damage
 * (ModifyHealth21 never observed); healing budget300 over30 MC ticks, capped by End.
 * Secondary splitting is deliberately absent: no child factory was authenticated.
 * Diagnostic factory snapshots are bounded/lossy; no claim of complete production transport.
 */
public final class RoadhogServer implements HeroServerModule {
    private static final com.google.gson.Gson EVIDENCE_JSON=new com.google.gson.Gson();
    public static final RoadhogServer INSTANCE=new RoadhogServer();
    public static final long HERO=0x02e0000000000040L;
    static final long SCRAP=0x040000000000029aL,SECONDARY=0x0400000000000295L,WHOLE_HOG=0x0400000000000405L;
    public record Scope(UUID owner,long world,long source,long model){}
    public record Sample(long hookCast,long hookSearch,long heal,long wholeHog){}
    public record Pellet(String identity,String volley,long resource,Vec3d direction,long wall){}
    public record View(long world,long source,long model,long wall,long resource,Vec3d at,Vec3d direction){}
    private static final class Flight {Vec3d at,velocity;long resource;double distance;int age;}
    private static final class Hook {Vec3d at,direction;UUID target;int age;double distance;}
    private final List<Flight> flights=new ArrayList<>();
    private final Set<String> seen=new HashSet<>(),volleys=new HashSet<>();
    private final Map<String,Long> factoryResources=new TreeMap<>();
    private Map<String,TanksNodeEvidence.Node> candidateEvidence=Map.of();
    /** Read-only candidate counters. No observed candidate authorizes an effect. */
    public void observeCandidates(Scope expected,long wall,Map<String,TanksNodeEvidence.Node> nodes){
        long age=System.currentTimeMillis()-wall;
        if(expected!=null&&expected.equals(scope)&&age>=-50&&age<=150){candidateEvidence=Map.copyOf(nodes);publish();}
    }
    private Scope scope;private Sample phases=new Sample(0,0,0,0);private Hook hook;
    private long lease,casts,primaryCasts,secondaryCasts,hookCasts,hookSearches,hookHits,pullTicks,hookBlocked,
        healCasts,qCasts,pellets,qPellets,hits,blockHits,expired,rejected,streamGaps;
    private double healBudget,healingApplied,damageApplied;private float ownerHealth;
    private volatile String json="{}";public volatile List<View> views=List.of();
    private RoadhogServer(){publish();}
    @Override public String statusKey(){return "roadhog";}
    @Override public String status(){return json;}
    private static boolean fresh(long wall){long age=System.currentTimeMillis()-wall;return age>=-50&&age<=150;}
    private static ServerPlayerEntity player(MinecraftServer server,Scope s){
        var p=s==null?null:server.getPlayerManager().getPlayer(s.owner());
        return p!=null&&p.isAlive()&&NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())==s.world()?p:null;
    }
    private void retire(){candidateEvidence=Map.of();flights.clear();hook=null;healBudget=0;phases=new Sample(0,0,0,0);views=List.of();}
    public void refresh(MinecraftServer server,Scope s,long wall,Sample next){
        if(!fresh(wall)||player(server,s)==null){rejected++;return;}
        if(!s.equals(scope)||!fresh(lease)){retire();seen.clear();volleys.clear();factoryResources.clear();scope=s;}
        lease=wall;ownerHealth=player(server,s).getHealth();
        if(next.hookCast()>0&&next.hookCast()!=phases.hookCast()){hookCasts++;casts++;hook=null;}
        if(next.hookSearch()>0&&next.hookSearch()!=phases.hookSearch()&&next.hookCast()>0){
            hookSearches++;var p=player(server,s);hook=new Hook();hook.at=p.getEyePos();hook.direction=p.getRotationVec(1).normalize();
        }
        if(next.hookCast()==0)hook=null;
        if(next.heal()>0&&next.heal()!=phases.heal()){healCasts++;casts++;healBudget=300*NativeShotSimulation.HP_SCALE;}
        if(next.heal()==0)healBudget=0;
        if(next.wholeHog()>0&&next.wholeHog()!=phases.wholeHog()){qCasts++;casts++;}
        phases=next;publish();
    }
    public void gap(Scope s){if(s.equals(scope)){streamGaps++;publish();}}
    public void observeResources(Scope expected,long wall,Map<Long,Long> resources){
        if(!expected.equals(scope)||!fresh(wall)||!fresh(lease))return;
        resources.forEach((resource,count)->{if(count>0&&count<=256)factoryResources.merge(String.format("%016x",resource),count,Long::sum);});
        publish();
    }
    public void suspend(Scope s){if(s.equals(scope)){lease=0;retire();publish();}}
    public void pellets(MinecraftServer server,Scope s,List<Pellet> rows){
        var p=player(server,s);if(p==null||!s.equals(scope)||!fresh(lease)){rejected+=rows.size();publish();return;}
        for(var row:rows){
            if(!fresh(row.wall())||row.direction()==null||!finite(row.direction())||Math.abs(row.direction().lengthSquared()-1)>.02
                    ||row.resource()!=SCRAP&&row.resource()!=SECONDARY&&row.resource()!=WHOLE_HOG){rejected++;continue;}
            if(row.resource()==WHOLE_HOG&&phases.wholeHog()==0){rejected++;continue;}
            if(seen.size()>=65536){rejected++;continue;}
            if(!seen.add(row.identity()))continue;
            if(volleys.add(row.volley())&&row.resource()!=WHOLE_HOG){casts++;if(row.resource()==SCRAP)primaryCasts++;else secondaryCasts++;}
            pellets++;
            if(row.resource()==WHOLE_HOG){qPellets++;trace(p,p.getEyePos(),p.getEyePos().add(row.direction().multiply(100)),7,true);continue;}
            if(flights.size()>=1024){rejected++;continue;}
            var f=new Flight();f.resource=row.resource();f.at=p.getEyePos();f.velocity=row.direction().multiply((row.resource()==SCRAP?80:60)/20.0);flights.add(f);
        }
        publish();
    }
    private static boolean finite(Vec3d v){return Double.isFinite(v.x)&&Double.isFinite(v.y)&&Double.isFinite(v.z);}
    private record Contact(Entity entity,Vec3d at,boolean blocked){}
    private static Contact contact(ServerPlayerEntity p,Vec3d from,Vec3d to,double radius){
        var w=p.getServerWorld();
        var clip=LoadedRayPrefix.clip(new NativeShotProtocol.Vec(from.x,from.y,from.z),new NativeShotProtocol.Vec(to.x,to.y,to.z),
            (x,z)->w.isChunkLoaded(new net.minecraft.util.math.BlockPos(x<<4,0,z<<4)));
        to=from.lerp(to,clip.fraction());
        var wall=w.raycast(new RaycastContext(from,to,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
        boolean blocked=wall.getType()==HitResult.Type.BLOCK;Vec3d end=blocked?wall.getPos():to;
        Entity best=null;double nearest=from.squaredDistanceTo(end);Vec3d at=end;
        for(var e:NativeDamageTargets.in(w,p,new Box(from,end).expand(radius))){
            if(e instanceof PlayerEntity)continue;
            var b=e.getBoundingBox().expand(radius);var hit=b.contains(from)?Optional.of(from):b.raycast(from,end);
            if(hit.isPresent()&&from.squaredDistanceTo(hit.get())<nearest){nearest=from.squaredDistanceTo(hit.get());best=e;at=hit.get();}
        }
        return best!=null?new Contact(best,at,false):blocked||!clip.complete()?new Contact(null,end,true):null;
    }
    private Contact trace(ServerPlayerEntity p,Vec3d from,Vec3d to,double damage,boolean push){
        var hit=contact(p,from,to,.01);if(hit==null)return null;
        if(hit.blocked()){blockHits++;return hit;}
        var r=NativeDamageTargets.projectileDamage(p.getServerWorld(),hit.entity(),p,damage*NativeShotSimulation.HP_SCALE);
        if(r.applied()){hits++;damageApplied+=r.healthLost();}
        if(push&&r.applied()){hit.entity().addVelocity(to.subtract(from).normalize().multiply(.12));hit.entity().velocityModified=true;}
        return hit;
    }
    @Override public void tick(MinecraftServer server){
        var p=player(server,scope);
        if(p==null||!fresh(lease)){retire();publish();return;}
        if(phases.heal()>0&&healBudget>0){double n=Math.min(healBudget,300*NativeShotSimulation.HP_SCALE/30);float before=p.getHealth();p.heal((float)n);healingApplied+=Math.max(0,p.getHealth()-before);healBudget-=n;}
        for(var it=flights.iterator();it.hasNext();){var f=it.next();double life=f.resource==SCRAP?5:.150000006;
            var step=f.velocity.multiply(Math.min(1,Math.max(0,life*20-f.age)));double length=Math.min(step.length(),100-f.distance);
            var end=f.at.add(step.normalize().multiply(length));var hit=trace(p,f.at,end,f.resource==SCRAP?9:50,false);
            f.at=hit==null?end:hit.at();f.distance+=length;f.age++;
            if(hit!=null||f.age>=life*20-1e-5||f.distance>=100){if(hit==null)expired++;it.remove();}
        }
        ownerHealth=p.getHealth();tickHook(p);publish();
    }
    private void tickHook(ServerPlayerEntity p){
        if(hook==null)return;var h=hook;h.age++;if(h.age>20){hook=null;return;}
        if(h.target==null){
            if(phases.hookSearch()==0||h.distance>=20){hook=null;return;}
            var end=h.at.add(h.direction.multiply(Math.min(2,20-h.distance)));var hit=contact(p,h.at,end,.3);
            if(hit==null){h.distance+=h.at.distanceTo(end);h.at=end;return;}
            h.at=hit.at();if(hit.blocked()){hookBlocked++;hook=null;return;}
            if(!(hit.entity() instanceof LivingEntity)||hit.entity() instanceof PlayerEntity){hook=null;return;}
            h.target=hit.entity().getUuid();hookHits++;
        }
        var e=p.getServerWorld().getEntity(h.target);
        if(e==null||!e.isAlive()||e.getWorld()!=p.getWorld()||e.squaredDistanceTo(p)>24*24){hook=null;return;}
        var delta=p.getPos().subtract(e.getPos());double distance=delta.length();
        if(distance<=2){hook=null;return;}
        var move=delta.normalize().multiply(Math.min(1,distance-2));
        var before=e.getPos();var dest=before.add(move);
        if(!p.getServerWorld().isChunkLoaded(net.minecraft.util.math.BlockPos.ofFloored(dest))){hookBlocked++;hook=null;return;}
        e.setVelocity(Vec3d.ZERO);e.move(MovementType.SELF,move);e.velocityModified=true;pullTicks++;
        h.at=e.getBoundingBox().getCenter();if(e.getPos().squaredDistanceTo(before)<1e-6){hookBlocked++;hook=null;}
    }
    private void publish(){
        var v=new ArrayList<View>();if(scope!=null)for(var f:flights)v.add(new View(scope.world(),scope.source(),scope.model(),System.currentTimeMillis(),f.resource,f.at,f.velocity.normalize()));views=List.copyOf(v);
        var o=new JsonObject();o.add("nativeCandidates",EVIDENCE_JSON.toJsonTree(candidateEvidence));
        o.addProperty("candidateEffectsEnabled",false);
        o.addProperty("casts",casts);o.addProperty("primaryCasts",primaryCasts);o.addProperty("secondaryCasts",secondaryCasts);
        o.addProperty("hookCasts",hookCasts);o.addProperty("hookSearches",hookSearches);o.addProperty("hookHits",hookHits);o.addProperty("pullTicks",pullTicks);o.addProperty("hookBlocked",hookBlocked);
        o.addProperty("healCasts",healCasts);o.addProperty("healingApplied",healingApplied);o.addProperty("ownerHealth",ownerHealth);o.addProperty("qCasts",qCasts);o.addProperty("qActive",phases.wholeHog()>0);
        o.addProperty("pellets",pellets);o.addProperty("qPellets",qPellets);o.addProperty("hits",hits);o.addProperty("damageApplied",damageApplied);o.addProperty("blockHits",blockHits);
        o.addProperty("expired",expired);o.addProperty("rejected",rejected);o.addProperty("streamGaps",streamGaps);o.addProperty("bodies",flights.size());o.addProperty("hookActive",hook!=null);
        o.addProperty("healActive",phases.heal()>0);o.addProperty("hookDamageEnabled",false);o.addProperty("secondarySplitEnabled",false);
        o.add("factoryResources",EVIDENCE_JSON.toJsonTree(factoryResources));
        o.addProperty("unmappedFactoryRows",factoryResources.entrySet().stream().filter(e->!Set.of("040000000000029a","0400000000000295","0400000000000405").contains(e.getKey())).mapToLong(Map.Entry::getValue).sum());
        o.addProperty("factoryTransport","existing emission16 factoryCalibration snapshots; bounded, no gap reconstruction");
        o.addProperty("mcAdaptation","eye origin, straight flight, Q rays/knockback, hook collision/pull, healing budget; no authenticated gravity");
        o.addProperty("unsupported","secondary split: no child factory; hook damage: node21 not entered; passive: no calibrated event");
        
        // integrator/models: presentation of accepted state only; preserve its real lease.
if(scope!=null&&hook!=null){
    var f=OriginalEffectFrames.frame(scope.owner(),scope.world(),scope.source(),scope.model(),lease);
    var e=OriginalEffectFrames.body(f,"roadhog-hook",hook.at,new Vec3d(.5,.5,.5),1,false);
    e.add("direction",OriginalEffectFrames.vec(hook.direction));
    o.add("models",f);
}
        json=o.toString();
    }
    @Override public void resetSession(){lease=0;scope=null;seen.clear();volleys.clear();retire();publish();}
}
