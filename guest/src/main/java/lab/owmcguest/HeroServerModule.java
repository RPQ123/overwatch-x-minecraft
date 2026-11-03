package lab.owmcguest;

import net.minecraft.server.MinecraftServer;

/** 新英雄的服务端模块（MC 补的物理/伤害/实体）。每个英雄一个类，加入 HeroServerModules.ALL 即被统一驱动。 */
public interface HeroServerModule {
    void tick(MinecraftServer server);
    void resetSession();
    default void clear(){resetSession();}
    /** /combat 诊断里的键名（如 "mercy"）与当前状态 JSON。 */
    String statusKey();
    String status();
}
