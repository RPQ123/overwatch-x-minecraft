package lab.owmcguest;

import com.google.gson.JsonObject;
import java.util.List;
import java.util.UUID;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.passive.PassiveEntity;
import net.minecraft.entity.effect.StatusEffectInstance;
import net.minecraft.entity.effect.StatusEffects;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.RaycastContext;

/** Mercy 24919: 006b:7/19 only prove native search-channel envelopes.
 * MC 适配: choose one live MC teammate/passive entity along the aim ray, range 15 m,
 * heal .25 MC HP/tick (5 HP/s), or Strength I (MC melee bonus, NOT a native 30% multiplier).
 * These are MC target/effect rules, not proof of original Aura18/26 or an OW UUID mapping.
 * Additional paths admit ONLY newly executed original Volley10/MoveTo2/MovementMod2/
 * ModifyHealth4 phases. Saved traces do not certify those new paths or live effects.
 * MC 适配: pistol eye launch/collision, guardian MC ally/18m/s, glide descent cap,
 * passive .1MC HP/tick. Search25/Q36 never activate them. Q/E remain blocked.
 */
public final class MercyServer implements HeroServerModule {
    public static final MercyServer INSTANCE=new MercyServer();
    public static final long HERO=0x02e0000000000004L;
    public record Scope(UUID owner,long world,long source,long model,long serial){
        boolean sameIdentity(Scope other){return other!=null&&owner.equals(other.owner)&&world==other.world&&source==other.source&&model==other.model;}
    }
    public enum Channel { HEAL,BOOST }
    // MC 适配值; no healing/range/multiplier literal was established in the brief.
    private static final double RANGE=15,RAY_MARGIN=.35;
    private static final float HEAL_PER_TICK=.25f;
    private static final int BOOST_TICKS=4;
    private record Lease(Scope scope,long wall){}
    private volatile Lease permission;
    private volatile Scope flightAuthority;
    private Scope running;
    private Channel channel;
    private long beginTick,healTick,boostTick,shiftTick,qTick,pistolTick;
    private UUID targetId;
    private LivingEntity boosted;
    private LivingEntity lastTarget;
    private StatusEffectInstance ownedBoost;
    private long healAttempts,boostAttempts,guardianAttempts,resurrectAttempts,pistolCandidates;
    private long targetAcquisitions,targetLosses,healingTicks,boostTicks,rejections;
    private double healingApplied;
    private boolean guardianActive,glideActive,selfHealActive;
    private long guardianCasts,guardianMoves,glideBegins,selfHealBegins,selfHealingTicks,pistolCasts,pistolHits,pistolBlockHits;
    private double guardianDistance,selfHealingApplied,pistolDamageApplied;
    private UUID guardianTarget;
    private Vec3d previousGuardian;
    private final java.util.Map<String,Long> supportTicks=new java.util.HashMap<>();
    private static final class Bullet {Scope scope;Vec3d at,velocity;int age;double distance;}
    private final java.util.ArrayList<Bullet> bullets=new java.util.ArrayList<>();
    public record GuardianView(Scope scope,Vec3d destination,long wall){}
    public volatile GuardianView guardianView;
    private volatile String json="{}";
    /** Views contain only projectiles admitted by a fresh native Volley E. */
    public record ProjectileView(Scope scope,Vec3d at,Vec3d velocity,long wall){}
    public volatile List<ProjectileView> projectiles=List.of();
    private MercyServer(){publish(null);}

    // Only an immutable permission/lease crosses threads; entity changes stay on the server.
    public void permit(Scope s,long wall){flightAuthority=s;permission=new Lease(s,wall);}
    public void revoke(){permission=null;flightAuthority=null;}
    private ServerPlayerEntity owner(MinecraftServer server,Scope s){
        var lease=permission;if(lease==null)return null;long age=System.currentTimeMillis()-lease.wall();
        if(s==null||!s.equals(lease.scope())||age<0||age>150||s.source()<=0||s.model()<=0)return null;
        var p=server.getPlayerManager().getPlayer(s.owner());
        return p!=null&&p.isAlive()&&NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())==s.world()?p:null;
    }
    private void adopt(Scope s){
        if(!s.equals(running)){stop();stopSupport();lastTarget=null;
            if(!s.sameIdentity(running))bullets.clear();
            running=s;healTick=boostTick=shiftTick=qTick=pistolTick=0;supportTicks.clear();}
    }
    private static boolean fresh(long wall){long age=System.currentTimeMillis()-wall;return age>=0&&age<=150;}
    public void channel(MinecraftServer server,Scope s,Channel kind,long tick,boolean active,long wall){
        if(owner(server,s)==null||!fresh(wall)){rejections++;return;}adopt(s);
        if(!active){if(channel==kind)stop();publish(null);return;}
        long last=kind==Channel.HEAL?healTick:boostTick;
        if(tick<=0||tick<=last)return;
        if(kind==Channel.HEAL){healTick=tick;healAttempts++;}else{boostTick=tick;boostAttempts++;}
        stop();channel=kind;beginTick=tick;publish(null);
    }
    public void attempt(MinecraftServer server,Scope s,String kind,long tick,long wall){
        if(owner(server,s)==null||tick<=0||!fresh(wall)){rejections++;return;}adopt(s);
        switch(kind){
            case "guardian" -> {if(tick>shiftTick){shiftTick=tick;guardianAttempts++;}}
            case "resurrect" -> {if(tick>qTick){qTick=tick;resurrectAttempts++;}}
            case "pistol" -> {if(tick>pistolTick){pistolTick=tick;pistolCandidates++;}}
            default -> throw new IllegalArgumentException("Mercy attempt kind");
        }publish(null);
    }
    public void stopChannel(Scope s){if(s.equals(running))stop();}
    public void stopSupport(Scope s){if(s.equals(running))stopSupport();}
    private void stopSupport(){guardianActive=glideActive=selfHealActive=false;guardianTarget=null;previousGuardian=null;guardianView=null;}
    /** Semantic state only; a search, animation or Q wait is never routed here. */
    public void support(MinecraftServer server,Scope s,String kind,long tick,boolean active,long wall){
        var p=owner(server,s);if(p==null||tick<=0||!fresh(wall)){rejections++;return;}adopt(s);
        if(active){if(tick<=supportTicks.getOrDefault(kind,0L))return;supportTicks.put(kind,tick);}
        switch(kind){
            case "guardian" -> {
                if(active&&!guardianActive){guardianCasts++;var target=aimedTarget(p);guardianTarget=target==null?null:target.getUuid();previousGuardian=p.getPos();}
                guardianActive=active;if(!active){guardianView=null;guardianTarget=null;previousGuardian=null;}
            }
            case "glide" -> {if(active&&!glideActive)glideBegins++;glideActive=active;}
            case "selfHeal" -> {if(active&&!selfHealActive)selfHealBegins++;selfHealActive=active;}
            default -> throw new IllegalArgumentException("Mercy support phase");
        }publish(null);
    }
    public void pistol(MinecraftServer server,Scope s,long tick,long wall){
        var p=owner(server,s);if(p==null||tick<=0||!fresh(wall)){rejections++;return;}adopt(s);
        if(tick<=pistolTick)return;pistolTick=tick;pistolCandidates++;
        if(bullets.size()>=64){rejections++;return;}
        var b=new Bullet();b.scope=s;b.at=p.getEyePos();b.velocity=p.getRotationVec(1).multiply(50/20.0);bullets.add(b);pistolCasts++;publish(null);
    }
    private static boolean friendly(ServerPlayerEntity p,LivingEntity e){
        return e!=p&&e.isAlive()&&!e.isSpectator()&&(p.isTeammate(e)||e instanceof PassiveEntity);
    }
    private static boolean visible(ServerPlayerEntity p,LivingEntity e){
        var w=p.getServerWorld();
        if(!friendly(p,e)||!w.isChunkLoaded(e.getBlockPos())||p.getEyePos().squaredDistanceTo(e.getBoundingBox().getCenter())>RANGE*RANGE)return false;
        return w.raycast(new RaycastContext(p.getEyePos(),e.getBoundingBox().getCenter(),
            RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p)).getType()==HitResult.Type.MISS;
    }
    private static LivingEntity aimedTarget(ServerPlayerEntity p){
        var from=p.getEyePos();var to=from.add(p.getRotationVec(1).multiply(RANGE));
        LivingEntity best=null;double nearest=Double.POSITIVE_INFINITY;
        for(var e:p.getServerWorld().getEntitiesByClass(LivingEntity.class,new Box(from,to).expand(RAY_MARGIN),x->friendly(p,x))){
            var hit=e.getBoundingBox().expand(RAY_MARGIN).raycast(from,to);
            if(hit.isPresent()&&visible(p,e)&&from.squaredDistanceTo(hit.get())<nearest){best=e;nearest=from.squaredDistanceTo(hit.get());}
        }return best;
    }
    private void releaseBoost(){
        if(boosted!=null&&ownedBoost!=null){
            var current=boosted.getStatusEffect(StatusEffects.STRENGTH);
            // Never erase a pre-existing buff or a longer/stronger external replacement.
            if(current==ownedBoost&&current.getAmplifier()==0&&current.getDuration()<=BOOST_TICKS)
                boosted.removeStatusEffect(StatusEffects.STRENGTH);
        }boosted=null;ownedBoost=null;
    }
    private void stop(){releaseBoost();channel=null;targetId=null;beginTick=0;}
    private void pistolTick(MinecraftServer server){
        long now=System.currentTimeMillis();var draw=new java.util.ArrayList<ProjectileView>();
        for(var it=bullets.iterator();it.hasNext();){
            var b=it.next();var p=server.getPlayerManager().getPlayer(b.scope.owner());
            if(!b.scope.sameIdentity(flightAuthority)||p==null||!p.isAlive()||NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())!=b.scope.world()
                    ||++b.age>100||b.distance>=100){it.remove();continue;}
            var w=p.getServerWorld();var end=b.at.add(b.velocity.multiply(Math.min(1,(100-b.distance)/b.velocity.length())));
            var clip=LoadedRayPrefix.clip(new NativeShotProtocol.Vec(b.at.x,b.at.y,b.at.z),new NativeShotProtocol.Vec(end.x,end.y,end.z),
                (x,z)->w.isChunkLoaded(new net.minecraft.util.math.BlockPos(x<<4,0,z<<4)));
            if(clip.fraction()==0){it.remove();continue;}end=b.at.lerp(end,clip.fraction());
            var block=w.raycast(new RaycastContext(b.at,end,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
            double nearest=block.getType()==HitResult.Type.BLOCK?b.at.squaredDistanceTo(block.getPos()):Double.POSITIVE_INFINITY;
            net.minecraft.entity.Entity victim=null;
            for(var e:NativeDamageTargets.in(w,p,new Box(b.at,end).expand(.1))){
                if(p.isTeammate(NativeDamageTargets.owner(e)))continue;
                var box=e.getBoundingBox().expand(.1);var hit=box.contains(b.at)?java.util.Optional.of(b.at):box.raycast(b.at,end);
                if(hit.isPresent()&&b.at.squaredDistanceTo(hit.get())<nearest){nearest=b.at.squaredDistanceTo(hit.get());victim=e;}
            }
            if(victim!=null){var result=NativeDamageTargets.projectileDamage(w,victim,p,20*NativeShotSimulation.HP_SCALE);
                if(result.applied()){pistolHits++;pistolDamageApplied+=result.healthLost();}it.remove();continue;}
            if(block.getType()==HitResult.Type.BLOCK){pistolBlockHits++;it.remove();continue;}
            if(!clip.complete()){it.remove();continue;}
            b.distance+=b.at.distanceTo(end);b.at=end;draw.add(new ProjectileView(b.scope,b.at,b.velocity,now));
        }projectiles=List.copyOf(draw);
    }
    @Override public void tick(MinecraftServer server){
        pistolTick(server);
        var p=owner(server,running);
        if(p==null){stop();stopSupport();lastTarget=null;running=null;publish(null);return;}
        if(selfHealActive){float hp=p.getHealth();p.heal(.1f);double gained=Math.max(0,p.getHealth()-hp);selfHealingApplied+=gained;if(gained>0)selfHealingTicks++;}
        if(guardianActive){
            var e=guardianTarget==null?null:p.getServerWorld().getEntity(guardianTarget);
            if(e instanceof LivingEntity ally&&visible(p,ally)){
                guardianView=new GuardianView(running,ally.getPos(),System.currentTimeMillis());
                if(previousGuardian!=null){double distance=previousGuardian.distanceTo(p.getPos());if(distance>1e-6&&distance<2){guardianDistance+=distance;guardianMoves++;}}
                previousGuardian=p.getPos();
            }else{guardianView=null;guardianTarget=null;}
        }
        if(channel==null){publish(null);return;}
        var e=targetId==null?null:p.getServerWorld().getEntity(targetId);
        LivingEntity target=e instanceof LivingEntity living&&visible(p,living)?living:null;
        if(target==null){
            if(targetId!=null){targetLosses++;releaseBoost();targetId=null;}
            target=aimedTarget(p);
            if(target!=null){targetId=target.getUuid();targetAcquisitions++;}
        }
        if(target!=null){
            if(channel==Channel.HEAL){
                float hp=target.getHealth();target.heal(HEAL_PER_TICK);
                double gained=Math.max(0,target.getHealth()-hp);healingApplied+=gained;if(gained>0)healingTicks++;
            }else{
                var current=target.getStatusEffect(StatusEffects.STRENGTH);
                if(current==null||(target==boosted&&current==ownedBoost&&current.getAmplifier()==0&&current.getDuration()<=BOOST_TICKS)){
                    if(current==null){
                        var effect=new StatusEffectInstance(StatusEffects.STRENGTH,BOOST_TICKS,0,false,false,true);
                        target.addStatusEffect(effect);boosted=target;ownedBoost=target.getStatusEffect(StatusEffects.STRENGTH);
                    }else target.addStatusEffect(new StatusEffectInstance(StatusEffects.STRENGTH,BOOST_TICKS,0,false,false,true));
                    if(ownedBoost!=null&&target.getStatusEffect(StatusEffects.STRENGTH)==ownedBoost&&ownedBoost.getAmplifier()==0)boostTicks++;
                }
            }
        }publish(target);
    }
    private void publish(LivingEntity target){
        if(target!=null)lastTarget=target;
        var o=new JsonObject();o.addProperty("casts",healAttempts+boostAttempts+pistolCasts);o.addProperty("hits",healingTicks+boostTicks+pistolHits);
        o.addProperty("damageApplied",pistolDamageApplied);o.addProperty("healAttempts",healAttempts);o.addProperty("boostAttempts",boostAttempts);
        o.addProperty("guardianAttempts",guardianAttempts);o.addProperty("resurrectAttempts",resurrectAttempts);o.addProperty("pistolCandidates",pistolCandidates);
        o.addProperty("targetAcquisitions",targetAcquisitions);o.addProperty("targetLosses",targetLosses);o.addProperty("healingTicks",healingTicks);
        o.addProperty("healingApplied",healingApplied);o.addProperty("boostTicks",boostTicks);o.addProperty("rejections",rejections);
        o.addProperty("channel",channel==null?"none":channel.name());o.addProperty("beginTick",beginTick);
        o.addProperty("target",targetId==null?"":targetId.toString());
        if(lastTarget!=null){
            o.addProperty("lastTarget",lastTarget.getUuid().toString());o.addProperty("targetHealth",lastTarget.getHealth());
            var strength=lastTarget.getStatusEffect(StatusEffects.STRENGTH);
            o.addProperty("targetStrengthAmplifier",strength==null?-1:strength.getAmplifier());
            o.addProperty("targetStrengthTicks",strength==null?0:strength.getDuration());
        }
        o.addProperty("mcAdaptation","MC 适配: MC友方目标/15m视线断链/5HP每秒/Strength I近战增益; 非原版Aura提交或通用30%增伤");
        o.addProperty("supportAdaptation","MC 适配: 手枪MC眼位/直线无重力/.1m碰撞余量; 守护天使MC友方15m/18m每秒; 滑翔下降钳制-.1; 被动2HP每秒; 新路径尚无实测验收");
        o.addProperty("guardianCasts",guardianCasts);o.addProperty("guardianActive",guardianActive);o.addProperty("guardianMoves",guardianMoves);o.addProperty("guardianDistance",guardianDistance);
        o.addProperty("glideBegins",glideBegins);o.addProperty("glideActive",glideActive);o.addProperty("selfHealBegins",selfHealBegins);o.addProperty("selfHealActive",selfHealActive);
        o.addProperty("selfHealingTicks",selfHealingTicks);o.addProperty("selfHealingApplied",selfHealingApplied);
        o.addProperty("pistolCasts",pistolCasts);o.addProperty("pistolHits",pistolHits);o.addProperty("pistolBlockHits",pistolBlockHits);o.addProperty("pistolDamageApplied",pistolDamageApplied);
        o.addProperty("guardian","MoveTo2 B/E only; MC ally/collision/18m per second; saved trace has no Begin; travel hook required");
        o.addProperty("resurrection","attempt only: no original resurrection commit");
        o.addProperty("pistol","fresh 006d:10 Volley E only; original20/50/5/100; no saved pistol firing tick; MC eye/collision/gravity0 adaptation");
        o.addProperty("e","unavailable: no independent graph/node identified");
        o.addProperty("passive","fresh 0071:2/4 B/E only; MC glide/.1HP per tick; baseline active4 is not replayed; no new phase in saved trace");
        o.addProperty("projectiles",bullets.size());
        // integrator/models: presentation of accepted state only; preserve its real lease.
if(target!=null&&running!=null&&channel!=null&&target.getServer()!=null){
    var p=owner(target.getServer(),running);var lease=permission;
    if(p!=null&&lease!=null&&lease.scope().equals(running)){
        var f=OriginalEffectFrames.frame(running.owner(),running.world(),running.source(),running.model(),lease.wall());
        OriginalEffectFrames.beam(f,"mercy-heal-beam",p.getEyePos().add(0,-.25,0),target.getBoundingBox().getCenter(),.08f,.8f);
        OriginalEffectFrames.body(f,"mercy-target-glow",target.getBoundingBox().getCenter(),new Vec3d(.35,.35,.35),.7f,true);
        o.add("models",f);
    }
}
        json=o.toString();
    }
    @Override public void resetSession(){revoke();stop();stopSupport();bullets.clear();supportTicks.clear();lastTarget=null;running=null;projectiles=List.of();publish(null);}
    @Override public String statusKey(){return "mercy";}
    @Override public String status(){return json;}
}
