package lab.owmcguest;

import java.util.*;
import lab.owmcguest.NativeShotProtocol.*;
import lab.owmcguest.NativeShotSimulation.Hit;

/** Passive presentation lifecycle only; not a native or in-game visual oracle. */
public final class HanzoArrowPresentationCheck {
    private static void check(boolean value,String reason){if(!value)throw new AssertionError(reason);}
    private static final Vec ZERO=new Vec(0,0,0),FORWARD=new Vec(0,0,90);
    private static Shot shot(String id,long resource){
        return new Shot(1,1,1000,ZERO,FORWARD,125,5,false,100,id,false,false,
            new Effect(HanzoSonicArrowState.HERO,resource,0,9.800000190734863,0,0,0,0,0));
    }
    public static void main(String[] args){
        var scope=new HanzoArrowPresentation.Scope(UUID.randomUUID(),1,2,new Source(3,4,5,6));
        var normal=shot("normal",0x0400000000000144L);var sonic=shot("sonic",HanzoSonicArrowState.STRONG);
        var contact=new Vec(0,-.1,4);
        HanzoArrowPresentation.segment(scope,normal,ZERO,contact,null,10);
        HanzoArrowPresentation.publish(scope,List.of(normal),10,1000);
        check(HanzoArrowPresentation.view.arrows().getFirst().at().equals(contact),"exact sweep endpoint; no renderer-side ballistic prediction");
        HanzoArrowPresentation.segment(scope,normal,contact,contact,new Hit(true,0,contact),11);
        HanzoArrowPresentation.publish(scope,List.of(),11,1050);
        check(HanzoArrowPresentation.view.arrows().getFirst().stuck(),"loaded real block embeds");
        var embedded=HanzoArrowPresentation.view.arrows().getFirst();
        check(embedded.direction().lengthSquared()>0,"zero-length final contact keeps previous direction");
        HanzoArrowPresentation.segment(scope,normal,ZERO,new Vec(1,2,3),new Hit(true,0,new Vec(1,2,3)),20);
        HanzoArrowPresentation.publish(scope,List.of(),20,1100);
        check(HanzoArrowPresentation.view.arrows().getFirst().equals(embedded),"replayed retired contact cannot move or extend arrow");
        HanzoArrowPresentation.segment(scope,sonic,ZERO,contact,new Hit(true,0,contact,false),20);
        HanzoArrowPresentation.publish(scope,List.of(),20,1100);
        check(HanzoArrowPresentation.view.arrows().size()==1,"unloaded boundary cannot embed Sonic");
        HanzoArrowPresentation.publish(scope,List.of(),211,1200);
        check(HanzoArrowPresentation.view.arrows().isEmpty(),"200 tick MC retention expires exactly");
        HanzoArrowPresentation.segment(scope,sonic,ZERO,contact,null,212);
        HanzoArrowPresentation.publish(scope,List.of(),212,1250);
        check(HanzoArrowPresentation.view.arrows().isEmpty(),"expired/unloaded flight never resurrects");
        var newScope=new HanzoArrowPresentation.Scope(scope.owner(),2,2,scope.source());
        HanzoArrowPresentation.segment(newScope,sonic,ZERO,contact,null,213);
        HanzoArrowPresentation.publish(newScope,List.of(sonic),213,1300);
        check(HanzoArrowPresentation.view.arrows().getFirst().kind()==HanzoArrowPresentation.Kind.SONIC,"new world has independent scope");
        HanzoArrowPresentation.publish(newScope,List.of(),214,1350);
        check(HanzoArrowPresentation.view.arrows().isEmpty(),"simulator retirement removes flying model");
        HanzoArrowPresentation.reset();check(HanzoArrowPresentation.view==null,"session reset clears view");
        check(HanzoArrowPresentation.kind(shot("scatter",0x04000000000001a4L))==null,"separate Scatter authority cannot double-render");
        System.out.println("HanzoArrowPresentationCheck passed (presentation fixtures only)");
    }
}
