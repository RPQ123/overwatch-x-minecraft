package lab.owmcguest;

import com.google.gson.JsonObject;
import java.util.*;
import net.minecraft.entity.Entity;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.effect.StatusEffectInstance;
import net.minecraft.entity.effect.StatusEffects;
import net.minecraft.entity.passive.PassiveEntity;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.math.*;
import net.minecraft.world.RaycastContext;

/** Beta24919 / HERO-BRIEFS-NEW8-20261025 §7.
 * 左键只消费真实工厂子发（不是按一次B生成四发）：速度40、寿命5、射程100、伤害20来自声明。
 * MC 适配：无重力直线（重力未声明）、MC眼位起射、.1碰撞扩张；原版工厂方向及逐发标识保留。
 * 65仅认证音爆动作，serverOnly28/29未执行，故只计尝试，不凭动画施加伤害/击退。
 * 切歌3只认证变量提交，3d <- 1d8 的语义、前后值未校准，不能把3/9各自当一次切换或猜初始歌曲。
 * 保留治疗/加速/强音服务端结算逻辑，但歌曲UNKNOWN时关闭，待认证变量映射后接入。
 * 音障0 B/E认证Aura包络，MC适配：12m、视线、自己/同队/被动生物、临时吸收40 MC HP、最多8s安全寿命。
 * 治疗/速度MC适配值（待歌曲认证）：12m，12/40 OW HP/s，SPEED 0/1，强音只跟随11 B/E，不拿动画2500当时长。
 * 新增路径只从原版29 ModifyHealth B结算音爆、0263:25 WallMove B/E准入滑墙；
 * 保存的generic2中均未执行，仍待实机校准。MC适配音爆5m/60度半角/水平1.2+向上.15速度，伤害未猜。
 * 歌曲9写0004/06c7；3d的0→.25→0是过渡值，绝不按它或按Shift切换HEAL/SPEED。
 */
public final class LucioServer implements HeroServerModule {
    public static final LucioServer INSTANCE=new LucioServer();
    public static final long HERO=0x02e0000000000079L;
    public record Scope(UUID owner,long world,long source,long model){}
    public record View(long world,Vec3d at,Vec3d velocity,long wall){}
    public enum Song {UNKNOWN,HEAL,SPEED}
    private static final double RADIUS=12,HEAL_RATE=12,AMP_HEAL_RATE=40;
    private static final class Pulse {Vec3d at,velocity;int age;}
    private record Window(long opened,long closed){}
    private record Owned(LivingEntity entity,StatusEffectInstance effect){}
    private final List<Pulse> pulses=new ArrayList<>();private final List<Owned> shields=new ArrayList<>(),speeds=new ArrayList<>();
    private final LinkedHashMap<String,Boolean> factories=new LinkedHashMap<>();
    private final Map<String,String> seen=new HashMap<>();private final Map<Long,Window> windows=new HashMap<>();
    private Scope scope;private long lease,volleyBegin;private boolean volley,amp,barrier;private Song song=Song.UNKNOWN;
    private boolean wallMove;
    private Vec3d previousWall;
    private long boopCasts,boopHits,wallBegins,wallTicks;
    private double wallDistance;
    private long volleys,subshots,duplicates,refused,boopAttempts,songCommits,ampCasts,barrierCasts,shieldGrants,hits,heals,speedGrants;
    private double damageApplied,healingApplied;private volatile String json="{}";
    public volatile List<View> views=List.of();
    private LucioServer(){publish();}
    private ServerPlayerEntity owner(MinecraftServer s){var p=scope==null?null:s.getPlayerManager().getPlayer(scope.owner());return p!=null&&p.isAlive()&&NativeWorldIdentity.of(s,p.getWorld().getRegistryKey())==scope.world()?p:null;}
    private boolean valid(MinecraftServer s,Scope next,long wall){
        long now=System.currentTimeMillis();if(next==null||next.world()==0||next.source()==0||next.model()==0||wall>now+50||now-wall>150)return false;
        if(!next.equals(scope)){resetSession();scope=next;}lease=wall;return owner(s)!=null;
    }
    public void heartbeat(MinecraftServer s,Scope next,long wall){if(valid(s,next,wall))publish();}
    public void signal(MinecraftServer s,Scope next,String node,long tick,boolean active,long wall){
        if(!valid(s,next,wall)||tick<=0)return;String id=tick+":"+active;String prior=seen.put(node,id);if(id.equals(prior))return;
        if(active&&prior!=null&&prior.endsWith(":true")&&(node.equals("boop")||node.equals("ampCast")))return;
        switch(node){
            case "volley" -> {
                if(active){if(!volley){volleys++;volleyBegin=tick;windows.put(tick,new Window(wall,0));}volley=true;}
                else{volley=false;var w=windows.get(volleyBegin);if(w!=null)windows.put(volleyBegin,new Window(w.opened(),wall));}
            }
            case "boop" -> {if(active)boopAttempts++;}
            case "boopCommit" -> {if(active){boopCasts++;boop(s);}}
            case "wallMove" -> {if(active&&!wallMove)wallBegins++;wallMove=active;if(!active)previousWall=null;}
            case "songCommit" -> {if(!active){songCommits++;song=Song.UNKNOWN;clearSpeed();}}
            case "ampCast" -> {if(active)ampCasts++;}
            case "ampWindow" -> amp=active;
            case "barrier" -> {
                if(active&&!barrier){barrierCasts++;var p=owner(s);if(p!=null)for(var e:friends(p))grantShield(e);}
                if(!active)clearShields();barrier=active;
            }
            default -> throw new IllegalArgumentException("unknown Lucio node");
        }publish();
    }
    private void boop(MinecraftServer s){
        var p=owner(s);if(p==null)return;var from=p.getEyePos();var forward=p.getRotationVec(1).normalize();
        var hit=new HashSet<UUID>();
        for(var part:NativeDamageTargets.in(p.getServerWorld(),p,p.getBoundingBox().expand(5))){
            var target=NativeDamageTargets.owner(part);
            if(!(target instanceof LivingEntity living)||p.isTeammate(target)||target instanceof PassiveEntity||!hit.add(target.getUuid()))continue;
            var delta=part.getBoundingBox().getCenter().subtract(from);double length=delta.length();
            if(length<1e-6||length>5||delta.dotProduct(forward)/length<.5||!visible(p,from,part.getBoundingBox().getCenter()))continue;
            var horizontal=new Vec3d(forward.x,0,forward.z);if(horizontal.lengthSquared()<1e-8)continue;
            living.setVelocity(living.getVelocity().add(horizontal.normalize().multiply(1.2)).add(0,.15,0));living.velocityModified=true;boopHits++;
        }
    }
    /** 只准入当前原版窗口里的已验证工厂子发；重复journal快照不会产生第二发。不写共享combat ACK。 */
    public void factory(MinecraftServer s,Scope next,String id,long begin,long captured,Vec3d direction,long wall){
        if(!valid(s,next,wall))return;var w=windows.get(begin);
        if(w==null||captured<w.opened()-50||(w.closed()!=0&&captured>w.closed()+50)||wall-captured>150||captured>wall+50
            ||!Double.isFinite(direction.lengthSquared())||Math.abs(direction.lengthSquared()-1)>.01){refused++;publish();return;}
        if(factories.putIfAbsent(id,true)!=null){duplicates++;return;}while(factories.size()>512)factories.remove(factories.keySet().iterator().next());
        var p=owner(s);if(p==null||pulses.size()>=128){refused++;return;}
        var b=new Pulse();b.at=p.getEyePos();b.velocity=direction.multiply(40/20.0);pulses.add(b);subshots++;publish();
    }
    private static boolean visible(ServerPlayerEntity p,Vec3d from,Vec3d to){var w=p.getServerWorld();return w.isChunkLoaded(BlockPos.ofFloored(to))&&w.raycast(new RaycastContext(from,to,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p)).getType()==HitResult.Type.MISS;}
    private static List<LivingEntity> friends(ServerPlayerEntity p){
        var out=new ArrayList<LivingEntity>();out.add(p);
        for(var e:p.getServerWorld().getEntitiesByClass(LivingEntity.class,p.getBoundingBox().expand(RADIUS),LivingEntity::isAlive)){
            if(e==p||e.isSpectator()||e.squaredDistanceTo(p)>RADIUS*RADIUS)continue;
            // MC 适配友方规则显式限定；不把所有敌对生物当治疗目标。
            if(!(e instanceof PassiveEntity)&&!(p.getScoreboardTeam()!=null&&p.isTeammate(e)))continue;
            if(visible(p,p.getEyePos(),e.getEyePos()))out.add(e);
        }return out;
    }
    private void grantShield(LivingEntity e){
        // 不覆盖其他来源的吸收效果或吸收量，回收也只移除自己仍持有的实例。
        if(e.hasStatusEffect(StatusEffects.ABSORPTION)||e.getAbsorptionAmount()>0)return;
        if(e.addStatusEffect(new StatusEffectInstance(StatusEffects.ABSORPTION,160,9,false,false))){shields.add(new Owned(e,e.getStatusEffect(StatusEffects.ABSORPTION)));shieldGrants++;}
    }
    private void clearShields(){for(var o:shields)if(o.entity().getStatusEffect(StatusEffects.ABSORPTION)==o.effect())o.entity().removeStatusEffect(StatusEffects.ABSORPTION);shields.clear();}
    private void clearSpeed(){for(var o:speeds)if(o.entity().getStatusEffect(StatusEffects.SPEED)==o.effect())o.entity().removeStatusEffect(StatusEffects.SPEED);speeds.clear();}
    /** 服务端光环路径保持UNKNOWN关闭；当前证据不足以调用此路径选择某首歌曲。 */
    private void songTick(ServerPlayerEntity p){
        if(song==Song.UNKNOWN)return;
        if(song==Song.HEAL){clearSpeed();for(var e:friends(p)){float before=e.getHealth();e.heal((float)((amp?AMP_HEAL_RATE:HEAL_RATE)*NativeShotSimulation.HP_SCALE/20));double lost=e.getHealth()-before;if(lost>0){heals++;healingApplied+=lost;}}}
        else if(p.age%4==0){
            for(var e:friends(p)){
                if(e.hasStatusEffect(StatusEffects.SPEED))continue;
                if(e.addStatusEffect(new StatusEffectInstance(StatusEffects.SPEED,5,amp?1:0,false,false))){speeds.add(new Owned(e,e.getStatusEffect(StatusEffects.SPEED)));speedGrants++;}
            }
            speeds.removeIf(o->o.entity().getStatusEffect(StatusEffects.SPEED)!=o.effect());
        }
    }
    @Override public void tick(MinecraftServer s){
        if(scope==null)return;var p=owner(s);long now=System.currentTimeMillis();if(p==null||now-lease>200){resetSession();return;}
        if(wallMove){wallTicks++;if(previousWall!=null){double distance=p.getPos().distanceTo(previousWall);if(distance<2)wallDistance+=distance;}previousWall=p.getPos();}
        windows.entrySet().removeIf(e->e.getValue().closed()!=0&&now-e.getValue().closed()>500);var w=p.getServerWorld();var draw=new ArrayList<View>();
        for(var b:new ArrayList<>(pulses)){
            var end=b.at.add(b.velocity);if(++b.age>100||b.age*2>100||!w.isChunkLoaded(BlockPos.ofFloored(end))){pulses.remove(b);continue;}
            var block=w.raycast(new RaycastContext(b.at,end,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
            Vec3d stop=block.getType()==HitResult.Type.BLOCK?block.getPos():end;double nearest=block.getType()==HitResult.Type.BLOCK?b.at.squaredDistanceTo(stop):Double.POSITIVE_INFINITY;Entity target=null;
            for(var e:NativeDamageTargets.in(w,p,new Box(b.at,stop).expand(.1))){
                if(e instanceof PlayerEntity&&p.isTeammate(e))continue;var box=e.getBoundingBox().expand(.1);var h=box.contains(b.at)?Optional.of(b.at):box.raycast(b.at,stop);
                if(h.isPresent()&&b.at.squaredDistanceTo(h.get())<nearest&&visible(p,b.at,e.getBoundingBox().getCenter())){nearest=b.at.squaredDistanceTo(h.get());target=e;}
            }
            if(target!=null){var r=NativeDamageTargets.projectileDamage(w,target,p,20*NativeShotSimulation.HP_SCALE);if(r.applied()){hits++;damageApplied+=r.healthLost();}pulses.remove(b);continue;}
            if(block.getType()==HitResult.Type.BLOCK){pulses.remove(b);continue;}
            b.at=end;draw.add(new View(scope.world(),b.at,b.velocity,now));w.spawnParticles(ParticleTypes.END_ROD,b.at.x,b.at.y,b.at.z,1,0,0,0,0);
        }
        songTick(p);views=List.copyOf(draw);publish();
    }
    @Override public void resetSession(){clearShields();clearSpeed();pulses.clear();factories.clear();windows.clear();seen.clear();scope=null;lease=volleyBegin=0;volley=amp=barrier=wallMove=false;previousWall=null;song=Song.UNKNOWN;views=List.of();publish();}
    private void publish(){
        var o=new JsonObject();o.addProperty("volleys",volleys);o.addProperty("subshots",subshots);o.addProperty("volleyActive",volley);o.addProperty("active",pulses.size());o.addProperty("duplicates",duplicates);o.addProperty("refused",refused);
        o.addProperty("boopAttempts",boopAttempts);o.addProperty("boopCasts",boopCasts);o.addProperty("boopHits",boopHits);o.addProperty("songCommits",songCommits);o.addProperty("song",song.name());o.addProperty("ampCasts",ampCasts);o.addProperty("ampWindow",amp);
        o.addProperty("wallBegins",wallBegins);o.addProperty("wallActive",wallMove);o.addProperty("wallTicks",wallTicks);o.addProperty("wallDistance",wallDistance);
        o.addProperty("barrierCasts",barrierCasts);o.addProperty("barrierActive",barrier);o.addProperty("shieldGrants",shieldGrants);o.addProperty("heals",heals);o.addProperty("healingApplied",healingApplied);o.addProperty("speedGrants",speedGrants);
        o.addProperty("hits",hits);o.addProperty("damageApplied",damageApplied);
        o.addProperty("blocked","音爆29/滑墙0263:25已接真实B/E但保存录证未执行；歌曲0004/06c7未采到且语义未认证，治疗/加速保持UNKNOWN；3d不是歌曲枚举");
        o.addProperty("supportAdaptation","MC 适配: 真实音爆29B→5m/60度半角敌方击退1.2水平+.15竖直; WallMove25B/E→MC墙面碰撞/滑行; 原版未校准，无实测验收");
        o.addProperty("adaptation","MC 适配：工厂方向+MC眼位、直线弹道、光环友方筛选、音障40HP临时吸收；音障随原版Aura E回收");
        o.addProperty("projectileModel","原版19f2/19b6模板经models helper居中绘制；尺寸/billboard为MC呈现适配，安装/像素待验收");
        // integrator/models: presentation of accepted state only; preserve its real lease.
if(scope!=null&&barrier){
    var target=shields.stream().map(Owned::entity).filter(e->e.isAlive()&&e.getUuid().equals(scope.owner())).findFirst().orElse(null);
    if(target!=null){
        var f=OriginalEffectFrames.frame(scope.owner(),scope.world(),scope.source(),scope.model(),lease);
        OriginalEffectFrames.body(f,"lucio-sound-barrier",target.getPos().add(0,.3,0),new Vec3d(12,1,12),.6f,false);
        o.add("models",f);
    }
}
        json=o.toString();
    }
    @Override public String statusKey(){return "lucio";}
    @Override public String status(){return json;}
}
