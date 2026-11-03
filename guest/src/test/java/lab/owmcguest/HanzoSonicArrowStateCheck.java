package lab.owmcguest;

import java.util.UUID;
import lab.owmcguest.HanzoSonicArrowState.*;

/** Pure fixtures only: no claim of native event or actual MC pixels. */
public final class HanzoSonicArrowStateCheck {
    private static void check(boolean value,String why){if(!value)throw new AssertionError(why);}
    public static void main(String[] args){
        var owner=UUID.randomUUID();var a=new Scope(owner,11,22,33);var b=new Scope(owner,12,22,33);
        var s=new HanzoSonicArrowState();s.configure(a);
        check(!s.impact(a,"key-only",new Point(0,0,0),true,0),"no input-only/impact-only admission");
        check(!s.admit(a,"primary",0x0400000000000144L,1000,5,1000,0),"ordinary arrow not sonar");
        check(!s.admit(a,"stale",HanzoSonicArrowState.STRONG,400,5,1000,0),"stale original refused");
        check(s.admit(a,"real",HanzoSonicArrowState.STRONG,1000,5,1000,1),"accepted original strong variant");
        check(!s.admit(a,"real",HanzoSonicArrowState.STRONG,1000,5,1000,1),"no duplicate factory");
        check(!s.reveals(new Point(0,0,0)),"no reveal while arrow flying");
        check(s.impact(a,"real",new Point(0,0,0),true,20),"real contact starts duration");
        check(s.reveals(new Point(10,0,0))&&!s.reveals(new Point(10.001,0,0)),"10m boundary");
        check(s.reveals(new Point(0,9.99,0))&&!s.reveals(new Point(8,8,0)),"sphere and vertical boundary");
        check(!s.impact(a,"real",new Point(30,0,0),true,21),"no duplicate impact/reanchor");
        s.advance(a,219);check(s.reveals(new Point(0,0,0)),"last active tick");
        s.advance(a,220);check(!s.reveals(new Point(0,0,0)),"200ticks since impact expires");
        check(!s.admit(a,"real",HanzoSonicArrowState.STRONG,2000,5,2000,220),"expired event still cannot replay");
        check(s.admit(a,"weak",HanzoSonicArrowState.WEAK,2000,5,2000,221),"weak special variant allowed");
        check(!s.impact(a,"weak",new Point(1,0,0),false,222),"unloaded collision no sonar");
        check(!s.impact(a,"weak",new Point(1,0,0),true,223),"unloaded contact consumed once");
        check(s.admit(a,"late",HanzoSonicArrowState.STRONG,3000,5,3000,224),"second real launch");
        check(!s.impact(a,"late",new Point(0,0,0),true,325),"expired flight cannot start sonar");
        check(s.admit(a,"world",HanzoSonicArrowState.STRONG,4000,5,4000,326),"before portal launch");
        s.configure(b);check(!s.impact(b,"world",new Point(0,0,0),true,327),"old world collision rejected");
        check(!s.admit(a,"old",HanzoSonicArrowState.STRONG,4000,5,4000,327),"foreign owner scope rejected");
        check(s.admit(b,"new",HanzoSonicArrowState.WEAK,4000,5,4000,328),"new world fresh launch");
        check(s.impact(b,"new",new Point(0,0,0),true,329),"new world contact");
        s.advance(b,328);check(s.pulses().isEmpty()&&s.scope()==null,"backwards tick fails closed");
        s.configure(a);check(s.admit(a,"reset",HanzoSonicArrowState.STRONG,5000,5,5000,1),"fresh restart scope");
        check(!s.impact(a,"reset",new Point(Double.NaN,0,0),true,2),"nonfinite impact refuses");
        s.clear();check(s.pulses().isEmpty()&&s.flights()==0,"server stop clears all permissions");
        System.out.println("HanzoSonicArrowStateCheck passed (lifecycle fixtures only)");
    }
}
