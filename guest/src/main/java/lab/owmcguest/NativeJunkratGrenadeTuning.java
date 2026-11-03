package lab.owmcguest;

/** 2026-10-27 用户手感数值，均为 MC 适配；只用于原版准入的左键榴弹。 */
public final class NativeJunkratGrenadeTuning {
    public static final int FUSE_TICKS=30;
    public static final float RENDER_SCALE=2f;
    public static final double DAMAGE_MULTIPLIER=2;
    private NativeJunkratGrenadeTuning(){}
    /** 只有向上的碰撞面启动引信；墙/顶面和后续反弹均不能重置首次触地时间。 */
    public static int groundContact(int firstGroundAge,int age,double normalY){
        return firstGroundAge<0&&normalY>.5?age:firstGroundAge;
    }
    public static boolean expired(int age,int firstGroundAge){return firstGroundAge>=0&&age-firstGroundAge>=FUSE_TICKS;}
    public static double damage(double nativeDamage){return nativeDamage*DAMAGE_MULTIPLIER;}
    public static double terrainStrength(double helix){
        if(!Double.isFinite(helix)||helix<=0||helix>4)throw new IllegalArgumentException("helix terrain strength");
        return Math.min(4,(helix+.25)*2);
    }
}
