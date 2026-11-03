package lab.owmcguest;

import java.util.*;
import lab.owmcguest.NativeShotProtocol.*;
import lab.owmcguest.NativeShotSimulation.Hit;

public final class HanzoFixtureCleanupCheck {
    private static Shot shot(String id,long wall){return new Shot(1,1,wall,new Vec(0,0,0),new Vec(0,0,90),125,5,false,100,id,false,false,
        new Effect(HanzoSonicArrowState.HERO,0x0400000000000144L,0,9.8,0,0,0,0,0));}
    private static void check(boolean value,String message){if(!value)throw new AssertionError(message);}
    public static void main(String[] args){
        var scope=new HanzoArrowPresentation.Scope(UUID.randomUUID(),1,2,new Source(3,4,5,6));var end=new Vec(0,0,10);var old=shot("old",1000);
        HanzoArrowPresentation.segment(scope,old,old.start(),end,new Hit(true,0,end),20);HanzoArrowPresentation.publish(scope,List.of(),20,1000);
        check(HanzoArrowPresentation.view.arrows().size()==1,"real embedded fixture model");
        HanzoArrowPresentation.retireForFixtureCleanup(2000);check(HanzoArrowPresentation.view==null&&HanzoArrowEffects.view==null,"cleanup withdraws owned visuals");
        HanzoArrowPresentation.segment(scope,old,old.start(),end,new Hit(true,0,end),21);HanzoArrowPresentation.publish(scope,List.of(old),21,2100);
        check(HanzoArrowPresentation.view.arrows().isEmpty(),"queued pre-cleanup sweep cannot recreate a floating model");
        var fresh=shot("fresh",3000);HanzoArrowPresentation.segment(scope,fresh,fresh.start(),end,null,22);HanzoArrowPresentation.publish(scope,List.of(fresh),22,3000);
        check(HanzoArrowPresentation.view.arrows().size()==1,"new post-cleanup shots still render");HanzoArrowPresentation.reset();
        System.out.println("HanzoFixtureCleanupCheck passed (cosmetic cleanup boundary only)");
    }
}
