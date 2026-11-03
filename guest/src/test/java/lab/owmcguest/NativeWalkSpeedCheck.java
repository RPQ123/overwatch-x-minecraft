package lab.owmcguest;
public final class NativeWalkSpeedCheck {
    static void near(double a,double b){if(Math.abs(a-b)>1e-7)throw new AssertionError(a+" != "+b);}
    public static void main(String[] args){
        double[] speeds={6,5.4,6,3,3,3};
        near(NativeWalkSpeed.local(1,speeds)[1]*20,6);near(NativeWalkSpeed.local(2,speeds)[1]*20,-5.4);
        near(NativeWalkSpeed.local(8,speeds)[0]*20,6);near(NativeWalkSpeed.local(4,speeds)[0]*20,-6);
        var diagonal=NativeWalkSpeed.local(9,speeds);near(Math.hypot(diagonal[0],diagonal[1])*20,6);
        var crouch=NativeWalkSpeed.local(41,speeds);near(Math.hypot(crouch[0],crouch[1])*20,3);
        near(NativeWalkSpeed.local(3,speeds)[1],0);near(NativeWalkSpeed.local(12,speeds)[0],0);
        near(NativeWalkSpeed.local(1,null)[1],0);
        System.out.println("PASS: directional and crouched native speeds, no diagonal boost, opposed input cancellation, missing profile stop");
    }
}
