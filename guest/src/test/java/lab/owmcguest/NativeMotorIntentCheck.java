package lab.owmcguest;
public final class NativeMotorIntentCheck {
    static void check(boolean b){if(!b)throw new AssertionError();}
    public static void main(String[] args){
        check(NativeMotorIntent.bastionForm(true,false,false).equals("recon"));
        check(NativeMotorIntent.bastionForm(false,true,false).equals("sentry"));
        check(NativeMotorIntent.bastionForm(false,false,true).equals("tank"));
        check(NativeMotorIntent.bastionForm(false,false,false).equals("transition"));
        check(NativeMotorIntent.bastionForm(true,false,true).equals("transition"));
        check(NativeMotorIntent.bastionForm(false,true,true).equals("transition"));
        check(NativeMotorIntent.bastionForm(true,true,true).equals("transition"));
        check(NativeMotorIntent.bastionRooted(false,true,false));
        check(NativeMotorIntent.bastionRooted(false,false,false));
        check(NativeMotorIntent.bastionRooted(true,true,false));
        check(!NativeMotorIntent.bastionRooted(true,false,false)&&!NativeMotorIntent.bastionRooted(false,false,true));
        check(NativeMotorIntent.hero(0x02e000000000006eL)&&!NativeMotorIntent.hero(0x02e0000000000029L));
        check(NativeMotorIntent.horizontal(1,new double[]{0,0,-.275})[1]==-.275);
        check(NativeMotorIntent.horizontal(1,new double[]{0,0,-.4125})[1]==-.4125);
        check(NativeMotorIntent.horizontal(1,new double[]{0,0,0})[1]==0);
        check(NativeMotorIntent.horizontal(0,new double[]{5.5,0,0})[0]==0);
        check(NativeMotorIntent.horizontal(15,new double[]{5.5,0,0})[0]==0);
        check(NativeMotorIntent.horizontal(1,new double[]{Double.NaN,0,0})[0]==0);
        check(NativeMotorIntent.horizontal(1,new double[]{31,0,0})[0]==0);
        check(NativeMotorIntent.responsive(0x02e0000000000002L)&&NativeMotorIntent.responsive(0x02e000000000006eL));
        check(!NativeMotorIntent.responsive(0x02e0000000000005L));
        check(NativeMotorIntent.responsiveStep(new double[]{0,.2475},new double[]{0,0,-5.5},5.5)[1]==.2475); // reverse now
        check(NativeMotorIntent.responsiveStep(new double[]{0,0},new double[]{8.25,0,0},5.5)[0]==0); // no release drift
        check(Math.abs(NativeMotorIntent.responsiveStep(new double[]{0,-.275},new double[]{0,0,-8.25},5.5)[1]+.4125)<1e-8);
        check(NativeMotorIntent.responsiveStep(new double[]{.275,0},new double[]{0,0,-.2},5.5)[0]==.275); // no old-direction ramp
        check(NativeMotorIntent.responsiveStep(new double[]{0,.275},new double[]{0,0,Double.NaN},5.5)[1]==0);
        System.out.println("PASS: native run/sprint/root intent, opposing/no-input drift and numeric bounds");
    }
}
