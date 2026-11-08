package lab.owmcguest;

import lab.owmcguest.NativeShotProtocol.Vec;

/** Shared cosmetic pickup movement. Server collision/eligibility still decides
 * whether a step or a pickup is allowed; this never awards a resource itself. */
public final class PickupKinematics {
    public static final double RADIUS=3,CONTACT=.35,MAX_STEP=.32,ACCELERATION=.035;
    public record Step(Vec at,double speed,boolean attracting){}
    public record Pose(double yaw,double lift){}
    private PickupKinematics(){}
    private static boolean finite(Vec p){return p!=null&&Double.isFinite(p.x())&&Double.isFinite(p.y())&&Double.isFinite(p.z());}
    public static Step toward(Vec from,Vec target,double previousSpeed,boolean clear){
        if(!finite(from)||!finite(target)||!Double.isFinite(previousSpeed)||previousSpeed<0)throw new IllegalArgumentException("pickup motion");
        var delta=target.subtract(from);double distance=Math.sqrt(delta.lengthSquared());
        if(!clear||distance>RADIUS||distance<1e-8)return new Step(from,0,false);
        double speed=Math.min(MAX_STEP,Math.max(.06,previousSpeed)+ACCELERATION),move=Math.min(speed,distance);
        return new Step(from.add(delta.multiply(move/distance)),speed,true);
    }
    public static Pose pose(boolean landed,boolean attracting,int age,long wall,long now){
        if(!landed||attracting)return new Pose(0,0);
        double ticks=age+Math.clamp((now-wall)/50.,0,1);
        return new Pose(ticks*1.8,.025*(1+Math.sin(ticks*.09)));
    }
}
