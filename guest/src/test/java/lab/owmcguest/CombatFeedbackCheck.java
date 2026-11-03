package lab.owmcguest;

import java.util.UUID;

/** Death identity, contribution deadline and distant lock readability regressions. */
public final class CombatFeedbackCheck {
    private static void check(boolean b,String m){if(!b)throw new AssertionError(m);}
    public static void main(String[] args){
        var l=new CombatFeedbackLedger();var a=UUID.randomUUID();
        check(!l.death(a,0,10),"uncredited death");
        check(!l.damage(a,0,20,10),"zero-health-loss event");
        check(l.damage(a,4,16,20),"actual positive loss");
        check(!l.death(a,16,30),"alive removal is not a kill");
        check(l.death(a,0,1000),"delayed environmental death after actual damage");
        check(!l.death(a,0,1000),"duplicate part/death");
        check(!l.damage(a,1,0,1001),"splash after resolved lethal hit");
        var b=UUID.randomUUID();l.damage(b,2,18,0);check(!l.death(b,0,5001),"old contribution");
        var c=UUID.randomUUID();l.damage(c,2,18,10);l.clear();check(!l.death(c,0,11),"old world/hero contribution");
        for(double d:new double[]{3,8,16,32,60}){
            double unit=DeadeyeMarkerLayout.unit(d,1.6,1080);
            double px=unit*1.82*1.6*1080/(2*d);
            check(px>=34&&px<=40,"skull pixel height at "+d+": "+px);
        }
        check(DeadeyeMarkerLayout.unit(Double.NaN,1,1080)==0,"invalid distance");
        check(DeadeyeMarkerLayout.ring(0)>DeadeyeMarkerLayout.ring(1),"real charging circle shrinks");
        System.out.println("Combat feedback deadlines/death deduplication and marker readability passed");
    }
}
