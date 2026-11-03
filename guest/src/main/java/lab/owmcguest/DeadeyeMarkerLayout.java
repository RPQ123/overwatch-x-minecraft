package lab.owmcguest;

/** Readable at distance while the real lock fraction still owns readiness. */
public final class DeadeyeMarkerLayout {
    public static double unit(double distance,double projectionY,int height){
        if(!Double.isFinite(distance)||!Double.isFinite(projectionY)||distance<=0||projectionY<=0||height<=0)return 0;
        // One unit = half of a 38px skull at1080p; scale with viewport height.
        return Math.max(.075,Math.min(4,distance*38/(1080*projectionY)));
    }
    public static double ring(double fraction){return 1.34+1.8*(1-Math.clamp(fraction,0,1));}
}
