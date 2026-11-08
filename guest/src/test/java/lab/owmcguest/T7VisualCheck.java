package lab.owmcguest;
import java.util.*;
import lab.owmcguest.NativeShotProtocol.*;
import lab.owmcguest.NativeShotSimulation.Hit;

/** Actual victim mapping, terrain-volume and terminal-presentation behavior;
 * no renderer, native game or MC world is launched. */
public final class T7VisualCheck {
    static int assertions;
    static void check(boolean b,String why){assertions++;if(!b)throw new AssertionError(why);}
    static void near(double a,double b){check(Math.abs(a-b)<1e-6,a+" != "+b);}
    static void refused(Runnable r){boolean caught=false;try{r.run();}catch(IllegalArgumentException expected){caught=true;}check(caught,"unsafe terrain rejected");}
    static Shot shot(long sequence){return new Shot(1,sequence,1000,new Vec(0,0,0),new Vec(0,0,70),75,5,false,100,"native-icicle-"+sequence,false,false,new Effect(MeiIciclePresentation.HERO,MeiIciclePresentation.RESOURCE,0,0,0,0,0,0,0));}
    public static void main(String[] args){
        var names=Map.of("skeleton",SoulHeadVisual.Kind.SKELETON,"wither_skeleton",SoulHeadVisual.Kind.WITHER_SKELETON,"zombie",SoulHeadVisual.Kind.ZOMBIE,"creeper",SoulHeadVisual.Kind.CREEPER,"piglin",SoulHeadVisual.Kind.PIGLIN,"ender_dragon",SoulHeadVisual.Kind.DRAGON);
        names.forEach((type,kind)->check(SoulHeadVisual.kind("minecraft:"+type,false,false)==kind,"victim head "+type));
        check(SoulHeadVisual.kind("minecraft:cow",false,false)==SoulHeadVisual.Kind.ENTITY,"T8 resolves entity head before any fallback");
        check(SoulHeadVisual.kind("minecraft:player",true,false)==SoulHeadVisual.Kind.PLAYER,"player head");
        check(SoulHeadVisual.kind("owmcguest:hero_npc",false,true)==SoulHeadVisual.Kind.PLAYER,"hero NPC player head");
        check(SoulHeadVisual.scale(SoulHeadVisual.Kind.SKELETON)<.85&&SoulHeadVisual.HALO_RADIUS<.38,"smaller model and halo");
        check(SoulHeadVisual.scale(SoulHeadVisual.Kind.DRAGON)<SoulHeadVisual.scale(SoulHeadVisual.Kind.SKELETON),"large vanilla dragon head normalized");
        for(boolean alongX:new boolean[]{true,false})for(double base:new double[]{0,.5,.9375}){
            var ground=new ArrayList<IceWallGeometry.Ground>();
            for(int i=0;i<IceWallGeometry.WIDTH;i++)for(int d=0;d<IceWallGeometry.THICKNESS;d++)ground.add(new IceWallGeometry.Ground(alongX?i:d,alongX?d:i,base));
            var p=new IceWallGeometry.Plan(alongX,ground);var cells=p.cells(1);
            near(cells.stream().mapToDouble(c->c.top()/16.-c.lower()).sum(),132);
            check(cells.stream().map(c->c.x()+":"+c.y()+":"+c.z()).distinct().count()==cells.size(),"unique collision cells");
            check(cells.stream().mapToInt(c->alongX?c.x():c.z()).max().orElseThrow()+1==11,"11m width");
            check(cells.stream().mapToInt(c->alongX?c.z():c.x()).max().orElseThrow()+1==3,"3m thickness");
            check(p.pillars(1).size()==5,"five native pillars");
            for(var pillar:p.pillars(1)){
                near(pillar.height(),4);double center=alongX?pillar.x():pillar.z(),scale=IceWallGeometry.PILLAR_WIDTH/IceWallGeometry.SOURCE_X;
                check(center+p.sourceMinX(pillar)*scale>=-1e-6&&center+p.sourceMaxX(pillar)*scale<=11.000001,"mesh clipped to collision width");
            }
            for(int rise=0;rise<=8;rise++)near(p.cells(rise/8.).stream().mapToDouble(c->c.top()/16.-c.lower()).sum(),132*rise/8.);
            var invalid=new ArrayList<>(ground);var at=invalid.get(IceWallGeometry.THICKNESS+1);invalid.set(IceWallGeometry.THICKNESS+1,new IceWallGeometry.Ground(at.x(),at.z(),at.y()+2));refused(()->new IceWallGeometry.Plan(alongX,invalid));
        }
        var scope=new MeiIciclePresentation.Scope(UUID.randomUUID(),1,2,new Source(3,4,5,6));var origin=new Vec(0,0,0);var hit=new Vec(0,0,4.2);
        for(int mode=0;mode<3;mode++){
            MeiIciclePresentation.reset();var s=shot(mode+1);
            MeiIciclePresentation.segment(scope,s,origin,hit,new Hit(mode!=1,99,hit,mode!=2),0,.06,1100,100);
            MeiIciclePresentation.publish(scope,List.of(),1100,100);var f=MeiIciclePresentation.view.flights().getFirst();
            check(f.embedded()==(mode==0),"only loaded block contacts embed");
            if(mode==0){
                near(MeiIciclePresentation.sample(f,1500,1000).at().z(),4.2);near(MeiIciclePresentation.opacity(f,279),1);near(MeiIciclePresentation.opacity(f,290),.5);near(MeiIciclePresentation.opacity(f,300),0);
                MeiIciclePresentation.segment(scope,s,hit,new Vec(0,0,9),null,.06,.1,1200,101);MeiIciclePresentation.publish(scope,List.of(),1200,101);
                check(MeiIciclePresentation.view.flights().getFirst().path().size()==1,"terminal cannot move or restart");
                MeiIciclePresentation.publish(scope,List.of(),100000,299);check(MeiIciclePresentation.view.flights().size()==1,"server ticks own lifetime, wall time does not expire stuck model");
                MeiIciclePresentation.publish(scope,List.of(),100001,300);check(MeiIciclePresentation.view.flights().isEmpty(),"same 200tick retention as Hanzo");
            }else check(MeiIciclePresentation.sample(f,1500,1000)==null,"entity/unloaded contact no lingering model");
        }
        MeiIciclePresentation.reset();var s=shot(9);MeiIciclePresentation.segment(scope,s,origin,hit,new Hit(true,0,hit),0,.06,1100,100);
        MeiIciclePresentation.publish(new MeiIciclePresentation.Scope(scope.owner(),2,2,scope.source()),List.of(),1100,100);check(MeiIciclePresentation.view.flights().isEmpty(),"world change clears embedded model");
        System.out.println("PASS T7 visuals: "+assertions+" assertions; victim heads,11x3x4/132m3,five original pillars,block-only200tick retention+20tick fade,scope cleanup");
    }
}
