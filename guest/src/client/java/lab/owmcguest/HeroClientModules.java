package lab.owmcguest;

import java.util.List;
import net.minecraft.client.MinecraftClient;

/** 新英雄客户端模块注册表：由 Claude 统一维护，Codex 线程只新增各自英雄的模块类。 */
public final class HeroClientModules {
    public static final List<HeroClientModule> ALL=List.of(
        NativeRocketSelfImpulseClient.INSTANCE,
        MercyClient.INSTANCE,ZenyattaClient.INSTANCE,ReinhardtClient.INSTANCE,ZaryaClient.INSTANCE,
        RoadhogClient.INSTANCE,DVaClient.INSTANCE,SymmetraClient.INSTANCE,LucioClient.INSTANCE
    );
    static void tick(MinecraftClient c){for(var m:ALL)try{m.tick(c);}catch(RuntimeException e){System.err.println("OWMC module "+m.errorKey()+" tick: "+e);}}
    static void resetSession(){for(var m:ALL)m.resetSession();}
    static void registerRender(){for(var m:ALL)m.registerRender();}
    static void errors(com.google.gson.JsonObject out){for(var m:ALL)out.addProperty(m.errorKey(),m.error());}
}
