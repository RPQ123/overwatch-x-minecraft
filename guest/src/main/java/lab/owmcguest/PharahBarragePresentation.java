package lab.owmcguest;

import java.util.*;
import lab.owmcguest.NativeShotProtocol.*;

/** Server-owned cosmetic facts. Only admissions and resolved real impacts enter. */
public final class PharahBarragePresentation {
    public record Launch(long sequence,Shot shot){}
    public record Impact(long sequence,long wallMs,Vec point,Vec normal){}
    public record View(long world,UUID player,Source source,long model,List<Launch> launches,List<Impact> impacts){}
    private static final ArrayDeque<Launch> launches=new ArrayDeque<>();
    private static final ArrayDeque<Impact> impacts=new ArrayDeque<>();
    private static long sequence;
    public static volatile View view;
    public static volatile long admitted,detonated;
    public static void launch(Shot shot){
        if(!shot.barrage())return;
        if(launches.size()>=128)launches.removeFirst();
        launches.addLast(new Launch(++sequence,shot));admitted++;
    }
    public static void impact(Shot shot,NativeShotSimulation.Hit hit){
        if(!shot.barrage()||!hit.loaded())return;
        if(impacts.size()>=96)impacts.removeFirst();
        impacts.addLast(new Impact(++sequence,System.currentTimeMillis(),hit.point(),hit.normal()));detonated++;
    }
    public static void publish(long world,UUID player,Source source,long model,long now){
        launches.removeIf(c->now-c.shot.wallMs()>350||now<c.shot.wallMs());
        impacts.removeIf(c->now-c.wallMs()>420||now<c.wallMs());
        view=new View(world,player,source,model,List.copyOf(launches),List.copyOf(impacts));
    }
    public static void reset(){view=null;launches.clear();impacts.clear();}
}
