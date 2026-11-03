package lab.owmcguest;

import java.util.*;
import com.google.gson.JsonObject;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.attribute.EntityAttributeModifier;
import net.minecraft.entity.attribute.EntityAttributes;
import net.minecraft.entity.decoration.ArmorStandEntity;
import net.minecraft.entity.mob.Monster;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.entity.passive.VillagerEntity;
import net.minecraft.entity.effect.StatusEffectInstance;
import net.minecraft.entity.effect.StatusEffects;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvents;
import net.minecraft.util.Identifier;
import net.minecraft.util.hit.BlockHitResult;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.math.*;
import net.minecraft.world.RaycastContext;

/** 原版 f4 放置动画、01cc Volley5、f3 ModifyHealth24、01c2 Core 状态驱动。
 * MC 适配：炮台物理/血量/索敌，锤子接触/修理/升级，真实 MC 敌人死亡废料，拾取/资源/HUD/护甲消耗。
 * MC 适配值：废料25/上限200/包耗50；修理50、升级进度100；炮台150/300/800HP，14伤/10或5tick，
 * Core护甲300（原版19声明但未认证原生护甲池）、攻速+50%、三级火箭80/20tick，护甲包75。
 * 2026-10-27第五次反馈：常规锤子仅1→2，Core期间2级临时变3级，结束恢复2级；
 * 包排除投掷者，其他玩家/友好村民用MC吸收效果。
 * HP均按0.1映射；没有把MC吸收护盾声称为原生逐击减伤护甲。 */
public final class NativeTorbjornRuntime {
    public record Scope(UUID owner,long world,long source,long model){}
    public record TurretView(Vec3d at,float yaw,int level,boolean firing,long world,long wall){}
    public record ScrapView(Vec3d at,int value,long world,long wall){}
    private static final class Turret{Scope scope;Vec3d pos;float yaw;int cooldown,rocketCooldown,upgrade;int level=1;ArmorStandEntity entity;}
    private static final class Pack{Scope scope;Vec3d pos,vel;boolean landed,ownerRejected;int age;}
    private static final class Scrap{Vec3d pos;int age;}
    private static final Identifier CORE_ARMOR=Identifier.of("owmcguest","torb_core_armor"),CORE_SPEED=Identifier.of("owmcguest","torb_core_speed");
    static final double RANGE=40,SHOT=14,ARMOR=75;static final int PACK_LIFE=600;
    private static Scope currentScope;private static ServerPlayerEntity boundOwner;
    private static Turret turret;private static final List<Pack> packs=new ArrayList<>();private static final List<Scrap> scrap=new ArrayList<>();
    private static final Set<UUID> deaths=new HashSet<>();private static final NativeTorbjornScrapBudget budget=new NativeTorbjornScrapBudget();
    private static final NativeTorbjornCoreAdmission coreAdmissions=new NativeTorbjornCoreAdmission();
    private static boolean core;private static long coreWall,coreBegin;private static float coreRemaining,lastAbsorption;
    private static long deploys,shots,hits,packsThrown,packsTaken,packsDenied,hammerSwings,hammerHits,repairs,upgrades,scrapDrops,scrapTaken,coreCasts,coreEnds,rockets;
    private static double damageApplied,repaired;
    private static long ownerPickupDenied;private static String lastPackRecipient="";private static float lastPackAbsorption;
    public static volatile TurretView view;public static volatile List<Vec3d> packViews=List.of();public static volatile List<ScrapView> scrapViews=List.of();
    public static volatile int scrapAmount;public static volatile long viewWorld,viewWall;public static volatile String status="{}";
    public static volatile String nativeSignals="{\"ready\":false,\"error\":\"waiting for native bindings\"}";
    private static long deployAttempts;private static String lastDeployRejection="";
    public static volatile String packTestRecipient="";
    static{ServerLivingEntityEvents.AFTER_DEATH.register((victim,source)->{
        if(!(victim instanceof Monster)||!(victim.getWorld() instanceof ServerWorld)||currentScope==null||boundOwner==null||!boundOwner.isAlive()
            ||!valid(boundOwner,currentScope)||victim.getWorld()!=boundOwner.getWorld()||victim.squaredDistanceTo(boundOwner)>RANGE*RANGE
            ||!deaths.add(victim.getUuid()))return;
        var s=new Scrap();s.pos=victim.getPos();scrap.add(s);if(scrap.size()>128)scrap.remove(0);scrapDrops++;
        if(deaths.size()>4096)deaths.clear();publish();
    });}
    private static boolean valid(ServerPlayerEntity p,Scope s){return p!=null&&s!=null&&p.isAlive()&&p.getUuid().equals(s.owner())&&NativeWorldIdentity.of(p.getServer(),p.getWorld().getRegistryKey())==s.world();}
    private static ServerPlayerEntity owner(MinecraftServer server,Scope s){var p=s==null?null:server.getPlayerManager().getPlayer(s.owner());return s!=null&&s.equals(currentScope)&&valid(p,s)?p:null;}
    public static void observe(MinecraftServer server,Scope s){
        var p=server.getPlayerManager().getPlayer(s.owner());if(!valid(p,s))return;
        if(!s.equals(currentScope)){resetSession();currentScope=s;boundOwner=p;lastAbsorption=p.getAbsorptionAmount();}publish();
    }
    public static void cancel(Scope s){if(s!=null&&s.equals(currentScope))resetSession();}
    public static void injureForTest(MinecraftServer server,UUID owner){
        var p=server.getPlayerManager().getPlayer(owner);if(!NativeBuildersLab.allowed(p)||turret==null||!turret.scope.owner().equals(owner))throw new IllegalStateException("no owned turret fixture");
        turret.entity.setHealth(Math.max(1,turret.entity.getHealth()-5));publish();
    }
    public static void approachForTest(MinecraftServer server,UUID owner,Vec3d forward){
        var p=server.getPlayerManager().getPlayer(owner);if(!NativeBuildersLab.allowed(p)||turret==null||!turret.scope.owner().equals(owner))throw new IllegalStateException("no owned turret fixture");
        var at=turret.pos.subtract(forward.multiply(1,0,1).normalize().multiply(2));
        if(!p.getServerWorld().isSpaceEmpty(p,p.getBoundingBox().offset(at.subtract(p.getPos()))))throw new IllegalStateException("occupied approach");
        p.requestTeleport(at.x,at.y,at.z);
    }
    public static void packForTest(MinecraftServer server,UUID owner){
        var p=server.getPlayerManager().getPlayer(owner);if(!NativeBuildersLab.allowed(p)||packs.isEmpty())throw new IllegalStateException("no pack fixture");
        var at=packs.get(0).pos;if(p.squaredDistanceTo(at)>100||!p.getServerWorld().isSpaceEmpty(p,p.getBoundingBox().offset(at.subtract(p.getPos()))))throw new IllegalStateException("unsafe pack approach");
        p.requestTeleport(at.x,at.y,at.z);
    }
    public static Vec3d packPositionForTest(MinecraftServer server,UUID owner){
        var p=server.getPlayerManager().getPlayer(owner);
        if(!NativeBuildersLab.allowed(p)||packs.isEmpty()||!packs.get(0).scope.owner().equals(owner))throw new IllegalStateException("no owned pack fixture");
        return packs.get(0).pos;
    }
    /** 原版的预览动画结束，MC 放置在真实地面；不借隐藏 OW 地形确认。 */
    public static void deploy(MinecraftServer server,Scope s){
        deployAttempts++;var p=owner(server,s);if(p==null){lastDeployRejection="scope-or-owner-invalid";publish();return;}var w=p.getServerWorld();var eye=p.getEyePos();
        var h=w.raycast(new RaycastContext(eye,eye.add(p.getRotationVec(1).multiply(5)),RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
        Vec3d at=h.getType()==HitResult.Type.BLOCK&&((BlockHitResult)h).getSide()==Direction.UP?h.getPos():p.getPos().add(p.getRotationVec(1).multiply(1,0,1).normalize());
        var floor=w.raycast(new RaycastContext(at.add(0,.2,0),at.add(0,-2,0),RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
        if(floor.getType()!=HitResult.Type.BLOCK||((BlockHitResult)floor).getSide()!=Direction.UP){lastDeployRejection="no-upward-ground";publish();return;}at=floor.getPos();
        var entity=new NativeBuildersBody(w,at.x,at.y,at.z,s.owner());
        entity.getAttributeInstance(EntityAttributes.GENERIC_MAX_HEALTH).setBaseValue(15);entity.setHealth(15);
        if(!w.isSpaceEmpty(entity,new Box(at.add(-.55,0,-.55),at.add(.55,1.4,.55)))){entity.discard();lastDeployRejection="occupied-placement";publish();return;}
        if(!w.spawnEntity(entity)){entity.discard();lastDeployRejection="spawn-refused";publish();return;}
        if(turret!=null)turret.entity.discard();turret=new Turret();turret.scope=s;turret.pos=at;turret.entity=entity;turret.yaw=p.getYaw();deploys++;lastDeployRejection="";
        w.playSound(null,at.x,at.y,at.z,SoundEvents.BLOCK_ANVIL_PLACE,SoundCategory.PLAYERS,.6f,1.4f);publish();
    }
    public static void throwPack(MinecraftServer server,Scope s){
        var p=owner(server,s);if(p==null)return;
        if(!budget.spendArmor()){packsDenied++;publish();return;}
        var k=new Pack();k.scope=s;k.pos=p.getEyePos();k.vel=p.getRotationVec(1).multiply(.75); // 原版 15m/s，重力9.8
        packs.add(k);if(packs.size()>8)packs.remove(0);packsThrown++;publish();
    }
    /** 只在原版 ModifyHealth24 新 tick 到达时调用；命中炮台优先，否则真实 MC 近战命中。 */
    public static void hammer(MinecraftServer server,Scope s){
        var p=owner(server,s);if(p==null)return;hammerSwings++;
        var w=p.getServerWorld();var from=p.getEyePos();var to=from.add(p.getRotationVec(1).multiply(2.5));
        var wall=w.raycast(new RaycastContext(from,to,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
        if(wall.getType()==HitResult.Type.BLOCK)to=wall.getPos();
        var turretHit=turret==null?Optional.<Vec3d>empty():new Box(turret.pos.add(-.6,0,-.6),turret.pos.add(.6,1.4,.6)).expand(.15).raycast(from,to);
        LivingEntity best=null;double nearest=turretHit.map(v->from.squaredDistanceTo(v)).orElse(Double.MAX_VALUE);
        for(var e:w.getEntitiesByClass(LivingEntity.class,new Box(from,to).expand(.4),e->e.isAlive()&&!(e instanceof PlayerEntity)&&(turret==null||e!=turret.entity))){
            var hit=e.getBoundingBox().expand(.2).raycast(from,to);
            if(hit.isPresent()&&from.squaredDistanceTo(hit.get())<nearest){nearest=from.squaredDistanceTo(hit.get());best=e;}
        }
        if(best!=null){var result=NativeDamageTargets.meleeDamage(w,best,p,75*NativeShotSimulation.HP_SCALE);if(result.applied()){hammerHits++;damageApplied+=result.healthLost();}}
        else if(turretHit.isPresent()){
            var t=turret;float before=t.entity.getHealth(),maximum=t.entity.getMaxHealth();
            if(before<maximum){t.entity.setHealth(Math.min(maximum,before+5));repairs++;repaired+=(t.entity.getHealth()-before)/NativeShotSimulation.HP_SCALE;}
            else{
                var next=NativeTorbjornTuning.hammer(t.level,t.upgrade);t.level=next.level();t.upgrade=next.progress();
                if(next.upgraded()){upgrades++;float maximumHealth=(float)(NativeTorbjornTuning.health(t.level,core)*NativeShotSimulation.HP_SCALE);
                    t.entity.getAttributeInstance(EntityAttributes.GENERIC_MAX_HEALTH).setBaseValue(maximumHealth);t.entity.setHealth(maximumHealth);}
            }
            w.playSound(null,t.pos.x,t.pos.y,t.pos.z,SoundEvents.BLOCK_ANVIL_USE,SoundCategory.PLAYERS,.6f,1.3f);
        }
        publish();
    }
    /** 原版 Core19/20/17 生命周期；不使用 Q 按键或猜测20s计时。 */
    public static void core(MinecraftServer server,Scope s,boolean active,long cycle,long observedWall){
        var p=owner(server,s);long now=System.currentTimeMillis();if(p==null||now-observedWall>150||observedWall>now+50)return;
        absorptionSpent();
        if(active&&(!core||cycle!=coreBegin)){
            if(!coreAdmissions.admit(new NativeTorbjornCoreAdmission.Actor(s.owner(),s.source(),s.model()),cycle))return;
            // 若漏掉前一个 End，也先撤销旧效果，再执行已认证的新 Begin。
            endCore();coreBegin=cycle;core=true;coreCasts++;coreRemaining=30;
            p.getAttributeInstance(EntityAttributes.GENERIC_MAX_ABSORPTION).addTemporaryModifier(new EntityAttributeModifier(CORE_ARMOR,30,EntityAttributeModifier.Operation.ADD_VALUE));
            p.getAttributeInstance(EntityAttributes.GENERIC_ATTACK_SPEED).addTemporaryModifier(new EntityAttributeModifier(CORE_SPEED,.5,EntityAttributeModifier.Operation.ADD_MULTIPLIED_TOTAL));
            p.setAbsorptionAmount(p.getAbsorptionAmount()+30);lastAbsorption=p.getAbsorptionAmount();
            if(turret!=null&&turret.level==2){turret.entity.getAttributeInstance(EntityAttributes.GENERIC_MAX_HEALTH).setBaseValue(80);turret.entity.setHealth(turret.entity.getHealth()+50);}
        }else if(!active&&core)endCore();coreWall=observedWall;publish();
    }
    private static void absorptionSpent(){
        if(boundOwner==null)return;float now=boundOwner.getAbsorptionAmount(),spent=Math.max(0,lastAbsorption-now);
        float used=Math.min(coreRemaining,spent);coreRemaining-=used;lastAbsorption=now;
    }
    private static void endCore(){
        if(!core)return;absorptionSpent();core=false;coreEnds++;
        if(boundOwner!=null){float amount=Math.max(0,boundOwner.getAbsorptionAmount()-coreRemaining);
            boundOwner.getAttributeInstance(EntityAttributes.GENERIC_MAX_ABSORPTION).removeModifier(CORE_ARMOR);
            boundOwner.getAttributeInstance(EntityAttributes.GENERIC_ATTACK_SPEED).removeModifier(CORE_SPEED);boundOwner.setAbsorptionAmount(amount);lastAbsorption=boundOwner.getAbsorptionAmount();}
        coreRemaining=0;
        if(turret!=null){float max=(float)(NativeTorbjornTuning.health(turret.level,false)*NativeShotSimulation.HP_SCALE);
            turret.entity.getAttributeInstance(EntityAttributes.GENERIC_MAX_HEALTH).setBaseValue(max);turret.entity.setHealth(Math.min(max,turret.entity.getHealth()));}
    }
    public static void tick(MinecraftServer server){
        if(currentScope==null)return;var p=owner(server,currentScope);if(p==null){resetSession();return;}
        absorptionSpent();if(core&&System.currentTimeMillis()-coreWall>250)endCore();
        if(turret!=null){if(!turret.entity.isAlive()||turret.entity.isRemoved())turret=null;else tickTurret(p);}
        for(var k:new ArrayList<>(packs)){
            if(++k.age>PACK_LIFE){packs.remove(k);continue;}var w=p.getServerWorld();
            if(!k.landed){var next=k.pos.add(k.vel);var h=w.raycast(new RaycastContext(k.pos,next,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
                if(h.getType()==HitResult.Type.BLOCK){k.pos=h.getPos().add(Vec3d.of(((BlockHitResult)h).getSide().getVector()).multiply(.03));k.landed=true;}else{k.pos=next;k.vel=k.vel.add(0,-9.8/400,0);}}
            if(!k.ownerRejected&&p.getBoundingBox().expand(.8).contains(k.pos)){k.ownerRejected=true;ownerPickupDenied++;}
            for(var recipient:w.getEntitiesByClass(LivingEntity.class,new Box(k.pos,k.pos).expand(1.2),e->
                NativeTorbjornTuning.recipient(k.scope.owner(),e.getUuid(),e.isAlive(),e.isSpectator())
                &&(e instanceof PlayerEntity&&(p.getScoreboardTeam()==null||p.isTeammate(e))||e instanceof VillagerEntity)
                &&e.getAbsorptionAmount()<ARMOR*NativeShotSimulation.HP_SCALE)){
                float before=recipient.getAbsorptionAmount();
                // MC适配：原版包75HP→7.5吸收，标准效果负责60秒到期/存档/属性清理；不在换英雄时剥夺他人已拾取的护甲。
                recipient.addStatusEffect(new StatusEffectInstance(StatusEffects.ABSORPTION,20*60,1,false,true));
                recipient.setAbsorptionAmount(Math.max(before,(float)(ARMOR*NativeShotSimulation.HP_SCALE)));
                if(recipient.getAbsorptionAmount()<=before)continue;
                packs.remove(k);packsTaken++;lastPackRecipient=recipient.getUuidAsString();lastPackAbsorption=recipient.getAbsorptionAmount();
                w.playSound(null,k.pos.x,k.pos.y,k.pos.z,SoundEvents.ITEM_ARMOR_EQUIP_IRON.value(),SoundCategory.PLAYERS,1f,1f);
                break;
            }
        }
        for(var s:new ArrayList<>(scrap)){
            if(++s.age>600){scrap.remove(s);continue;}
            if(p.getBoundingBox().expand(1.2).contains(s.pos)&&budget.collect()){scrap.remove(s);scrapTaken++;}
        }
        publish();
    }
    private static void tickTurret(ServerPlayerEntity p){
        var w=p.getServerWorld();var t=turret;if(t.cooldown>0)t.cooldown--;if(t.rocketCooldown>0)t.rocketCooldown--;
        var muzzle=t.pos.add(0,.9,0);LivingEntity best=null;double bd=RANGE*RANGE;
        for(var e:w.getEntitiesByClass(LivingEntity.class,new Box(muzzle,muzzle).expand(RANGE),e->e.isAlive()&&e instanceof Monster)){
            var c=e.getBoundingBox().getCenter();double d=c.squaredDistanceTo(muzzle);if(d>=bd)continue;
            if(w.raycast(new RaycastContext(muzzle,c,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p)).getType()==HitResult.Type.MISS){bd=d;best=e;}}
        boolean firing=false;int level=NativeTorbjornTuning.effectiveLevel(t.level,core);
        if(best!=null){var c=best.getBoundingBox().getCenter().subtract(muzzle);t.yaw=(float)Math.toDegrees(Math.atan2(-c.x,c.z));
            if(t.cooldown==0){t.cooldown=core?5:10;shots++;firing=true;var r=NativeDamageTargets.projectileDamage(w,best,p,SHOT*(t.level>=2?2:1)*NativeShotSimulation.HP_SCALE);if(r.applied()){hits++;damageApplied+=r.healthLost();}
                w.spawnParticles(ParticleTypes.SMOKE,muzzle.x,muzzle.y,muzzle.z,2,.03,.03,.03,0);}
            if(level==3&&t.rocketCooldown==0){t.rocketCooldown=20;rockets++;var result=NativeDamageTargets.explosionDamage(w,best,p,80*NativeShotSimulation.HP_SCALE);if(result.applied())damageApplied+=result.healthLost();}
        }
        view=new TurretView(t.pos,t.yaw,level,firing,t.scope.world(),System.currentTimeMillis());
    }
    private static void publish(){
        long now=System.currentTimeMillis();viewWorld=currentScope==null?0:currentScope.world();viewWall=now;if(turret==null)view=null;else view=new TurretView(turret.pos,turret.yaw,NativeTorbjornTuning.effectiveLevel(turret.level,core),view!=null&&view.firing(),turret.scope.world(),now);
        packViews=packs.stream().map(k->k.pos).toList();scrapViews=currentScope==null?List.of():scrap.stream().map(s->new ScrapView(s.pos,25,currentScope.world(),now)).toList();scrapAmount=budget.amount();
        var o=new JsonObject();o.addProperty("turret",turret!=null);o.addProperty("deploys",deploys);o.addProperty("shots",shots);o.addProperty("hits",hits);o.addProperty("damageApplied",damageApplied);
        o.addProperty("deployAttempts",deployAttempts);o.addProperty("lastDeployRejection",lastDeployRejection);o.add("signals",com.google.gson.JsonParser.parseString(nativeSignals));
        o.addProperty("level",view==null?0:view.level());o.addProperty("turretHealth",turret==null?0:turret.entity.getHealth()/NativeShotSimulation.HP_SCALE);o.addProperty("upgrade",turret==null?0:turret.upgrade);
        o.addProperty("baseLevel",turret==null?0:turret.level);o.addProperty("maxLevel",NativeTorbjornTuning.MAX_LEVEL);o.addProperty("coreLevel",NativeTorbjornTuning.CORE_LEVEL);o.addProperty("upgradeRequired",NativeTorbjornTuning.UPGRADE_REQUIRED);
        o.addProperty("packs",packs.size());o.addProperty("packsThrown",packsThrown);o.addProperty("packsTaken",packsTaken);o.addProperty("packsDenied",packsDenied);o.addProperty("armorPackCost",50);
        o.addProperty("hammerSwings",hammerSwings);o.addProperty("hammerHits",hammerHits);o.addProperty("repairs",repairs);o.addProperty("repaired",repaired);o.addProperty("upgrades",upgrades);
        o.addProperty("scrap",budget.amount());o.addProperty("scrapDrops",scrapDrops);o.addProperty("scrapTaken",scrapTaken);o.addProperty("scrapOnGround",scrap.size());o.addProperty("scrapSpent",budget.spent());
        o.addProperty("core",core);o.addProperty("coreCasts",coreCasts);o.addProperty("coreEnds",coreEnds);o.addProperty("coreBegin",coreBegin);o.addProperty("coreArmorRemaining",coreRemaining);o.addProperty("armorRemaining",0);o.addProperty("coreAttackSpeedMultiplier",core?1.5:1);o.addProperty("turretInterval",core?5:10);o.addProperty("rockets",rockets);
        o.addProperty("ownerPickupAllowed",false);o.addProperty("ownerPickupDenied",ownerPickupDenied);o.addProperty("lastPackRecipient",lastPackRecipient);o.addProperty("lastPackAbsorption",lastPackAbsorption);
        o.addProperty("packTestRecipient",packTestRecipient);
        o.addProperty("adapter","MC scrap/armor/contact/physics; native attack ticks and Core lifecycle");status=o.toString();
    }
    public static void resetSession(){
        endCore();
        // 这里只清理 MC 效果。coreAdmissions 的原版执行令牌必须跨 cleanup/reset/换世界保留。
        if(turret!=null)turret.entity.discard();turret=null;packs.clear();scrap.clear();deaths.clear();budget.clear();currentScope=null;boundOwner=null;coreBegin=0;lastAbsorption=0;packTestRecipient="";publish();
    }
    public static void clear(){resetSession();}
}
