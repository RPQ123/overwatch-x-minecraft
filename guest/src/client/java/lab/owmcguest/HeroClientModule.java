package lab.owmcguest;

import net.minecraft.client.MinecraftClient;

/** 新英雄的客户端模块：读取原版节点（NativeSkillReader，规格用 NativeSkillReader.register 登记）并把触发交给服务端模块。
 * 可选：注册渲染（OriginalMeshPack 画原版模型）。每个英雄一个类，加入 HeroClientModules.ALL。 */
public interface HeroClientModule {
    void tick(MinecraftClient client);
    void resetSession();
    /** Same pawn camera/focus transitions may retain an authenticated ability. */
    default void revalidateSession(java.util.UUID player,long world,long hero,long model,long source){resetSession();}
    default void registerRender(){}
    String errorKey();
    String error();
}
