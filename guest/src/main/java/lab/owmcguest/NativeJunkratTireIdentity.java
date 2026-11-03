package lab.owmcguest;

import java.util.UUID;

/** 轮胎快照只能作用于同一原版英雄与完整 owner/world/source/model 身份。 */
public record NativeJunkratTireIdentity(UUID owner,long world,long source,long model) {
    public static boolean fresh(long viewWall,long observedFrame,long observedWall,long hostFrame,long now){
        return viewWall>0&&viewWall<=now&&now-viewWall<=250&&observedFrame>0&&hostFrame>=observedFrame
            &&observedWall>0&&observedWall<=now&&now-observedWall<=150;
    }
    public boolean matches(UUID player,long hero,long currentWorld,long currentSource,long currentModel){
        return owner!=null&&owner.equals(player)&&hero==0x02e0000000000065L
            &&world!=0&&source!=0&&model!=0&&world==currentWorld&&source==currentSource&&model==currentModel;
    }
}
