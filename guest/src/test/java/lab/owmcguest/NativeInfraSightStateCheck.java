package lab.owmcguest;
import java.util.UUID;
public final class NativeInfraSightStateCheck {
    private static void check(boolean ok,String why){if(!ok)throw new AssertionError(why);}
    public static void main(String[] args){
        var a=new NativeInfraSightState.Scope(UUID.randomUUID(),11,22,33);var b=new NativeInfraSightState.Scope(a.owner(),12,22,33);var s=new NativeInfraSightState();
        check(!s.observe(a,1,true,1000,1000),"already active is baseline");check(!s.observe(a,1,true,1050,1050),"cannot join old Q");
        s.observe(a,1,false,1100,1100);check(s.observe(a,2,true,1150,1150),"new original Begin");
        check(!s.active(b,1200)&&!s.active(a,1301),"foreign world and stale view refused");
        for(int t=1200;t<16150;t+=50)s.observe(a,2,true,t,t);
        check(!s.observe(a,2,true,16150,16150),"repeated active snapshots cannot extend 15s");
        check(!s.observe(b,2,true,16200,16200),"world handoff active baseline");
        s.observe(b,2,false,16250,16250);check(s.observe(b,3,true,16300,16300),"fresh Begin in new world");
        check(!s.observe(b,3,false,16350,16350)&&!s.active(b,16350),"native End clears immediately");
        check(!s.observe(b,4,true,16000,16500),"stale observation cannot grant");
        check(!s.observe(b,4,true,17000,16500),"future observation refused");
        System.out.println("Infra-Sight original Begin/End, baseline, repeat, scope and freshness fixtures passed");
    }
}
