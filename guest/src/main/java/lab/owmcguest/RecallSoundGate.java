package lab.owmcguest;

import java.util.UUID;

/** A caller-authenticated original Recall Begin owns exactly one start sound. */
public final class RecallSoundGate {
    public record Scope(UUID owner,long world,long source,long model) {}
    private Scope scope;
    private long begin;
    public boolean claim(Scope next,long tick){
        if(next==null||next.owner()==null||next.world()==0||next.source()==0||next.model()==0||tick<=0)return false;
        if(!next.equals(scope)){scope=next;begin=0;}
        if(tick<=begin)return false;
        begin=tick;return true;
    }
}
