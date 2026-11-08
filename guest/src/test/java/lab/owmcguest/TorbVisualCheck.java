package lab.owmcguest;
import java.util.*;
import lab.owmcguest.NativeShotProtocol.*;
import lab.owmcguest.NativeShotSimulation.Hit;
public final class TorbVisualCheck {
    static void check(boolean b,String reason){if(!b)throw new AssertionError(reason);}
    static void near(double a,double b){check(Math.abs(a-b)<1e-7,a+" != "+b);}
    static final Vec ZERO=new Vec(0,0,0);
    static Shot shot(String id,long resource,long wall){return new Shot(1,1,wall,ZERO,new Vec(0,0,70),55,5,false,100,id,false,false,new Effect(TorbRivetPresentation.HERO,resource,0,0,0,0,0,0,0));}
    public static void main(String[] args){
        var scope=new TorbRivetPresentation.Scope(UUID.randomUUID(),1,2,new Source(3,4,5,6));
        var shot=shot("rivet",TorbRivetPresentation.PRIMARY,1000);
        TorbRivetPresentation.segment(scope,shot,ZERO,new Vec(0,0,1.75),null,0,.025,1100);
        TorbRivetPresentation.segment(scope,shot,new Vec(0,0,1.75),new Vec(0,0,3.5),null,.025,.05,1100);
        var impact=new Vec(0,0,4.2);TorbRivetPresentation.segment(scope,shot,new Vec(0,0,3.5),impact,new Hit(true,0,impact),.05,.06,1100);
        TorbRivetPresentation.publish(scope,List.of(),1100);var f=TorbRivetPresentation.view.flights().getFirst();
        near(TorbRivetPresentation.sample(f,1112).at().z(),.63);near(TorbRivetPresentation.sample(f,1130).at().z(),1.575);
        near(TorbRivetPresentation.sample(f,1130).nativeSpeed(),70);near(TorbRivetPresentation.sample(f,1130).visualSpeed(),52.5);near(TorbRivetPresentation.sample(f,1180).at().z(),4.2);
        near(TorbRivetPresentation.sample(f,1220).at().z(),4.2);check(TorbRivetPresentation.sample(f,1261)==null,"cosmetic slow model retires after its own contact tail");
        check(TorbRivetPresentation.kind(shot("pellet",TorbRivetPresentation.SECONDARY,1000))==TorbRivetPresentation.Kind.PELLET,"alternate kind");
        var instant=new Shot(2,0,1000,ZERO,new Vec(0,0,1),10,0,true,100,"instant",false,false,new Effect(TorbRivetPresentation.HERO,TorbRivetPresentation.SECONDARY,0,0,0,0,0,0,0));
        TorbRivetPresentation.segment(scope,instant,ZERO,new Vec(0,0,5),new Hit(false,3,new Vec(0,0,5)),0,0,1100);
        TorbRivetPresentation.publish(scope,List.of(),1100);var instantFlight=TorbRivetPresentation.view.flights().stream().filter(x->x.instant()).findFirst().orElseThrow();
        var instantSample=TorbRivetPresentation.sample(instantFlight,1150);near(instantSample.at().z(),2.25);near(instantSample.nativeSpeed(),0);near(instantSample.visualSpeed(),45);
        check(TorbRivetPresentation.bodies(instantFlight,instantSample).stream().allMatch(v->v.z()>0&&v.z()<5),"instant volumes stay inside the real ray");
        check(TorbRivetPresentation.sample(instantFlight,1292)==null,"native hitscan cosmetic travel expires");
        long old=TorbRivetPresentation.segments;TorbRivetPresentation.segment(scope,shot,ZERO,impact,null,0,.06,1101);check(TorbRivetPresentation.segments==old,"terminal replay");
        TorbRivetPresentation.publish(scope,List.of(),1600);check(TorbRivetPresentation.view.flights().isEmpty(),"bounded slow presentation expiry");
        var foreign=new TorbRivetPresentation.Scope(scope.owner(),9,scope.model(),scope.source());TorbRivetPresentation.publish(foreign,List.of(),1212);
        check(TorbRivetPresentation.view.flights().isEmpty(),"world transition clears history");
        TorbRivetPresentation.reset();var unload=shot("unloaded",TorbRivetPresentation.PRIMARY,1500);
        TorbRivetPresentation.segment(scope,unload,ZERO,impact,new Hit(true,0,impact,false),0,.06,1550);TorbRivetPresentation.publish(scope,List.of(),1550);
        check(!TorbRivetPresentation.sample(TorbRivetPresentation.view.flights().getFirst(),1630).impact(),"loaded prefix may replay but never invent an unloaded impact");
        // Real solver -> real clipped hit -> timed presentation callback. The
        // presentation is neither a trace oracle nor a second damage source.
        var sim=new NativeShotSimulation();var physical=shot("physical",TorbRivetPresentation.PRIMARY,3000);
        sim.admit(new Batch(scope.source(),0,1,List.of(new Entry(1,physical,null))));var times=new ArrayList<Double>();
        sim.tick(new NativeShotSimulation.WorldAccess(){
            public Hit trace(Vec from,Vec to){return from.z()<=2.4&&to.z()>=2.4?new Hit(true,0,new Vec(0,0,2.4)):null;}
            public double damage(Hit h,double hp,long entity){throw new AssertionError("block cannot damage entity");}
            public void present(Shot s,Vec a,Vec b,Hit h,double begin,double end){if(h!=null){near(b.z(),2.4);times.add(end);}}
        },3200);
        check(sim.blockHits==1&&sim.active()==0&&times.size()==1,"one actual collision");near(times.getFirst(),2.4/70);
        var at=new Vec(10,20,30);var one=TorbTurretGeometry.muzzle(at,0,1);near(one.y(),20.8447);near(one.z(),30.4968);
        var two=TorbTurretGeometry.muzzle(at,90,2);var core=TorbTurretGeometry.muzzle(at,90,3);
        near(two.x(),9.1929);near(two.z(),30);check(two.equals(core),"Core retains the midpoint of both barrels");
        TorbRivetPresentation.retireForFixtureCleanup(4000);TorbRivetPresentation.segment(scope,physical,ZERO,impact,null,0,.06,4100);TorbRivetPresentation.publish(scope,List.of(),4100);
        check(TorbRivetPresentation.view.flights().isEmpty(),"cleanup rejects old sweeps");
        System.out.println("PASS: original-speed sweep sampling, clipped impact/no overshoot, two weapon kinds, world/unloaded/replay/cleanup retirement, real solver timings and measured turret muzzles");
    }
}
