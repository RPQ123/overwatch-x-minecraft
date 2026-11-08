package lab.owmcguest;

import java.util.*;
import java.util.concurrent.ArrayBlockingQueue;
import net.minecraft.entity.Entity;
import net.minecraft.entity.LivingEntity;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;

/** All heroes share actual MC health/absorption loss and death, never input. */
public final class NativeCombatFeedback {
    public record Cue(UUID owner,long world,long hero,long model,long generation,long sequence,long wall,boolean kill){}
    private static final ArrayBlockingQueue<Cue> pending=new ArrayBlockingQueue<>(128);
    private static final CombatFeedbackLedger ledger=new CombatFeedbackLedger();
    private static final LinkedHashMap<UUID,LivingEntity> tracked=new LinkedHashMap<>();
    private static UUID owner;private static long world,hero,model,generation,sequence;
    public static volatile long hitEvents,killEvents,dropped;
    public static void configure(UUID p,long w,long h,long m,long g){resetSession();owner=p;world=w;hero=h;model=m;generation=g;}
    private static boolean matches(ServerPlayerEntity player){return owner!=null&&owner.equals(player.getUuid())&&hero!=0&&model!=0&&generation!=0
        &&NativeWorldIdentity.of(player.getServer(),player.getWorld().getRegistryKey())==world;}
    public static void contact(ServerPlayerEntity player){if(matches(player))emit(System.currentTimeMillis(),false);}
    public static void damage(ServerPlayerEntity player,Entity victim,double loss){
        if(!matches(player)||!(victim instanceof LivingEntity living))return;
        long now=System.currentTimeMillis();
        if(!ledger.damage(living.getUuid(),loss,living.getHealth(),now))return;
        if(living.getHealth()<=0){death(living,now);return;}
        tracked.put(living.getUuid(),living);if(tracked.size()>4096)tracked.remove(tracked.keySet().iterator().next());
        emit(now,false);
    }
    private static void emit(long now,boolean kill){
        if(kill)killEvents++;else hitEvents++;
        if(!pending.offer(new Cue(owner,world,hero,model,generation,++sequence,now,kill)))dropped++;
    }
    private static void death(LivingEntity victim,long now){
        tracked.remove(victim.getUuid());if(ledger.death(victim.getUuid(),victim.getHealth(),now))emit(now,true);
    }
    public static void tick(MinecraftServer server){
        var player=owner==null?null:server.getPlayerManager().getPlayer(owner);long now=System.currentTimeMillis();
        if(player==null||!player.isAlive()||!matches(player)){pending.clear();tracked.clear();ledger.clear();return;}
        for(var victim:new ArrayList<>(tracked.values())){
            if(victim.getHealth()<=0)death(victim,now);
            else if(victim.isRemoved()||!ledger.tracking(victim.getUuid(),now))tracked.remove(victim.getUuid());
        }
        ledger.expire(now);
    }
    public static Cue poll(){return pending.poll();}
    public static void resetSession(){owner=null;world=hero=model=generation=sequence=0;pending.clear();tracked.clear();ledger.clear();}
}
