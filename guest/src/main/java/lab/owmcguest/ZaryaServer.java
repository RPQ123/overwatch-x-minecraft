package lab.owmcguest;

import com.google.gson.JsonObject;
import java.util.*;
import net.minecraft.entity.Entity;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.attribute.EntityAttributeInstance;
import net.minecraft.entity.attribute.EntityAttributeModifier;
import net.minecraft.entity.attribute.EntityAttributes;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.util.Identifier;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.math.*;
import net.minecraft.world.RaycastContext;

/** Offline24919, HERO-BRIEFS-NEW8-20261025 §6. Native beam36 B/E is an APPEARANCE
 * channel: MC supplies target/hit authority, not a claim that BeamEffect dealt
 * native damage. Grenade42/Q2 are fresh Volley events, B/E counted once.
 * Declared grenade: GUID03db, speed25, g9.8000001907, lifetime3s, range100.
 * Declared Q: GUID08ce, same speed/g/range, lifetime5s, impact5 (NOT total Q).
 * Self Aura15 B/E is one envelope. E24 is only a search ATTEMPT; Aura43 and Pet32
 * have no success evidence, so no projected shield. Passive absorption->energy
 * event/formula is absent: no invented energy or native ammo/cooldown/HUD writes.
 * MC 适配值: beam15m/.2width,95 OW DPS; grenade80 OW damage,inner.5/outer2m
 * linear falloff; self shield20MC absorption HP,max2s; Q contacts create a 6m/4s
 * MC gravity field, pull4m/s,5 OW DPS. No Boss/teammate/player pull or root.
 * Energy scaling, cleanse, break/native feedback, projected target mapping pending.
 * Native Q field creation/despawn not seen: MC CONTACT creates this adapted field,
 * never the Q key/volley itself. Lease200ms, no damage through walls.
 * Asset-chain03db/08ce completed, no LOD0/texture; optional mesh names zarya-grenade,
 * zarya-graviton. Missing meshes use explicit MC particles. Shield GUID unknown. */
public final class ZaryaServer implements HeroServerModule {
    private static final com.google.gson.Gson EVIDENCE_JSON=new com.google.gson.Gson();
    public static final ZaryaServer INSTANCE=new ZaryaServer();
    public static final long HERO=0x02e0000000000068L;
    public record Scope(UUID owner,long world,long source,long model){}
    public record SelfSignal(boolean readable,long tick,boolean active,boolean baseline){}
    public record View(long world,long wall,Vec3d at,Vec3d velocity,boolean ultimate,boolean field,int age){}
    private static final class Body {Vec3d pos,vel;boolean ultimate,field;int age,fieldAge;double travelled;}
    private static final double GRAVITY=9.800000190734863/400,BEAM_RANGE=15,BEAM_DPS=95,BEAM_WIDTH=.2;
    private static final double GRENADE=80,INNER=.5,OUTER=2,FIELD_RADIUS=6,FIELD_DPS=5;
    private static final float SHIELD_HP=20;
    private static final Identifier SHIELD_CAPACITY_ID=Identifier.of("owmcguest","zarya_self_barrier_capacity");
    private final List<Body> bodies=new ArrayList<>();
    public volatile List<View> views=List.of();
    private Map<String,TanksNodeEvidence.Node> candidateEvidence=Map.of();
    /** Read-only candidate counters. No observed candidate authorizes an effect. */
    public void observeCandidates(Scope expected,long wall,Map<String,TanksNodeEvidence.Node> nodes){
        long age=System.currentTimeMillis()-wall;
        if(expected!=null&&expected.equals(scope)&&age>=-50&&age<=150){candidateEvidence=Map.copyOf(nodes);publish();}
    }
    private Scope scope;
    private long heartbeat,shieldWall;
    private Vec3d beamFrom,beamTo;private long beamWall;
    private final long[] seen=new long[5];
    private boolean beam,shield;
    private ServerPlayerEntity shieldOwner;
    private EntityAttributeInstance shieldCapacity;
    private EntityAttributeModifier shieldCapacityModifier;
    private float shieldRemaining,lastAbsorption;
    private long casts,beamCasts,beamHits,grenades,gravitons,explosions,directHits,blastHits,fields,pulls;
    private long selfCasts,shieldEnds,projectedAttempts,projectedCandidates,rejected;
    private long selfGrantFailures,selfNodeBaselines,selfLastBeginTick;
    private SelfSignal selfSignal=new SelfSignal(false,0,false,false);
    private double damageApplied,absorptionConsumed,selfGranted;
    private volatile boolean resetRequested;
    private volatile String json="{\"active\":false}";

    private ServerPlayerEntity player(MinecraftServer server,Scope s){
        var p=s==null?null:server.getPlayerManager().getPlayer(s.owner());
        return p!=null&&p.isAlive()&&s.source()!=0&&s.model()!=0
            &&NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())==s.world()?p:null;
    }
    public void sample(MinecraftServer server,Scope next,long wall,long[] events,boolean beamActive,boolean selfActive,SelfSignal signal){
        long now=System.currentTimeMillis();var p=player(server,next);
        if(wall>now+50||now-wall>150||p==null){rejected++;return;}
        if(resetRequested){clearOwned();resetRequested=false;}
        if(!next.equals(scope)){clearOwned();scope=next;Arrays.fill(seen,0);}
        heartbeat=now;
        selfSignal=signal;if(signal.baseline())selfNodeBaselines++;
        for(int i=0;i<events.length;i++)if(events[i]>seen[i]){
            seen[i]=events[i];
            switch(i){
                case 0->{beamCasts++;casts++;}
                case 1->launch(p,false);
                case 2->{selfLastBeginTick=events[i];beginShield(p,now);}
                case 3->projectedAttempts++;
                case 4->launch(p,true);
                default->throw new IllegalArgumentException("Zarya event slot");
            }
        }
        beam=beamActive;
        if(!selfActive)endShield();
        publish();
    }
    /** Record a future projected Aura candidate without inventing a target. */
    public void projectedCandidate(MinecraftServer server,Scope expected,long wall){
        if(expected.equals(scope)&&player(server,scope)!=null&&Math.abs(System.currentTimeMillis()-wall)<=150)projectedCandidates++;
    }
    public void invalidate(MinecraftServer server,Scope expected){if(expected!=null&&expected.equals(scope)){clearOwned();publish();}}
    private void launch(ServerPlayerEntity p,boolean ultimate){
        if(bodies.size()>=32){rejected++;return;}
        var b=new Body();b.ultimate=ultimate;
        // Start at the eye: the very first segment is collision tested as well.
        b.pos=p.getEyePos();b.vel=p.getRotationVec(1).normalize().multiply(25/20.0);bodies.add(b);
        casts++;if(ultimate)gravitons++;else grenades++;
    }
    @Override public void tick(MinecraftServer server){
        if(resetRequested){clearOwned();resetRequested=false;}
        var p=player(server,scope);
        if(p==null||System.currentTimeMillis()-heartbeat>200){clearOwned();publish();return;}
        if(shield){accountShield();if(System.currentTimeMillis()-shieldWall>2000||shieldRemaining<=0)endShield();}
        if(beam)beam(p);
        for(var it=bodies.iterator();it.hasNext();){var b=it.next();b.age++;
            if(b.field){if(++b.fieldAge>80){it.remove();continue;}field(p,b);continue;}
            if(b.age>(b.ultimate?100:60)||b.travelled>=100){it.remove();continue;}
            var w=p.getServerWorld();var next=b.pos.add(b.vel);
            if(!w.isChunkLoaded(BlockPos.ofFloored(next))){it.remove();continue;}
            var wall=w.raycast(new RaycastContext(b.pos,next,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
            var end=wall.getType()==HitResult.Type.BLOCK?wall.getPos():next;
            Entity victim=null;Vec3d contact=null;double nearest=b.pos.squaredDistanceTo(end);
            for(var e:NativeDamageTargets.in(w,p,new Box(b.pos,end).expand(.2))){
                if(!enemy(p,e))continue;var at=e.getBoundingBox().expand(.1).raycast(b.pos,end);
                if(at.isPresent()&&at.get().squaredDistanceTo(b.pos)<nearest){nearest=at.get().squaredDistanceTo(b.pos);victim=e;contact=at.get();}}
            if(victim!=null||wall.getType()==HitResult.Type.BLOCK){
                b.pos=contact!=null?contact:end;
                if(b.ultimate){
                    if(victim!=null){var r=NativeDamageTargets.projectileDamage(w,victim,p,5*NativeShotSimulation.HP_SCALE);if(r.applied()){directHits++;damageApplied+=r.healthLost();}}
                    b.field=true;b.vel=Vec3d.ZERO;fields++;
                }else{explode(p,b);it.remove();}
            }else{b.travelled+=b.pos.distanceTo(next);b.pos=next;b.vel=b.vel.add(0,-GRAVITY,0);}
        }
        publish();
    }
    private static boolean enemy(ServerPlayerEntity p,Entity e){var owner=NativeDamageTargets.owner(e);return owner!=p&&!(owner instanceof PlayerEntity)&&!p.isTeammate(owner);}
    private static boolean visible(ServerPlayerEntity p,Vec3d from,Vec3d to){
        var hit=p.getServerWorld().raycast(new RaycastContext(from,to,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
        return hit.getType()!=HitResult.Type.BLOCK||from.squaredDistanceTo(hit.getPos())>=from.squaredDistanceTo(to)-.001;
    }
    private void beam(ServerPlayerEntity p){
        var w=p.getServerWorld();var from=p.getEyePos();var end=from.add(p.getRotationVec(1).normalize().multiply(BEAM_RANGE));
        var wall=w.raycast(new RaycastContext(from,end,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
        if(wall.getType()==HitResult.Type.BLOCK)end=wall.getPos();
        Entity best=null;double nearest=from.squaredDistanceTo(end);
        for(var e:NativeDamageTargets.in(w,p,new Box(from,end).expand(BEAM_WIDTH))){
            if(!enemy(p,e))continue;var at=e.getBoundingBox().expand(BEAM_WIDTH).raycast(from,end);
            if(at.isPresent()&&at.get().squaredDistanceTo(from)<nearest&&visible(p,from,at.get())){nearest=at.get().squaredDistanceTo(from);best=e;}}
        if(best!=null){var r=NativeDamageTargets.beamDamage(w,best,p,BEAM_DPS/20*NativeShotSimulation.HP_SCALE);if(r.applied()){beamHits++;damageApplied+=r.healthLost();}}
        // Keep the actual selected entity intercept, or the actual block/range end.
        beamFrom=from;beamTo=best==null?end:from.add(end.subtract(from).normalize().multiply(Math.sqrt(nearest)));beamWall=heartbeat;
        var d=end.subtract(from);for(int i=1;i<=20;i++){var at=from.add(d.multiply(i/20.0));w.spawnParticles(ParticleTypes.END_ROD,at.x,at.y,at.z,1,0,0,0,0);}
    }
    private void explode(ServerPlayerEntity p,Body b){
        explosions++;var w=p.getServerWorld();w.spawnParticles(ParticleTypes.EXPLOSION,b.pos.x,b.pos.y,b.pos.z,1,0,0,0,0);
        var damaged=new HashSet<Integer>();
        for(var e:NativeDamageTargets.in(w,p,new Box(b.pos,b.pos).expand(OUTER+1))){
            if(!enemy(p,e))continue;int id=NativeDamageTargets.owner(e).getId();if(damaged.contains(id))continue;
            double dist=Math.sqrt(e.getBoundingBox().squaredMagnitude(b.pos));if(dist>OUTER||!visible(p,b.pos,e.getBoundingBox().getCenter()))continue;
            damaged.add(id);double factor=dist<=INNER?1:Math.max(0,(OUTER-dist)/(OUTER-INNER));
            var r=NativeDamageTargets.explosionDamage(w,e,p,GRENADE*factor*NativeShotSimulation.HP_SCALE);
            if(r.applied()){blastHits++;damageApplied+=r.healthLost();}
        }
    }
    private void field(ServerPlayerEntity p,Body b){
        var w=p.getServerWorld();w.spawnParticles(ParticleTypes.PORTAL,b.pos.x,b.pos.y,b.pos.z,12,.6,.6,.6,.05);
        for(var e:w.getEntitiesByClass(LivingEntity.class,new Box(b.pos,b.pos).expand(FIELD_RADIUS),Entity::isAlive)){
            if(!enemy(p,e)||!(e instanceof net.minecraft.entity.mob.MobEntity)||RandomBossTravel.isBoss(e))continue;
            var delta=b.pos.subtract(e.getBoundingBox().getCenter());double distance=delta.length();
            if(distance>FIELD_RADIUS||!visible(p,b.pos,e.getBoundingBox().getCenter()))continue;
            var motion=distance<.2?Vec3d.ZERO:delta.normalize().multiply(Math.min(.2,distance*.08));
            e.setVelocity(motion);e.velocityModified=true;pulls++;
            if(b.fieldAge%10==0){var r=NativeDamageTargets.beamDamage(w,e,p,FIELD_DPS/2*NativeShotSimulation.HP_SCALE);if(r.applied())damageApplied+=r.healthLost();}
        }
    }
    private void accountShield(){
        if(shieldOwner==null)return;float current=shieldOwner.getAbsorptionAmount();
        float used=Math.min(shieldRemaining,Math.max(0,lastAbsorption-current));
        shieldRemaining-=used;absorptionConsumed+=used;lastAbsorption=current;
    }
    private void beginShield(ServerPlayerEntity p,long now){
        endShield();selfCasts++;casts++;
        var capacity=p.getAttributeInstance(EntityAttributes.GENERIC_MAX_ABSORPTION);
        if(capacity==null||capacity.hasModifier(SHIELD_CAPACITY_ID)){selfGrantFailures++;return;}
        // 1.21.1 clamps setAbsorptionAmount to getMaxAbsorption (default 0),
        // independently of creative/survival. Raise capacity BEFORE granting.
        // A temporary, uniquely-owned modifier preserves base values and potions.
        shieldOwner=p;shieldCapacity=capacity;shieldWall=now;
        shieldCapacityModifier=new EntityAttributeModifier(SHIELD_CAPACITY_ID,SHIELD_HP,EntityAttributeModifier.Operation.ADD_VALUE);
        float before=p.getAbsorptionAmount();capacity.addTemporaryModifier(shieldCapacityModifier);
        p.setAbsorptionAmount(before+SHIELD_HP);
        lastAbsorption=p.getAbsorptionAmount();shieldRemaining=Math.max(0,lastAbsorption-before);
        selfGranted+=shieldRemaining;shield=shieldRemaining>0;
        if(!shield){selfGrantFailures++;endShield();}
    }
    private void endShield(){
        if(shieldOwner!=null){accountShield();shieldOwner.setAbsorptionAmount(Math.max(0,shieldOwner.getAbsorptionAmount()-shieldRemaining));shieldEnds++;}
        if(shieldCapacity!=null&&shieldCapacity.getModifier(SHIELD_CAPACITY_ID)==shieldCapacityModifier)shieldCapacity.removeModifier(SHIELD_CAPACITY_ID);
        shieldCapacity=null;shieldCapacityModifier=null;
        shieldOwner=null;shieldRemaining=0;shield=false;
    }
    private void clearOwned(){candidateEvidence=Map.of();endShield();bodies.clear();scope=null;beam=false;beamFrom=beamTo=null;beamWall=0;heartbeat=0;views=List.of();selfSignal=new SelfSignal(false,0,false,false);}
    private void publish(){
        long now=System.currentTimeMillis();var v=new ArrayList<View>();
        if(scope!=null)for(var b:bodies)v.add(new View(scope.world(),now,b.pos,b.vel,b.ultimate,b.field,b.age));views=List.copyOf(v);
        var o=new JsonObject();o.add("nativeCandidates",EVIDENCE_JSON.toJsonTree(candidateEvidence));
        o.addProperty("candidateEffectsEnabled",false);
        o.addProperty("active",scope!=null);o.addProperty("casts",casts);o.addProperty("hits",beamHits+directHits+blastHits);
        o.addProperty("damageApplied",damageApplied);o.addProperty("beamActive",beam);o.addProperty("beamCasts",beamCasts);o.addProperty("beamHits",beamHits);
        o.addProperty("grenades",grenades);o.addProperty("gravitons",gravitons);o.addProperty("explosions",explosions);o.addProperty("directHits",directHits);o.addProperty("blastHits",blastHits);
        o.addProperty("fields",fields);o.addProperty("pulls",pulls);o.addProperty("bodies",bodies.size());o.addProperty("fieldActive",bodies.stream().anyMatch(b->b.field));
        o.addProperty("selfCasts",selfCasts);o.addProperty("selfActive",shield);o.addProperty("shieldRemaining",shieldRemaining);o.addProperty("shieldEnds",shieldEnds);
        o.addProperty("selfGranted",selfGranted);o.addProperty("selfGrantFailures",selfGrantFailures);
        o.addProperty("selfNodeReadable",selfSignal.readable());o.addProperty("selfNativeTick",selfSignal.tick());o.addProperty("selfNativeActive",selfSignal.active());
        o.addProperty("selfNativeBaseline",selfSignal.baseline());o.addProperty("selfNodeBaselines",selfNodeBaselines);o.addProperty("selfLastBeginTick",selfLastBeginTick);
        o.addProperty("shieldPlayerAbsorption",shieldOwner==null?0:shieldOwner.getAbsorptionAmount());
        o.addProperty("shieldMaxAbsorption",shieldOwner==null?0:shieldOwner.getMaxAbsorption());
        o.addProperty("absorptionConsumed",absorptionConsumed);o.addProperty("projectedAttempts",projectedAttempts);o.addProperty("projectedCandidates",projectedCandidates);o.addProperty("projectedEnabled",false);
        o.addProperty("energySynchronized",false);o.addProperty("rejected",rejected);
        o.addProperty("pending","E search is not shield confirmation; native absorb->energy/cleanse/target mapping and shield GUID unavailable; no native Q field lifecycle proof");
        o.addProperty("mcAdaptation","beam hit/95DPS; grenade80/falloff; self20MC absorption; Q contact field6m/4s/pull/5DPS; no energy scaling");
        // integrator/models: presentation of accepted state only; preserve its real lease.
if(scope!=null&&shield&&shieldOwner!=null){
    var f=OriginalEffectFrames.frame(scope.owner(),scope.world(),scope.source(),scope.model(),heartbeat);
    OriginalEffectFrames.body(f,"zarya-barrier",shieldOwner.getBoundingBox().getCenter(),new Vec3d(1,1,1),.22f,false);
    o.add("models",f);
}
        
        // integrator/models: only real state/geometry, never input-derived effects.
if(scope!=null&&beam&&beamFrom!=null&&beamTo!=null&&beamWall>0){
            var f=o.has("models")?o.getAsJsonObject("models"):OriginalEffectFrames.frame(scope.owner(),scope.world(),scope.source(),scope.model(),beamWall);
            f.addProperty("wall",Math.min(f.get("wall").getAsLong(),beamWall));
            OriginalEffectFrames.beam(f,"zarya-beam",beamFrom,beamTo,.08f,.8f);o.add("models",f);
        }
        json=o.toString();
    }
    @Override public void resetSession(){resetRequested=true;}
    /** Existing registry calls clear on SERVER_STOPPING, before world saving. */
    @Override public void clear(){clearOwned();resetRequested=false;publish();}
    @Override public String statusKey(){return "zarya";}
    @Override public String status(){return json;}
}
