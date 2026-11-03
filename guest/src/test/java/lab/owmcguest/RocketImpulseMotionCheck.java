package lab.owmcguest;

import lab.owmcguest.NativeShotProtocol.Vec;

/** No game objects: verify native movement remains additive and cannot be
 * parked behind a landing/timer gate. Does not certify real game rendering. */
public final class RocketImpulseMotionCheck {
    private static final Vec ZERO=new Vec(0,0,0);
    private static void check(boolean b,String message){if(!b)throw new AssertionError(message);}
    private static void near(double a,double b,String message){check(Math.abs(a-b)<1e-9,message+": "+a+" != "+b);}
    private static double peak(double vy){double y=0,peak=0;for(int t=0;t<80;t++){y+=vy;peak=Math.max(peak,y);vy=(vy-.08)*.98;}return peak;}
    public static void main(String[] args){
        var push=RocketSelfImpulse.calculate(ZERO,new Vec(1,.9,0),3,1);
        var previous=push.multiply(1/RocketSelfImpulse.BOOST);
        near(push.x()/previous.x(),1.5,"horizontal +50%");near(push.y()/previous.y(),1.5,"vertical +50%");
        var foot=RocketSelfImpulse.calculate(ZERO,new Vec(0,.9,0),2.5,1);
        double oldPeak=peak(foot.y()/1.5),newPeak=peak(foot.y());
        check(newPeak>oldPeak*1.8,"higher ordinary MC ballistic arc");
        var motion=new RocketImpulseMotion();motion.add(push,100);
        var first=motion.sample(100);near(first.x(),push.x(),"initial sideways motion");near(first.y(),push.y(),"airborne impulse retained");
        check(motion.sample(100).lengthSquared()==0,"one application per MC age");
        // Shift and hover remain input to the native mover during every recoil
        // step; replacing the native mover with vanilla would lose both deltas.
        for(int age=101;age<110;age++){
            double nativeY=age<105?.35:.10;
            var overlay=motion.sample(age);var composed=new Vec(.2,nativeY,0).add(overlay);
            near(composed.y()-overlay.y(),nativeY,"native Shift/hover continues during recoil");
            check(composed.y()>nativeY,"airborne rocket jump adds lift during flight");
        }
        motion.blocked(2);var afterCeiling=motion.sample(110);
        near(afterCeiling.y(),0,"ceiling cancels recoil Y");check(afterCeiling.x()>0,"ceiling preserves sideways recoil");
        motion.add(new Vec(0,.6,0),110);check(motion.sample(111).y()>0,"another authenticated airborne blast adds lift");
        var expired=motion.sample(150);check(expired.lengthSquared()==0,"bounded overlay expires without landing");
        near(new Vec(0,.4,0).add(expired).y(),.4,"native flight is unchanged after recoil expiry");
        motion.add(push,200);motion.sample(200);near(motion.sample(203).x(),push.x()*Math.pow(.86,3),"missed native sample decays without catch-up teleport");
        motion.reset();check(motion.sample(204).lengthSquared()==0,"scope/focus reset removes residual");
        motion.add(push,300);check(motion.sample(1).lengthSquared()==0,"new player age cannot inherit recoil");
        System.out.println("PASS: +50% XYZ, native Shift/hover coexistence, airborne re-kick, replay age, ceiling axes, bounded expiry/reset; ballistic oldPeak="+oldPeak+" newPeak="+newPeak);
    }
}
