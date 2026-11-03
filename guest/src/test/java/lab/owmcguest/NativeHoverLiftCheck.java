package lab.owmcguest;
public final class NativeHoverLiftCheck {
    static void check(boolean value){if(!value)throw new AssertionError();}
    public static void main(String[] args){
        check(Math.abs(NativeHoverLift.apply(.09,1.8,true)-.396)<1e-9);
        check(NativeHoverLift.apply(.12,1.8,true)==NativeHoverLift.apply(.06,1.8,true));
        check(NativeHoverLift.apply(.12,1.8,true)<=8.0/20);
        check(NativeHoverLift.apply(.12,1.835,true)==8.0/20);
        check(NativeHoverLift.apply(.09,1.8,false)==.09);
        check(NativeHoverLift.apply(-.5,-10,true)==-.5);
        check(NativeHoverLift.apply(0,1.8,true)==0);
        check(NativeHoverLift.apply(1,20,true)==1);
        check(NativeHoverLift.apply(.1,2.5,true)>.1&&NativeHoverLift.apply(.1,2.5,true)<=.4);
        try{NativeHoverLift.apply(Double.NaN,1,true);throw new AssertionError();}catch(IllegalArgumentException expected){}
        System.out.println("PASS: held-Space lift, native thrust required, release/descent and Jump Jet isolation");
    }
}
