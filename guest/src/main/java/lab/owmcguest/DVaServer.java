package lab.owmcguest;

import com.google.gson.JsonObject;
import java.util.*;
import net.minecraft.entity.Entity;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.RaycastContext;

/** Offline 24919 D.Va PILOT only, HERO-BRIEFS-NEW8-20261025 §8.
 * Native02b8:12 B/E is a channel, factories are individual shots: damage14, speed50,
 * lifetime5, range100, entity0400000000001000. MC adaptation: eye origin and
 * straight flight (gravity undeclared), collision and HP_SCALE conversion.
 * No timer/key-derived bullets. 026a:41 is only an unresolved call-mech attempt.
 * Mech guns/boosters/matrix/self-destruct/ejection are unavailable without actual
 * mech-form creation/model/ability evidence; pilot Shift/E produced no new nodes.
 */
public final class DVaServer implements HeroServerModule {
    private static final com.google.gson.Gson EVIDENCE_JSON=new com.google.gson.Gson();
    public static final DVaServer INSTANCE=new DVaServer();
    public static final long HERO=0x02e000000000007aL;
    static final long PISTOL=0x0400000000001000L;
    public record Scope(UUID owner,long world,long source,long model){}
    public record Pellet(String identity,Vec3d direction,long wall){}
    public record View(long world,long source,long model,long wall,Vec3d at,Vec3d direction){}
    private static final class Flight {Vec3d at,velocity;int age;double distance;}
    private final List<Flight> flights=new ArrayList<>();private final Set<String> seen=new HashSet<>();
    private Map<String,TanksNodeEvidence.Node> candidateEvidence=Map.of();
    /** Read-only candidate counters. No observed candidate authorizes an effect. */
    public void observeCandidates(Scope expected,long wall,Map<String,TanksNodeEvidence.Node> nodes){
        long age=System.currentTimeMillis()-wall;
        if(expected!=null&&expected.equals(scope)&&age>=-50&&age<=150){candidateEvidence=Map.copyOf(nodes);publish();}
    }
    private Scope scope;private long lease,channel,callMech,casts,channels,callMechAttempts,shots,hits,blockHits,expired,rejected,streamGaps;
    private double damageApplied;private volatile String json="{}";public volatile List<View> views=List.of();
    private long nativeHero,nativeModel,identityChanges;
    private DVaServer(){publish();}
    @Override public String statusKey(){return "dva";}
    @Override public String status(){return json;}
    private static boolean fresh(long wall){long age=System.currentTimeMillis()-wall;return age>=-50&&age<=150;}
    private static ServerPlayerEntity player(MinecraftServer server,Scope s){var p=s==null?null:server.getPlayerManager().getPlayer(s.owner());return p!=null&&p.isAlive()&&NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())==s.world()?p:null;}
    private void retire(){candidateEvidence=Map.of();flights.clear();channel=callMech=0;views=List.of();}
    public void refresh(MinecraftServer server,Scope s,long wall,long firing,long attempt){
        if(!fresh(wall)||player(server,s)==null){rejected++;return;}
        if(!s.equals(scope)||!fresh(lease)){retire();seen.clear();scope=s;nativeHero=HERO;nativeModel=s.model();}
        lease=wall;if(firing>0&&firing!=channel){channels++;casts++;}if(attempt>0&&attempt!=callMech)callMechAttempts++;
        channel=firing;callMech=attempt;publish();
    }
    public void suspend(Scope s){if(s.equals(scope)){lease=0;retire();publish();}}
    /** A changed identity is evidence to rebind, not a mech-form grant. The
     * controller hero GUID and model entity ID are distinct native identities. */
    public void observeIdentity(MinecraftServer server,Scope expected,long wall,long hero,long model){
        if(!expected.equals(scope)||player(server,expected)==null||!fresh(wall)||!fresh(lease)||hero==0||model==0)return;
        if(nativeHero!=0&&(nativeHero!=hero||nativeModel!=model))identityChanges++;
        nativeHero=hero;nativeModel=model;publish();
    }
    public void gap(Scope s){if(s.equals(scope)){streamGaps++;publish();}}
    public void pellets(MinecraftServer server,Scope s,List<Pellet> rows){
        var p=player(server,s);if(p==null||!s.equals(scope)||!fresh(lease)||channel==0){rejected+=rows.size();publish();return;}
        for(var row:rows){var d=row.direction();
            if(!fresh(row.wall())||d==null||!Double.isFinite(d.x)||!Double.isFinite(d.y)||!Double.isFinite(d.z)||Math.abs(d.lengthSquared()-1)>.02||seen.size()>=65536){rejected++;continue;}
            if(!seen.add(row.identity()))continue;
            if(flights.size()>=512){rejected++;continue;}
            var f=new Flight();f.at=p.getEyePos();f.velocity=d.multiply(50/20.0);flights.add(f);shots++;
        }publish();
    }
    @Override public void tick(MinecraftServer server){
        var p=player(server,scope);if(p==null||!fresh(lease)){retire();publish();return;}var w=p.getServerWorld();
        for(var it=flights.iterator();it.hasNext();){var f=it.next();var end=f.at.add(f.velocity.multiply(Math.min(1,(100-f.distance)/f.velocity.length())));
            var clip=LoadedRayPrefix.clip(new NativeShotProtocol.Vec(f.at.x,f.at.y,f.at.z),new NativeShotProtocol.Vec(end.x,end.y,end.z),
                (x,z)->w.isChunkLoaded(new net.minecraft.util.math.BlockPos(x<<4,0,z<<4)));end=f.at.lerp(end,clip.fraction());
            var wall=w.raycast(new RaycastContext(f.at,end,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
            boolean blocked=wall.getType()==HitResult.Type.BLOCK;Vec3d stop=blocked?wall.getPos():end;
            Entity target=null;double nearest=f.at.squaredDistanceTo(stop);Vec3d at=stop;
            for(var e:NativeDamageTargets.in(w,p,new Box(f.at,stop).expand(.01))){
                if(e instanceof PlayerEntity)continue;var b=e.getBoundingBox();var hit=b.contains(f.at)?Optional.of(f.at):b.raycast(f.at,stop);
                if(hit.isPresent()&&f.at.squaredDistanceTo(hit.get())<nearest){nearest=f.at.squaredDistanceTo(hit.get());target=e;at=hit.get();}
            }
            f.distance+=f.at.distanceTo(at);f.at=at;f.age++;
            if(target!=null){it.remove();var r=NativeDamageTargets.projectileDamage(w,target,p,14*NativeShotSimulation.HP_SCALE);if(r.applied()){hits++;damageApplied+=r.healthLost();}}
            else if(blocked||!clip.complete()){blockHits++;it.remove();}
            else if(f.age>=100||f.distance>=100){expired++;it.remove();}
        }publish();
    }
    private void publish(){
        var v=new ArrayList<View>();if(scope!=null)for(var f:flights)v.add(new View(scope.world(),scope.source(),scope.model(),System.currentTimeMillis(),f.at,f.velocity.normalize()));views=List.copyOf(v);
        var o=new JsonObject();o.add("nativeCandidates",EVIDENCE_JSON.toJsonTree(candidateEvidence));
        o.addProperty("candidateEffectsEnabled",false);
        o.addProperty("form","pilot-evidence-only");o.addProperty("casts",casts);o.addProperty("channels",channels);o.addProperty("firing",channel>0);
        o.addProperty("callMechAttempts",callMechAttempts);o.addProperty("shots",shots);o.addProperty("hits",hits);o.addProperty("damageApplied",damageApplied);o.addProperty("blockHits",blockHits);
        o.addProperty("expired",expired);o.addProperty("rejected",rejected);o.addProperty("streamGaps",streamGaps);o.addProperty("bodies",flights.size());
        o.addProperty("nativeHero",Long.toUnsignedString(nativeHero));o.addProperty("nativeModel",Long.toUnsignedString(nativeModel));
        o.addProperty("identityChanges",identityChanges);o.addProperty("identityChangeProvesMech",false);
        o.addProperty("mechCreated",false);o.addProperty("mechWeaponsEnabled",false);o.addProperty("boostersEnabled",false);o.addProperty("defenseMatrixEnabled",false);o.addProperty("selfDestructEnabled",false);o.addProperty("microMissilesEnabled",false);
        o.addProperty("unsupported","mech weapons/boosters/matrix/self-destruct/ejection: no mech-form commit or calibrated event; pilot Shift/E unchanged; Q41 unresolved precursor only");
        o.addProperty("factoryTransport","existing emission16 factoryCalibration snapshots; bounded, no gap reconstruction");o.addProperty("mcAdaptation","eye origin, straight flight (gravity undeclared), server collision and HP conversion");json=o.toString();
    }
    @Override public void resetSession(){lease=0;scope=null;seen.clear();retire();publish();}
}
