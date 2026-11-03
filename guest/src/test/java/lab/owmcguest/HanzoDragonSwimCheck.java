package lab.owmcguest;

/** Standalone numeric fixture; does not load Minecraft or certify visible animation. */
public final class HanzoDragonSwimCheck {
    private static void near(double a,double b,double epsilon){if(Math.abs(a-b)>epsilon)throw new AssertionError(a+" != "+b);}
    public static void main(String[] args){
        double e=1e-5,max=0;
        for(double phase:new double[]{0,.7,3.2})for(double z=-39;z<-.1;z+=.25){
            var a=HanzoDragonSwim.sample(z,phase);var left=HanzoDragonSwim.sample(z-e,phase);var right=HanzoDragonSwim.sample(z+e,phase);
            near(a.slopeX(),(right.x()-left.x())/(2*e),1e-7);near(a.slopeY(),(right.y()-left.y())/(2*e),1e-7);
            var opposite=HanzoDragonSwim.sample(z,phase+Math.PI);near(a.x(),-opposite.x(),1e-12);near(a.y(),-opposite.y(),1e-12);
            if(Math.abs(a.x())>HanzoDragonSwim.AMPLITUDE||Math.abs(a.y())>.35*HanzoDragonSwim.AMPLITUDE)throw new AssertionError("unbounded swim");
            max=Math.max(max,Math.abs(a.x()));
        }
        if(max<.35)throw new AssertionError("no body wave");
        var a=HanzoDragonSwim.sample(-17,0);var b=HanzoDragonSwim.sample(-17,10*HanzoDragonSwim.PHASE_PER_TICK);
        if(Math.abs(a.x()-b.x())<.02)throw new AssertionError("static body");
        System.out.println("HanzoDragonSwimCheck: passed (MC approximation; no native clip/pixels)");
    }
}
