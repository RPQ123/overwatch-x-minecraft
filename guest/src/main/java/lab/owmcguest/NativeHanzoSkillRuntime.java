package lab.owmcguest;

import java.util.*;
import java.util.concurrent.ArrayBlockingQueue;
import com.google.gson.JsonObject;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.particle.DustParticleEffect;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvents;
import net.minecraft.util.hit.BlockHitResult;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.RaycastContext;
import org.joml.Vector3f;

/** 半藏 E 散射箭、Q 龙击。原版 graph b9 的 Volley26/Volley76 新 tick 各准入一次；分裂、反弹、龙体由 MC 补。
 * 原版声明（SKILL-BRIEFS-20261025.md §6）：父箭 90 m/s、重力 9.8；子箭 6 支、散布 20°、反弹系数 .9、最多 5 次；
 * 龙击起始箭 20 m/s、射程 10 m、寿命 5 s、无重力；0132:25 的 1a6=4 绑定 TrackTargets.m_radius。
 * 龙体速度/射程/伤害、穿墙策略和缠绕动画仍是 MC 适配，见 docs/NATIVE-HANZO-DRAGON.md。
 * 缺少同次认证工厂+typed2a5/1dc/980时，保留母箭90/子箭52 m/s；伤害75×4=300。
 * MC 适配：用户要求，原版参数与fallback的母/子箭伤害均×4，反弹沿用该值；status明确标原因。 */
public final class NativeHanzoSkillRuntime {
    public record Scope(UUID owner,long world,long source,long model){}
    private static long arrowSequence;
    private static final class Arrow{final long visualId=++arrowSequence;Scope scope;Vec3d pos,vel;boolean child,parent;int bounces,age;double distance;
        double damage=ARROW_DAMAGE,childDamage=ARROW_DAMAGE,childSpeed=CHILD;final Set<UUID> hit=new HashSet<>();}
    private record Embedded(Scope scope,Vec3d at,Vec3d direction,boolean child,int expires){}
    private static final List<Embedded> embedded=new ArrayList<>();
    // MC presentation adaptation: beta block-arrow retention has not been authenticated.
    static final int STUCK_TICKS=200,MAX_EMBEDDED=256;
    private static final class Dragon{Scope scope;Vec3d start,dir,pos,previous;int age;double travelled;boolean released;long begin;final Map<UUID,Integer> lastHit=new HashMap<>();}
    static final double PARENT=90/20.0,CHILD=52/20.0,G=9.8/400,SPREAD=Math.toRadians(20),RESTITUTION=.9,ARROW_DAMAGE=HanzoScatterContext.FALLBACK_DAMAGE;
    // 原版 b9:76：速度20 m/s、range10 m、lifetime5 s（MC 20 tick/s 换算）。
    static final double DRAGON_START=20/20.0,DRAGON_START_RANGE=10;
    static final int DRAGON_START_LIFETIME=5*20;
    // 原版 0132:25 -> 1a6=4 -> TrackTargets:1/7/10/20/36/38/44.m_radius。
    static final double DRAGON_RADIUS=4;
    // MC 适配：双龙的原版运动/伤害表达式未完成解释，保留原实现数值。
    // MC 适配：用户要求（2026-10-27）——射程 60→120 m，沿途生物秒杀、方块清除（不可破坏方块除外，无掉落）。
    static final double DRAGON_SPEED=20/20.0,DRAGON_RANGE=120,DRAGON_DPS=200;
    static final boolean DRAGON_DEVOUR=true;
    private static long dragonBlocksCleared,dragonKills;
    static final int DRAGON_HIT_INTERVAL=10; // MC 适配：每0.5秒一次，合计200 OW HP/s。
    static final double DRAGON_COIL_RADIUS=1.2,DRAGON_ANGULAR_SPEED=.6; // MC 适配：m、rad/tick。
    static final int CHILDREN=6,MAX_BOUNCES=5;
    private static final DustParticleEffect BLUE=new DustParticleEffect(new Vector3f(.35f,.75f,1f),1.6f);
    private static final List<Arrow> arrows=new ArrayList<>();private static final List<Dragon> dragons=new ArrayList<>();
    private static long scatters,splits,childHits,dragonCasts,dragonHits;private static double damageApplied;
    private static long scatterNativeContexts,scatterFallbackContexts,scatterChildrenCreated;
    private static HanzoScatterContext.Parameters lastScatterContext=HanzoScatterContext.fallback("no Scatter cast yet");
    public record ArrowView(Vec3d at,Vec3d vel,Scope scope,boolean scatter,boolean child,boolean stuck,long wall,String visualId){
        public ArrowView(Vec3d at,Vec3d vel,Scope scope,boolean scatter,boolean child,boolean stuck,long wall){this(at,vel,scope,scatter,child,stuck,wall,"");}
        // Existing dragon-start publication retains its old constructor/behavior.
        public ArrowView(Vec3d at,Vec3d vel,Scope scope){this(at,vel,scope,false,false,false,System.currentTimeMillis());}
    }
    public static volatile List<ArrowView> arrowViews=List.of();
    public record DragonView(Vec3d previous,Vec3d at,Vec3d direction,Scope scope,int age,
                             double travelled,boolean released,long sampledNanos){}
    public static volatile List<DragonView> dragonViews=List.of();
    public record DragonFlight(Scope scope,long begin,boolean released,long wall){}
    public static volatile DragonFlight dragonFlight;
    public static volatile long controlsEpoch;
    // 语音挂接：真实放龙回执供客户端播放私有空间音效，不走人声队列。
    public record DragonRoar(Scope scope,Vec3d at,long sequence,long observedNanos){}
    private static final ArrayBlockingQueue<DragonRoar> dragonRoars=new ArrayBlockingQueue<>(16);
    private static long dragonReleases;
    public static DragonRoar pollDragonRoar(){return dragonRoars.poll();}
    public static volatile String status="{}";

    private static ServerPlayerEntity owner(MinecraftServer server,Scope s){
        var p=s==null?null:server.getPlayerManager().getPlayer(s.owner());
        return p!=null&&p.isAlive()&&NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())==s.world()?p:null;
    }
    public static void scatter(MinecraftServer server,Scope scope){
        scatter(server,scope,HanzoScatterContext.fallback("no context supplied; unchanged MC fallback"));
    }
    public static void scatter(MinecraftServer server,Scope scope,HanzoScatterContext.Parameters parameters){
        scatter(server,scope,parameters,"");
    }
    public static void scatter(MinecraftServer server,Scope scope,HanzoScatterContext.Parameters parameters,String visualLaunch){
        var p=owner(server,scope);if(p==null)return;var a=new Arrow();a.scope=scope;a.parent=true;
        MuzzlePresentation.alias(visualLaunch,"scatter:"+a.visualId);
        var values=parameters==null?HanzoScatterContext.fallback("Scatter context unavailable"):parameters;
        a.pos=p.getEyePos();a.vel=values.nativeValues()?new Vec3d(values.velocity().x(),values.velocity().y(),values.velocity().z()).multiply(1/20.0):p.getRotationVec(1).multiply(PARENT);
        a.damage=values.parentDamage();a.childDamage=values.childDamage();a.childSpeed=values.childSpeed()/20;
        lastScatterContext=values;if(values.nativeValues())scatterNativeContexts++;else scatterFallbackContexts++;
        arrows.add(a);scatters++;publish();
    }
    public static void dragon(MinecraftServer server,Scope scope){
        dragon(server,scope,0);
    }
    public static void dragon(MinecraftServer server,Scope scope,long begin){
        var p=owner(server,scope);if(p==null)return;var d=new Dragon();d.scope=scope;d.start=p.getEyePos();d.dir=p.getRotationVec(1).normalize();d.pos=d.previous=d.start;
        d.begin=begin;dragonFlight=new DragonFlight(scope,begin,false,System.currentTimeMillis());
        dragons.add(d);dragonCasts++;publish();
    }
    public static void tick(MinecraftServer server){
        if(arrows.isEmpty()&&dragons.isEmpty()&&embedded.isEmpty())return;
        embedded.removeIf(a->server.getTicks()>=a.expires()||scatterOwner(server,a.scope())==null);
        for(var a:new ArrayList<>(arrows)){
            var p=scatterOwner(server,a.scope);if(p==null||++a.age>200||a.distance>=300){arrows.remove(a);continue;}
            var w=p.getServerWorld();var next=a.pos.add(a.vel);
            double step=a.pos.distanceTo(next);if(step>300-a.distance)next=a.pos.lerp(next,(300-a.distance)/step);
            // Keep loaded-prefix contacts; an unavailable chunk is never itself
            // an impact, split, bounce or embedded arrow.
            var clip=LoadedRayPrefix.clip(new NativeShotProtocol.Vec(a.pos.x,a.pos.y,a.pos.z),
                new NativeShotProtocol.Vec(next.x,next.y,next.z),(x,z)->w.getChunkManager().isChunkLoaded(x,z));
            if(clip.fraction()==0){arrows.remove(a);continue;}
            next=a.pos.lerp(next,clip.fraction());
            var hit=w.raycast(new RaycastContext(a.pos,next,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
            a.distance+=a.pos.distanceTo(hit.getType()==HitResult.Type.BLOCK?hit.getPos():next);
            var mob=firstMob(w,a.pos,hit.getType()==HitResult.Type.BLOCK?hit.getPos():next,a.hit);  // 只判墙前的目标
            if(mob!=null){a.hit.add(mob.getUuid());var r=NativeDamageTargets.projectileDamage(w,mob,p,a.damage*NativeShotSimulation.HP_SCALE);if(r.applied()){childHits++;damageApplied+=r.healthLost();}
                if(a.parent){var contact=mob.getBoundingBox().expand(.1).raycast(a.pos,next).orElse(mob.getPos().add(0,mob.getHeight()/2,0));present(a,contact,HanzoArrowEffects.Contact.SPLIT);split(a,contact,a.vel.normalize().multiply(-1));arrows.remove(a);continue;}}
            if(!clip.complete()&&hit.getType()!=HitResult.Type.BLOCK){present(a,next,HanzoArrowEffects.Contact.NONE);arrows.remove(a);continue;}
            if(hit.getType()==HitResult.Type.BLOCK){var bh=(BlockHitResult)hit;var n=Vec3d.of(bh.getSide().getVector());
                if(a.parent){present(a,bh.getPos(),HanzoArrowEffects.Contact.SPLIT);embed(server,a,bh.getPos());split(a,bh.getPos().add(n.multiply(.05)),n);arrows.remove(a);w.playSound(null,bh.getPos().x,bh.getPos().y,bh.getPos().z,SoundEvents.ENTITY_ARROW_HIT,SoundCategory.PLAYERS,1f,1.4f);continue;}
                if(++a.bounces>MAX_BOUNCES){present(a,bh.getPos(),HanzoArrowEffects.Contact.STUCK);embed(server,a,bh.getPos());arrows.remove(a);continue;}
                present(a,bh.getPos(),HanzoArrowEffects.Contact.BOUNCE);
                var vn=n.multiply(a.vel.dotProduct(n));a.vel=a.vel.subtract(vn.multiply(2)).multiply(RESTITUTION);a.pos=bh.getPos().add(n.multiply(.05));
            }else {present(a,next,HanzoArrowEffects.Contact.NONE);a.pos=next;}
            a.vel=a.vel.add(0,-G,0);
        }
        for(var d:new ArrayList<>(dragons)){
            var p=owner(server,d.scope);if(p==null){dragons.remove(d);continue;}var w=p.getServerWorld();d.age++;d.previous=d.pos;
            if(!d.released){
                if(d.age>DRAGON_START_LIFETIME){dragons.remove(d);continue;}
                d.pos=d.pos.add(d.dir.multiply(DRAGON_START));
                if(d.pos.distanceTo(d.start)>=DRAGON_START_RANGE){d.released=true;
                    if(dragonFlight!=null&&dragonFlight.scope().equals(d.scope)&&dragonFlight.begin()==d.begin)
                        dragonFlight=new DragonFlight(d.scope,d.begin,true,System.currentTimeMillis());
                    // 语音挂接：原版龙吼由客户端私有素材播放，删除末影龙替代声。
                    dragonRoars.offer(new DragonRoar(d.scope,d.pos,++dragonReleases,System.nanoTime()));}
                continue;
            }
            // MC 适配：保留穿墙和单球伤害体；原版7个TrackTargets的布局/遮挡未完整复原。
            d.pos=d.pos.add(d.dir.multiply(DRAGON_SPEED));d.travelled+=DRAGON_SPEED;
            if(d.travelled>DRAGON_RANGE){dragons.remove(d);continue;}
            var side=new Vec3d(0,1,0).crossProduct(d.dir);if(side.lengthSquared()<1e-4)side=new Vec3d(1,0,0);side=side.normalize();var up=d.dir.crossProduct(side).normalize();
            double phase=d.age*DRAGON_ANGULAR_SPEED;for(int k=0;k<2;k++){double ph=phase+k*Math.PI;var at=d.pos.subtract(d.dir.multiply(2)).add(side.multiply(Math.cos(ph)*DRAGON_COIL_RADIUS)).add(up.multiply(Math.sin(ph)*DRAGON_COIL_RADIUS));w.spawnParticles(BLUE,at.x,at.y,at.z,1,.1,.1,.1,0);}
            for(var e:w.getEntitiesByClass(LivingEntity.class,new Box(d.pos,d.pos).expand(DRAGON_RADIUS),e->e.isAlive()&&!(e instanceof PlayerEntity))){
                if(e.getBoundingBox().getCenter().distanceTo(d.pos)>DRAGON_RADIUS+.5)continue;
                if(DRAGON_DEVOUR){
                    // 先以半藏为攻击者打满（保留击杀归属/击杀语音），仍存活再直接击杀。
                    var r=NativeDamageTargets.explosionDamage(w,e,p,(e.getMaxHealth()+e.getAbsorptionAmount())*4+1000);
                    if(r.applied()){dragonHits++;damageApplied+=r.healthLost();}
                    if(e.isAlive())e.kill();
                    if(!e.isAlive())dragonKills++;
                    continue;
                }
                var last=d.lastHit.get(e.getUuid());if(last!=null&&d.age-last<DRAGON_HIT_INTERVAL)continue;
                d.lastHit.put(e.getUuid(),d.age);var r=NativeDamageTargets.explosionDamage(w,e,p,DRAGON_DPS*DRAGON_HIT_INTERVAL/20.0*NativeShotSimulation.HP_SCALE);if(r.applied()){dragonHits++;damageApplied+=r.healthLost();}
            }
            if(DRAGON_DEVOUR)devourBlocks(w,d.pos);
        }
        publish();
    }
    /** MC 适配：清除龙体球内全部可破坏方块；只处理已加载区块，不掉落物品，不碰基岩等不可破坏方块。 */
    private static void devourBlocks(ServerWorld w,Vec3d at){
        int r=(int)Math.ceil(DRAGON_RADIUS);var c=net.minecraft.util.math.BlockPos.ofFloored(at);var m=new net.minecraft.util.math.BlockPos.Mutable();
        for(int x=-r;x<=r;x++)for(int y=-r;y<=r;y++)for(int z=-r;z<=r;z++){
            if(x*x+y*y+z*z>DRAGON_RADIUS*DRAGON_RADIUS)continue;m.set(c.getX()+x,c.getY()+y,c.getZ()+z);
            if(w.isOutOfHeightLimit(m)||!w.isChunkLoaded(m.getX()>>4,m.getZ()>>4))continue;
            var state=w.getBlockState(m);if(state.isAir()||state.getHardness(w,m)<0)continue;
            if(w.setBlockState(m,net.minecraft.block.Blocks.AIR.getDefaultState(),net.minecraft.block.Block.NOTIFY_ALL|net.minecraft.block.Block.SKIP_DROPS))dragonBlocksCleared++;
        }
    }
    /** 原版 6 支子箭：以撞击面法线为轴，在 20° 散布内均匀分布。 */
    private static void split(Arrow parent,Vec3d at,Vec3d normal){
        splits++;scatterChildrenCreated+=CHILDREN;var axis=normal.normalize();var t=axis.crossProduct(new Vec3d(0,1,0));if(t.lengthSquared()<1e-4)t=new Vec3d(1,0,0);t=t.normalize();var b=axis.crossProduct(t).normalize();
        for(int i=0;i<CHILDREN;i++){double az=2*Math.PI*i/CHILDREN;var dir=axis.multiply(Math.cos(SPREAD)).add(t.multiply(Math.sin(SPREAD)*Math.cos(az))).add(b.multiply(Math.sin(SPREAD)*Math.sin(az))).normalize();
            var c=new Arrow();c.scope=parent.scope;c.child=true;c.pos=at;c.vel=dir.multiply(parent.childSpeed);c.damage=parent.childDamage;c.hit.addAll(parent.hit);arrows.add(c);}
    }
    private static LivingEntity firstMob(ServerWorld w,Vec3d from,Vec3d to,Set<UUID> skip){
        LivingEntity best=null;double bd=Double.MAX_VALUE;
        for(var e:w.getEntitiesByClass(LivingEntity.class,new Box(from,to).expand(.3),e->e.isAlive()&&!(e instanceof PlayerEntity)&&!skip.contains(e.getUuid()))){
            var h=e.getBoundingBox().expand(.1).raycast(from,to);if(h.isPresent()){double d=from.squaredDistanceTo(h.get());if(d<bd){bd=d;best=e;}}}
        return best;
    }
    private static ServerPlayerEntity scatterOwner(MinecraftServer server,Scope scope){
        var p=owner(server,scope);
        return p!=null&&NativeEliminationRuntime.sessionMatches(scope.owner(),scope.world(),HanzoSonicArrowState.HERO,scope.model(),scope.source())?p:null;
    }
    private static void embed(MinecraftServer server,Arrow arrow,Vec3d at){
        if(embedded.size()>=MAX_EMBEDDED)embedded.remove(0);
        embedded.add(new Embedded(arrow.scope,at,arrow.vel,arrow.child,server.getTicks()+STUCK_TICKS));
    }
    private static void present(Arrow a,Vec3d to,HanzoArrowEffects.Contact contact){
        if(contact!=HanzoArrowEffects.Contact.NONE)MuzzlePresentation.contact("scatter:"+a.visualId,new NativeShotProtocol.Vec(to.x,to.y,to.z));
        var s=a.scope;HanzoArrowEffects.segment(new HanzoArrowEffects.Scope(s.owner(),s.world(),s.model(),s.source()),
            "scatter:"+a.visualId,HanzoArrowEffects.Kind.SCATTER,a.child,
            new NativeShotProtocol.Vec(a.pos.x,a.pos.y,a.pos.z),new NativeShotProtocol.Vec(to.x,to.y,to.z),contact);
    }
    private static void publish(){
        long wall=System.currentTimeMillis();
        var av=new ArrayList<ArrowView>();for(var x:arrows)av.add(new ArrowView(x.pos,x.vel,x.scope,true,x.child,false,wall,"scatter:"+x.visualId));
        for(var x:embedded)av.add(new ArrowView(x.at(),x.direction(),x.scope(),true,x.child(),true,wall));
        arrowViews=List.copyOf(av);
        var dv=new ArrayList<DragonView>();long sampled=System.nanoTime();
        for(var d:dragons)dv.add(new DragonView(d.previous,d.pos,d.dir,d.scope,d.age,d.travelled,d.released,sampled));
        dragonViews=List.copyOf(dv);
        var o=new JsonObject();o.addProperty("arrows",arrows.size());o.addProperty("dragons",dragons.size());o.addProperty("scatters",scatters);o.addProperty("splits",splits);
        o.addProperty("dragonRadius",DRAGON_RADIUS);o.addProperty("dragonSpeedMps",DRAGON_SPEED*20);o.addProperty("dragonRange",DRAGON_RANGE);o.addProperty("dragonDps",DRAGON_DPS);o.addProperty("dragonMcAdapted",true);o.addProperty("dragonDevour",DRAGON_DEVOUR);o.addProperty("dragonKills",dragonKills);o.addProperty("dragonBlocksCleared",dragonBlocksCleared);
        o.addProperty("childHits",childHits);o.addProperty("dragonCasts",dragonCasts);o.addProperty("dragonHits",dragonHits);o.addProperty("damageApplied",damageApplied);o.addProperty("embeddedArrows",embedded.size());o.addProperty("embeddedRetentionTicks",STUCK_TICKS);
        o.addProperty("scatterNativeContexts",scatterNativeContexts);o.addProperty("scatterFallbackContexts",scatterFallbackContexts);
        o.addProperty("scatterChildrenCreated",scatterChildrenCreated);
        var anchors=new com.google.gson.JsonArray();for(var anchor:embedded){var row=new JsonObject();row.addProperty("kind",anchor.child()?"SCATTER_CHILD":"SCATTER_PARENT");
            row.addProperty("x",anchor.at().x);row.addProperty("y",anchor.at().y);row.addProperty("z",anchor.at().z);row.addProperty("expiresTick",anchor.expires());anchors.add(row);}o.add("embeddedAnchors",anchors);
        var context=new com.google.gson.Gson().toJsonTree(lastScatterContext).getAsJsonObject();context.addProperty("chargeRead",lastScatterContext.nativeValues()?"typed original 0d800000000002a5":"unavailable; retained 90/52 m/s; damage 75×4=300 HP");
        context.addProperty("damageMultiplier",HanzoScatterContext.DAMAGE_MULTIPLIER);context.addProperty("damageAdaptation",HanzoScatterContext.DAMAGE_ADAPTATION);
        context.addProperty("baseParentDamage",lastScatterContext.parentDamage()/HanzoScatterContext.DAMAGE_MULTIPLIER);context.addProperty("baseChildDamage",lastScatterContext.childDamage()/HanzoScatterContext.DAMAGE_MULTIPLIER);
        o.add("scatterContext",context);status=o.toString();
        HanzoArrowEffects.publish();
    }
    public static void resetSession(){controlsEpoch++;arrows.clear();embedded.clear();HanzoArrowEffects.reset();dragons.clear();dragonRoars.clear();dragonFlight=null;publish();}
    public static void clear(){resetSession();}
}
