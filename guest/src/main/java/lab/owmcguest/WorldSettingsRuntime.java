package lab.owmcguest;

import java.util.List;
import java.util.UUID;
import net.minecraft.entity.effect.StatusEffectInstance;
import net.minecraft.entity.effect.StatusEffects;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.GameRules;

/** F7 世界设置（用户要求的 MC 创造模式便利功能）：时间、永远白天、永久夜视。只在服务端线程执行。 */
public final class WorldSettingsRuntime {
    public static final List<String> OPTIONS=List.of("day","night","dusk","always_day","cancel_always_day","night_vision","cancel_night_vision");
    public static volatile String status="{}";
    private static long requests;
    // 永久夜视：死亡/重生后效果会被清掉，每秒补回。
    private static final java.util.Set<UUID> nightVision=java.util.concurrent.ConcurrentHashMap.newKeySet();
    public static void tick(MinecraftServer server){
        for(var id:nightVision){var p=server.getPlayerManager().getPlayer(id);
            if(p!=null&&p.isAlive()&&!p.hasStatusEffect(StatusEffects.NIGHT_VISION))
                p.addStatusEffect(new StatusEffectInstance(StatusEffects.NIGHT_VISION,StatusEffectInstance.INFINITE,0,false,false,true));}
    }
    private WorldSettingsRuntime(){}
    private static void time(MinecraftServer server,long ticks,boolean cycle){
        NativeWorldSettings.userControlled=true;NativeWorldSettings.lockedTime=cycle?null:ticks;
        for(var world:server.getWorlds()){
            world.getGameRules().get(GameRules.DO_DAYLIGHT_CYCLE).set(cycle,server);
            long base=world.getTimeOfDay()-world.getTimeOfDay()%24000;world.setTimeOfDay(base+ticks);
        }
    }
    /** @return empty string on success, otherwise a lang key. */
    public static String apply(MinecraftServer server,UUID owner,String option){
        requests++;
        var p=server.getPlayerManager().getPlayer(owner);
        if(!server.isOnThread()||p==null||!p.isAlive())return "menu.owmcguest.world.denied";
        switch(option){
            case "day"->time(server,1000,true);
            case "night"->time(server,13000,true);
            case "dusk"->time(server,12000,true);
            case "always_day"->time(server,6000,false);
            case "cancel_always_day"->{NativeWorldSettings.userControlled=true;NativeWorldSettings.lockedTime=null;
                for(var world:server.getWorlds())world.getGameRules().get(GameRules.DO_DAYLIGHT_CYCLE).set(true,server);}
            case "night_vision"->{nightVision.add(owner);}
            case "cancel_night_vision"->{nightVision.remove(owner);p.removeStatusEffect(StatusEffects.NIGHT_VISION);}
            default->{return "menu.owmcguest.world.unknown";}
        }
        tick(server);var w=server.getOverworld();
        status="{\"requests\":"+requests+",\"last\":\""+option+"\",\"timeOfDay\":"+w.getTimeOfDay()+",\"daylightCycle\":"+w.getGameRules().getBoolean(GameRules.DO_DAYLIGHT_CYCLE)
            +",\"lockedTime\":"+NativeWorldSettings.lockedTime+",\"nightVision\":"+p.hasStatusEffect(StatusEffects.NIGHT_VISION)+"}";
        return "";
    }
}
