package lab.owmcguest;

import java.util.*;
import lab.owmcguest.NativeShotProtocol.Vec;

/** Cosmetic geometry history only; cannot establish native visual acceptance. */
public final class HanzoArrowEffectsCheck {
    private static void check(boolean v,String message){if(!v)throw new AssertionError(message);}
    public static void main(String[] args)throws Exception{
        var scope=new HanzoArrowEffects.Scope(UUID.randomUUID(),1,2,3);var a=new Vec(0,0,0);var b=new Vec(0,-.01,2);
        long oldBounces=HanzoArrowEffects.bounces;
        for(int i=0;i<6;i++)HanzoArrowEffects.segment(scope,"child:"+i,HanzoArrowEffects.Kind.SCATTER,true,a,new Vec(i*.1,b.y(),b.z()),HanzoArrowEffects.Contact.NONE);
        HanzoArrowEffects.segment(scope,"parent",HanzoArrowEffects.Kind.SCATTER,false,a,b,HanzoArrowEffects.Contact.SPLIT);
        HanzoArrowEffects.publish();var view=HanzoArrowEffects.view;
        check(view.trails().size()==7,"one parent and six child visual identities");
        check(view.trails().stream().filter(HanzoArrowEffects.Trail::child).count()==6,"all six children keep blue-light eligibility");
        var parent=view.trails().stream().filter(t->t.id().equals("parent")).findFirst().orElseThrow();
        check(parent.points().getFirst().at().equals(a)&&parent.points().getLast().at().equals(b),"only actual loaded sweep coordinates, no prediction");
        check(parent.expires()>System.nanoTime(),"terminal sweep survives its server tick for short cosmetic afterglow");
        HanzoArrowEffects.segment(scope,"child:0",HanzoArrowEffects.Kind.SCATTER,true,b,new Vec(0,0,1),HanzoArrowEffects.Contact.BOUNCE);
        HanzoArrowEffects.publish();check(HanzoArrowEffects.bounces==oldBounces+1,"real bounce presentation counted");
        check(HanzoArrowEffects.view.flashes().stream().anyMatch(f->f.contact()==HanzoArrowEffects.Contact.BOUNCE),"contact afterglow has original contact coordinate");
        Thread.sleep(150);HanzoArrowEffects.publish();check(HanzoArrowEffects.view.trails().isEmpty()&&HanzoArrowEffects.view.flashes().isEmpty(),"cosmetic afterglow expires independently of arrow lifetime");
        var other=new HanzoArrowEffects.Scope(scope.owner(),2,2,3);
        HanzoArrowEffects.segment(other,"fresh",HanzoArrowEffects.Kind.PRIMARY,false,a,b,HanzoArrowEffects.Contact.NONE);HanzoArrowEffects.publish();
        check(HanzoArrowEffects.view.trails().size()==1&&HanzoArrowEffects.view.scope().world()==2,"new world cannot retain old trail");
        HanzoArrowEffects.reset();check(HanzoArrowEffects.view==null,"reset clears all visual permissions");
        System.out.println("HanzoArrowEffectsCheck passed (cosmetic lifecycle only)");
    }
}
