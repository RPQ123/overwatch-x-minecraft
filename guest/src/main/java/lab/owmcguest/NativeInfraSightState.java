package lab.owmcguest;

import java.util.UUID;

/** Fresh native event scope; joining an already-active original Q is a baseline. */
public final class NativeInfraSightState {
    public static final long HERO=0x02e000000000000aL;
    public record Scope(UUID owner,long world,long generation,long model){}
    private Scope scope;
    private boolean baseline,active;
    private long seen,begin,wall,deadline;
    public boolean observe(Scope next,long tick,boolean running,long published,long now){
        if(next==null||next.owner()==null||next.world()==0||next.generation()==0||next.model()==0||tick<0||now-published>150||published>now+50){reset();return false;}
        if(!next.equals(scope)){reset();scope=next;}
        if(!baseline){baseline=true;seen=tick;return false;}
        if(tick<seen){active=false;return false;}
        if(!running){seen=Math.max(seen,tick);active=false;return false;}
        if(tick>seen){seen=begin=tick;deadline=now+15000;active=true;}
        wall=published;return active(next,now);
    }
    public boolean active(Scope expected,long now){return active&&scope!=null&&scope.equals(expected)&&begin>0&&now-wall<=150&&wall<=now+50&&now<deadline;}
    public long begin(){return begin;}
    public void reset(){scope=null;baseline=active=false;seen=begin=wall=deadline=0;}
}
