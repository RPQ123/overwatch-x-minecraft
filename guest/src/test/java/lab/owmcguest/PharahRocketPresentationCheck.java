package lab.owmcguest;
public final class PharahRocketPresentationCheck {
    static void check(boolean v){if(!v)throw new AssertionError();}
    public static void main(String[] args){
        for(double fov:new double[]{60,75,90,110})for(double aspect:new double[]{16.0/9,4.0/3}){
            var m=PharahRocketPresentation.launch(0,fov,aspect);
            double halfHeight=m.forward()*Math.tan(Math.toRadians(fov)/2);
            check(Math.abs(m.right()/halfHeight/aspect-PharahRocketPresentation.MUZZLE_X)<1e-12);
            check(Math.abs(m.up()/halfHeight-PharahRocketPresentation.MUZZLE_Y)<1e-12);
            // First visible point must be in front of the lens. Previously the
            // lateral offset was applied at eye depth, projecting off-screen.
            for(double age=0;age<.3;age+=.001){var p=PharahRocketPresentation.launch(age,fov,aspect);check(35*age+p.forward()>=.9);}
            check(PharahRocketPresentation.launch(.16,fov,aspect).equals(new PharahRocketPresentation.Offset(0,0,0)));
            check(PharahRocketPresentation.launch(.2,fov,aspect).equals(new PharahRocketPresentation.Offset(0,0,0)));
        }
        try{PharahRocketPresentation.launch(Double.NaN,90,1);throw new AssertionError();}catch(IllegalArgumentException expected){}
        // Straight up/down and crossing the zenith retain the same camera-right
        // direction instead of flipping the muzzle offset or collapsing to zero.
        for(double pitch:new double[]{-90,-89.99,-45,0,45,89.99,90,90.01}){
            double a=Math.toRadians(pitch);var f=new NativeShotProtocol.Vec(0,Math.sin(a),-Math.cos(a));
            var basis=PharahRocketPresentation.basis(f,new NativeShotProtocol.Vec(1,0,0));
            check(basis.right().x()>.999999);check(Math.abs(basis.up().lengthSquared()-1)<1e-12);
            check(Math.abs(f.x()*basis.up().x()+f.y()*basis.up().y()+f.z()*basis.up().z())<1e-12);
        }
        System.out.println("PASS: muzzle projection, near-lens continuity and unchanged distant eye ray");
    }
}
