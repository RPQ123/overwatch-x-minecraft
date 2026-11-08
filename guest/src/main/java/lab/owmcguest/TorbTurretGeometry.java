package lab.owmcguest;
import lab.owmcguest.NativeShotProtocol.Vec;
/** Measured original092e gun aperture centre, in pack metres (+Z). Levels2/3
 * use the midpoint between both barrels; LOS and tracking share this point. */
public final class TorbTurretGeometry {
    private TorbTurretGeometry(){}
    public static Vec muzzle(Vec at,float yaw,int level){
        if(level<1||level>3||!Float.isFinite(yaw))throw new IllegalArgumentException("turret geometry");
        double angle=Math.toRadians(yaw),side=0,forward=level==1?.4968:.8071,y=level==1?.8447:.8415;
        return at.add(new Vec(-Math.sin(angle)*forward+Math.cos(angle)*side,y,Math.cos(angle)*forward+Math.sin(angle)*side));
    }
}
