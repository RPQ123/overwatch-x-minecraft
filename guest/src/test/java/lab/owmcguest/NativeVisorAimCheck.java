package lab.owmcguest;
import lab.owmcguest.NativeShotProtocol.*;

public final class NativeVisorAimCheck {
    static void require(boolean ok){if(!ok)throw new AssertionError();}
    static Shot shot(long hero,long resource,long model,long tick,boolean ray){return new Shot(1,0,1000,new Vec(0,1.6,0),new Vec(0,0,-1),17,1,ray,100,"factory:"+hero+":"+model+":123:"+tick+":0:0",false,false,new Effect(hero,resource,0,0,0,0,0,0,0));}
    public static void main(String[] args){
        long hero=NativeVisorAim.HERO,rifle=0x04000000000003d4L;var s=new NativeVisorAim.Scope(7,19,23,1000,500,true,45,45,990);
        var shot=shot(hero,rifle,19,501,true);
        require(NativeVisorAim.eligible(s,shot,23,7,1000));
        require(!NativeVisorAim.eligible(s,shot,24,7,1000)); // dimension/server
        require(!NativeVisorAim.eligible(s,shot,23,8,1000)); // source restart
        require(!NativeVisorAim.eligible(s,shot,23,7,1151)); // stale/paused worker
        require(!NativeVisorAim.eligible(s,shot,23,7,949)); // future state
        require(!NativeVisorAim.eligible(s,shot(hero,rifle,20,501,true),23,7,1000));
        // Real factory counter1772 and logger milliseconds71120 are distinct.
        // A lower factory counter must still lock after confirmed native Begin.
        var unrelatedClock=new NativeVisorAim.Scope(7,19,23,1000,71120,true,45,45,990);
        require(NativeVisorAim.eligible(unrelatedClock,shot(hero,rifle,19,1772,true),23,7,1000));
        var before=new Shot(1,0,989,new Vec(0,1.6,0),new Vec(0,0,-1),17,0,true,100,"factory:"+hero+":19:123:1771:0:0",false,false,new Effect(hero,rifle,0,0,0,0,0,0,0));
        require(!NativeVisorAim.eligible(unrelatedClock,before,23,7,1000)); // delayed pre-Begin bullet
        require(!NativeVisorAim.eligible(s,shot(hero,0x040000000000072cL,19,501,false),23,7,1000)); // no homing Helix
        require(!NativeVisorAim.eligible(s,shot(0x02e0000000000042L,rifle,19,501,true),23,7,1000));
        require(!NativeVisorAim.eligible(new NativeVisorAim.Scope(7,19,23,1000,500,false,45,45,990),shot,23,7,1000));
        require(!NativeVisorAim.eligible(new NativeVisorAim.Scope(7,19,23,1000,500,true,45,45,1001),shot,23,7,1000));
        var window=new NativeVisorAim.Window();
        require(window.observe(7,19,23,71120,false,980)==0); // windup has no target Begin
        require(window.observe(7,19,23,71120,true,990)==990);
        require(window.observe(7,19,23,71120,true,1000)==990);
        require(window.observe(7,19,24,71120,true,1010)==1010); // dimension
        require(window.observe(7,20,24,71120,true,1020)==1020); // hero/model replacement
        require(window.observe(8,20,24,71120,true,1030)==1030); // source restart
        require(window.observe(8,20,24,71121,true,1040)==1040); // next activation
        require(window.observe(8,20,24,71121,false,1050)==0); // native End
        require(window.observe(8,20,24,71122,true,1060)==1060);
        window.reset();require(window.observe(8,20,24,71122,true,1070)==1070);
        var f=new Vec(0,0,-1);
        require(NativeVisorAim.score(f,new Vec(0,0,-6),45,45)==1);
        require(NativeVisorAim.score(f,new Vec(1.5,0,-6),45,45)>0);
        require(NativeVisorAim.score(f,new Vec(4,0,-6),45,45)<0);
        require(NativeVisorAim.score(f,new Vec(0,0,6),45,45)<0);
        require(NativeVisorAim.score(f,new Vec(0,0,-45.01),45,45)<0);
        require(NativeVisorAim.score(f,new Vec(0,0,0),45,45)<0);
        require(NativeVisorAim.score(f,new Vec(Double.NaN,0,-6),45,45)<0);
        System.out.println("PASS: native Visor Begin/End, independent native clocks, pre-Begin wall boundary, rifle-only identity, lifecycle/freshness and range/cone guards");
    }
}
