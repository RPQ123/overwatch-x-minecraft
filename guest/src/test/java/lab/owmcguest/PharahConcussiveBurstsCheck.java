package lab.owmcguest;

import java.util.*;
import lab.owmcguest.NativeShotProtocol.*;

public final class PharahConcussiveBurstsCheck {
    private static void check(boolean b,String message){if(!b)throw new AssertionError(message);}
    private static Shot shot(long id,Effect effect){return new Shot(id,0,System.currentTimeMillis(),new Vec(0,1,0),new Vec(0,0,60),0,5,false,100,"native:"+id,false,false,effect);}
    public static void main(String[] args){
        var effect=new Effect(0x02e0000000000008L,0x040000000000010fL,3,0,0,8,0,0,0);
        var source=new Source(1,2,3,4);var player=UUID.randomUUID();
        var hit=new NativeShotSimulation.Hit(true,0,new Vec(0,1,3));
        PharahConcussiveBursts.reset();
        PharahConcussiveBursts.impact(shot(1,effect),new NativeShotSimulation.Hit(true,0,hit.point(),false));
        PharahConcussiveBursts.impact(shot(2,null),hit);
        PharahConcussiveBursts.publish(8,player,source,11,System.currentTimeMillis());
        check(PharahConcussiveBursts.view.bursts().isEmpty(),"unloaded/foreign collision has no pressure wave");
        var actual=shot(3,effect);PharahConcussiveBursts.impact(actual,hit);PharahConcussiveBursts.impact(actual,hit);
        PharahConcussiveBursts.publish(8,player,source,11,System.currentTimeMillis());
        check(PharahConcussiveBursts.view.bursts().size()==1,"real collision once; replay inert");
        long wall=PharahConcussiveBursts.view.bursts().getFirst().wallMs();
        PharahConcussiveBursts.publish(8,player,source,11,wall+500);
        check(PharahConcussiveBursts.view.bursts().isEmpty(),"completed shell retires");
        PharahConcussiveBursts.impact(shot(4,effect),hit);
        PharahConcussiveBursts.publish(9,player,source,11,System.currentTimeMillis());
        check(PharahConcussiveBursts.view.bursts().isEmpty(),"old-world collisions cannot inherit new world");
        PharahConcussiveBursts.impact(shot(5,effect),hit);
        PharahConcussiveBursts.publish(9,player,source,12,System.currentTimeMillis());
        check(PharahConcussiveBursts.view.bursts().isEmpty(),"old model cannot draw on recreated Pharah");
        for(int i=0;i<64;i++)PharahConcussiveBursts.impact(shot(100+i,effect),hit);
        PharahConcussiveBursts.publish(9,player,source,12,System.currentTimeMillis());
        check(PharahConcussiveBursts.view.bursts().size()==32,"bounded frame backlog");
        double previous=0;for(double age=0;age<.4;age+=.01){
            double r=PharahConcussiveBursts.radius(age),a=PharahConcussiveBursts.opacity(age);
            check(Double.isFinite(r)&&r>=previous&&r<2&&a>=0&&a<=1,"finite expanding bounded pressure shell");previous=r;
        }
        check(PharahConcussiveBursts.opacity(.41)==0&&PharahConcussiveBursts.radius(-1)==0,"no stale/future rendering");
        PharahConcussiveBursts.reset();check(PharahConcussiveBursts.view==null,"session cleanup");
        System.out.println("PASS: actual E impact admission, replay, unloaded/world/model cancellation, expiry and bounded pressure waves");
    }
}
