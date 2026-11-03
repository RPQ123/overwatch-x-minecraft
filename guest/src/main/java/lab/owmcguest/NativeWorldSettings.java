package lab.owmcguest;

import net.minecraft.server.MinecraftServer;
import net.minecraft.world.GameRules;

/** User-selected permanent midday and clear weather for this isolated passthrough world. */
public final class NativeWorldSettings {
    public static volatile String status="{}";
    public static void apply(MinecraftServer server){
        if(Boolean.getBoolean("owmc.dayNightCycle")) {
            for(var world:server.getWorlds()) {
                world.getGameRules().get(GameRules.DO_DAYLIGHT_CYCLE).set(true,server);
                world.getGameRules().get(GameRules.DO_WEATHER_CYCLE).set(false,server);
                world.setWeather(6000,0,false,false);
            }
            report(server);
            return;
        }
        for(var world:server.getWorlds()){
            world.getGameRules().get(GameRules.DO_DAYLIGHT_CYCLE).set(false,server);
            world.getGameRules().get(GameRules.DO_WEATHER_CYCLE).set(false,server);
            world.setTimeOfDay(6000);world.setWeather(6000,0,false,false);
        }
        report(server);
    }
    // F7 世界设置：一旦玩家选择过时间，就由玩家控制（lockedTime 非空表示“永远白天”固定时刻）。
    public static volatile boolean userControlled=false;
    public static volatile Long lockedTime=null;
    public static void tick(MinecraftServer server){
        if(server.getTicks()%20!=0)return;
        WorldSettingsRuntime.tick(server);
        if(userControlled){
            Long locked=lockedTime;
            for(var world:server.getWorlds()){
                if(locked!=null&&world.getTimeOfDay()%24000!=locked)world.setTimeOfDay(locked);
                if(world.isRaining()||world.isThundering())world.setWeather(6000,0,false,false);
            }
            report(server);return;
        }
        if(Boolean.getBoolean("owmc.dayNightCycle")) { report(server); return; }
        for(var world:server.getWorlds())if(world.getTimeOfDay()!=6000||world.isRaining()||world.isThundering()){
            world.setTimeOfDay(6000);world.setWeather(6000,0,false,false);
        }
        report(server);
    }
    private static void report(MinecraftServer server){
        var world=server.getOverworld();status="{\"timeOfDay\":"+world.getTimeOfDay()+",\"daylightCycle\":"+world.getGameRules().getBoolean(GameRules.DO_DAYLIGHT_CYCLE)+",\"weatherCycle\":"+world.getGameRules().getBoolean(GameRules.DO_WEATHER_CYCLE)+",\"raining\":"+world.isRaining()+",\"thundering\":"+world.isThundering()+"}";
    }
}
