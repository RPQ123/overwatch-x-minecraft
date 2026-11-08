package lab.owmcguest;

import java.util.List;
import net.minecraft.server.MinecraftServer;

/** 新英雄服务端模块注册表：由 Claude 统一维护，Codex 线程只新增各自英雄的模块类。 */
public final class HeroServerModules {
    public static final List<HeroServerModule> ALL=List.of(
        NativeRocketSelfImpulse.INSTANCE,WinstonServer.INSTANCE,
        MercyServer.INSTANCE,ZenyattaServer.INSTANCE,ReinhardtServer.INSTANCE,ZaryaServer.INSTANCE,
        RoadhogServer.INSTANCE,DVaServer.INSTANCE,SymmetraServer.INSTANCE,LucioServer.INSTANCE
    );
    public static void tick(MinecraftServer s){for(var m:ALL)try{m.tick(s);}catch(RuntimeException e){System.err.println("OWMC module "+m.statusKey()+" tick: "+e);}}
    public static void resetSession(){for(var m:ALL)m.resetSession();}
    public static void revalidateSession(java.util.UUID p,long w,long h,long m,long s){for(var module:ALL)module.revalidateSession(p,w,h,m,s);}
    public static void clear(){for(var m:ALL)m.clear();}
    public static void status(com.google.gson.JsonObject out){for(var m:ALL)out.add(m.statusKey(),com.google.gson.JsonParser.parseString(m.status()));}
}
