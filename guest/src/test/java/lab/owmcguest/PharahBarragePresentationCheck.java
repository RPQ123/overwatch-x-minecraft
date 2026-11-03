package lab.owmcguest;
import java.util.*;
import lab.owmcguest.NativeShotProtocol.*;
public final class PharahBarragePresentationCheck {
    private static void check(boolean b,String m){if(!b)throw new AssertionError(m);}
    public static void main(String[] args){
        var source=new Source(1,2,3,4);var owner=UUID.randomUUID();long now=System.currentTimeMillis();
        var effect=new Effect(0x02e0000000000008L,0x0400000000000052L,1,0,30,1.5,0,0,0,.5,.3);
        var wave=new PharahBarrageMotion.Wave(0,.2,.5,.5,1,20,true);
        var shot=new Shot(1,0,now,new Vec(0,1,0),new Vec(0,0,45),10,5,false,100,"native:1",false,false,effect,List.of(wave,wave));
        var sim=new NativeShotSimulation();var batch=new Batch(source,0,1,List.of(new Entry(1,shot,"")));
        sim.admit(batch);for(var s:sim.admissions())PharahBarragePresentation.launch(s);
        PharahBarragePresentation.publish(8,owner,source,10,now);
        check(PharahBarragePresentation.view.launches().size()==1,"actual admission retained even for immediate hit");
        sim.admit(batch);for(var s:sim.admissions())PharahBarragePresentation.launch(s);
        PharahBarragePresentation.publish(8,owner,source,10,now);
        check(PharahBarragePresentation.view.launches().size()==1,"replay cannot create firing cue");
        PharahBarragePresentation.impact(shot,new NativeShotSimulation.Hit(true,0,new Vec(1,2,3),false));
        PharahBarragePresentation.publish(8,owner,source,10,now);
        check(PharahBarragePresentation.view.impacts().isEmpty(),"unloaded retirement has no explosion cue");
        PharahBarragePresentation.impact(shot,new NativeShotSimulation.Hit(true,0,new Vec(1,2,3)));
        now=System.currentTimeMillis();PharahBarragePresentation.publish(8,owner,source,10,now);
        check(PharahBarragePresentation.view.impacts().size()==1,"real collision cues one blast");
        PharahBarragePresentation.publish(8,owner,source,10,now+1000);
        check(PharahBarragePresentation.view.impacts().isEmpty()&&PharahBarragePresentation.view.launches().isEmpty(),"expired effects and firing cannot persist");
        for(int i=0;i<256;i++){PharahBarragePresentation.launch(shot);PharahBarragePresentation.impact(shot,new NativeShotSimulation.Hit(true,0,new Vec(1,2,3)));}
        PharahBarragePresentation.publish(8,owner,source,10,System.currentTimeMillis());
        check(PharahBarragePresentation.view.impacts().size()==96&&PharahBarragePresentation.view.launches().size()==128,"bounded queues");
        PharahBarragePresentation.reset();check(PharahBarragePresentation.view==null,"world/model/source reset removes old presentation");
        System.out.println("PASS: admitted-only firing, replay, unloaded impact, expiry, bounded queues and session reset");
    }
}
