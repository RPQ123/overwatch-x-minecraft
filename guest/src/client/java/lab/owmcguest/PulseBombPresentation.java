package lab.owmcguest;

/** Pure visual math; runtime contact/damage coordinates never pass through here. */
final class PulseBombPresentation {
    private PulseBombPresentation(){}
    static double contactOffset(double halfThickness,boolean attached,boolean blockAttached){
        if(!Double.isFinite(halfThickness)||halfThickness<0||halfThickness>.2)throw new IllegalArgumentException("Pulse thickness");
        if(!attached)return 0;
        // Runtime block contact already has .04m padding; entity contact does not.
        return Math.max(0,halfThickness+.003-(blockAttached?.04:0));
    }
    static double spinDegrees(long now,long launchedWall,boolean attached){
        if(attached||now<launchedWall)return 0;
        // Preserve the earlier1rev/s cosmetic spin, with this actual launch's phase.
        return ((now-launchedWall)%1000)*.36;
    }
}
