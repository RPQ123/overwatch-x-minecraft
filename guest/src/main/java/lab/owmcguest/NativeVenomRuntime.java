package lab.owmcguest;

import java.util.*;
import com.google.gson.JsonObject;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.particle.DustParticleEffect;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvents;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.RaycastContext;
import org.joml.Vector3f;

/** Widowmaker Venom Mine. The original E throw (graph0056 WeaponVolley node1) admits one
 * throw; the beta hands the mine itself to a server that does not exist here, so MC owns
 * flight, sticking, proximity trigger and poison. Beta policy: 75 damage over 5 s, scaled by
 * the project HP_SCALE; one mine per owner (a new throw replaces the old one).
 * MC adaptation (2026-10-27): one unbiased server-side draw per admitted native E;
 * 50% keeps the mine, 50% uses the same ballistics to land a tiny cave spider. */
public final class NativeVenomRuntime {
    public record Scope(UUID owner,long world,long source,long model){}
    // Original volley declarations (widow-venom-declarations.json): 20 m/s, 9.8 m/s², 5 s lifetime.
    static final double SPEED=20/20.0,GRAVITY=9.8/400.0,TRIGGER=3.0,NATIVE_TOTAL=75;
    static final int POISON_TICKS=100,FLIGHT_TICKS=100;
    private static final DustParticleEffect PURPLE=new DustParticleEffect(new Vector3f(.55f,.1f,.75f),1.2f);
    private static final class Mine{Scope scope;Vec3d pos,vel,normal=new Vec3d(0,1,0);boolean stuck,spider;int age;float yaw;String visualId="";}
    /** Presentation snapshot for the client renderer (original mesh). */
    public record View(UUID owner,long world,Vec3d at,Vec3d normal,boolean stuck,float yaw,int age,long wall,boolean spider,String visualId){
        public View(UUID owner,long world,Vec3d at,Vec3d normal,boolean stuck,float yaw,int age,long wall,boolean spider){this(owner,world,at,normal,stuck,yaw,age,wall,spider,"");}
    }
    public static volatile View view;
    /** Independent outline contribution; never changes a target's glowing flag or potion effects. */
    public record Revealed(UUID uuid,int ticksRemaining){}
    public record PoisonReveal(Scope scope,String dimension,long wall,Map<Integer,Revealed> entities){}
    public static volatile PoisonReveal poisonReveal;
    private record Poison(UUID owner,int startTick){}
    private static JsonObject models;
    private static final Map<UUID,Scope> poisonScopes=new HashMap<>();
    private static Mine mine;private static final Map<UUID,Poison> poisoned=new HashMap<>();
    private static final Map<UUID,WidowSpiderEntity> spiders=new HashMap<>();
    private static long mineRolls,spiderRolls,spiderSpawns,spiderSpawnFailures,spiderHits,spiderTimeouts,spiderDecayTicks;
    private static double spiderDamageApplied,spiderHealthDecayed;
    private static long throwsAdmitted,stuckCount,detonations,poisonHits,expired;private static double damageApplied;
    public static volatile String status="{\"mine\":false}";

    private static ServerPlayerEntity owner(MinecraftServer server,Scope s){
        var p=s==null?null:server.getPlayerManager().getPlayer(s.owner());
        return p!=null&&p.isAlive()&&NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())==s.world()
            &&NativeEliminationRuntime.sessionMatches(s.owner(),s.world(),0x02e000000000000aL,s.model(),s.source())?p:null;
    }
    /** One original throw: called once per fresh node1 tick. */
    public static void cast(MinecraftServer server,Scope scope){
        cast(server,scope,"");
    }
    public static void cast(MinecraftServer server,Scope scope,String visualId){
        var p=owner(server,scope);if(p==null)return;
        var m=new Mine();m.scope=scope;m.pos=p.getEyePos().add(p.getRotationVec(1).multiply(.5));m.vel=p.getRotationVec(1).multiply(SPEED);m.yaw=p.getYaw();
        m.visualId=visualId;
        m.spider=p.getRandom().nextBoolean();if(m.spider)spiderRolls++;else mineRolls++;
        mine=m;throwsAdmitted++;publish();
    }
    public static void tick(MinecraftServer server){
        int now=server.getTicks();
        boolean hadSpiders=!spiders.isEmpty();
        boolean hadPoison=!poisoned.isEmpty();
        spiders.values().removeIf(e->e.isRemoved()||!e.isAlive());
        if(hadPoison)tickPoison(server,now);
        sampleModels(server);
        sampleReveals(server,now);
        if(mine==null){if(hadSpiders||hadPoison)publish();return;}var p=owner(server,mine.scope);if(p==null){mine=null;publish();return;}
        var w=p.getServerWorld();var m=mine;m.age++;
        if(!m.stuck){
            var next=m.pos.add(m.vel);var hit=w.raycast(new RaycastContext(m.pos,next,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
            if(hit.getType()==HitResult.Type.BLOCK){
                var block=(net.minecraft.util.hit.BlockHitResult)hit;
                m.pos=hit.getPos();m.normal=Vec3d.of(block.getSide().getVector());
                if(m.spider){
                    if(block.getSide()==net.minecraft.util.math.Direction.UP){landSpider(w,m);mine=null;publish();return;}
                    // A wall/ceiling stops the horizontal throw; drop to actual ground before spawning.
                    m.pos=m.pos.add(m.normal.multiply(.12));m.vel=new Vec3d(0,Math.min(m.vel.y,0)-GRAVITY,0);
                }else{
                    m.stuck=true;stuckCount++;w.playSound(null,m.pos.x,m.pos.y,m.pos.z,SoundEvents.BLOCK_SLIME_BLOCK_PLACE,SoundCategory.PLAYERS,.8f,1.3f);
                }
            }
            else{m.pos=next;m.vel=m.vel.add(0,-GRAVITY,0);w.spawnParticles(PURPLE,m.pos.x,m.pos.y,m.pos.z,1,0,0,0,0);}
            if(!m.stuck&&m.age>FLIGHT_TICKS){mine=null;expired++;publish();return;}
        }
        if(m.stuck){
            if(m.age%10==0)w.spawnParticles(PURPLE,m.pos.x,m.pos.y+.05,m.pos.z,2,.05,.02,.05,0);
            var targets=targets(w,p,m.pos);if(!targets.isEmpty())detonate(w,p,m,targets,now);
        }
        publish();
    }
    private static void landSpider(ServerWorld world,Mine m){
        var spider=new WidowSpiderEntity(WidowSpiderEntity.TYPE,world);spider.launchedBy(m.scope);
        spider.refreshPositionAndAngles(m.pos.x,m.pos.y+.01,m.pos.z,m.yaw,0);
        if(!world.isChunkLoaded(spider.getBlockPos())||!world.isSpaceEmpty(spider,spider.getBoundingBox())
            ||!world.spawnEntity(spider)){spider.discard();spiderSpawnFailures++;return;}
        spiders.put(spider.getUuid(),spider);spiderSpawns++;
    }
    static void spiderHit(double lost){spiderHits++;spiderDamageApplied+=lost;}
    static void spiderDecay(double lost){spiderDecayTicks++;spiderHealthDecayed+=lost;}
    static void spiderTimedOut(){spiderTimeouts++;}
    private static List<LivingEntity> targets(ServerWorld w,ServerPlayerEntity p,Vec3d at){
        var box=new Box(at,at).expand(TRIGGER);List<LivingEntity> out=new ArrayList<>();
        for(var e:w.getEntitiesByClass(LivingEntity.class,box,e->e.isAlive()&&!(e instanceof PlayerEntity)&&!e.isSpectator())){
            var c=e.getBoundingBox().getCenter();if(c.squaredDistanceTo(at)>TRIGGER*TRIGGER)continue;
            var los=w.raycast(new RaycastContext(at.add(0,.1,0),c,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
            if(los.getType()==HitResult.Type.MISS||los.getPos().squaredDistanceTo(c)<.25)out.add(e);
        }
        return out;
    }
    private static void detonate(ServerWorld w,ServerPlayerEntity p,Mine m,List<LivingEntity> hit,int now){
        detonations++;mine=null;
        w.spawnParticles(PURPLE,m.pos.x,m.pos.y+.4,m.pos.z,60,1.2,.6,1.2,0);
        w.playSound(null,m.pos.x,m.pos.y,m.pos.z,SoundEvents.ENTITY_SPLASH_POTION_BREAK,SoundCategory.PLAYERS,1f,.8f);
        for(var e:hit){poisoned.put(e.getUuid(),new Poison(p.getUuid(),now));poisonScopes.put(e.getUuid(),m.scope);}
        sampleReveals(w.getServer(),now);
    }
    private static void tickPoison(MinecraftServer server,int now){
        double perSecond=NATIVE_TOTAL/(POISON_TICKS/20.0)*NativeShotSimulation.HP_SCALE;
        var it=poisoned.entrySet().iterator();
        while(it.hasNext()){
            var en=it.next();var po=en.getValue();int age=now-po.startTick();
            var p=server.getPlayerManager().getPlayer(po.owner());
            if(p==null||age>POISON_TICKS){it.remove();publish();continue;}
            if(age==0||age%20!=0)continue;
            var e=p.getServerWorld().getEntity(en.getKey());
            if(!(e instanceof LivingEntity l)||!l.isAlive()){it.remove();publish();continue;}
            var r=NativeDamageTargets.explosionDamage(p.getServerWorld(),l,p,perSecond);
            if(r.applied()){poisonHits++;damageApplied+=r.healthLost();}
            p.getServerWorld().spawnParticles(PURPLE,l.getX(),l.getY()+l.getHeight()*.6,l.getZ(),6,.3,.4,.3,0);
            // The fifth damage tick closes the same 100-tick interval used by the outline.
            if(age==POISON_TICKS)it.remove();
        }
    }
    private static void sampleReveals(MinecraftServer server,int now){
        Scope scope=null;String dimension=null;var revealed=new LinkedHashMap<Integer,Revealed>();
        for(var entry:poisoned.entrySet()){
            var poison=entry.getValue();int remaining=POISON_TICKS-(now-poison.startTick());
            var s=poisonScopes.get(entry.getKey());var p=owner(server,s);
            if(remaining<=0||remaining>POISON_TICKS||p==null)continue;
            var entity=p.getServerWorld().getEntity(entry.getKey());
            if(!(entity instanceof LivingEntity living)||!living.isAlive()||living.isSpectator())continue;
            if(scope==null){scope=s;dimension=p.getWorld().getRegistryKey().getValue().toString();}
            if(!scope.equals(s))continue;
            revealed.put(living.getId(),new Revealed(living.getUuid(),remaining));
        }
        poisonReveal=revealed.isEmpty()?null:new PoisonReveal(scope,dimension,System.currentTimeMillis(),Map.copyOf(revealed));
    }
    // Read only current poison targets on the server tick; never invent a trigger from age.
    private static void sampleModels(MinecraftServer server){
        models=null;poisonScopes.keySet().retainAll(poisoned.keySet());
        for(var id:poisoned.keySet()){
            var s=poisonScopes.get(id);var p=owner(server,s);
            if(p==null||!NativeEliminationRuntime.sessionMatches(s.owner(),s.world(),0x02e000000000000aL,s.model(),s.source()))continue;
            var e=p.getServerWorld().getEntity(id);if(!(e instanceof LivingEntity l)||!l.isAlive())continue;
            if(models==null)models=OriginalEffectFrames.frame(s.owner(),s.world(),s.source(),s.model(),System.currentTimeMillis());
            if(models.get("source").getAsLong()!=s.source()||models.get("model").getAsLong()!=s.model()||models.get("world").getAsLong()!=s.world())continue;
            if(models.getAsJsonArray("effects").size()>=128)break;
            OriginalEffectFrames.body(models,"widow-venom-gas",l.getBoundingBox().getCenter(),new Vec3d(1.2,1.2,1.2),.6f,true);
        }
    }
    private static void publish(){
        view=mine==null?null:new View(mine.scope.owner(),mine.scope.world(),mine.pos,mine.normal,mine.stuck,mine.yaw,mine.age,System.currentTimeMillis(),mine.spider,mine.visualId);
        var o=new JsonObject();o.addProperty("mine",mine!=null);o.addProperty("stuck",mine!=null&&mine.stuck);o.addProperty("throws",throwsAdmitted);
        o.addProperty("stuckCount",stuckCount);o.addProperty("detonations",detonations);o.addProperty("poisonHits",poisonHits);o.addProperty("expired",expired);
        o.addProperty("damageApplied",damageApplied);o.addProperty("poisoned",poisoned.size());
        var reveal=poisonReveal;o.addProperty("poisonRevealed",reveal==null?0:reveal.entities().size());
        o.addProperty("poisonRevealDurationTicks",POISON_TICKS);var revealTargets=new com.google.gson.JsonArray();
        if(reveal!=null)for(var entry:reveal.entities().entrySet()){
            var target=new JsonObject();target.addProperty("id",entry.getKey());target.addProperty("uuid",entry.getValue().uuid().toString());
            target.addProperty("ticksRemaining",entry.getValue().ticksRemaining());revealTargets.add(target);
        }
        o.add("poisonRevealTargets",revealTargets);
        o.addProperty("mineRolls",mineRolls);o.addProperty("spiderRolls",spiderRolls);o.addProperty("spiderProjectile",mine!=null&&mine.spider);
        o.addProperty("spiderSpawns",spiderSpawns);o.addProperty("spiderSpawnFailures",spiderSpawnFailures);
        o.addProperty("spidersAlive",spiders.size());o.addProperty("spiderHits",spiderHits);o.addProperty("spiderDamageApplied",spiderDamageApplied);
        o.addProperty("spiderTimeouts",spiderTimeouts);o.addProperty("spiderDecayTicks",spiderDecayTicks);o.addProperty("spiderHealthDecayed",spiderHealthDecayed);
        var active=new com.google.gson.JsonArray();
        for(var spider:spiders.values()){
            var s=new JsonObject();s.addProperty("uuid",spider.getUuid().toString());s.addProperty("age",spider.lifeTicks());
            s.addProperty("health",spider.getHealth());s.addProperty("width",spider.getWidth());s.addProperty("height",spider.getHeight());
            s.addProperty("scale",spider.getScale());s.addProperty("attackDamage",spider.getAttributeValue(net.minecraft.entity.attribute.EntityAttributes.GENERIC_ATTACK_DAMAGE));
            s.addProperty("target",spider.getTarget()==null?"":spider.getTarget().getUuid().toString());active.add(s);
        }
        o.add("spiders",active);
        if(mine!=null){o.addProperty("x",mine.pos.x);o.addProperty("y",mine.pos.y);o.addProperty("z",mine.pos.z);}
        
        // integrator/models: only real state/geometry, never input-derived effects.
if(models!=null)o.add("models",models);
        status=o.toString();
    }
    public static void resetSession(){mine=null;poisoned.clear();poisonScopes.clear();models=null;poisonReveal=null;for(var s:spiders.values())s.discard();spiders.clear();publish();}
    public static void clear(){resetSession();}
}
