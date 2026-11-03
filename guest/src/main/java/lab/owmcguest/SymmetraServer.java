package lab.owmcguest;

import com.google.gson.JsonObject;
import java.util.*;
import net.minecraft.entity.Entity;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.attribute.EntityAttributeModifier;
import net.minecraft.entity.attribute.EntityAttributes;
import net.minecraft.entity.decoration.ArmorStandEntity;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.*;
import net.minecraft.world.RaycastContext;

/** Beta 24919 / HERO-BRIEFS-NEW8-20261025 §3.
 * 原版 0139:77 B/E 门控 MC 光束；锁定/伤害/升级是 MC 适配，并非16/89/107已执行。
 * 原版声明/保存变量：射程5m、基础30、伤害周期.25s；档位30/60/120与每1s升级为MC适配值。
 * E成功链01c3:16 -> 0.finished -> 39.true -> 3播放01c4；01c4:1引用护盾量50。
 * 只在新16 Begin后收到新3 E才给MC友方盾；27搜索失败绝不发盾。
 * 原版自身护盾仍归原版；未发现命中护盾返弹或独立被动信号，不移植后续版本能力。
 * MC 适配：球伤害 25..125、半径 .15.. .5、蓄力 1.5s、直线无重力（原版未声明重力），
 * 球速度10/寿命5/射程300来自声明；按原版 Volley 释放，穿透每目标一次。
 * 炮台017e:2.finished ->47、传送器0169:2.finished ->66：仅新完成分支允许MC放置。
 * 这些成功分支是离线图声明，旧实测未执行；不再读取MC左键作为确认。
 * MC 适配值：放置15m/六炮台/炮台25 DPS、10m、60s、1 MC HP；传送器双端同维度、六次、60s、5 MC HP。
 * 原版预览实体 GUID 见 prepare_hero_symmetra.py 的离线资源证据；不宣称原版创建成功。
 */
public final class SymmetraServer implements HeroServerModule {
    public static final SymmetraServer INSTANCE=new SymmetraServer();
    public static final long HERO=0x02e0000000000016L;
    public record Scope(UUID owner,long world,long source,long model,long serial){}
    public record View(long world,String mesh,Vec3d at,Vec3d direction,float scale,long wall){}
    private static final double PLACE_RANGE=15,TURRET_RANGE=10,TURRET_DPS=25,ORB_MIN=25,ORB_MAX=125;
    private static final int MAX_TURRETS=6,LIFETIME=1200;
    // MC适配：15度准星获取/60度断链；持续命中20/40tick升级，3秒后25OW HP/s回盾。
    private static final double BEAM_RANGE=5,BEAM_BASE_DPS=30,SHIELD_AMOUNT=5;
    private static final int BEAM_PERIOD=5,SHIELD_DELAY=60;
    private static final Identifier SHIELD_POOL=Identifier.of("owmcguest","symmetra_photon_shield");
    private record Permission(Scope scope,long wall){}
    private volatile Permission permission;
    public void permit(Scope next,long wall){permission=new Permission(next,wall);}
    public void revoke(){permission=null;}
    private static final class Orb {Vec3d at,velocity;double amount,radius;int age;final Set<UUID> hit=new HashSet<>();}
    private static final class Construct {ArmorStandEntity body;Vec3d at;int age;}
    private static final class Shield {LivingEntity target;float owned,lastHealth;int quiet;}
    private record Placement(boolean portal,Vec3d at,Vec3d entrance,long expires){}
    private final List<Orb> orbs=new ArrayList<>();
    private final List<Construct> turrets=new ArrayList<>();
    private record Phase(long tick,boolean active){}
    private final Map<String,Phase> seen=new HashMap<>();
    private final Map<UUID,Shield> shields=new HashMap<>();
    private Scope scope;private long lease,chargeWall,previewWall,confirmTick;
    private boolean beam,charging,turretPreview,portalPreview;private Vec3d entrance,exit,previewEntrance;
    private Entity beamTarget;private int beamTicks,beamTier;private UUID shieldTarget;private long shieldWindupWall;
    private Placement placement;private boolean previewIsPortal;
    private Construct portal;private int uses,portalCooldown;
    private long beamCasts,orbCasts,turretPreviews,portalPreviews,turretBuilds,portalBuilds,shieldAttempts,teleports,hits,refused;
    private double damageApplied;private volatile String json="{}";
    private long beamLocks,beamBreaks,beamHits,beamUpgrades,nativeDamagePhases,shieldGrants,shieldMisses,shieldRegens,shieldConflicts;
    private long turretCommits,portalCommits,shieldCommits,shieldWindups;
    private double beamDamageApplied,shieldRegenApplied;
    public volatile List<View> views=List.of();
    public volatile long beamMeshFrames,shieldMeshFrames;
    private SymmetraServer(){publish();}
    private ServerPlayerEntity owner(MinecraftServer s){
        var p=scope==null?null:s.getPlayerManager().getPlayer(scope.owner());
        return p!=null&&p.isAlive()&&NativeWorldIdentity.of(s,p.getWorld().getRegistryKey())==scope.world()?p:null;
    }
    private boolean valid(MinecraftServer s,Scope next,long wall){
        long now=System.currentTimeMillis();var permit=permission;
        if(permit==null||next==null||!next.equals(permit.scope())||now-permit.wall()<0||now-permit.wall()>150
            ||next.source()==0||next.model()==0||next.world()==0||wall>now||now-wall>150)return false;
        if(!next.equals(scope)){resetSession();scope=next;}lease=wall;return owner(s)!=null;
    }
    public void heartbeat(MinecraftServer s,Scope next,long wall){if(valid(s,next,wall))publish();}
    public void release(Scope old){if(old.equals(scope))resetSession();}
    public void signal(MinecraftServer s,Scope next,String node,long tick,boolean active,long wall){
        if(!valid(s,next,wall)||tick<=0)return;
        var phase=new Phase(tick,active);var last=seen.get(node);
        if(last!=null&&(tick<last.tick()||phase.equals(last)))return;seen.put(node,phase);
        var p=owner(s);if(p==null)return;
        switch(node){
            case "beam" -> {if(active){beamCasts++;stopBeam();}beam=active;if(!active)stopBeam();}
            case "nativeDamage16","nativeDamage89","nativeDamage107" -> {if(active)nativeDamagePhases++;}
            case "charge" -> {charging=active;chargeWall=active?wall:0;}
            case "orb" -> { // 本轮只采到 E；B 不发射，防止 B/E 双发。
                if(!active&&charging&&wall>=chargeWall&&wall-chargeWall<=5000){
                    double power=Math.max(0,Math.min(1,(wall-chargeWall)/1500.0));
                    var b=new Orb();b.at=p.getEyePos();b.velocity=p.getRotationVec(1).multiply(10/20.0);
                    b.amount=ORB_MIN+(ORB_MAX-ORB_MIN)*power;b.radius=.15+.35*power;
                    if(orbs.size()<32){orbs.add(b);orbCasts++;}else refused++;
                    charging=false;chargeWall=0;
                }else if(!active){refused++;}
            }
            case "turretPreview" -> {if(active){turretPreviews++;turretPreview=true;portalPreview=false;previewIsPortal=false;previewWall=wall;placement=null;}}
            case "portalPreview" -> {if(active){portalPreviews++;portalPreview=true;turretPreview=false;previewIsPortal=true;previewWall=wall;previewEntrance=groundUnder(p);placement=null;}}
            case "turretGhost" -> {if(!active)turretPreview=false;}
            case "portalGhost" -> {if(!active)portalPreview=false;}
            case "shieldAttempt" -> {if(!active)shieldAttempts++;}
            case "shieldWindup" -> {if(active){shieldWindups++;var target=shieldAim(p);shieldTarget=target==null?null:target.getUuid();shieldWindupWall=wall;}}
            case "shieldCommit" -> {if(!active){shieldCommits++;grantShield(p,wall);}}
            case "turretPlace","portalPlace" -> {
                if(active)armPlacement(p,node.equals("portalPlace"),wall);
                else if(placement!=null&&placement.portal()==node.equals("portalPlace"))
                    placement=new Placement(placement.portal(),placement.at(),placement.entrance(),Math.min(placement.expires(),wall+150));
            }
            case "turretCommit" -> {if(!active){turretCommits++;place(s,next,false,wall);}}
            case "portalCommit" -> {if(!active){portalCommits++;place(s,next,true,wall);}}
            default -> throw new IllegalArgumentException("unknown Symmetra node");
        }publish();
    }
    /** Native placement timer Begin freezes the MC location. The ghost may end
     * here, a full1/2 seconds BEFORE the success action; End alone never commits. */
    private void armPlacement(ServerPlayerEntity p,boolean portalCast,long wall){
        placement=null;
        if(previewWall<=0||wall-previewWall>10000||previewIsPortal!=portalCast){refused++;return;}
        var at=groundAim(p);if(at==null){refused++;return;}
        placement=new Placement(portalCast,at,portalCast?previewEntrance:null,wall+5000);
    }
    /** 仅由原版成功分支的新E调用；预览、逻辑按键、计时器End均不能直接创建。 */
    private void place(MinecraftServer s,Scope next,boolean portalCommit,long wall){
        if(!valid(s,next,wall)||wall<=confirmTick)return;
        var pending=placement;placement=null;
        var p=owner(s);if(p==null||pending==null||pending.portal()!=portalCommit||wall>pending.expires()){refused++;return;}
        var at=pending.at();if(!safe(p,at)){refused++;publish();return;}
        if(!portalCommit){
            var c=construct(p,at,1);if(c==null){refused++;return;}
            if(turrets.size()>=MAX_TURRETS)turrets.remove(0).body.discard();turrets.add(c);turretBuilds++;
        }else{
            if(pending.entrance()==null||!safe(p,pending.entrance())||at.squaredDistanceTo(pending.entrance())<4){refused++;publish();return;}
            var c=construct(p,at,5);if(c==null){refused++;return;}
            if(portal!=null)portal.body.discard();portal=c;entrance=pending.entrance();exit=at;uses=6;portalCooldown=40;portalBuilds++;
        }
        confirmTick=wall;turretPreview=portalPreview=false;publish();
    }
    private static boolean ally(ServerPlayerEntity p,Entity e){
        return e!=p&&e.isAlive()&&!e.isSpectator()&&(p.isTeammate(e)||e.getCommandTags().contains("owmc-symmetra-ally"));
    }
    private LivingEntity shieldAim(ServerPlayerEntity p){
        LivingEntity target=null;double nearest=20;var from=p.getEyePos();var to=from.add(p.getRotationVec(1).multiply(20));
        for(var e:p.getServerWorld().getEntitiesByClass(LivingEntity.class,new Box(from,to).expand(.4),e->ally(p,e))){
            var hit=e.getBoundingBox().expand(.35).raycast(from,to);if(hit.isEmpty()||!visible(p,from,e.getBoundingBox().getCenter()))continue;
            double d=from.distanceTo(hit.get());if(d<nearest){nearest=d;target=e;}
        }return target;
    }
    private void grantShield(ServerPlayerEntity p,long wall){
        var entity=shieldTarget==null?null:p.getServerWorld().getEntity(shieldTarget);shieldTarget=null;
        if(!(entity instanceof LivingEntity target)||wall-shieldWindupWall<0||wall-shieldWindupWall>2000||!ally(p,target)
            ||p.getEyePos().squaredDistanceTo(target.getBoundingBox().getCenter())>400||!visible(p,p.getEyePos(),target.getBoundingBox().getCenter())){shieldMisses++;return;}
        var cap=target.getAttributeInstance(EntityAttributes.GENERIC_MAX_ABSORPTION);
        if(shields.containsKey(target.getUuid())||target.getAbsorptionAmount()>0||cap==null||cap.hasModifier(SHIELD_POOL)){shieldMisses++;return;}
        cap.addTemporaryModifier(new EntityAttributeModifier(SHIELD_POOL,SHIELD_AMOUNT,EntityAttributeModifier.Operation.ADD_VALUE));
        var shield=new Shield();shield.target=target;shield.owned=(float)SHIELD_AMOUNT;shield.lastHealth=target.getHealth();shield.quiet=0;
        target.setAbsorptionAmount(shield.owned);shields.put(target.getUuid(),shield);shieldGrants++;
    }
    private void tickShields(ServerPlayerEntity p,ArrayList<View> draw,long now){
        for(var shield:new ArrayList<>(shields.values())){
            var e=shield.target;
            if(!e.isAlive()||e.getWorld()!=p.getWorld()||!ally(p,e)||!p.getServerWorld().isChunkLoaded(e.getBlockPos())){
                releaseShield(shield);shields.remove(e.getUuid());continue;
            }
            float current=e.getAbsorptionAmount();
            if(current>shield.owned+.001f){ // Other absorption arrived: retain its delta and relinquish this pool.
                releaseShield(shield);shields.remove(e.getUuid());shieldConflicts++;continue;
            }
            if(current<shield.owned-.001f||e.getHealth()<shield.lastHealth-.001f)shield.quiet=0;
            else shield.quiet++;
            shield.owned=current;shield.lastHealth=e.getHealth();
            if(shield.quiet>=SHIELD_DELAY&&shield.owned<SHIELD_AMOUNT){
                float amount=(float)Math.min(.125,SHIELD_AMOUNT-shield.owned);shield.owned+=amount;e.setAbsorptionAmount(shield.owned);
                shieldRegens++;shieldRegenApplied+=amount;
            }
            draw.add(new View(scope.world(),"symmetra-shield",e.getBoundingBox().getCenter(),new Vec3d(0,0,1),e.getHeight()*1.15f,now));
        }
    }
    private static void releaseShield(Shield shield){
        float keep=Math.max(0,shield.target.getAbsorptionAmount()-shield.owned);
        var cap=shield.target.getAttributeInstance(EntityAttributes.GENERIC_MAX_ABSORPTION);if(cap!=null)cap.removeModifier(SHIELD_POOL);
        shield.target.setAbsorptionAmount(keep);
    }
    private void stopBeam(){if(beamTarget!=null)beamBreaks++;beamTarget=null;beamTicks=beamTier=0;}
    private boolean beamEligible(ServerPlayerEntity p,Entity e,boolean retain){
        if(e==null||!e.isAlive()||e.isSpectator()||e instanceof PlayerEntity||own(e)||ally(p,e))return false;
        var from=p.getEyePos();var center=e.getBoundingBox().getCenter();var delta=center.subtract(from);
        if(delta.lengthSquared()<.0001||e.getBoundingBox().squaredMagnitude(from)>BEAM_RANGE*BEAM_RANGE)return false;
        if(p.getRotationVec(1).dotProduct(delta.normalize())<Math.cos(Math.toRadians(retain?60:15)))return false;
        return visible(p,from,center);
    }
    private void tickBeam(ServerPlayerEntity p,ArrayList<View> draw,long now){
        if(!beam){stopBeam();return;}
        if(beamTarget!=null&&!beamEligible(p,beamTarget,true))stopBeam();
        if(beamTarget==null){
            double best=Double.MAX_VALUE;
            for(var e:NativeDamageTargets.in(p.getServerWorld(),p,p.getBoundingBox().expand(BEAM_RANGE+1))){
                if(!beamEligible(p,e,false))continue;double d=e.getBoundingBox().getCenter().squaredDistanceTo(p.getEyePos());
                if(d<best){best=d;beamTarget=e;}
            }
            if(beamTarget!=null){beamLocks++;beamTicks=0;beamTier=1;}
        }
        if(beamTarget==null)return;
        int tier=1+Math.min(2,beamTicks/20);if(tier>beamTier)beamUpgrades++;beamTier=tier;beamTicks++;
        var from=p.getEyePos();var to=beamTarget.getBoundingBox().getCenter();var delta=to.subtract(from);
        draw.add(new View(scope.world(),"symmetra-beam",from,delta,(float)delta.length(),now));
        // MC beam simulation consumes native channel B/E; serverOnly ModifyHealth counters are diagnostic only.
        if(beamTicks%BEAM_PERIOD==0){
            double damage=BEAM_BASE_DPS*(1<<(tier-1))*.25*NativeShotSimulation.HP_SCALE;
            var result=NativeDamageTargets.beamDamage(p.getServerWorld(),beamTarget,p,damage);
            if(result.applied()){beamHits++;hits++;beamDamageApplied+=result.healthLost();damageApplied+=result.healthLost();}
        }
        for(int i=1;i<=4;i++){var at=from.add(delta.multiply(i/4.0));p.getServerWorld().spawnParticles(ParticleTypes.END_ROD,at.x,at.y,at.z,1,0,0,0,0);}
    }
    private Construct construct(ServerPlayerEntity p,Vec3d at,float hp){
        var a=new ArmorStandEntity(p.getServerWorld(),at.x,at.y,at.z);a.setInvisible(true);a.setSilent(true);a.setNoGravity(true);a.setHealth(hp);
        if(!p.getServerWorld().spawnEntity(a))return null;var c=new Construct();c.body=a;c.at=at;return c;
    }
    private static Vec3d groundUnder(ServerPlayerEntity p){
        var w=p.getServerWorld();var at=p.getPos();var below=BlockPos.ofFloored(at).down();
        return w.isChunkLoaded(below)&&!w.getBlockState(below).getCollisionShape(w,below).isEmpty()&&safe(p,at)?at:null;
    }
    private static boolean safe(ServerPlayerEntity p,Vec3d at){
        var w=p.getServerWorld();var b=BlockPos.ofFloored(at);
        return w.isChunkLoaded(b)&&w.isChunkLoaded(b.up())&&w.getWorldBorder().contains(b)
            &&w.getBlockState(b).getFluidState().isEmpty()&&w.isSpaceEmpty(p,p.getBoundingBox().offset(at.subtract(p.getPos())))
            &&!w.getBlockState(b.down()).getCollisionShape(w,b.down()).isEmpty();
    }
    private static Vec3d groundAim(ServerPlayerEntity p){
        var w=p.getServerWorld();var from=p.getEyePos();var to=from.add(p.getRotationVec(1).multiply(PLACE_RANGE));
        if(!w.isChunkLoaded(BlockPos.ofFloored(to)))return null;
        var hit=w.raycast(new RaycastContext(from,to,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
        if(hit.getType()!=HitResult.Type.BLOCK||hit.getSide()!=Direction.UP)return null;
        var at=hit.getPos().add(0,.02,0);return safe(p,at)?at:null;
    }
    private static boolean visible(ServerPlayerEntity p,Vec3d from,Vec3d to){
        var w=p.getServerWorld();return w.isChunkLoaded(BlockPos.ofFloored(to))&&w.raycast(new RaycastContext(from,to,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p)).getType()==HitResult.Type.MISS;
    }
    private boolean own(Entity e){return turrets.stream().anyMatch(c->c.body==e)||(portal!=null&&portal.body==e);}
    @Override public void tick(MinecraftServer s){
        if(scope==null)return;var p=owner(s);
        var permit=permission;long age=permit==null?Long.MAX_VALUE:System.currentTimeMillis()-permit.wall();
        if(p==null||permit==null||!scope.equals(permit.scope())||age<0||age>150||System.currentTimeMillis()-lease>150){resetSession();return;}
        var w=p.getServerWorld();var draw=new ArrayList<View>();long now=System.currentTimeMillis();
        for(var b:new ArrayList<>(orbs)){
            var to=b.at.add(b.velocity);if(++b.age>100||!w.isChunkLoaded(BlockPos.ofFloored(to))){orbs.remove(b);continue;}
            var wall=w.raycast(new RaycastContext(b.at,to,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
            var end=wall.getType()==HitResult.Type.BLOCK?wall.getPos():to;
            for(var e:NativeDamageTargets.in(w,p,new Box(b.at,end).expand(b.radius))){
                if(e instanceof PlayerEntity||own(e)||ally(p,e)||!e.getBoundingBox().expand(b.radius).intersects(new Box(b.at,end).expand(b.radius)))continue;
                var box=e.getBoundingBox().expand(b.radius);if(!box.contains(b.at)&&box.raycast(b.at,end).isEmpty())continue;
                // 球的体积扩张不能让墙后的目标提前命中。
                if(!visible(p,b.at,e.getBoundingBox().getCenter()))continue;
                if(!b.hit.add(NativeDamageTargets.owner(e).getUuid()))continue;
                var r=NativeDamageTargets.projectileDamage(w,e,p,b.amount*NativeShotSimulation.HP_SCALE);if(r.applied()){hits++;damageApplied+=r.healthLost();}
            }
            b.at=end;if(wall.getType()==HitResult.Type.BLOCK){orbs.remove(b);continue;}
            draw.add(new View(scope.world(),"symmetra-orb",b.at,b.velocity,(float)(b.radius/.5),now));
            w.spawnParticles(ParticleTypes.END_ROD,b.at.x,b.at.y,b.at.z,1,0,0,0,0);
        }
        for(var c:new ArrayList<>(turrets)){
            if(!c.body.isAlive()||++c.age>LIFETIME||!w.isChunkLoaded(c.body.getBlockPos())){c.body.discard();turrets.remove(c);continue;}
            draw.add(new View(scope.world(),"symmetra-turret",c.at,new Vec3d(0,0,1),1,now));
            if(c.age%4!=0)continue;
            Entity target=null;double best=TURRET_RANGE*TURRET_RANGE;var from=c.at.add(0,.4,0);
            for(var e:NativeDamageTargets.in(w,p,new Box(from,from).expand(TURRET_RANGE))){
            if(e instanceof PlayerEntity||own(e)||ally(p,e))continue;double d=e.getBoundingBox().getCenter().squaredDistanceTo(from);
                if(d<best&&visible(p,from,e.getBoundingBox().getCenter())){best=d;target=e;}
            }
            if(target!=null){var r=NativeDamageTargets.beamDamage(w,target,p,TURRET_DPS*.2*NativeShotSimulation.HP_SCALE);if(r.applied()){hits++;damageApplied+=r.healthLost();}}
        }
        if(portal!=null){
            if(!portal.body.isAlive()||++portal.age>LIFETIME||uses<=0){portal.body.discard();portal=null;entrance=exit=null;}
            else{
                draw.add(new View(scope.world(),"symmetra-teleporter",entrance,new Vec3d(0,0,1),1,now));
                draw.add(new View(scope.world(),"symmetra-teleporter",exit,new Vec3d(0,0,1),1,now));
                if(--portalCooldown<=0&&p.getPos().squaredDistanceTo(entrance)<1&&safe(p,exit)){
                    p.requestTeleport(exit.x,exit.y,exit.z);p.fallDistance=0;uses--;teleports++;portalCooldown=40;
                }
            }
        }
        if((turretPreview||portalPreview)&&now-previewWall<=10000){var at=groundAim(p);if(at!=null)w.spawnParticles(ParticleTypes.END_ROD,at.x,at.y+.1,at.z,1,.15,0,.15,0);}
        tickBeam(p,draw,now);tickShields(p,draw,now);
        views=List.copyOf(draw);publish();
    }
    @Override public void resetSession(){
        for(var c:turrets)c.body.discard();if(portal!=null)portal.body.discard();
        for(var shield:shields.values())releaseShield(shield);shields.clear();stopBeam();shieldTarget=null;shieldWindupWall=0;
        turrets.clear();orbs.clear();seen.clear();scope=null;portal=null;entrance=exit=previewEntrance=null;
        beam=charging=turretPreview=portalPreview=false;placement=null;lease=chargeWall=previewWall=confirmTick=0;uses=0;views=List.of();publish();
    }
    private void publish(){
        var o=new JsonObject();o.addProperty("beamCasts",beamCasts);o.addProperty("beamActive",beam);o.addProperty("orbCasts",orbCasts);
        o.addProperty("turretPreviews",turretPreviews);o.addProperty("portalPreviews",portalPreviews);o.addProperty("turretBuilds",turretBuilds);o.addProperty("portalBuilds",portalBuilds);
        o.addProperty("turretPreviewActive",turretPreview);o.addProperty("portalPreviewActive",portalPreview);
        o.addProperty("placementArmed",placement!=null&&System.currentTimeMillis()<=placement.expires());
        o.addProperty("turretCommits",turretCommits);o.addProperty("portalCommits",portalCommits);o.addProperty("shieldCommits",shieldCommits);o.addProperty("shieldWindups",shieldWindups);
        o.addProperty("shieldAttempts",shieldAttempts);o.addProperty("shieldGrants",shieldGrants);o.addProperty("shieldMisses",shieldMisses);
        o.addProperty("shields",shields.size());o.addProperty("shieldRegens",shieldRegens);o.addProperty("shieldRegenApplied",shieldRegenApplied);o.addProperty("shieldConflicts",shieldConflicts);
        o.addProperty("beamDamageApplied",beamDamageApplied);o.addProperty("beamHits",beamHits);o.addProperty("beamLocks",beamLocks);o.addProperty("beamBreaks",beamBreaks);
        o.addProperty("beamUpgrades",beamUpgrades);o.addProperty("beamTier",beamTier);o.addProperty("beamLockTicks",beamTicks);
        o.addProperty("beamMeshFrames",beamMeshFrames);o.addProperty("shieldMeshFrames",shieldMeshFrames);
        o.addProperty("beamTarget",beamTarget==null?"":NativeDamageTargets.owner(beamTarget).getUuidAsString());o.addProperty("nativeDamagePhases",nativeDamagePhases);
        o.addProperty("turrets",turrets.size());o.addProperty("orbs",orbs.size());o.addProperty("portal",portal!=null);o.addProperty("portalUses",uses);o.addProperty("teleports",teleports);
        o.addProperty("hits",hits);o.addProperty("damageApplied",damageApplied);o.addProperty("refused",refused);
        o.addProperty("placementMode","原版成功分支017e:47/0169:66的新E；MC适配真实地面/双端/炮台效果；不读MC左键");
        o.addProperty("beamMode","MC适配目标/锁定/30-60-120升级；原版77 B/E门控，基础30/射程5/.25秒来自声明；非原版服务端命中证明");
        o.addProperty("shieldMode","原版01c3:16新B + 3新E；MC适配友方标签/队伍与50OW HP吸收池；禁止由27搜索加盾");
        o.addProperty("shieldVisualMode","原版0401效果的0dbf球面；颜色材质无已认证漫反射贴图，灰色fallback为MC适配；非原版着色器复现");
        o.addProperty("passiveMode","自身护盾仍由原版；MC适配友方盾3秒后25OW HP/s再生；没有独立被动触发");
        o.addProperty("blocked","新提交分支待实机；未发现护盾命中返弹信号，不实现后续版本返弹/光子屏障");
        o.add("fixture",SymmetraLab.status());
        o.addProperty("orbModel","原版022e/02ef资源链无LOD0；END_ROD为MC适配呈现");json=o.toString();
    }
    @Override public String statusKey(){return "symmetra";}
    @Override public String status(){return json;}
}
