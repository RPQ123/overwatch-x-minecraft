package lab.owmcguest;

import com.google.gson.JsonObject;
import java.util.*;
import net.minecraft.entity.*;
import net.minecraft.entity.damage.DamageSource;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.registry.tag.DamageTypeTags;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.math.*;
import net.minecraft.world.RaycastContext;
import lab.owmcguest.NativeShotProtocol.*;

/** Native Begin/End owns ability timing/HUD. MC alone owns collisions, pulling,
 * HP and requested mitigation. The beta declares hook30/6s and heal300/8s.
 * Hook flight40m/s, force-latched pull1m/tick then arrival by20steps, stop2.75m
 * and50% E mitigation are MC policies; only outbound flight uses block collision.
 * Weapons are resolved once by NativeCombatRuntime; no second damage consumer. */
public final class RoadhogServer implements HeroServerModule {
    public static final RoadhogServer INSTANCE=new RoadhogServer();
    public static final long HERO=RoadhogRules.HERO;
    static final long SCRAP=RoadhogRules.SCRAP,SECONDARY=RoadhogRules.SECONDARY,WHOLE_HOG=RoadhogRules.WHOLE_HOG;
    public record Scope(UUID owner,long world,long source,long model){}
    public record Sample(long hookCast,long hookSearch,long heal,long wholeHog,long breatherCast){}
    public record HookView(Scope scope,long wall,String id,Vec3d at,Vec3d direction,String stage){}
    private enum Stage{OUT,PULL,RETURN}
    private static final class Hook {String id;Vec3d at,direction;UUID target;Entity targetEntity;Scope owner;RoadhogHookPull pull;int age,pulls;double distance;Stage stage=Stage.OUT;}
    private Scope scope;private long lease,lastHookCast,lastHookSearch,lastHeal,lastQ;private Sample phases=new Sample(0,0,0,0,0);private Hook hook;
    private final RoadhogRules.Healing healing=new RoadhogRules.Healing();private final Set<String> volleys=new HashSet<>();
    private long primaryCasts,secondaryCasts,hookCasts,hookSearches,hookHits,pullTicks,hookBlocked,hookReturns,healCasts,qCasts,pellets,qPellets,hits,rejected;
    private double healingApplied,damageApplied,hookDamageApplied,damagePrevented;
    private long hookCompleted,hookCancelled,hookForcedArrivals;private String hookEndReason="";
    private float ownerHealth;private volatile String json="{}";public volatile HookView hookView;
    private RoadhogServer(){publish();}
    @Override public String statusKey(){return "roadhog";}
    @Override public String status(){return json;}
    private static boolean fresh(long wall){long age=System.currentTimeMillis()-wall;return wall>0&&age>=-50&&age<=150;}
    private static ServerPlayerEntity player(MinecraftServer server,Scope s){
        var p=s==null?null:server.getPlayerManager().getPlayer(s.owner());
        return p!=null&&p.isAlive()&&NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())==s.world()?p:null;
    }
    static String hookId(Scope s,long token){return "roadhog-hook:"+s.source()+":"+s.model()+":"+token;}
    // A lost native lease spends transient windows. A confirmed MC target
    // latch has its own actor/world lifetime and survives reader resets.
    private boolean pulling(){return hook!=null&&hook.stage==Stage.PULL&&hook.pull!=null;}
    private void retire(){if(!pulling()){hook=null;hookView=null;}healing.refresh(0);phases=new Sample(0,0,0,0,0);}
    private void cancelHook(String reason){hook=null;hookView=null;hookCancelled++;hookEndReason=reason;}
    public void refresh(MinecraftServer server,Scope s,long wall,Sample next){
        var p=player(server,s);if(!server.isOnThread()||!fresh(wall)||p==null){rejected++;return;}
        if(!s.equals(scope)){retire();healing.clear();lastHookCast=lastHookSearch=lastHeal=lastQ=0;volleys.clear();scope=s;}
        else if(!fresh(lease))retire();
        lease=wall;ownerHealth=p.getHealth();
        if(next.hookCast()>0&&next.hookCast()!=lastHookCast){lastHookCast=next.hookCast();hookCasts++;if(!pulling())hook=null;}
        if(next.hookSearch()>0&&next.hookSearch()!=lastHookSearch&&next.hookCast()>0){
            lastHookSearch=next.hookSearch();hookSearches++;
            if(!pulling()){hook=new Hook();hook.owner=s;hook.id=hookId(s,next.hookCast());hook.at=p.getEyePos();hook.direction=p.getRotationVec(1).normalize();}
        }
        // A fresh native search authorizes one launch. Its short End only ends
        // OW target search; MC completes its already launched flight/pull with
        // the same bounded lease, just as gun projectiles outlive Volley End.
        if(next.heal()>0&&next.heal()!=lastHeal){lastHeal=next.heal();healCasts++;}
        healing.refresh(next.heal());
        if(next.wholeHog()>0&&next.wholeHog()!=lastQ){lastQ=next.wholeHog();qCasts++;}
        phases=next;publish();
    }
    public void suspend(Scope expected){if(expected.equals(scope)){lease=0;retire();RoadhogPresentation.reset();publish();}}
    /** Called only for admissions of the acknowledged native journal. */
    public void admitted(Shot shot){
        if(!RoadhogRules.is(shot))return;pellets++;
        if(RoadhogRules.wholeHog(shot))qPellets++;
        else if(volleys.size()<65536&&volleys.add(shot.identity().substring(0,shot.identity().lastIndexOf(':')))){
            if(RoadhogRules.secondary(shot))secondaryCasts++;else primaryCasts++;
        }
    }
    public void weaponReceipt(Shot shot,NativeDamageTargets.Result receipt){if(RoadhogRules.is(shot)&&receipt.applied()){hits++;damageApplied+=receipt.healthLost();publish();}}
    /** Called on the server at LivingEntity.damage HEAD, before MC armor/HP. */
    public float reduceDamage(LivingEntity entity,DamageSource source,float amount){
        if(entity.getWorld().isClient||!entity.isAlive()||entity.isInvulnerableTo(source)||!Float.isFinite(amount)||amount<=0||scope==null||!fresh(lease)
           ||phases.breatherCast()==0||!scope.owner().equals(entity.getUuid())||source.isIn(DamageTypeTags.BYPASSES_INVULNERABILITY)
           ||entity.getServer()==null||NativeWorldIdentity.of(entity.getServer(),entity.getWorld().getRegistryKey())!=scope.world())return amount;
        float reduced=(float)(amount*RoadhogRules.BREATHER_DAMAGE_SCALE);damagePrevented+=amount-reduced;return reduced;
    }
    private record Contact(Entity entity,Vec3d at,boolean blocked){}
    private static Contact contact(ServerPlayerEntity p,Vec3d from,Vec3d to){
        var w=p.getServerWorld();var a=new Vec(from.x,from.y,from.z);var b=new Vec(to.x,to.y,to.z);
        var clip=LoadedRayPrefix.clip(a,b,(x,z)->w.isChunkLoaded(new BlockPos(x<<4,0,z<<4)));
        to=from.lerp(to,clip.fraction());var wall=w.raycast(new RaycastContext(from,to,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
        boolean blocked=wall.getType()==HitResult.Type.BLOCK;Vec3d end=blocked?wall.getPos():to;
        Entity best=null;double nearest=from.squaredDistanceTo(end);Vec3d at=end;
        for(var e:NativeDamageTargets.in(w,p,new Box(from,end).expand(RoadhogRules.HOOK_RADIUS))){
            if(e instanceof PlayerEntity||!(NativeDamageTargets.owner(e) instanceof LivingEntity))continue;
            var box=e.getBoundingBox().expand(RoadhogRules.HOOK_RADIUS);var hit=box.contains(from)?Optional.of(from):box.raycast(from,end);
            if(hit.isPresent()&&from.squaredDistanceTo(hit.get())<nearest){nearest=from.squaredDistanceTo(hit.get());best=e;at=hit.get();}
        }
        return best!=null?new Contact(best,at,false):blocked||!clip.complete()?new Contact(null,end,true):null;
    }
    private void retract(){if(hook!=null&&hook.stage!=Stage.RETURN){hook.stage=Stage.RETURN;hook.target=null;hook.targetEntity=null;hook.pull=null;hookReturns++;}}
    private void tickHook(ServerPlayerEntity p){
        if(hook==null)return;var h=hook;if(++h.age>40&&h.stage!=Stage.PULL){hook=null;return;}
        if(h.stage==Stage.RETURN){var delta=p.getEyePos().subtract(h.at);if(delta.length()<.5){hook=null;return;}h.at=h.at.add(delta.normalize().multiply(Math.min(3,delta.length())));return;}
        if(h.stage==Stage.OUT){
            if(h.distance>=RoadhogRules.HOOK_RANGE){retract();return;}
            var end=h.at.add(h.direction.multiply(Math.min(RoadhogRules.HOOK_SPEED/20,RoadhogRules.HOOK_RANGE-h.distance)));
            if(!p.getServerWorld().getWorldBorder().contains(BlockPos.ofFloored(end))){hookBlocked++;retract();return;}
            var hit=contact(p,h.at,end);
            if(hit==null){h.distance+=h.at.distanceTo(end);h.at=end;return;}
            h.at=hit.at();if(hit.blocked()){hookBlocked++;retract();return;}
            var target=NativeDamageTargets.owner(hit.entity());
            h.target=target.getUuid();h.targetEntity=target;h.stage=Stage.PULL;
            h.pull=new RoadhogHookPull(h.owner.owner(),h.owner.world(),h.target);hookHits++;
            var receipt=NativeDamageTargets.projectileDamage(p.getServerWorld(),hit.entity(),p,RoadhogRules.HOOK_DAMAGE*NativeShotSimulation.HP_SCALE);
            hookDamageApplied+=receipt.healthLost();damageApplied+=receipt.healthLost();NativeUltimateRuntime.credit(receipt.healthLost());
        }
        var e=h.targetEntity;if(e==null){cancelHook("target-left-world");return;}
        long targetWorld=NativeWorldIdentity.of(p.getServer(),e.getWorld().getRegistryKey());
        var actors=new RoadhogHookPull.Actors(p.getUuid(),h.owner.world(),p.isAlive(),e.getUuid(),targetWorld,e.isAlive(),e.isRemoved());
        var feet=new Vec(p.getX(),p.getY(),p.getZ());var facing=p.getRotationVec(1);var forward=new Vec(facing.x,facing.y,facing.z);
        var step=h.pull.advance(actors,new Vec(e.getX(),e.getY(),e.getZ()),feet,forward);
        if(step==null)return;
        if(!step.cancelled().isEmpty()){cancelHook(step.cancelled());return;}
        var at=step.destination();boolean completed=step.complete();
        // An unloaded intermediate chunk is never a disconnection. Finish in
        // the owner's loaded vicinity rather than synchronously loading a path.
        if(!p.getServerWorld().isChunkLoaded(BlockPos.ofFloored(at.x(),at.y(),at.z()))){at=RoadhogRules.hookGoal(feet,forward);completed=true;hookForcedArrivals++;}
        e.stopRiding();e.setVelocity(Vec3d.ZERO);e.requestTeleport(at.x(),at.y(),at.z());e.velocityModified=true;e.fallDistance=0;pullTicks++;h.pulls++;
        h.at=e.getBoundingBox().getCenter();
        if(completed){hookCompleted++;hookEndReason="arrived";retract();}
    }
    @Override public void tick(MinecraftServer server){
        var p=player(server,pulling()?hook.owner:scope);
        if(p==null){if(pulling())cancelHook("owner-dead-or-left-world");retire();publish();return;}
        if(!fresh(lease)){retire();if(!pulling()){publish();return;}}
        double amount=fresh(lease)&&phases.heal()>0?healing.tick():0;
        if(amount>0){float before=p.getHealth();p.heal((float)amount);healingApplied+=Math.max(0,p.getHealth()-before);}
        if(phases.breatherCast()>0&&server.getTicks()%2==0){var at=p.getEyePos().add(p.getRotationVec(1).multiply(.25));p.getServerWorld().spawnParticles(ParticleTypes.CLOUD,at.x,at.y-.15,at.z,2,.12,.08,.12,.005);}
        tickHook(p);ownerHealth=p.getHealth();publish();
    }
    private void publish(){
        hookView=hook==null||!pulling()&&!fresh(lease)?null:new HookView(hook.owner,pulling()?System.currentTimeMillis():lease,hook.id,hook.at,hook.direction,hook.stage.name());
        var o=new JsonObject();o.addProperty("primaryCasts",primaryCasts);o.addProperty("secondaryCasts",secondaryCasts);o.addProperty("hookCasts",hookCasts);
        o.addProperty("hookSearches",hookSearches);o.addProperty("hookHits",hookHits);o.addProperty("pullTicks",pullTicks);o.addProperty("hookBlocked",hookBlocked);o.addProperty("hookReturns",hookReturns);
        o.addProperty("hookCompleted",hookCompleted);o.addProperty("hookCancelled",hookCancelled);o.addProperty("hookForcedArrivals",hookForcedArrivals);o.addProperty("hookEndReason",hookEndReason);
        o.addProperty("hookLatched",pulling());o.addProperty("hookLatchPolicy","RH3: death/removal/world separation only; no native lease,range,LOS or collision release; forced arrival by20steps");
        o.addProperty("healCasts",healCasts);o.addProperty("healingApplied",healingApplied);o.addProperty("damagePrevented",damagePrevented);o.addProperty("ownerHealth",ownerHealth);
        o.addProperty("qCasts",qCasts);o.addProperty("qActive",phases.wholeHog()>0);o.addProperty("pellets",pellets);o.addProperty("qPellets",qPellets);o.addProperty("hits",hits);
        o.addProperty("damageApplied",damageApplied);o.addProperty("hookDamageApplied",hookDamageApplied);o.addProperty("hookActive",hook!=null);o.addProperty("healActive",phases.heal()>0);
        o.addProperty("hookDamageEnabled",true);o.addProperty("secondarySplitEnabled",true);o.addProperty("rejected",rejected);o.addProperty("factoryTransport","acknowledged emission17; same native owner, no calibration required");
        o.addProperty("mcAdaptation","nested child cone/replay; hook sweep/pull/chain; E 50% mitigation; Q bounded strong impulse");
        o.addProperty("originalTiming","native hook cooldown6s, breather8s, ammo/reload, Q cost and Begin/End retained");
        o.addProperty("shardFrames",RoadhogPresentation.shardFrames);o.addProperty("secondaryFrames",RoadhogPresentation.secondaryFrames);
        o.addProperty("hookFrames",RoadhogPresentation.hookFrames);o.addProperty("chainFrames",RoadhogPresentation.chainFrames);
        o.addProperty("fireFrames",RoadhogPresentation.fireFrames);o.addProperty("trailFrames",RoadhogPresentation.trailFrames);
        o.add("splitSound",com.google.gson.JsonParser.parseString(RoadhogPresentation.splitSoundStatus));
        o.addProperty("splitCuesQueued",RoadhogSplitCues.INSTANCE.admitted);o.addProperty("splitCuesDuplicates",RoadhogSplitCues.INSTANCE.duplicates);o.addProperty("splitCuesOverflow",RoadhogSplitCues.INSTANCE.overflow);
        o.addProperty("projectileModelPolicy","24919 Roadhog14c0 secondary;1197/11dc original debris reused for primary/child/Q;Q0801 sprite retained");
        o.addProperty("hookOriginPolicy","shared left-palm reference for head/chain; frozen outbound launch, live attached chain root; MC screen-pose adapter");
        o.addProperty("renderError",RoadhogPresentation.renderError);json=o.toString();
    }
    @Override public void resetSession(){lease=0;scope=null;lastHookCast=lastHookSearch=lastHeal=lastQ=0;volleys.clear();retire();healing.clear();RoadhogPresentation.reset();RoadhogSplitCues.INSTANCE.clear();publish();}
    /** Server stopping / explicit world cleanup removes the actual world too. */
    @Override public void clear(){hook=null;resetSession();}
}
