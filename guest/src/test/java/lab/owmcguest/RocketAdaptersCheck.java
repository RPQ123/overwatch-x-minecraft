package lab.owmcguest;

import java.util.List;
import lab.owmcguest.NativeShotProtocol.*;

/** Offline fixtures: these are NOT actual game/lighting/visible fusion proof. */
public final class RocketAdaptersCheck {
    private static void check(boolean b,String why){if(!b)throw new AssertionError(why);}
    private static void near(double actual,double expected,String why){check(Math.abs(actual-expected)<1e-9,why+": "+actual);}
    private static Shot shot(long id,double speed,boolean rocket,Effect effect,List<PharahBarrageMotion.Wave> waves){
        return new Shot(id,0,1000,new Vec(0,1,0),new Vec(0,0,speed),40,5,false,100,"native:"+id,false,rocket,effect,waves);
    }
    public static void main(String[] args){
        var primary=shot(1,35,true,null,List.of());
        var e=shot(2,60,false,new Effect(0x02e0000000000008L,0x040000000000010fL,3,0,0,8,0,0,0),List.of());
        var tank=shot(3,60,false,new Effect(0x02e0000000000015L,0x04000000000003ceL,1,0,140,4,0,0,0),List.of());
        var wave=new PharahBarrageMotion.Wave(0,.2,.5,.5,1,20,true);
        var barrage=shot(4,45,false,new Effect(0x02e0000000000008L,0x0400000000000052L,1,0,30,1.5,0,0,0),List.of(wave,wave));
        var helix=shot(5,50,false,new Effect(0x02e000000000006eL,0x040000000000072cL,1,0,80,3,0,0,0),List.of());
        for(var original:List.of(primary,e,tank,barrage)){
            var adapted=RocketFlightTuning.adapt(original);
            near(adapted.velocity().z(),original.velocity().z()*.75,"MC speed scale");
            check(adapted.id()==original.id()&&adapted.identity().equals(original.identity())&&adapted.wallMs()==original.wallMs()
                &&adapted.start().equals(original.start())&&adapted.effect()==original.effect()&&adapted.waves()==original.waves(),"native identity, effect and waves preserved");
            near(adapted.nativeDamage(),original.nativeDamage(),"damage preserved");
            near(RocketFlightTuning.adapt(original).velocity().z(),adapted.velocity().z(),"replay of original cannot compound speed");
        }
        check(RocketFlightTuning.adapt(helix)==helix,"Soldier flight was not requested to change");
        check(RocketSelfImpulse.hero(primary)==0x02e0000000000008L&&RocketSelfImpulse.hero(helix)==0x02e000000000006eL
            &&RocketSelfImpulse.hero(tank)==0x02e0000000000015L,"all three self blast owners");
        check(RocketSelfImpulse.hero(e)==0&&RocketSelfImpulse.hero(barrage)==0,"E keeps accepted existing push; Q has no added self impulse");
        var source=new Source(1,2,3,4);var raw=new Batch(source,0,2,List.of(new Entry(1,primary,""),new Entry(2,null,"native rejection")));
        var tuned=RocketFlightTuning.adapt(raw);
        check(tuned.source()==raw.source()&&tuned.acknowledged()==0&&tuned.lastId()==2&&tuned.entries().get(1)==raw.entries().get(1),"proof/source/ordered rejects retained");
        var sim=new NativeShotSimulation();sim.admit(tuned);double[] end={0};int[] explosions={0};
        var world=new NativeShotSimulation.WorldAccess(){
            public NativeShotSimulation.Hit trace(Vec a,Vec b){end[0]=b.z();return null;}
            public double damage(NativeShotSimulation.Hit h,double hp,long nativeEntity){throw new AssertionError("no invented hit");}
        };
        sim.tick(world,1500);near(end[0],13.125,"actual server sweep is slower");
        near(PharahBarrageMotion.position(sim.activeProjectiles().getFirst(),.5).z(),end[0],"renderer and server share adapted position");
        sim.admit(tuned);check(sim.admissions().isEmpty()&&sim.active()==1,"replay cannot duplicate flight");
        sim.tick(new NativeShotSimulation.WorldAccess(){
            public NativeShotSimulation.Hit trace(Vec a,Vec b){return new NativeShotSimulation.Hit(true,0,a);}
            public double damage(NativeShotSimulation.Hit h,double hp,long nativeEntity){throw new AssertionError();}
            public double explode(Shot s,NativeShotSimulation.Hit h){explosions[0]++;return 12;}
        },1600);
        sim.tick(world,1700);check(explosions[0]==1&&sim.explosions==1&&sim.damageApplied==12,"one admitted real contact, one explosion");
        var blast=new Vec(0,0,0);var up=RocketSelfImpulse.calculate(blast,new Vec(0,.9,0),2.5,1);
        near(up.x(),0,"vertical aim no X");near(up.z(),0,"vertical aim no Z");check(up.y()>.42,"foot blast exceeds vanilla jump velocity");
        var side=RocketSelfImpulse.calculate(blast,new Vec(1,.9,0),2.5,1);check(side.x()>0&&side.y()>0,"away from blast including Y");
        var far=RocketSelfImpulse.calculate(blast,new Vec(0,2,0),2.5,1);check(far.y()<up.y(),"distance falloff");
        near(RocketSelfImpulse.calculate(blast,new Vec(0,.9,0),2.5,.5).y(),up.y()*.5,"cover exposure scales impulse");
        for(double exposure:new double[]{0,Double.NaN})near(RocketSelfImpulse.calculate(blast,new Vec(0,.9,0),2.5,exposure).lengthSquared(),0,"cover/invalid exposure");
        near(RocketSelfImpulse.calculate(blast,new Vec(0,2.5,0),2.5,1).lengthSquared(),0,"outside blast");
        check(RocketSelfImpulse.calculate(blast,blast,2.5,1).y()>0,"degenerate centered blast lifts up");
        double y=0,peak=0,vy=up.y();for(int tick=0;tick<60;tick++){y+=vy;peak=Math.max(peak,y);vy=(vy-.08)*.98;}
        check(peak>2,"ordinary MC gravity permits vertical rocket jump");
        System.out.println("PASS: post-validation slow flight, identity/replay, actual swept flight, three self owners, Y impulse/falloff/cover and MC jump arc; peak="+peak);
    }
}
