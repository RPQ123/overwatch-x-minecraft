package lab.owmcguest;

public final class HeroSelectCalloutGateCheck {
    private static void check(boolean value){if(!value)throw new AssertionError("hero selection voice gate");}
    public static void main(String[] args){
        var g=new HeroSelectCalloutGate();
        check(!g.observe(10,0x29,false,0));check(!g.observe(10,0x29,true,10));
        check(!g.observe(10,0x29,true,509));check(g.observe(10,0x29,true,510));
        check(!g.observe(10,0x29,true,2000)); // Same hero never repeats.
        check(!g.observe(10,0x42,false,2200)); // Hover is not selection.
        check(!g.observe(10,0x29,true,3300)); // H/back without change.
        check(!g.observe(10,0x42,true,4000));check(!g.observe(10,0x6e,true,4500));
        check(!g.observe(10,0x6e,true,4999));check(g.observe(10,0x6e,true,5000));
        check(!g.observe(10,0x42,true,6000));g.cancelPending();
        check(!g.observe(10,0x42,true,8000)); // World/model reset cancels pending.
        check(!g.observe(11,0x42,true,9000));check(g.observe(11,0x42,true,10000));
        check(!g.observe(0,0,true,11000));check(!g.observe(11,0x42,true,12000));
        check(!g.observe(11,0x29,true,13000));check(!g.observe(11,0x29,false,13500));
        check(!g.observe(11,0x29,true,15000)); // Leaving first person cancels it.
        System.out.println("PASS: 500ms delay, rapid reselection cancellation, picker and session guards");
    }
}
