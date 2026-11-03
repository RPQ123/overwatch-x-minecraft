package lab.owmcguest;

/** Three visual strands around ONE admitted beta projectile, never three hits. */
final class HelixPresentation {
    static final double RADIUS=.12;
    static NativeShotProtocol.Vec strand(double age,int index){
        if(!Double.isFinite(age)||age<0||index<0||index>2)throw new IllegalArgumentException("helix frame");
        double angle=age*26+index*Math.PI*2/3,radius=RADIUS*Math.min(1,age/.04);
        return new NativeShotProtocol.Vec(Math.cos(angle)*radius,Math.sin(angle)*radius,0);
    }
    // Approximate beta rest muzzle measured from the composed 2560x1440 frame.
    // Visual adapter only; animated bone attachment is not available here.
    static PharahRocketPresentation.Offset launch(double age,double fov,double aspect){
        double t=Math.clamp(age/.12,0,1),weight=1-t*t*(3-2*t),depth=.9;
        double half=depth*Math.tan(Math.toRadians(fov)/2);
        return new PharahRocketPresentation.Offset(.13*half*aspect*weight,-.15*half*weight,depth*weight);
    }
}
