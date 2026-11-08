package lab.owmcguest;
import java.util.*;
import java.nio.*;
import lab.owmcguest.NativeShotProtocol.*;
import lab.owmcguest.NativeShotSimulation.Hit;
/** Offline protocol, native-event admission and actual swept-path boundaries. */
public final class T6BehaviorCheck {
    static void check(boolean v,String why){if(!v)throw new AssertionError(why);}
    static void near(double a,double b){check(Math.abs(a-b)<1e-6,a+" != "+b);}
    public static void main(String[] args){
        var gate=new GrappleCastGate();check(!gate.observe(0,0,false,false,true,0),"attach baseline");
        check(gate.observe(100,90,true,true,true,0)&&gate.pending(),"real fire opens pending native cooldown receipt");
        check(!gate.observe(101,91,true,true,true,0),"no second MC cast while receipt pending");gate.receipt(true);
        check(!gate.observe(102,92,true,true,true,12),"real native cooldown blocks another fire");
        check(!gate.observe(200,190,true,true,true,5),"ongoing countdown");check(!gate.observe(201,191,true,true,false,0),"focus/menu input blocked");
        check(!gate.observe(201,191,true,true,true,0),"focus return cannot replay old fire");check(gate.observe(300,290,true,true,true,0),"native zero re-arms fresh cast");
        gate.reset();gate.observe(0,0,false,false,true,0);check(!gate.observe(400,390,true,true,true,Double.NaN),"invalid native timer fails closed");check(!gate.observe(400,390,true,true,true,0),"failed read cannot be replayed as a cast");
        var b=new MuzzlePresentation.Basis(new Vec(0,0,1),new Vec(1,0,0),new Vec(0,1,0));
        for(double fov:new double[]{60,90,110})for(double aspect:new double[]{1.3,16/9.,2.1}){var hand=GrappleHandOrigin.offset(b,fov,aspect);check(hand.x()<0&&hand.y()<0&&hand.z()>0,"left-hand origin for every lens/aspect");}
        var yaw=new MuzzlePresentation.Basis(new Vec(1,0,0),new Vec(0,0,-1),new Vec(0,1,0));check(GrappleHandOrigin.offset(yaw,90,16/9.).z()>0,"camera rotation preserves left side");
        var launch=GrappleCancelMomentum.release(new Vec(.9,.2,.1));near(launch.x(),.9);near(launch.z(),.1);check(launch.y()>=1.1,"stronger cancel jump");
        var capped=GrappleCancelMomentum.release(new Vec(9,9,9));near(Math.hypot(capped.x(),capped.z()),1.4);near(capped.y(),1.55);
        double y=0,v=1.55,peak=0;int flight=0;for(int t=1;t<100;t++){y+=v;peak=Math.max(peak,y);v=(v-.08)*.98;if(y<0){flight=t;break;}}check(peak>11&&peak<14&&flight<50,"gravity returns enhanced jump to ground");
        for(boolean x:new boolean[]{true,false}){var ground=new ArrayList<IceWallGeometry.Ground>();for(int i=0;i<IceWallGeometry.WIDTH;i++)for(int d=0;d<IceWallGeometry.THICKNESS;d++)ground.add(new IceWallGeometry.Ground(x?i:d,x?d:i,0));var plan=new IceWallGeometry.Plan(x,ground);
            for(var p:plan.pillars(1)){double at=x?p.x():p.z(),scale=IceWallGeometry.PILLAR_WIDTH/IceWallGeometry.SOURCE_X;check(at+plan.sourceMinX(p)*scale>=-1e-6&&at+plan.sourceMaxX(p)*scale<=IceWallGeometry.WIDTH+.000001,"original mesh clipped to same preview/collision footprint");}
            near(plan.cells(1).stream().mapToDouble(c->c.top()/16.-c.lower()).sum(),IceWallGeometry.WIDTH*IceWallGeometry.THICKNESS*4);
        }
        var request=new PlacementActionProtocol.Request(33,44,55,2000,66,77,0x400000,19,0x500000,0x600000,0x700000,90,4);var wire=ByteBuffer.wrap(PlacementActionProtocol.encode(request)).order(ByteOrder.LITTLE_ENDIAN);check(wire.remaining()==112&&wire.getInt(104)==4,"grapple fire packet uses existing112-byte channel");
        var scope=new MeiIciclePresentation.Scope(UUID.randomUUID(),1,2,new Source(3,4,5,6));var zero=new Vec(0,0,0);var hit=new Vec(0,0,4.2);
        var shot=new Shot(1,1,1000,zero,new Vec(0,0,70),75,5,false,100,"native-icicle",false,false,new Effect(MeiIciclePresentation.HERO,MeiIciclePresentation.RESOURCE,0,0,0,0,0,0,0));
        check(MeiIciclePresentation.isIcicle(shot),"exact original Mei projectile");
        MeiIciclePresentation.segment(scope,shot,zero,new Vec(0,0,3.5),null,0,.05,1100,20);MeiIciclePresentation.segment(scope,shot,new Vec(0,0,3.5),hit,new Hit(true,0,hit),.05,.06,1100,20);MeiIciclePresentation.publish(scope,List.of(),1100,20);
        var path=MeiIciclePresentation.view.flights().getFirst();near(MeiIciclePresentation.sample(path,1025,1000).at().z(),1.75);near(MeiIciclePresentation.sample(path,1080,1000).at().z(),4.2);near(MeiIciclePresentation.sample(path,1200,1000).at().z(),4.2);check(path.embedded(),"block contact remains fixed for T7 retention");
        MeiIciclePresentation.publish(new MeiIciclePresentation.Scope(scope.owner(),2,2,scope.source()),List.of(),1200,21);check(MeiIciclePresentation.view.flights().isEmpty(),"world change cannot replay model");
        System.out.println("PASS: T6 native-fire/receipt/cooldown/focus guards,left-hand lens/yaw,stronger bounded gravity peak="+peak+",flightTicks="+flight+",original wall footprint,kind4 wire,original icicle swept contact");
    }
}
