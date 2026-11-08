package lab.owmcguest;

import lab.owmcguest.NativeShotProtocol.Vec;

/** Explicit MC adaptation of a manual grapple-cancel launch, in blocks/tick.
 * Natural arrival keeps its existing release path. Gravity stays vanilla. */
public final class GrappleCancelMomentum {
    public static final double MAX_HORIZONTAL=1.4,MIN_UP=1.10,UP_BONUS=.95,MAX_UP=1.55;
    private GrappleCancelMomentum(){}
    public static Vec release(Vec actual){
        if(actual==null||!Double.isFinite(actual.x())||!Double.isFinite(actual.y())||!Double.isFinite(actual.z())||actual.lengthSquared()<.0025)return null;
        double horizontal=Math.hypot(actual.x(),actual.z()),scale=horizontal>MAX_HORIZONTAL?MAX_HORIZONTAL/horizontal:1;
        return new Vec(actual.x()*scale,Math.clamp(Math.max(0,actual.y())+UP_BONUS,MIN_UP,MAX_UP),actual.z()*scale);
    }
}
