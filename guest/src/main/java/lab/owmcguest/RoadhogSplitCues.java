package lab.owmcguest;

import java.util.*;
import lab.owmcguest.NativeShotProtocol.*;

/** Exactly one second-stage cue per successfully split, acknowledged parent.
 * No keys, child-hit callbacks, file I/O or native sound calls. */
public final class RoadhogSplitCues {
    public static final RoadhogSplitCues INSTANCE=new RoadhogSplitCues();
    public record Cue(RoadhogPresentation.Scope scope,String parent,Vec at,long wall){}
    private RoadhogPresentation.Scope scope;
    private final LinkedHashSet<String> seen=new LinkedHashSet<>();
    private final ArrayDeque<Cue> pending=new ArrayDeque<>();
    public long admitted,duplicates,overflow;
    public synchronized boolean emit(RoadhogPresentation.Scope next,Shot parent,Vec at,long now){
        if(next==null||!RoadhogRules.secondary(parent)||at==null||!Double.isFinite(at.lengthSquared()))return false;
        if(!next.equals(scope)){pending.clear();seen.clear();scope=next;}
        if(!seen.add(parent.identity())){duplicates++;return false;}
        if(seen.size()>2048)seen.remove(seen.iterator().next());
        if(pending.size()>=64){overflow++;return false;}
        pending.addLast(new Cue(next,parent.identity(),at,now));admitted++;return true;
    }
    public synchronized Cue poll(){return pending.pollFirst();}
    public synchronized void drain(){pending.clear();}
    public synchronized void clear(){pending.clear();seen.clear();scope=null;}
    public static boolean current(Cue cue,RoadhogServer.Scope current,long now){
        var s=cue.scope();return current!=null&&s.owner().equals(current.owner())&&s.world()==current.world()
            &&s.model()==current.model()&&s.source().hostGeneration()==current.source()&&now>=cue.wall()&&now-cue.wall()<=250;
    }
}
