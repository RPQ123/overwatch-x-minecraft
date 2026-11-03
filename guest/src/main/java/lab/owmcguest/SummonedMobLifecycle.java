package lab.owmcguest;

import com.google.gson.JsonObject;
import java.util.*;
import net.fabricmc.fabric.api.event.lifecycle.v1.*;
import net.minecraft.entity.Entity;
import net.minecraft.entity.LivingEntity;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.world.ServerWorld;

/** F9-only labels and persisted expiry. discard() never invokes death/loot/XP. */
public final class SummonedMobLifecycle {
    private static boolean registered;
    private static final Map<MinecraftServer,Map<UUID,Entity>> loaded=new IdentityHashMap<>();
    private static long named,expired,reloaded;
    public static volatile String status="{}";
    private SummonedMobLifecycle(){}
    public static synchronized void register(){
        if(registered)return;registered=true;
        ServerEntityEvents.ENTITY_LOAD.register(SummonedMobLifecycle::onLoad);
        ServerEntityEvents.ENTITY_UNLOAD.register((entity,world)->{var rows=loaded.get(world.getServer());if(rows!=null)rows.remove(entity.getUuid(),entity);publish();});
        ServerTickEvents.END_SERVER_TICK.register(SummonedMobLifecycle::tick);
        ServerLifecycleEvents.SERVER_STOPPED.register(server->{loaded.remove(server);publish();});
    }
    public static void mark(Entity entity,ServerWorld world){
        if(!(entity instanceof LivingEntity)||!world.getServer().isOnThread())throw new IllegalStateException("F9 server entity required");
        var tags=entity.getCommandTags();
        if(!tags.contains(SummonedMobExpiry.OWNED)){
            long until=SummonedMobExpiry.deadline(world.getServer().getOverworld().getTime());
            if(!entity.addCommandTag(SummonedMobExpiry.PREFIX+until)||!entity.addCommandTag(SummonedMobExpiry.OWNED))throw new IllegalStateException("F9 expiry tags unavailable");
            named++;
        }
        if(SummonedMobExpiry.expired(world.getServer().getOverworld().getTime(),SummonedMobExpiry.read(entity.getCommandTags())))throw new IllegalStateException("F9 expiry already elapsed");
        if(!entity.hasCustomName())entity.setCustomName(entity.getType().getName().copy());entity.setCustomNameVisible(true); // 保留如“老吴”这类自定义名
        entity.addCommandTag("owmc-player-random-mob");
    }
    private static void onLoad(Entity entity,ServerWorld world){
        if(!(entity instanceof LivingEntity)||!entity.getCommandTags().contains(SummonedMobExpiry.OWNED))return;
        long until=SummonedMobExpiry.read(entity.getCommandTags());
        if(SummonedMobExpiry.expired(world.getServer().getOverworld().getTime(),until)){SummonSpawnScope.discardSilently(entity,world);expired++;publish();return;}
        if(!entity.hasCustomName())entity.setCustomName(entity.getType().getName().copy());entity.setCustomNameVisible(true); // 保留如“老吴”这类自定义名
        loaded.computeIfAbsent(world.getServer(),s->new HashMap<>()).put(entity.getUuid(),entity);reloaded++;publish();
    }
    private static void tick(MinecraftServer server){
        var rows=loaded.get(server);if(rows==null)return;long now=server.getOverworld().getTime();
        var iterator=rows.entrySet().iterator();var remove=new ArrayList<Entity>();
        while(iterator.hasNext()){
            var entity=iterator.next().getValue();
            if(entity.isRemoved()){iterator.remove();continue;}
            if(SummonedMobExpiry.expired(now,SummonedMobExpiry.read(entity.getCommandTags()))){iterator.remove();remove.add(entity);}
        }
        // Entity unload callbacks can mutate rows; never discard inside its iterator.
        for(var entity:remove){SummonSpawnScope.discardSilently(entity,(ServerWorld)entity.getWorld());expired++;}
        if(!remove.isEmpty()||now%20==0)publish();
    }
    private static void publish(){status=diagnostics().toString();}
    public static JsonObject diagnostics(){
        var out=new JsonObject();out.addProperty("named",named);out.addProperty("expired",expired);out.addProperty("loadEvents",reloaded);
        out.addProperty("loaded",loaded.values().stream().mapToInt(Map::size).sum());out.addProperty("lifetimeTicks",SummonedMobExpiry.LIFETIME_TICKS);return out;
    }
}
