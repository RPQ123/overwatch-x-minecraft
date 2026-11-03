package lab.owmcguest;

/** User's MC terrain rule, deliberately separate from original native damage metadata. */
public final class NativeExplosionTerrain {
    public static final double PHARAH_PRIMARY=2.5,TANK=2.0,HELIX=1.5,BARRAGE=.6,FALLBACK=1.0;
    // Explicit user exceptions: control grenades retain their own flash/air
    // effect but never call the terrain-only explosion helper.
    public static final double FLASHBANG=0,CONCUSSIVE=0,PULSE=3.0;
    private NativeExplosionTerrain(){}
    public static double strength(NativeShotProtocol.Shot shot){
        if(shot==null)throw new IllegalArgumentException("missing admitted explosion");
        if(shot.rocket())return PHARAH_PRIMARY;
        if(shot.tankShell())return TANK;
        if(shot.helix())return HELIX;
        if(shot.barrage())return BARRAGE;
        // Older calibrated generic adapters may already carry an explicit MC
        // terrain preference. A native zero still stays zero in the journal;
        // only this separate user policy supplies the positive fallback.
        double configured=shot.effect()==null?0:shot.effect().terrain();
        return Double.isFinite(configured)&&configured>0?Math.clamp(configured,.25,4):FALLBACK;
    }
    /** Vanilla resistance still decides which eligible blocks actually break. */
    public static boolean breakable(double hardness){return Double.isFinite(hardness)&&hardness>=0;}
}
