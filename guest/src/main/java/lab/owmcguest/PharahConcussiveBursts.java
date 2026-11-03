package lab.owmcguest;

import java.util.*;
import lab.owmcguest.NativeShotProtocol.*;

/** Cosmetic pressure waves from actual loaded E collisions, never from a key. */
public final class PharahConcussiveBursts {
    public record Burst(long shotId,long wallMs,Vec point) {}
    public record View(long world,UUID player,Source source,long model,List<Burst> bursts) {}
    private static final ArrayDeque<Burst> pending=new ArrayDeque<>();
    private static final Set<Long> seen=new HashSet<>();
    public static volatile View view;
    public static void impact(Shot shot,NativeShotSimulation.Hit hit){
        var effect=shot.effect();
        if(effect==null||effect.hero()!=0x02e0000000000008L||effect.resource()!=0x040000000000010fL||effect.kind()!=3||!hit.loaded()||!seen.add(shot.id()))return;
        if(pending.size()>=32)pending.removeFirst();
        pending.addLast(new Burst(shot.id(),System.currentTimeMillis(),hit.point()));
        // The simulation already rejects journal replay. Bound the additional
        // cosmetic receipt set across long same-world play sessions as well.
        if(seen.size()>4096){seen.clear();for(var b:pending)seen.add(b.shotId());}
    }
    public static void publish(long world,UUID player,Source source,long model,long now){
        if(view!=null&&(view.world()!=world||view.model()!=model||!view.player().equals(player)||!view.source().equals(source)))reset();
        pending.removeIf(b->now<b.wallMs()||now-b.wallMs()>420);
        view=new View(world,player,source,model,List.copyOf(pending));
    }
    public static double radius(double age){return !Double.isFinite(age)||age<0||age>.4?0:.12+1.7*Math.sin(Math.min(1,age/.4)*Math.PI/2);}
    public static double opacity(double age){return !Double.isFinite(age)||age<0||age>.4?0:Math.pow(1-age/.4,1.5);}
    public static void reset(){pending.clear();seen.clear();view=null;}
}
