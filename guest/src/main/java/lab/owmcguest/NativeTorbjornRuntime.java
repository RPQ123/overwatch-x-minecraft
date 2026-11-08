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
    public record TurretView(Vec3d at,float yaw,int level,boolean firing,long world,long wall,Vec3d muzzle,Vec3d target,UUID targetId){}
    public record PackView(long id,Vec3d at,boolean landed,int age,String visualId,Vec3d previous,boolean attracting,long motionWall){public PackView(long id,Vec3d at,boolean landed,int age){this(id,at,landed,age,"",at,false,System.currentTimeMillis());}}
    public record PreviewView(Vec3d at,float yaw,boolean valid,long token,long wall){}
    public record VisualView(Scope scope,TurretView turret,List<PackView> packs,List<ScrapView> scrap,long wall){}
    public record ScrapView(long id,Vec3d at,Vec3d previous,boolean landed,int age,boolean attracting,int value,long world,long wall,long motionWall){}
    public record ScrapCredit(Scope scope,long sequence,long item){}
    private static final class Turret{Scope scope;Vec3d pos,muzzle,target;UUID targetId;float yaw;int cooldown,rocketCooldown,upgrade;int level=1;ArmorStandEntity entity;}
    private static final class Pack{Scope scope;long id,motionWall;Vec3d pos,previous,vel;boolean landed,ownerRejected,attracting;int age;double magnetSpeed;UUID target;String visualId="";}
    private static final class Scrap{long id,motionWall;Vec3d pos,previous;double velocity=.06,magnetSpeed;boolean landed,attracting,creditFailed;int age;}
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
    private static long targetChanges,targetLosses,packsExpired;
    public static volatile PreviewView previewView;
    private static long previewStarts,placementConfirms,placementCancels;
    public static volatile VisualView visualView;
    public static volatile TurretView view;public static volatile List<Vec3d> packViews=List.of();public static volatile List<ScrapView> scrapViews=List.of();
    public static volatile int scrapAmount;public static volatile long viewWorld,viewWall;public static volatile String status="{}";
    public static volatile String nativeSignals="{\"ready\":false,\"error\":\"waiting for native bindings\"}";
    public static volatile ScrapCredit scrapCreditView;
    private static long creditSequence=System.currentTimeMillis()*1024,scrapIds,nativeScrapWall,creditFailures,scrapExpired,scrapAttractionTicks,packAttractionTicks;
    private static boolean nativeScrapReady;
    public static volatile boolean nativeScrapAvailable;
    private static String lastScrapCreditError="";
    private static long deployAttempts;private static String lastDeployRejection="";
    public static volatile String packTestRecipient="";
    public static void killed(ServerPlayerEntity killer,LivingEntity victim){
        if(victim.getHealth()>0||victim.isSpectator()||killer==victim||!(victim.getWorld() instanceof ServerWorld)||currentScope==null||boundOwner==null||killer!=boundOwner||!boundOwner.isAlive()
            ||!valid(boundOwner,currentScope)||victim.getWorld()!=boundOwner.getWorld()
            ||!NativeEliminationRuntime.sessionMatches(currentScope.owner(),currentScope.world(),0x02e0000000000006L,currentScope.model(),currentScope.source())
            ||!deaths.add(victim.getUuid()))return;
        var s=new Scrap();s.id=++scrapIds;s.motionWall=System.currentTimeMillis();s.pos=s.previous=victim.getPos().add(0,.45,0);scrap.add(s);
        if(scrap.size()>128)scrap.stream().filter(item->scrapCreditView==null||scrapCreditView.item()!=item.id).findFirst().ifPresent(scrap::remove);scrapDrops++;
        if(deaths.size()>4096)deaths.clear();publish();
    }
    public static void nativeScrap(Scope scope,int value,long wall){
        if(scope==null||!scope.equals(currentScope)||wall<nativeScrapWall||value<0||value>200)return;
        budget.observeNative(value);nativeScrapWall=wall;nativeScrapReady=true;publish();
    }
    public static void scrapReceipt(Scope scope,ScrapCreditProtocol.Receipt receipt){
        var request=scrapCreditView;if(request==null||!scope.equals(currentScope)||!scope.equals(request.scope())||receipt.sequence()!=request.sequence()||!valid(boundOwner,scope))return;
        var item=scrap.stream().filter(s->s.id==request.item()).findFirst().orElse(null);scrapCreditView=null;if(item==null)return;
        if(receipt.phase()==1){
            scrap.remove(item);scrapTaken++;lastScrapCreditError="";nativeScrap(scope,receipt.after(),receipt.wall());
            if(boundOwner!=null)boundOwner.getServerWorld().playSound(null,item.pos.x,item.pos.y,item.pos.z,SoundEvents.ENTITY_ITEM_PICKUP,SoundCategory.PLAYERS,.7f,1.2f);
        }else if(receipt.phase()==2)nativeScrap(scope,receipt.after(),receipt.wall());
        else{item.creditFailed=true;creditFailures++;lastScrapCreditError="original Set&Notify failed/readback uncertain; this drop is not retried";}
        publish();
    }
    private static boolean valid(ServerPlayerEntity p,Scope s){return p!=null&&s!=null&&p.isAlive()&&p.getUuid().equals(s.owner())&&NativeWorldIdentity.of(p.getServer(),p.getWorld().getRegistryKey())==s.world();}
    private static ServerPlayerEntity owner(MinecraftServer server,Scope s){var p=s==null?null:server.getPlayerManager().getPlayer(s.owner());return s!=null&&s.equals(currentScope)&&valid(p,s)?p:null;}
    public static void observe(MinecraftServer server,Scope s){
        var p=server.getPlayerManager().getPlayer(s.owner());if(!valid(p,s))return;
        if(!s.equals(currentScope)){resetSession();currentScope=s;boundOwner=p;lastAbsorption=p.getAbsorptionAmount();}publish();
    }
    public static PlacementCooldowns.Scope cooldown(Scope s){return new PlacementCooldowns.Scope(s.owner(),s.world(),s.source(),s.model(),2);}
    /** Losing an input lease cancels selection, not an already placed turret. */
    public static void cancel(Scope s){if(s!=null&&s.equals(currentScope)){previewView=null;publish();}}
    public static void revalidateSession(UUID player,long world,long hero,long model,long source){
        if(currentScope!=null&&(!currentScope.owner().equals(player)||currentScope.world()!=world||currentScope.source()!=source
            ||model!=0&&currentScope.model()!=model||hero!=0&&hero!=0x02e0000000000006L))resetSession();
    }
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
    private record Placement(Vec3d at,String rejection){}
    private static Placement placement(ServerPlayerEntity p){
        var w=p.getServerWorld();var eye=p.getEyePos();
        var h=w.raycast(new RaycastContext(eye,eye.add(p.getRotationVec(1).multiply(5)),RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
        Vec3d at=h.getType()==HitResult.Type.BLOCK&&((BlockHitResult)h).getSide()==Direction.UP?h.getPos():p.getPos().add(p.getRotationVec(1).multiply(1,0,1).normalize());
        var floor=w.raycast(new RaycastContext(at.add(0,.2,0),at.add(0,-2,0),RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
        if(floor.getType()!=HitResult.Type.BLOCK||((BlockHitResult)floor).getSide()!=Direction.UP)return new Placement(at,"no-upward-ground");at=floor.getPos();
        var box=new Box(at.add(-.55,0,-.55),at.add(.55,1.4,.55));
        return new Placement(at,p.getBoundingBox().intersects(box)||!w.isSpaceEmpty(p,box)?"occupied-placement":"");
    }
    public static void preview(MinecraftServer server,Scope s,long token,boolean active){
        var p=owner(server,s);if(p==null)return;
        if(!active){if(previewView!=null)placementCancels++;previewView=null;publish();return;}
        var at=placement(p);if(previewView==null)previewStarts++;
        previewView=new PreviewView(at.at(),p.getYaw(),at.rejection().isEmpty()&&PlacementCooldowns.available(cooldown(s)),token,System.currentTimeMillis());publish();
    }
    /** An actual LMB edge during the current original preview is the only
     * production caller. Animation completion never confirms an MC turret. */
    public static boolean confirm(MinecraftServer server,Scope s,long token){
        deployAttempts++;placementConfirms++;var p=owner(server,s);var v=previewView;
        if(p==null||v==null||!v.valid()||v.token()!=token||System.currentTimeMillis()-v.wall()>250){lastDeployRejection="no-current-preview";publish();return false;}
        var candidate=placement(p);if(!candidate.rejection().isEmpty()||candidate.at().squaredDistanceTo(v.at())>.25){lastDeployRejection=candidate.rejection().isEmpty()?"preview-moved":candidate.rejection();publish();return false;}
        boolean accepted=PlacementCooldowns.request(cooldown(s),token,()->deploy(server,s,v));if(accepted)previewView=null;publish();return accepted;
    }
    private static void deploy(MinecraftServer server,Scope s,PreviewView selected){
        var p=owner(server,s);if(p==null)return;var candidate=placement(p);
        if(!candidate.rejection().isEmpty()||candidate.at().squaredDistanceTo(selected.at())>.25){lastDeployRejection="placement changed before native cooldown receipt";publish();return;}
        var w=p.getServerWorld();var at=selected.at();
        var entity=new NativeBuildersBody(w,at.x,at.y,at.z,s.owner());
        entity.getAttributeInstance(EntityAttributes.GENERIC_MAX_HEALTH).setBaseValue(15);entity.setHealth(15);
        if(!w.isSpaceEmpty(entity,new Box(at.add(-.55,0,-.55),at.add(.55,1.4,.55)))){entity.discard();lastDeployRejection="occupied-placement";publish();return;}
        if(!w.spawnEntity(entity)){entity.discard();lastDeployRejection="spawn-refused";publish();return;}
        if(turret!=null)turret.entity.discard();turret=new Turret();turret.scope=s;turret.pos=at;turret.entity=entity;turret.yaw=p.getYaw();deploys++;lastDeployRejection="";
        previewView=null;w.playSound(null,at.x,at.y,at.z,SoundEvents.BLOCK_ANVIL_PLACE,SoundCategory.PLAYERS,.6f,1.4f);publish();
    }
    public static void throwPack(MinecraftServer server,Scope s){
        throwPack(server,s,"");
    }
    public static void throwPack(MinecraftServer server,Scope s,String visualId){
        var p=owner(server,s);if(p==null)return;
        // This entry is called only after a new native Volley5. The original
        // graph has already spent50 via entity Scrap0409; never debit twice.
        budget.nativeArmorAdmitted();
        var k=new Pack();k.scope=s;k.pos=p.getEyePos();k.vel=p.getRotationVec(1).multiply(.75); // 原版 15m/s，重力9.8
        k.previous=k.pos;
        k.motionWall=System.currentTimeMillis();
        k.id=++packsThrown;k.visualId=visualId;packs.add(k);if(packs.size()>8)packs.remove(0);publish();
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
        TorbArmorGrowthRuntime.tick(server);
        if(currentScope==null)return;var p=owner(server,currentScope);if(p==null){resetSession();return;}
        if(previewView!=null&&System.currentTimeMillis()-previewView.wall()>250)previewView=null;
        absorptionSpent();if(core&&System.currentTimeMillis()-coreWall>250)endCore();
        if(turret!=null){if(!turret.entity.isAlive()||turret.entity.isRemoved())turret=null;else tickTurret(p);}
        for(var k:new ArrayList<>(packs)){
            if(++k.age>PACK_LIFE){packs.remove(k);packsExpired++;continue;}var w=p.getServerWorld();
            if(!w.isChunkLoaded(BlockPos.ofFloored(k.pos))){packs.remove(k);packsExpired++;continue;}k.previous=k.pos;k.motionWall=System.currentTimeMillis();
            if(!k.landed){var next=k.pos.add(k.vel);var h=w.raycast(new RaycastContext(k.pos,next,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
                if(h.getType()==HitResult.Type.BLOCK){k.pos=h.getPos().add(Vec3d.of(((BlockHitResult)h).getSide().getVector()).multiply(.03));k.landed=true;}else{k.pos=next;k.vel=k.vel.add(0,-9.8/400,0);}}
            if(!k.ownerRejected&&p.getBoundingBox().expand(.8).contains(k.pos)){k.ownerRejected=true;ownerPickupDenied++;}
            var recipient=k.landed||k.attracting?PickupWorldMotion.nearest(w,p,k.pos,k.target,e->
                NativeTorbjornTuning.recipient(k.scope.owner(),e.getUuid(),e.isAlive(),e.isSpectator())
                &&(e.getAbsorptionAmount()<ARMOR*NativeShotSimulation.HP_SCALE||TorbArmorGrowthRuntime.canRefresh(e,server.getTicks()))):null;
            var motion=PickupWorldMotion.toward(w,p,k.pos,recipient,k.magnetSpeed);k.attracting=motion.attracting();k.magnetSpeed=motion.speed();k.target=recipient==null?null:recipient.getUuid();
            if(k.attracting){k.pos=motion.at();k.vel=Vec3d.ZERO;k.landed=false;packAttractionTicks++;}
            if(recipient!=null&&PickupWorldMotion.touching(k.pos,recipient)&&PickupWorldMotion.clear(w,p,k.pos,PickupWorldMotion.target(recipient))){
                float before=recipient.getAbsorptionAmount();
                boolean refreshing=TorbArmorGrowthRuntime.canRefresh(recipient,server.getTicks());
                if(!TorbArmorGrowthRuntime.apply(w,recipient,server.getTicks()))continue;
                // MC适配：原版包75HP→7.5吸收，标准效果负责60秒到期/存档/属性清理；不在换英雄时剥夺他人已拾取的护甲。
                recipient.addStatusEffect(new StatusEffectInstance(StatusEffects.ABSORPTION,20*60,1,false,true));
                recipient.setAbsorptionAmount(Math.max(before,(float)(ARMOR*NativeShotSimulation.HP_SCALE)));
                if(recipient.getAbsorptionAmount()<=before&&!refreshing)continue;
                packs.remove(k);packsTaken++;lastPackRecipient=recipient.getUuidAsString();lastPackAbsorption=recipient.getAbsorptionAmount();
                w.playSound(null,k.pos.x,k.pos.y,k.pos.z,SoundEvents.ITEM_ARMOR_EQUIP_IRON.value(),SoundCategory.PLAYERS,1f,1f);
            }
        }
        for(var s:new ArrayList<>(scrap)){
            var w=p.getServerWorld();++s.age;boolean pending=scrapCreditView!=null&&scrapCreditView.item()==s.id;
            if(s.age>(pending?620:600)||!w.isChunkLoaded(BlockPos.ofFloored(s.pos))){scrap.remove(s);scrapExpired++;if(pending)scrapCreditView=null;continue;}
            s.previous=s.pos;s.motionWall=System.currentTimeMillis();
            if(!s.landed&&!s.attracting){s.velocity=Math.max(-.5,s.velocity-.04);var next=s.pos.add(0,s.velocity,0);
                var hit=w.raycast(new RaycastContext(s.pos,next.add(0,-.08,0),RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
                if(hit.getType()==HitResult.Type.BLOCK&&s.velocity<0){s.pos=hit.getPos().add(0,.08,0);s.velocity=0;s.landed=true;}else s.pos=next;}
            boolean eligible=nativeScrapReady&&System.currentTimeMillis()-nativeScrapWall<=500&&budget.amount()<200&&!s.creditFailed&&(s.landed||s.attracting);
            var recipient=eligible?PickupWorldMotion.nearest(w,p,s.pos,p.getUuid(),e->e==p):null;
            var motion=PickupWorldMotion.toward(w,p,s.pos,recipient,s.magnetSpeed);s.attracting=motion.attracting();s.magnetSpeed=motion.speed();
            if(s.attracting){s.pos=motion.at();s.landed=false;s.velocity=0;scrapAttractionTicks++;}
            if(scrapCreditView==null&&recipient!=null&&PickupWorldMotion.touching(s.pos,p)&&PickupWorldMotion.clear(w,p,s.pos,PickupWorldMotion.target(p))){
                creditSequence=Math.max(creditSequence+1,System.currentTimeMillis()*1024);scrapCreditView=new ScrapCredit(currentScope,creditSequence,s.id);
            }
        }
        publish();
    }
    private static void tickTurret(ServerPlayerEntity p){
        var w=p.getServerWorld();var t=turret;if(t.cooldown>0)t.cooldown--;if(t.rocketCooldown>0)t.rocketCooldown--;
        int level=NativeTorbjornTuning.effectiveLevel(t.level,core);
        LivingEntity best=null;double bd=RANGE*RANGE;Vec3d muzzle=muzzle(t.pos,t.yaw,level);
        for(var e:w.getEntitiesByClass(LivingEntity.class,new Box(muzzle,muzzle).expand(RANGE),e->e.isAlive()&&e instanceof Monster)){
            var c=e.getBoundingBox().getCenter();double d=c.squaredDistanceTo(muzzle);if(d>=bd)continue;
            var direction=c.subtract(t.pos);float yaw=(float)Math.toDegrees(Math.atan2(-direction.x,direction.z));var origin=muzzle(t.pos,yaw,level);
            if(w.raycast(new RaycastContext(origin,c,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p)).getType()==HitResult.Type.MISS){bd=d;best=e;}}
        UUID previous=t.targetId;t.target=null;t.targetId=null;boolean firing=false;
        if(best!=null){var c=best.getBoundingBox().getCenter().subtract(t.pos);t.yaw=(float)Math.toDegrees(Math.atan2(-c.x,c.z));
            muzzle=muzzle(t.pos,t.yaw,level);t.target=best.getBoundingBox().getCenter();t.targetId=best.getUuid();
            if(t.cooldown==0){t.cooldown=core?5:10;shots++;firing=true;var r=NativeDamageTargets.projectileDamage(w,best,p,SHOT*(t.level>=2?2:1)*NativeShotSimulation.HP_SCALE);if(r.applied()){hits++;damageApplied+=r.healthLost();}
                TorbTurretShots.launch(t.scope,muzzle,t.target,level);
                w.spawnParticles(ParticleTypes.SMOKE,muzzle.x,muzzle.y,muzzle.z,2,.03,.03,.03,0);}
            if(level==3&&t.rocketCooldown==0){t.rocketCooldown=20;rockets++;var result=NativeDamageTargets.explosionDamage(w,best,p,80*NativeShotSimulation.HP_SCALE);if(result.applied())damageApplied+=result.healthLost();}
        }
        t.muzzle=muzzle;if(!Objects.equals(previous,t.targetId)){if(t.targetId==null)targetLosses++;else targetChanges++;}
        view=new TurretView(t.pos,t.yaw,level,firing,t.scope.world(),System.currentTimeMillis(),t.muzzle,t.target,t.targetId);
    }
    private static Vec3d muzzle(Vec3d at,float yaw,int level){var v=TorbTurretGeometry.muzzle(new NativeShotProtocol.Vec(at.x,at.y,at.z),yaw,level);return new Vec3d(v.x(),v.y(),v.z());}
    private static void publish(){
        TorbTurretShots.publish(currentScope,System.currentTimeMillis());
        long now=System.currentTimeMillis();viewWorld=currentScope==null?0:currentScope.world();viewWall=now;if(turret==null)view=null;else view=new TurretView(turret.pos,turret.yaw,NativeTorbjornTuning.effectiveLevel(turret.level,core),view!=null&&view.firing(),turret.scope.world(),now,turret.muzzle,turret.target,turret.targetId);
        packViews=packs.stream().map(k->k.pos).toList();scrapViews=currentScope==null?List.of():scrap.stream().map(s->new ScrapView(s.id,s.pos,s.previous,s.landed,s.age,s.attracting,25,currentScope.world(),now,s.motionWall)).toList();scrapAmount=budget.amount();nativeScrapAvailable=nativeScrapReady&&now-nativeScrapWall<=500;
        visualView=currentScope==null?null:new VisualView(currentScope,view,packs.stream().map(k->new PackView(k.id,k.pos,k.landed,k.age,k.visualId,k.previous,k.attracting,k.motionWall)).toList(),scrapViews,now);
        var o=new JsonObject();o.addProperty("turret",turret!=null);o.addProperty("deploys",deploys);o.addProperty("shots",shots);o.addProperty("hits",hits);o.addProperty("damageApplied",damageApplied);
        o.addProperty("deployAttempts",deployAttempts);o.addProperty("lastDeployRejection",lastDeployRejection);o.add("signals",com.google.gson.JsonParser.parseString(nativeSignals));
        o.addProperty("level",view==null?0:view.level());o.addProperty("turretHealth",turret==null?0:turret.entity.getHealth()/NativeShotSimulation.HP_SCALE);o.addProperty("upgrade",turret==null?0:turret.upgrade);
        o.addProperty("baseLevel",turret==null?0:turret.level);o.addProperty("maxLevel",NativeTorbjornTuning.MAX_LEVEL);o.addProperty("coreLevel",NativeTorbjornTuning.CORE_LEVEL);o.addProperty("upgradeRequired",NativeTorbjornTuning.UPGRADE_REQUIRED);
        o.addProperty("packs",packs.size());o.addProperty("packsThrown",packsThrown);o.addProperty("packsTaken",packsTaken);o.addProperty("packsDenied",packsDenied);o.addProperty("armorPackCost",50);
        o.addProperty("hammerSwings",hammerSwings);o.addProperty("hammerHits",hammerHits);o.addProperty("repairs",repairs);o.addProperty("repaired",repaired);o.addProperty("upgrades",upgrades);
        o.addProperty("scrap",budget.amount());o.addProperty("scrapDrops",scrapDrops);o.addProperty("scrapTaken",scrapTaken);o.addProperty("scrapOnGround",scrap.size());o.addProperty("scrapSpent",budget.spent());
        o.addProperty("nativeScrapReady",nativeScrapReady&&now-nativeScrapWall<=500);o.addProperty("nativeScrapWall",nativeScrapWall);o.addProperty("scrapCreditPending",scrapCreditView!=null);o.addProperty("scrapCreditFailures",creditFailures);
        o.addProperty("lastScrapCreditError",lastScrapCreditError);
        o.addProperty("scrapExpired",scrapExpired);o.addProperty("scrapAttractionTicks",scrapAttractionTicks);o.addProperty("packAttractionTicks",packAttractionTicks);o.addProperty("attractionRadius",PickupKinematics.RADIUS);o.addProperty("pickupRadius",PickupKinematics.CONTACT);
        o.addProperty("core",core);o.addProperty("coreCasts",coreCasts);o.addProperty("coreEnds",coreEnds);o.addProperty("coreBegin",coreBegin);o.addProperty("coreArmorRemaining",coreRemaining);o.addProperty("armorRemaining",0);o.addProperty("coreAttackSpeedMultiplier",core?1.5:1);o.addProperty("turretInterval",core?5:10);o.addProperty("rockets",rockets);
        o.addProperty("ownerPickupAllowed",false);o.addProperty("ownerPickupDenied",ownerPickupDenied);o.addProperty("lastPackRecipient",lastPackRecipient);o.addProperty("lastPackAbsorption",lastPackAbsorption);
        o.addProperty("packTestRecipient",packTestRecipient);
        o.addProperty("packsExpired",packsExpired);o.addProperty("targetChanges",targetChanges);o.addProperty("targetLosses",targetLosses);
        o.addProperty("tracking",turret!=null&&turret.target!=null);o.addProperty("targetId",turret==null||turret.targetId==null?"":turret.targetId.toString());
        o.addProperty("preview",previewView!=null);o.addProperty("previewValid",previewView!=null&&previewView.valid());o.addProperty("previewStarts",previewStarts);o.addProperty("placementConfirms",placementConfirms);o.addProperty("placementCancels",placementCancels);
        if(turret!=null){o.add("turretPosition",new com.google.gson.Gson().toJsonTree(turret.pos));if(turret.muzzle!=null)o.add("muzzle",new com.google.gson.Gson().toJsonTree(turret.muzzle));if(turret.target!=null)o.add("targetPosition",new com.google.gson.Gson().toJsonTree(turret.target));}
        o.add("packPositions",new com.google.gson.Gson().toJsonTree(packs.stream().map(k->new double[]{k.pos.x,k.pos.y,k.pos.z,k.landed?1:0,k.age}).toList()));
        o.addProperty("adapter","MC scrap/armor/contact/physics; native attack ticks and Core lifecycle");status=o.toString();
    }
    public static void resetSession(){
        if(currentScope!=null)PlacementCooldowns.cancel(cooldown(currentScope));
        TorbTurretShots.reset();
        endCore();
        // 这里只清理 MC 效果。coreAdmissions 的原版执行令牌必须跨 cleanup/reset/换世界保留。
        if(turret!=null)turret.entity.discard();turret=null;previewView=null;packs.clear();scrap.clear();deaths.clear();budget.clear();scrapCreditView=null;nativeScrapReady=false;nativeScrapWall=0;lastScrapCreditError="";currentScope=null;boundOwner=null;coreBegin=0;lastAbsorption=0;packTestRecipient="";publish();
    }
    public static void clear(){resetSession();}
}
