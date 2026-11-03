package lab.owmcguest;

/** Visual-only launch correction. Server flight/damage always retain the native eye ray. */
final class PharahRocketPresentation {
    // Measured beta launcher aperture at rest, normalized to the actual 16:9
    // native frame (not the different launcher in the modern website video).
    static final double MUZZLE_X=.068,MUZZLE_Y=-.166,MUZZLE_DEPTH=.90;
    record Offset(double right,double up,double forward) {}
    record Basis(NativeShotProtocol.Vec right,NativeShotProtocol.Vec up){}
    /** Project the launch camera's right axis onto the flight plane. World-up
     * cross products flip at the zenith and discard the native camera roll. */
    static Basis basis(NativeShotProtocol.Vec direction,NativeShotProtocol.Vec cameraRight){
        double length=Math.sqrt(direction.lengthSquared());
        if(!Double.isFinite(length)||length<1e-6)throw new IllegalArgumentException("rocket direction");
        var f=direction.multiply(1/length);double dot=f.x()*cameraRight.x()+f.y()*cameraRight.y()+f.z()*cameraRight.z();
        var r=cameraRight.subtract(f.multiply(dot));double size=Math.sqrt(r.lengthSquared());
        if(!Double.isFinite(size)||size<1e-6)throw new IllegalArgumentException("rocket camera basis");
        r=r.multiply(1/size);var up=new NativeShotProtocol.Vec(r.y()*f.z()-r.z()*f.y(),r.z()*f.x()-r.x()*f.z(),r.x()*f.y()-r.y()*f.x());
        return new Basis(r,up);
    }
    static Offset launch(double age,double verticalFov,double aspect){
        if(!Double.isFinite(age)||!Double.isFinite(verticalFov)||!Double.isFinite(aspect)||age<0||verticalFov<10||verticalFov>170||aspect<=0)throw new IllegalArgumentException("rocket projection");
        double t=Math.min(1,age/.16),weight=1-t*t*(3-2*t);
        if(weight==0)return new Offset(0,0,0);
        double halfHeight=MUZZLE_DEPTH*Math.tan(Math.toRadians(verticalFov)/2);
        return new Offset(MUZZLE_X*halfHeight*aspect*weight,MUZZLE_Y*halfHeight*weight,MUZZLE_DEPTH*weight);
    }
}
