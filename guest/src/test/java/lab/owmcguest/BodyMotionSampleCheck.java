package lab.owmcguest;

public final class BodyMotionSampleCheck {
    static void near(double a,double b){if(Math.abs(a-b)>1e-8)throw new AssertionError(a+" != "+b);}
    public static void main(String[] args){
        var s=new BodyMotionSample();var p=new Object();
        near(s.observe(p,1,2,3,4,10,new double[]{0,64,0},true)[2],0);
        near(s.observe(p,1,2,3,4,11,new double[]{0,64,-.3},true)[2],-6);
        near(s.observe(p,1,2,3,4,11,new double[]{0,64,-.3},true)[2],-6);
        near(s.observe(p,1,2,3,4,12,new double[]{0,64,-.03},true)[2],5.4);
        // Actual wall collision and key release publish zero, not the held key's desired speed.
        near(s.observe(p,1,2,3,4,13,new double[]{0,64,-.03},true)[2],0);
        near(s.observe(p,1,2,3,4,14,new double[]{0,64.42,-.03},false)[1],8.4);
        near(s.observe(p,1,2,3,4,15,new double[]{0,64.7,-.03},true)[1],0);
        near(s.observe(p,1,2,3,4,16,new double[]{100,90,200},false)[2],0); // teleport
        near(s.observe(p,1,2,3,4,19,new double[]{100,90,201},false)[2],0); // skipped ticks
        near(s.observe(p,1,2,8,4,20,new double[]{100,90,202},false)[2],0); // new model
        near(s.observe(p,9,2,8,4,21,new double[]{100,90,203},false)[2],0); // new dimension
        near(s.observe(p,9,2,8,7,22,new double[]{100,90,204},false)[2],0); // new source
        near(s.observe(new Object(),9,2,8,7,23,new double[]{100,90,205},false)[2],0);
        near(s.observe(p,9,2,8,7,24,new double[]{Double.NaN,90,206},false)[2],0);
        near(s.observe(p,9,2,8,7,25,new double[]{100,90,206},false)[2],0);
        System.out.println("PASS: actual displacement animation speed, collision/release, jump and identity/teleport baselines");
    }
}
