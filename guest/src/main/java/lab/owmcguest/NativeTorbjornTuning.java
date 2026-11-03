package lab.owmcguest;

import java.util.UUID;

/** MC接触适配：两次有效锤击由1升到2；Core临时使2级炮台变3级，结束恢复2级。投掷者不能拾取自己的护甲包。 */
public final class NativeTorbjornTuning {
    public static final int MAX_LEVEL=2,CORE_LEVEL=3,UPGRADE_REQUIRED=100,UPGRADE_PER_HIT=50;
    public record Upgrade(int level,int progress,boolean upgraded){}
    private NativeTorbjornTuning(){}
    public static Upgrade hammer(int level,int progress){
        if(level<1||level>MAX_LEVEL||progress<0||progress>=UPGRADE_REQUIRED)throw new IllegalArgumentException("turret upgrade state");
        if(level==MAX_LEVEL)return new Upgrade(level,0,false);
        int next=progress+UPGRADE_PER_HIT;
        return next>=UPGRADE_REQUIRED?new Upgrade(level+1,0,true):new Upgrade(level,next,false);
    }
    public static int effectiveLevel(int base,boolean core){
        if(base<1||base>MAX_LEVEL)throw new IllegalArgumentException("turret level");
        return core&&base==MAX_LEVEL?CORE_LEVEL:base;
    }
    public static double health(int base,boolean core){return switch(effectiveLevel(base,core)){case 1->150;case 2->300;default->800;};}
    public static boolean recipient(UUID owner,UUID other,boolean alive,boolean spectator){
        return owner!=null&&other!=null&&!owner.equals(other)&&alive&&!spectator;
    }
}
