package lab.owmcguest;

import java.util.UUID;
import java.util.LinkedHashMap;
import java.util.concurrent.ArrayBlockingQueue;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.Entity;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;

/** Server-confirmed eliminations request one reset of the current native Genji. */
public final class NativeEliminationRuntime {
    public record Reset(long world,long generation,long model,long wallMs,long sequence){}
    private static final ArrayBlockingQueue<Reset> pending=new ArrayBlockingQueue<>(64);
    private static final EliminationLedger ledger=new EliminationLedger();
    private static final LinkedHashMap<UUID,LivingEntity> tracked=new LinkedHashMap<>();
    private static UUID owner;private static long world,hero,model,generation,sequence;
    public static volatile long eliminations,requests,applied;
    public static void configure(UUID player,long nextWorld,long nextHero,long nextModel,long nextGeneration){
        resetSession();owner=player;world=nextWorld;hero=nextHero;model=nextModel;generation=nextGeneration;
    }
    public static void damage(ServerPlayerEntity player,Entity entity,double loss){
        if(hero!=0x02e0000000000029L||model==0||generation==0||!player.getUuid().equals(owner)
           ||NativeWorldIdentity.of(player.getServer(),player.getWorld().getRegistryKey())!=world||!(entity instanceof LivingEntity living)||loss<=0)return;
        long now=System.currentTimeMillis();ledger.damage(living.getUuid(),loss,now);tracked.put(living.getUuid(),living);
        if(living.getHealth()<=0)death(living,now);
    }
    private static void death(LivingEntity victim,long now){
        tracked.remove(victim.getUuid());
        if(ledger.death(victim.getUuid(),victim.getHealth(),now)){
            eliminations++;if(pending.offer(new Reset(world,generation,model,now,++sequence)))requests++;
        }
    }
    public static void tick(MinecraftServer server){
        long now=System.currentTimeMillis();var player=owner==null?null:server.getPlayerManager().getPlayer(owner);
        if(player==null||!player.isAlive()||NativeWorldIdentity.of(server,player.getWorld().getRegistryKey())!=world){pending.clear();tracked.clear();ledger.clear();return;}
        for(var victim:new java.util.ArrayList<>(tracked.values())){
            if(victim.getHealth()<=0)death(victim,now);
            else if(victim.isRemoved())tracked.remove(victim.getUuid());
        }
        ledger.expire(now);if(tracked.size()>4096)tracked.clear();
    }
    public static Reset poll(){return pending.poll();}
    public static boolean sessionMatches(UUID player,long expectedWorld,long expectedHero,long expectedModel,long expectedGeneration){
        return player.equals(owner)&&world==expectedWorld&&hero==expectedHero&&model==expectedModel&&generation==expectedGeneration;
    }
    public static long scopedModel(UUID player,long expectedWorld,long expectedHero,long expectedGeneration){
        return player.equals(owner)&&world==expectedWorld&&hero==expectedHero&&generation==expectedGeneration?model:0;
    }
    public static void resetSession(){pending.clear();ledger.clear();tracked.clear();owner=null;world=hero=model=generation=sequence=0;eliminations=requests=applied=0;}
}
