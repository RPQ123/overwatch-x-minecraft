package lab.owmcguest;

import java.util.LinkedHashSet;
import java.util.UUID;
import java.util.*;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.atomic.AtomicLong;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.entity.event.v1.ServerPlayerEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.entity.effect.StatusEffects;
import net.minecraft.entity.damage.DamageTypes;
import com.google.gson.JsonObject;

/** 语音挂接：MC 适配。真实服务端死亡/损血/重生，独立于源氏重置队列。 */
public final class HeroVoiceRuntime {
    public record Binding(long epoch,long source,long model,long world,long hero,UUID player,long wall) {
        public boolean same(Binding b){return b!=null&&epoch==b.epoch&&source==b.source&&model==b.model&&world==b.world&&hero==b.hero&&player.equals(b.player);}
    }
    public record Cue(Binding binding,String event,long sequence,long observedNs,String variant) {}
    private static volatile Binding binding;
    private static final ArrayBlockingQueue<Cue> cues=new ArrayBlockingQueue<>(64);
    private static final AtomicLong sequence=new AtomicLong();
    private static final LinkedHashSet<UUID> dead=new LinkedHashSet<>();
    private static Binding serverScope;
    private static float beforeHealth,lastHealth;
    private static boolean healthBaseline,healArmed;
    private static UUID respawnPlayer;private static long respawnSource,respawnWorld,respawnWall;
    private record Health(Binding binding,float ratio,boolean alive,long wall){}
    private static volatile Health health;
    private static volatile boolean statusBaselineRequested=true;
    private static final Set<String> statusStates=new LinkedHashSet<>();
    private static final Map<String,Long> statusCounts=new LinkedHashMap<>(),controlReceipts=new HashMap<>();
    private static final AtomicLong combatSequence=new AtomicLong();
    private static float effectHealth,effectMaximum;
    private static long lastHealTick=Long.MIN_VALUE/4;
    public static volatile String statusReport="{}";
    public static volatile long kills,deaths,pains,respawns,healingRequests,dropped;
    private HeroVoiceRuntime() {}
    public static void bind(Binding next){binding=next;}
    public static void unbind(){binding=null;cues.clear();statusBaselineRequested=true;}
    public static long combatRevision(){return combatSequence.get();}
    public static Cue poll(){return cues.poll();}
    public static boolean lowHealthCurrent(Binding b){var h=health;return b!=null&&h!=null&&b.same(h.binding)&&h.alive&&h.ratio<.35&&System.currentTimeMillis()-h.wall>=0&&System.currentTimeMillis()-h.wall<=200;}
    private static boolean matches(ServerPlayerEntity p,Binding b){
        long age=b==null?Long.MAX_VALUE:System.currentTimeMillis()-b.wall;
        return b!=null&&age>=0&&age<=500&&p.getServer().isSingleplayer()&&p.getUuid().equals(b.player)
            &&NativeWorldIdentity.of(p.getServer(),p.getWorld().getRegistryKey())==b.world;
    }
    private static void scope(Binding b){
        if(b!=null&&!b.same(serverScope)){serverScope=b;dead.clear();healthBaseline=false;beforeHealth=Float.NaN;statusBaselineRequested=true;controlReceipts.clear();}
    }
    private static void emit(Binding b,String event,String variant){
        if(!HeroVoicePolicy.allowed(event))return; // 语音挂接：不再生产痛叫/状态/闲聊等已清退语音。
        if(!event.equals("jump"))combatSequence.incrementAndGet();
        if(event.startsWith("status:"))statusCounts.merge(event,1L,Long::sum);
        if(!cues.offer(new Cue(b,event,sequence.incrementAndGet(),System.nanoTime(),variant)))dropped++;
    }
    /** 语音挂接：只由已认证“本人控制成功”生产者调用，不能把搜索/减速/按键当眩晕。
     * 当前原版技能多只作用MC怪物；这些入口没有接线时，不会自行产生状态声。 */
    public static boolean controlCommitted(ServerPlayerEntity victim,String event,long receipt){
        if(!Set.of("status:stunned","status:controlled","status:knocked_back","status:revived").contains(event)
            ||receipt<=0||!victim.getServer().isOnThread())return false;
        var b=binding;if(!matches(victim,b))return false;scope(b);
        long previous=controlReceipts.getOrDefault(event,0L);if(receipt<=previous)return false;
        controlReceipts.put(event,receipt);emit(b,event,"");return true;
    }
    public static void register(){
        ServerLivingEntityEvents.ALLOW_DAMAGE.register((entity,source,amount)->{
            if(entity instanceof ServerPlayerEntity p){var b=binding;if(matches(p,b)){scope(b);beforeHealth=p.getHealth();}}
            return true;
        });
        ServerLivingEntityEvents.AFTER_DAMAGE.register((entity,source,base,damage,blocked)->{
            if(source.getAttacker() instanceof ServerPlayerEntity attacker&&matches(attacker,binding)&&damage>0&&!blocked)
                combatSequence.incrementAndGet(); // 语音挂接：仅抑制闲聊，不从命中尝试播放状态声。
            if(!(entity instanceof ServerPlayerEntity p))return;
            var b=binding;if(!matches(p,b))return;scope(b);
            if(p.isAlive()&&Float.isFinite(beforeHealth)&&p.getHealth()<beforeHealth){
                pains++;emit(b,"pain","");health(p,b);
                if(source.isOf(DamageTypes.LIGHTNING_BOLT))emit(b,"status:electrocuted",""); // MC适配：真实闪电损血，不冒充眩晕。
            }
            beforeHealth=Float.NaN;
        });
        ServerLivingEntityEvents.AFTER_DEATH.register((entity,source)->{
            var b=binding;if(b==null)return;
            scope(b);
            if(entity instanceof ServerPlayerEntity p&&matches(p,b)){
                health=new Health(b,0,false,System.currentTimeMillis());
                statusBaselineRequested=true; // 语音挂接：死亡/重生的满血不算受治疗。
                if(dead.add(entity.getUuid())){deaths++;emit(b,"death",source.isIn(net.minecraft.registry.tag.DamageTypeTags.IS_FALL)?"fall":"");}
            }else if(source.getAttacker() instanceof ServerPlayerEntity p&&matches(p,b)&&p.isAlive()
                    &&entity.getWorld()==p.getWorld()&&dead.add(entity.getUuid())){
                kills++;emit(b,"kill","");
            }
            if(dead.size()>4096){var first=dead.iterator();first.next();first.remove();}
        });
        ServerPlayerEvents.AFTER_RESPAWN.register((oldPlayer,newPlayer,alive)->{
            var b=binding;
            if(!alive&&matches(oldPlayer,b)){
                statusBaselineRequested=true;
                respawnPlayer=newPlayer.getUuid();respawnSource=b.source;respawnWorld=NativeWorldIdentity.of(newPlayer.getServer(),newPlayer.getWorld().getRegistryKey());respawnWall=System.currentTimeMillis();
            }
        });
        ServerTickEvents.END_SERVER_TICK.register(HeroVoiceRuntime::tick);
        ServerLifecycleEvents.SERVER_STOPPED.register(server->clear());
    }
    private static void health(ServerPlayerEntity p,Binding b){
        float ratio=p.getHealth()/p.getMaxHealth();
        health=new Health(b,ratio,p.isAlive(),System.currentTimeMillis());
        if(!healthBaseline){healthBaseline=true;lastHealth=p.getHealth();healArmed=ratio>=.35;return;}
        if(ratio>=.5)healArmed=true;
        if(p.isAlive()&&ratio<.35&&healArmed&&p.getHealth()<lastHealth){
            healArmed=false;healingRequests++;emit(b,"healing_request","");
        }
        lastHealth=p.getHealth();
    }
    private static void tick(MinecraftServer server){
        var b=binding;if(b==null)return;var p=server.getPlayerManager().getPlayer(b.player);
        if(p==null||!matches(p,b))return;scope(b);
        if(respawnPlayer!=null){
            long age=System.currentTimeMillis()-respawnWall;
            if(age>3000||b.source!=respawnSource||b.world!=respawnWorld){respawnPlayer=null;}
            else if(p.isAlive()&&p.getUuid().equals(respawnPlayer)){
                respawnPlayer=null;dead.remove(p.getUuid());respawns++;emit(b,"respawn","");healthBaseline=false;
            }
        }
        if(p.isAlive()){health(p,b);statuses(p,b);}
    }
    private static void statuses(ServerPlayerEntity p,Binding b){
        // 语音挂接：MC适配。只能证明这些实际效果，不声称原版敌方技能已命中。
        var active=new LinkedHashSet<String>();
        if(p.isFrozen())active.add("status:frozen");
        if(p.getFrozenTicks()>0)active.add("status:cold");
        if(p.hasStatusEffect(StatusEffects.SLOWNESS))active.add("status:slowed");
        if(p.hasStatusEffect(StatusEffects.POISON))active.add("status:poisoned");
        if(p.hasStatusEffect(StatusEffects.WEAKNESS))active.add("status:debuffed");
        if(p.hasStatusEffect(StatusEffects.STRENGTH))active.add("status:damage_boosted");
        if(p.isOnFire())active.add("status:burning");
        float hp=p.getHealth(),maximum=p.getMaxHealth();long tick=p.getServerWorld().getTime();
        if(statusBaselineRequested){
            statusBaselineRequested=false;statusStates.clear();statusStates.addAll(active);lastHealTick=tick-1000;
        }else{
            for(String event:active)if(!statusStates.contains(event))emit(b,event,"");
            if(maximum==effectMaximum&&hp>effectHealth+.01f){
                if(tick-lastHealTick>40)emit(b,"status:healed",hp>=maximum-.001f?"full":"partial");
                lastHealTick=tick;
            }
            statusStates.clear();statusStates.addAll(active);
        }
        effectHealth=hp;effectMaximum=maximum;
        var out=new JsonObject();var states=new com.google.gson.JsonArray();for(String event:active)states.add(event);
        out.add("active",states);out.addProperty("frozenTicks",p.getFrozenTicks());out.addProperty("health",hp);out.addProperty("maxHealth",maximum);
        out.addProperty("hero",HeroVoicePolicy.heroName(b.hero()));out.addProperty("source",b.source());out.addProperty("model",b.model());out.addProperty("world",b.world());
        out.addProperty("sampledWallMs",System.currentTimeMillis());var counts=new JsonObject();statusCounts.forEach(counts::addProperty);out.add("events",counts);
        out.addProperty("policy","MC适配: 效果新出现/真实回血；不从减速推断眩晕，不把燃烧当OW表现评分");statusReport=out.toString();
    }
    private static void clear(){binding=serverScope=null;health=null;cues.clear();dead.clear();respawnPlayer=null;healthBaseline=false;beforeHealth=Float.NaN;statusStates.clear();controlReceipts.clear();statusBaselineRequested=true;statusReport="{}";}
}
