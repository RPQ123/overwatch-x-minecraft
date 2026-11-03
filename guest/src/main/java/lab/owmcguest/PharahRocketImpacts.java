package lab.owmcguest;

import java.util.*;
import lab.owmcguest.NativeShotProtocol.*;

/** Resolved primary impacts, independent of Barrage's accepted presentation. */
public final class PharahRocketImpacts {
    public record Impact(long sequence,long wall,Vec point,Vec normal){}
    public record View(long world,UUID player,Source source,long model,List<Impact> impacts){}
    private static final ArrayDeque<Impact> pending=new ArrayDeque<>();
    private static long sequence;public static volatile View view;
    public static volatile long detonated;
    public static void impact(Shot shot,NativeShotSimulation.Hit hit){
        if(!shot.rocket()||shot.barrage()||!hit.loaded())return;
        if(pending.size()>=64)pending.removeFirst();
        pending.addLast(new Impact(++sequence,System.currentTimeMillis(),hit.point(),hit.normal()));detonated++;
    }
    public static void publish(long world,UUID owner,Source source,long model,long now){
        pending.removeIf(i->now-i.wall()>380||now<i.wall());
        view=new View(world,owner,source,model,List.copyOf(pending));
    }
    public static void reset(){pending.clear();view=null;}
}
