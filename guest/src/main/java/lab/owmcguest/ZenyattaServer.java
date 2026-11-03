package lab.owmcguest;

import com.google.gson.JsonObject;
import java.util.*;
import net.minecraft.entity.Entity;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.passive.PassiveEntity;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.RaycastContext;

/** Zenyatta24919: 0164:28 single shot; 0164:32 B/E is ONE release envelope.
 * Secondary orb count/spacing come ONLY from fresh original per-orb factory identities,
 * never a fixed three/five-orb guess or a charge timer. Original speed90/lifetime3/range180,
 * damage45(primary)/35(secondary), motions=[] => gravity0. HP_SCALE=.1.
 * MC 适配: eye-position launch, server collision, .1 m hit margin, head region top25%/2x,
 * maximum64 flights; no original headshot geometry/multiplier was declared.
 * Harmony46/Discord41/Q19 remain attempts. New support paths require an actual fresh
 * health11/Aura6/health17 phase; those were NOT executed in the saved generic2 trace.
 * MC 适配: visible MC ally/30m/.15HP per tick; discord own native damage x1.3;
 * transcendence visible allies/10m/1.5HP per tick. No guessed immunity/shield recovery.
 * Confirmed flights belong to MC: a logger rebaseline/short transport gap closes NEW
 * admissions but does not delete existing flights. Actual owner/world/source/model changes,
 * death, range/lifetime and unloaded chunks still retire them. Serial is a reader baseline,
 * not a new native pawn. Admission retains exact serial and <=150ms freshness checks.
 */
public final class ZenyattaServer implements HeroServerModule {
    public static final ZenyattaServer INSTANCE=new ZenyattaServer();
    public static final long HERO=0x02e0000000000020L;
    public record Scope(UUID owner,long world,long source,long model,long serial){
        boolean sameFlightIdentity(Scope other){return other!=null&&owner.equals(other.owner)
            &&world==other.world&&source==other.source&&model==other.model;}
    }
    public record View(Scope scope,Vec3d at,Vec3d velocity,boolean secondary,long wall){}
    private static final double SPEED=90,RANGE=180,HIT_MARGIN=.1,HEAD_SCALE=2;
    private static final int LIFE=60,MAX_BODIES=64;
    private static final class Orb { Scope scope;Vec3d pos,velocity;boolean secondary;int age;double distance; }
    private final List<Orb> orbs=new ArrayList<>();
    private final Set<String> factories=new HashSet<>();
    private final Map<String,Long> attemptTicks=new HashMap<>();
    record Lease(Scope scope,long wall){
        boolean admits(Scope requested,long now){long age=now-wall;
            return requested!=null&&scope.equals(requested)&&age>=0&&age<=150;}
    }
    private volatile Lease permission;
    private volatile Scope flightAuthority;
    private Scope running;
    private long primaryTick,releaseTick,releaseEndedWall;
    private boolean releasing;
    private long primaryCasts,secondaryCasts,secondaryOrbs,hits,headshots,blockHits,expired,rejections,duplicates;
    private long harmonyAttempts,discordAttempts,transcendenceAttempts;
    private long launched,scopeExpired,lifetimeExpired,rangeExpired,unloadedExpired,damageRejected,readInterruptions;
    private String lastReadInterruption="";
    private double damageApplied;
    private boolean harmonyActive,discordActive,transcendenceActive,transcendenceAura;
    private UUID harmonyTarget,discordTarget;
    private long harmonyCasts,discordCasts,transcendenceCasts,harmonyHealingTicks,transcendenceHealingTicks,discordAmplifiedHits;
    private double healingApplied,harmonyHealingApplied,transcendenceHealingApplied,discordBonusApplied;
    private final Map<String,Long> supportTicks=new HashMap<>();
    public volatile List<View> views=List.of();
    private volatile String json="{}";
    private ZenyattaServer(){publish();}
    public void permit(Scope s,long wall){flightAuthority=s;permission=new Lease(s,wall);}
    public void suspendAdmission(){permission=null;}
    public void revoke(){permission=null;flightAuthority=null;}
    private ServerPlayerEntity owner(MinecraftServer server,Scope s){
        var lease=permission;
        if(lease==null||!lease.admits(s,System.currentTimeMillis())||s.source()<=0||s.model()<=0)return null;
        return mcOwner(server,s);
    }
    private ServerPlayerEntity flightOwner(MinecraftServer server,Scope s){
        return s.sameFlightIdentity(flightAuthority)?mcOwner(server,s):null;
    }
    private static ServerPlayerEntity mcOwner(MinecraftServer server,Scope s){
        var p=server.getPlayerManager().getPlayer(s.owner());
        return p!=null&&p.isAlive()&&NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())==s.world()?p:null;
    }
    private void adopt(Scope s){
        if(!s.equals(running)){
            if(!s.sameFlightIdentity(running)){
                // A genuine native/world identity transition, never just a logger rebaseline.
                scopeExpired+=orbs.size();expired+=orbs.size();orbs.clear();factories.clear();attemptTicks.clear();supportTicks.clear();primaryTick=releaseTick=0;
            }
            stopSupport();releasing=false;releaseEndedWall=0;running=s;
        }
    }
    public void readInterrupted(String reason){
        readInterruptions++;lastReadInterruption=reason.length()>240?reason.substring(0,240):reason;
        stopSupport();releasing=false;releaseEndedWall=0;publish();
    }
    public void stopSupport(Scope s){if(s.equals(running))stopSupport();}
    private void stopSupport(){harmonyActive=discordActive=transcendenceActive=transcendenceAura=false;harmonyTarget=discordTarget=null;}
    /** Attempts never call this method. Every admission is a typed original semantic phase. */
    public void support(MinecraftServer server,Scope s,String kind,long tick,boolean active,long wall){
        var p=owner(server,s);if(p==null||tick<=0||!fresh(wall)){rejections++;return;}adopt(s);
        if(active){if(tick<=supportTicks.getOrDefault(kind,0L))return;supportTicks.put(kind,tick);}
        switch(kind){
            case "harmony" -> {if(active&&!harmonyActive){harmonyCasts++;var target=aimed(p,true);harmonyTarget=target==null?null:target.getUuid();}harmonyActive=active;if(!active)harmonyTarget=null;}
            case "discord" -> {if(active&&!discordActive){discordCasts++;var target=aimed(p,false);discordTarget=target==null?null:target.getUuid();}discordActive=active;if(!active)discordTarget=null;}
            case "transcendence" -> {if(active&&!transcendenceActive)transcendenceCasts++;transcendenceActive=active;}
            case "transcendenceAura" -> transcendenceAura=active;
            default -> throw new IllegalArgumentException("Zenyatta support phase");
        }publish();
    }
    private static boolean friendly(ServerPlayerEntity p,LivingEntity e){return e==p||e instanceof PassiveEntity||p.isTeammate(e);}
    private static boolean visible(ServerPlayerEntity p,LivingEntity e,double range){
        return e.isAlive()&&!e.isSpectator()&&p.getServerWorld().isChunkLoaded(e.getBlockPos())&&p.squaredDistanceTo(e)<=range*range
            &&p.getServerWorld().raycast(new RaycastContext(p.getEyePos(),e.getBoundingBox().getCenter(),RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p)).getType()==HitResult.Type.MISS;
    }
    private static LivingEntity aimed(ServerPlayerEntity p,boolean ally){
        var from=p.getEyePos();var to=from.add(p.getRotationVec(1).multiply(30));LivingEntity best=null;double nearest=Double.POSITIVE_INFINITY;
        for(var e:p.getServerWorld().getEntitiesByClass(LivingEntity.class,new Box(from,to).expand(.35),e->e!=p&&friendly(p,e)==ally)){
            var hit=e.getBoundingBox().expand(.35).raycast(from,to);
            if(hit.isPresent()&&visible(p,e,30)&&from.squaredDistanceTo(hit.get())<nearest){nearest=from.squaredDistanceTo(hit.get());best=e;}
        }return best;
    }
    /** Shared damage adapter may call this on the server thread; own accepted native damage only.
     * Original multiplier was not decoded: x1.3 is explicitly an MC adaptation. */
    public double discordMultiplier(ServerPlayerEntity attacker,Entity victim){
        if(running==null||owner(attacker.getServer(),running)!=attacker||!discordActive||discordTarget==null)return 1;
        var target=NativeDamageTargets.owner(victim);
        if(!(target instanceof LivingEntity living)||!discordTarget.equals(target.getUuid())||!visible(attacker,living,30)||friendly(attacker,living))return 1;
        return 1.3;
    }
    public void discordReceipt(double bonus){if(bonus>0){discordAmplifiedHits++;discordBonusApplied+=bonus;}}
    private void supportTick(MinecraftServer server){
        var p=running==null?null:owner(server,running);if(p==null){stopSupport();return;}
        var entity=harmonyTarget==null?null:p.getServerWorld().getEntity(harmonyTarget);
        if(harmonyActive&&entity instanceof LivingEntity target&&friendly(p,target)&&visible(p,target,30)){
            float before=target.getHealth();target.heal(.15f);double gained=Math.max(0,target.getHealth()-before);
            harmonyHealingApplied+=gained;healingApplied+=gained;if(gained>0)harmonyHealingTicks++;
        }else harmonyTarget=null;
        entity=discordTarget==null?null:p.getServerWorld().getEntity(discordTarget);
        if(!(entity instanceof LivingEntity target)||friendly(p,target)||!visible(p,target,30))discordTarget=null;
        if(transcendenceActive){
            var targets=p.getServerWorld().getEntitiesByClass(LivingEntity.class,p.getBoundingBox().expand(10),e->friendly(p,e));
            for(var target:targets)if(visible(p,target,10)){
                float before=target.getHealth();target.heal(1.5f);double gained=Math.max(0,target.getHealth()-before);
                transcendenceHealingApplied+=gained;healingApplied+=gained;if(gained>0)transcendenceHealingTicks++;
            }
        }
    }
    private static boolean fresh(long wall){long age=System.currentTimeMillis()-wall;return age>=0&&age<=150;}
    public void primary(MinecraftServer server,Scope s,long tick,long wall){
        var p=owner(server,s);if(p==null||tick<=0||!fresh(wall)){rejections++;return;}adopt(s);
        if(tick<=primaryTick){duplicates++;return;}primaryTick=tick;primaryCasts++;
        launch(p,s,false,p.getRotationVec(1));publish();
    }
    public void release(MinecraftServer server,Scope s,long tick,boolean active,long wall){
        if(owner(server,s)==null||tick<=0||!fresh(wall)){rejections++;return;}adopt(s);
        if(active&&tick>releaseTick){releaseTick=tick;secondaryCasts++;releasing=true;releaseEndedWall=0;}
        else if(!active&&releasing){releasing=false;releaseEndedWall=wall;}
        publish();
    }
    public void secondary(MinecraftServer server,Scope s,long release,String factory,Vec3d direction,long wall){
        var p=owner(server,s);long age=System.currentTimeMillis()-wall;
        // A row produced before E can become visible in the same snapshot as E.
        // Accept that actual factory once; never extend emission past the observed E wall.
        if(p==null||!s.equals(running)||release!=releaseTick||(!releasing&&(releaseEndedWall==0||wall>releaseEndedWall))||age<0||age>150
                ||factory==null||factory.length()>180||!Double.isFinite(direction.lengthSquared())
                ||Math.abs(direction.lengthSquared()-1)>.01){rejections++;return;}
        if(factories.contains(factory)){duplicates++;return;}
        if(factories.size()>=4096){rejections++;return;} // fail closed; never evict and replay an identity
        factories.add(factory);secondaryOrbs++;launch(p,s,true,direction.normalize());publish();
    }
    public void attempt(MinecraftServer server,Scope s,String kind,long tick,long wall){
        if(owner(server,s)==null||tick<=0||!fresh(wall)){rejections++;return;}adopt(s);
        if(tick<=attemptTicks.getOrDefault(kind,0L))return;attemptTicks.put(kind,tick);
        switch(kind){case "harmony"->harmonyAttempts++;case "discord"->discordAttempts++;case "transcendence"->transcendenceAttempts++;
            default->throw new IllegalArgumentException("Zenyatta attempt kind");}publish();
    }
    private void launch(ServerPlayerEntity p,Scope s,boolean secondary,Vec3d direction){
        if(orbs.size()>=MAX_BODIES){rejections++;return;}
        var b=new Orb();b.scope=s;b.secondary=secondary;b.pos=p.getEyePos();b.velocity=direction.multiply(SPEED/20);orbs.add(b);launched++;
    }
    private static NativeShotProtocol.Vec vector(Vec3d v){return new NativeShotProtocol.Vec(v.x,v.y,v.z);}
    @Override public void tick(MinecraftServer server){
        for(var it=orbs.iterator();it.hasNext();){
            var b=it.next();var p=flightOwner(server,b.scope);
            if(p==null){scopeExpired++;expired++;it.remove();continue;}
            if(++b.age>LIFE){lifetimeExpired++;expired++;it.remove();continue;}
            if(b.distance>=RANGE){rangeExpired++;expired++;it.remove();continue;}
            var w=p.getServerWorld();var end=b.pos.add(b.velocity.multiply(Math.min(1,(RANGE-b.distance)/b.velocity.length())));
            var clip=LoadedRayPrefix.clip(vector(b.pos),vector(end),(x,z)->w.isChunkLoaded(new net.minecraft.util.math.BlockPos(x<<4,0,z<<4)));
            if(clip.fraction()==0){unloadedExpired++;expired++;it.remove();continue;}end=b.pos.lerp(end,clip.fraction());
            var wall=w.raycast(new RaycastContext(b.pos,end,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
            double nearest=wall.getType()==HitResult.Type.BLOCK?b.pos.squaredDistanceTo(wall.getPos()):Double.POSITIVE_INFINITY;
            net.minecraft.entity.Entity victim=null;Vec3d impact=null;
            for(var e:NativeDamageTargets.in(w,p,new Box(b.pos,end).expand(HIT_MARGIN))){
                if(p.isTeammate(NativeDamageTargets.owner(e)))continue;
                var box=e.getBoundingBox().expand(HIT_MARGIN);var hit=box.contains(b.pos)?Optional.of(b.pos):box.raycast(b.pos,end);
                if(hit.isPresent()&&b.pos.squaredDistanceTo(hit.get())<nearest){victim=e;impact=hit.get();nearest=b.pos.squaredDistanceTo(impact);}
            }
            if(victim!=null){
                var box=victim.getBoundingBox();boolean head=impact.y>=box.maxY-box.getLengthY()*.25;
                double amount=(b.secondary?35:45)*NativeShotSimulation.HP_SCALE*(head?HEAD_SCALE:1);
                // The shared adapter is deliberately not edited in this parallel round.
                // Until it is integrated, apply the same guarded multiplier to this hero's own orbs here.
                double multiplier=discordMultiplier(p,victim);
                var result=NativeDamageTargets.projectileDamage(w,victim,p,amount*multiplier);
                if(result.applied()&&multiplier>1)discordReceipt(result.healthLost()*(1-1/multiplier));
                if(result.applied()){hits++;damageApplied+=result.healthLost();if(head)headshots++;}
                else damageRejected++;
                it.remove();continue;
            }
            if(wall.getType()==HitResult.Type.BLOCK){blockHits++;it.remove();continue;}
            if(!clip.complete()){unloadedExpired++;expired++;it.remove();continue;}
            b.distance+=b.pos.distanceTo(end);b.pos=end;
        }
        if(running!=null&&owner(server,running)==null){releasing=false;releaseEndedWall=0;}
        supportTick(server);
        publish();
    }
    private void publish(){
        long now=System.currentTimeMillis();views=orbs.stream().map(b->new View(b.scope,b.pos,b.velocity,b.secondary,now)).toList();
        var o=new JsonObject();o.addProperty("casts",primaryCasts+secondaryCasts);o.addProperty("primaryCasts",primaryCasts);
        o.addProperty("secondaryCasts",secondaryCasts);o.addProperty("secondaryOrbs",secondaryOrbs);o.addProperty("hits",hits);
        o.addProperty("headshots",headshots);o.addProperty("damageApplied",damageApplied);o.addProperty("blockHits",blockHits);
        o.addProperty("expired",expired);o.addProperty("active",orbs.size());o.addProperty("duplicates",duplicates);o.addProperty("rejections",rejections);
        o.addProperty("launched",launched);o.addProperty("scopeExpired",scopeExpired);o.addProperty("lifetimeExpired",lifetimeExpired);
        o.addProperty("rangeExpired",rangeExpired);o.addProperty("unloadedExpired",unloadedExpired);o.addProperty("damageRejected",damageRejected);
        o.addProperty("readInterruptions",readInterruptions);o.addProperty("lastReadInterruption",lastReadInterruption);
        o.addProperty("harmonyAttempts",harmonyAttempts);o.addProperty("discordAttempts",discordAttempts);o.addProperty("transcendenceAttempts",transcendenceAttempts);
        o.addProperty("releasing",releasing);o.addProperty("releaseTick",releaseTick);
        o.addProperty("healingApplied",healingApplied);o.addProperty("buffsApplied",discordCasts);
        o.addProperty("harmonyCasts",harmonyCasts);o.addProperty("harmonyActive",harmonyActive);o.addProperty("harmonyHealingTicks",harmonyHealingTicks);o.addProperty("harmonyHealingApplied",harmonyHealingApplied);
        o.addProperty("discordCasts",discordCasts);o.addProperty("discordActive",discordActive);o.addProperty("discordAmplifiedHits",discordAmplifiedHits);o.addProperty("discordBonusApplied",discordBonusApplied);
        o.addProperty("harmonyTarget",harmonyTarget==null?"":harmonyTarget.toString());o.addProperty("discordTarget",discordTarget==null?"":discordTarget.toString());
        o.addProperty("transcendenceCasts",transcendenceCasts);o.addProperty("transcendenceActive",transcendenceActive);o.addProperty("transcendenceAura",transcendenceAura);
        o.addProperty("transcendenceHealingTicks",transcendenceHealingTicks);o.addProperty("transcendenceHealingApplied",transcendenceHealingApplied);
        o.addProperty("mcAdaptation","MC 适配: MC眼位发射/服务端碰撞/0.1m命中余量/顶部25%头部区域与2倍伤害; 非原版头部参数");
        o.addProperty("secondary","per-orb original factory identities required; scoped factoryCalibration must already be enabled; never fixed-count");
        o.addProperty("supportAdaptation","MC 适配: 30m MC友方谐之珠3HP/s; 乱之珠仅本英雄原版珠伤害x1.3; 圣10m/30HP/s; 不提供猜测免疫");
        o.addProperty("harmony","only fresh health11 B/E; search46 never heals; saved trace has no commit");
        o.addProperty("discord","only fresh Aura6 B/E; search41 never debuffs; saved trace has no commit");
        o.addProperty("transcendence","only fresh health17 B/E heals; Aura30 tracked separately, no guessed immunity; saved trace has only windup19");
        o.addProperty("passive","unavailable: no dedicated event; shared HealthPool is not shield-recovery proof");json=o.toString();
    }
    @Override public void resetSession(){revoke();stopSupport();supportTicks.clear();scopeExpired+=orbs.size();expired+=orbs.size();orbs.clear();factories.clear();attemptTicks.clear();running=null;primaryTick=releaseTick=releaseEndedWall=0;releasing=false;publish();}
    @Override public String statusKey(){return "zenyatta";}
    @Override public String status(){return json;}
}
