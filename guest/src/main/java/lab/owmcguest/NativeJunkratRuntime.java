package lab.owmcguest;

import java.util.*;
import com.google.gson.JsonObject;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.effect.StatusEffectInstance;
import net.minecraft.entity.effect.StatusEffects;
import net.minecraft.entity.player.PlayerEntity;
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

/** 狂鼠：原版负责开火/技能判定、动画、弹药与冷却；投射物物理、爆炸、夹子由 MC 补。
 * 原版声明（SKILL-BRIEFS-20261025.md §5）：榴弹 022b:31 速度 20、重力 9.8、直击 40、爆炸 80（内 .5 外 2 m）、反弹 .5；
 * 震荡地雷 096a:12 速度 20、重力 20；捕兽夹 09ba:7 速度 10、重力 20。
 * MC适配：左键首次触地后引信1.5s、显示2倍、直击/爆炸伤害2倍、地形强度(Helix+.25)*2；
 * 地雷复用共用自身击退；被动仍旧引信，夹子80伤害/定身1.5s。 */
public final class NativeJunkratRuntime {
    public enum Kind{GRENADE,MINE,TRAP,DEATH_BOMB}
    public record Scope(UUID owner,long world,long source,long model){}
    private static final class Body{Kind kind;Scope scope;Vec3d pos,vel;boolean stuck;int age,bounces,firstGroundAge=-1;UUID trapped;int trappedAt;int nativePid;long nativeTick;}
    public record View(Kind kind,Vec3d at,boolean stuck,int age,long world,long wall,String visualId){
        public View(Kind kind,Vec3d at,boolean stuck,int age,long world,long wall){this(kind,at,stuck,age,world,wall,"");}
    }
    public static String visualId(int pid,long tick,Kind kind){return "junk:"+pid+":"+tick+":"+kind;}
    static final double G_GRENADE=9.8/400,G_THROWN=20/400.0,RESTITUTION=.5,DIRECT=40,BLAST=80,INNER=.5,OUTER=2,OUTER_SCALE=.125,TRAP_DAMAGE=80;
    static final int DEATH_FUSE=50,TRAP_ROOT=30,MAX_BODIES=32;
    private static final List<Body> bodies=new ArrayList<>();
    private static long grenades,mines,traps,explosions,directHits,blastHits,trapTriggers,detonations;private static double damageApplied;
    private static long terrainBursts,terrainBlocks;private static String terrainError="";
    private static long grenadeGroundContacts,grenadeFuseExplosions,mineImpulseRequests,mineImpulses,lastMineNativeTick;
    private static int lastGrenadeFuseElapsedTicks,lastMineNativePid;
    public static volatile List<View> views=List.of();public static volatile String status="{}";
    /** 只读原版快照诊断，由 client 发布；不能授权任何攻击。 */
    public static volatile String nativeSignals="{\"ready\":false,\"error\":\"waiting for native bindings\"}";
    private static Scope currentScope;private static boolean wasAlive;private static Vec3d lastFeet;
    private static long deaths,deathBombs;
    static{net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents.AFTER_DEATH.register((entity,source)->{
        if(entity instanceof ServerPlayerEntity p&&currentScope!=null&&wasAlive&&p.getUuid().equals(currentScope.owner())
            &&NativeWorldIdentity.of(p.getServer(),p.getWorld().getRegistryKey())==currentScope.world()){
            dropDeathBombs(p,currentScope);wasAlive=false;
        }
    });}

    /** MC 适配：真实 MC 生死沿驱动被动；不把声明的 Volley 当成已经发生的原版死亡事件。 */
    public static void observe(MinecraftServer server,Scope scope){
        var p=server.getPlayerManager().getPlayer(scope.owner());
        if(p==null||NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())!=scope.world())return;
        if(!scope.equals(currentScope)){bodies.clear();NativeJunkratTireRuntime.clear();currentScope=scope;wasAlive=p.isAlive();}
        if(wasAlive&&!p.isAlive())dropDeathBombs(p,scope);
        wasAlive=p.isAlive();lastFeet=p.getPos();
    }
    private static void dropDeathBombs(ServerPlayerEntity p,Scope scope){
        deaths++;
        for(int i=0;i<6;i++){
            var b=new Body();b.kind=Kind.DEATH_BOMB;b.scope=scope;b.pos=lastFeet==null?p.getPos():lastFeet;
            double a=i*Math.PI/3;b.vel=new Vec3d(Math.cos(a)*.04,.12,Math.sin(a)*.04); // MC 被动散落速度，留在死亡点附近
            bodies.add(b);deathBombs++;
        }
        NativeJunkratTireRuntime.clear();publish();
    }

    private static ServerPlayerEntity owner(MinecraftServer server,Scope s){
        var p=s==null?null:server.getPlayerManager().getPlayer(s.owner());
        return p!=null&&p.isAlive()&&NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())==s.world()?p:null;
    }
    public static void cast(MinecraftServer server,Scope scope,Kind kind,int nativePid,long nativeTick){
        if(nativePid<=0||nativeTick<=0||nativeTick>0xffffffffL)return;
        var p=owner(server,scope);if(p==null||!scope.equals(currentScope)||kind==Kind.DEATH_BOMB||NativeJunkratTireRuntime.active())return;
        if(kind!=Kind.GRENADE)bodies.removeIf(b->b.kind==kind&&b.scope.owner().equals(scope.owner()));  // 一颗地雷、一个夹子
        if(bodies.size()>=MAX_BODIES)bodies.remove(0);
        var b=new Body();b.kind=kind;b.scope=scope;b.nativePid=nativePid;b.nativeTick=nativeTick;b.pos=p.getEyePos().add(p.getRotationVec(1).multiply(.5));
        b.vel=p.getRotationVec(1).multiply((kind==Kind.TRAP?10:20)/20.0);bodies.add(b);
        switch(kind){case GRENADE->grenades++;case MINE->mines++;case TRAP->traps++;default->throw new IllegalArgumentException();}
        publish();
    }
    /** MC 右键引爆适配；只能消耗当前完整作用域中已由原版投掷节点准入的地雷。 */
    public static void detonateMine(MinecraftServer server,Scope scope){
        if(!current(scope))return;
        for(var b:new ArrayList<>(bodies))if(b.kind==Kind.MINE&&b.scope.equals(scope)){var p=owner(server,b.scope);if(p!=null){explode(p,b,null);detonations++;}bodies.remove(b);}
        publish();
    }
    public static void tick(MinecraftServer server){
        if(currentScope!=null){
            var p=server.getPlayerManager().getPlayer(currentScope.owner());
            if(p==null||NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())!=currentScope.world()){resetSession();return;}
            if(wasAlive&&!p.isAlive())dropDeathBombs(p,currentScope);
            wasAlive=p.isAlive();if(p.isAlive())lastFeet=p.getPos();
        }
        NativeJunkratTireRuntime.tick(server);
        if(bodies.isEmpty()){publish();return;}int now=server.getTicks();
        for(var b:new ArrayList<>(bodies)){
            var p=b.kind==Kind.DEATH_BOMB?server.getPlayerManager().getPlayer(b.scope.owner()):owner(server,b.scope);
            if(p==null||!b.scope.equals(currentScope)||NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())!=b.scope.world()){bodies.remove(b);continue;}
            var w=p.getServerWorld();b.age++;
            boolean grenadeExpired=b.kind==Kind.GRENADE&&NativeJunkratGrenadeTuning.expired(b.age,b.firstGroundAge);
            if(grenadeExpired||b.kind==Kind.DEATH_BOMB&&b.age>DEATH_FUSE){
                if(grenadeExpired){grenadeFuseExplosions++;lastGrenadeFuseElapsedTicks=b.age-b.firstGroundAge;}
                explode(p,b,null);bodies.remove(b);continue;
            }
            if(b.kind==Kind.TRAP&&b.trapped!=null){
                if(now-b.trappedAt>TRAP_ROOT){bodies.remove(b);continue;}
                continue;
            }
            if(!b.stuck){
                var next=b.pos.add(b.vel);
                var hit=w.raycast(new RaycastContext(b.pos,next,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
                if(b.kind==Kind.GRENADE){
                    var hitMob=firstMob(w,p,b.pos,hit.getType()==HitResult.Type.BLOCK?hit.getPos():next);  // 只判墙前的目标
                    if(hitMob!=null){var r=NativeDamageTargets.projectileDamage(w,hitMob,p,NativeJunkratGrenadeTuning.damage(DIRECT)*NativeShotSimulation.HP_SCALE);if(r.applied()){directHits++;damageApplied+=r.healthLost();}explode(p,b,hitMob);bodies.remove(b);continue;}
                }
                if(hit.getType()==HitResult.Type.BLOCK){
                    var bh=(BlockHitResult)hit;var n=Vec3d.of(bh.getSide().getVector());
                    if(b.kind==Kind.GRENADE||b.kind==Kind.DEATH_BOMB){
                        if(b.kind==Kind.GRENADE){
                            int first=NativeJunkratGrenadeTuning.groundContact(b.firstGroundAge,b.age,n.y);
                            if(b.firstGroundAge<0&&first>=0)grenadeGroundContacts++;
                            b.firstGroundAge=first;
                        }
                        // 原版反弹系数 .5：法向分量反向并衰减，切向保留。
                        var vn=n.multiply(b.vel.dotProduct(n));b.vel=b.vel.subtract(vn).subtract(vn.multiply(RESTITUTION));
                        if(b.kind==Kind.DEATH_BOMB&&n.y>.5)b.vel=b.vel.multiply(.5,1,.5); // MC 掉落炸弹的地面摩擦
                        b.pos=bh.getPos().add(n.multiply(.05));b.bounces++;
                        w.playSound(null,b.pos.x,b.pos.y,b.pos.z,SoundEvents.BLOCK_STONE_HIT,SoundCategory.PLAYERS,.5f,1.4f);
                    }else{b.pos=bh.getPos().add(n.multiply(.02));b.stuck=true;
                        w.playSound(null,b.pos.x,b.pos.y,b.pos.z,b.kind==Kind.TRAP?SoundEvents.BLOCK_CHAIN_PLACE:SoundEvents.BLOCK_METAL_PLACE,SoundCategory.PLAYERS,.8f,1f);}
                }else b.pos=next;
                if(!b.stuck)b.vel=b.vel.add(0,-(b.kind==Kind.GRENADE||b.kind==Kind.DEATH_BOMB?G_GRENADE:G_THROWN),0);
                if(b.kind==Kind.GRENADE)w.spawnParticles(ParticleTypes.SMOKE,b.pos.x,b.pos.y,b.pos.z,1,0,0,0,0);
                // 空中超过10s的孤立物体仍回收；晚触地的手雷必须走完自己的30tick引信。
                if(!b.stuck&&b.age>200&&(b.kind!=Kind.GRENADE||b.firstGroundAge<0)){bodies.remove(b);continue;}
            }
            if(b.kind==Kind.TRAP&&b.stuck){
                var m=w.getEntitiesByClass(LivingEntity.class,new Box(b.pos,b.pos).expand(1.0),e->e.isAlive()&&!(e instanceof PlayerEntity)).stream().findFirst();
                if(m.isPresent()){var e=m.get();b.trapped=e.getUuid();b.trappedAt=now;trapTriggers++;
                    var r=NativeDamageTargets.meleeDamage(w,e,p,TRAP_DAMAGE*NativeShotSimulation.HP_SCALE);if(r.applied())damageApplied+=r.healthLost();
                    e.addStatusEffect(new StatusEffectInstance(StatusEffects.SLOWNESS,TRAP_ROOT,9,false,false));e.setVelocity(Vec3d.ZERO);e.velocityModified=true;
                    w.playSound(null,b.pos.x,b.pos.y,b.pos.z,SoundEvents.BLOCK_IRON_TRAPDOOR_CLOSE,SoundCategory.PLAYERS,1f,.6f);}
            }
        }
        publish();
    }
    private static LivingEntity firstMob(ServerWorld w,ServerPlayerEntity p,Vec3d from,Vec3d to){
        var box=new Box(from,to).expand(.3);LivingEntity best=null;double bd=Double.MAX_VALUE;
        for(var e:w.getEntitiesByClass(LivingEntity.class,box,e->e.isAlive()&&!(e instanceof PlayerEntity))){
            var hit=e.getBoundingBox().expand(.15).raycast(from,to);if(hit.isPresent()){double d=from.squaredDistanceTo(hit.get());if(d<bd){bd=d;best=e;}}}
        return best;
    }
    /** 原版两环爆炸：内半径内满伤，内外之间线性衰减到 0。 */
    private static void explode(ServerPlayerEntity p,Body b,LivingEntity direct){
        var w=p.getServerWorld();explosions++;
        w.spawnParticles(ParticleTypes.EXPLOSION,b.pos.x,b.pos.y,b.pos.z,2,.2,.2,.2,0);
        w.playSound(null,b.pos.x,b.pos.y,b.pos.z,SoundEvents.ENTITY_GENERIC_EXPLODE.value(),SoundCategory.PLAYERS,.9f,1.2f);
        for(var e:w.getEntitiesByClass(LivingEntity.class,new Box(b.pos,b.pos).expand(OUTER+1),e->e.isAlive()&&!(e instanceof PlayerEntity))){
            double d=Math.sqrt(e.getBoundingBox().squaredMagnitude(b.pos));if(d>OUTER)continue;
            // 原版两环：内半径满伤，到外半径线性降到 outerScale .125（022b current-volleys）。
            double f=d<=INNER?1:1-(1-OUTER_SCALE)*(d-INNER)/(OUTER-INNER);
            var c=e.getBoundingBox().getCenter();var los=w.raycast(new RaycastContext(b.pos,c,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
            if(los.getType()==HitResult.Type.BLOCK&&los.getPos().squaredDistanceTo(c)>.25)continue;  // 墙后不受爆炸伤害
            double blast=b.kind==Kind.GRENADE?NativeJunkratGrenadeTuning.damage(BLAST):BLAST;
            var r=NativeDamageTargets.explosionDamage(w,e,p,blast*f*NativeShotSimulation.HP_SCALE);if(r.applied()){blastHits++;damageApplied+=r.healthLost();}
        }
        if(b.kind==Kind.MINE){
            // 用投掷096a:12的真实PID/tick去重，不把右键或MC时间冒充原版引爆提交。
            // 爆心保留MC地雷的实际位置；地面/空中均走同一径向击退，不要求先起跳。
            mineImpulseRequests++;lastMineNativePid=b.nativePid;lastMineNativeTick=b.nativeTick;
            if(NativeRocketSelfImpulse.INSTANCE.concussiveMine(w,p,b.nativePid,b.scope.source(),b.scope.model(),b.nativeTick,b.pos,3.0))mineImpulses++;
        }
        // 所有伤害/遮挡判断完成后才破坏地形，避免新洞反过来让本次爆炸穿墙伤害。
        // 与76/NativeRocketExplosion相同的vanilla抗爆规则；复用已抽出的无重复伤害/击退/音效入口。
        if(b.kind==Kind.GRENADE){
            var terrain=NativeTerrainBurst.explode(w,p,b.pos,NativeJunkratGrenadeTuning.terrainStrength(NativeExplosionTerrain.HELIX));
            if(terrain.applied()){terrainBursts++;terrainBlocks+=terrain.blocksDestroyed();}terrainError=terrain.rejection();
        }
    }
    private static void publish(){
        var v=new ArrayList<View>();for(var b:bodies)v.add(new View(b.kind,b.pos,b.stuck,b.age,b.scope.world(),System.currentTimeMillis(),visualId(b.nativePid,b.nativeTick,b.kind)));views=List.copyOf(v);
        var o=new JsonObject();o.addProperty("bodies",bodies.size());o.addProperty("grenades",grenades);o.addProperty("mines",mines);o.addProperty("traps",traps);
        o.addProperty("explosions",explosions);o.addProperty("directHits",directHits);o.addProperty("blastHits",blastHits);o.addProperty("trapTriggers",trapTriggers);
        o.addProperty("detonations",detonations);o.addProperty("damageApplied",damageApplied);status=o.toString();
        o.addProperty("deaths",deaths);o.addProperty("deathBombs",deathBombs);
        o.add("tire",com.google.gson.JsonParser.parseString(NativeJunkratTireRuntime.status));
        o.add("signals",com.google.gson.JsonParser.parseString(nativeSignals));
        o.addProperty("grenadeScale",NativeJunkratGrenadeTuning.RENDER_SCALE);o.addProperty("grenadeFuseTicks",NativeJunkratGrenadeTuning.FUSE_TICKS);
        o.addProperty("grenadeFuseSeconds",NativeJunkratGrenadeTuning.FUSE_TICKS/20.0);
        o.addProperty("grenadeFuseStarts","first-ground-contact");o.addProperty("grenadeGroundContacts",grenadeGroundContacts);
        o.addProperty("grenadeFuseExplosions",grenadeFuseExplosions);o.addProperty("lastGrenadeFuseElapsedTicks",lastGrenadeFuseElapsedTicks);
        o.addProperty("grenadeDirectDamage",NativeJunkratGrenadeTuning.damage(DIRECT));o.addProperty("grenadeBlastDamage",NativeJunkratGrenadeTuning.damage(BLAST));
        o.addProperty("grenadeDamageMultiplier",NativeJunkratGrenadeTuning.DAMAGE_MULTIPLIER);
        o.addProperty("grenadeTerrainStrength",NativeJunkratGrenadeTuning.terrainStrength(NativeExplosionTerrain.HELIX));
        o.addProperty("terrainBursts",terrainBursts);o.addProperty("terrainBlocks",terrainBlocks);o.addProperty("terrainError",terrainError);
        o.addProperty("mineImpulseRequests",mineImpulseRequests);o.addProperty("mineImpulses",mineImpulses);
        o.addProperty("lastMineNativePid",lastMineNativePid);o.addProperty("lastMineNativeTick",lastMineNativeTick);
        o.addProperty("mineImpulsePolicy","MC actual mine position; shared self impulse keyed by admitted native throw; adapted RMB detonation");
        o.addProperty("passivePolicy","MC-death-edge; six declared 022a volleys; MC fuse/blast");status=o.toString();
    }
    public static boolean current(Scope scope){return scope!=null&&scope.equals(currentScope);}
    public static void cancel(Scope scope){if(current(scope))resetSession();}
    public static void resetSession(){bodies.clear();currentScope=null;lastFeet=null;wasAlive=false;NativeJunkratTireRuntime.clear();publish();}
    public static void clear(){resetSession();}
}
