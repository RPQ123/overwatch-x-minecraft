package lab.owmcguest;

import java.util.EnumSet;
import java.util.UUID;

/** Audio follows W2's admitted native receipts and actual MC contacts, never keys.
 * Attaching mid-cast, stale samples and counter rollback establish a baseline. */
public final class WinstonAudioGate {
    public enum Event { TAKEOFF, LANDING, THROW, DEPLOY, PRIMAL }
    public record Scope(UUID owner,long world,long source,long model) {}
    public record Sample(Scope scope,long wall,long jumpAck,long barrierAck,long primalBegin,
                         long jumps,long landings,long barriers,long deployments,long primals) {}
    public record NativeSample(Scope scope,long wall,long jumpSequence,long jumpToken,long takeoffTick,long landingTick,
                               long barrierSequence,long barrierToken,long throwTick,long petTick) {}
    public enum Owner { UNKNOWN, NATIVE, MINECRAFT }
    /** An original Effect execution owns its own SFX. Only a certified missing
     * effect is supplemented; unknown reads cannot add an echo over native audio. */
    public static Owner owner(Sample cast,NativeSample nativeSample,Event event,long now){
        if(cast==null||nativeSample==null||!cast.scope().equals(nativeSample.scope())||now<nativeSample.wall()||now-nativeSample.wall()>200)return Owner.UNKNOWN;
        boolean jump=event==Event.TAKEOFF||event==Event.LANDING;
        if(event==Event.PRIMAL)return Owner.UNKNOWN;
        long sequence=jump?nativeSample.jumpSequence():nativeSample.barrierSequence(),token=jump?nativeSample.jumpToken():nativeSample.barrierToken();
        if(sequence!=(jump?cast.jumpAck():cast.barrierAck())||sequence<=0||token<=0)return Owner.UNKNOWN;
        long tick=switch(event){case TAKEOFF->nativeSample.takeoffTick();case LANDING->nativeSample.landingTick();case THROW->nativeSample.throwTick();case DEPLOY->nativeSample.petTick();default->-1;};
        return tick<0?Owner.UNKNOWN:tick>=token?Owner.NATIVE:Owner.MINECRAFT;
    }
    private Sample previous;
    private long admittedJump,admittedBarrier;
    public EnumSet<Event> observe(Sample s,Scope current,long now){
        var events=EnumSet.noneOf(Event.class);
        if(s==null||current==null||!current.equals(s.scope())||now<s.wall()||now-s.wall()>200){reset();return events;}
        var old=previous;previous=s;
        if(old==null||!s.scope().equals(old.scope())||s.jumps()<old.jumps()||s.landings()<old.landings()
            ||s.barriers()<old.barriers()||s.deployments()<old.deployments()||s.primals()<old.primals()
            ||s.jumpAck()<old.jumpAck()||s.barrierAck()<old.barrierAck()||s.primalBegin()<old.primalBegin()){
            admittedJump=admittedBarrier=0;return events;
        }
        if(s.jumps()>old.jumps()&&s.jumpAck()>old.jumpAck()&&s.jumpAck()>0){admittedJump=s.jumpAck();events.add(Event.TAKEOFF);}
        if(s.landings()>old.landings()&&admittedJump>0&&s.jumpAck()==admittedJump){admittedJump=0;events.add(Event.LANDING);}
        if(s.barriers()>old.barriers()&&s.barrierAck()>old.barrierAck()&&s.barrierAck()>0){admittedBarrier=s.barrierAck();events.add(Event.THROW);}
        if(s.deployments()>old.deployments()&&admittedBarrier>0&&s.barrierAck()==admittedBarrier){admittedBarrier=0;events.add(Event.DEPLOY);}
        // Q has no placement cooldown. The producer commits this only after the
        // real native HealthPool Begin has passed W2's scoped server admission.
        if(s.primals()>old.primals()&&s.primalBegin()>old.primalBegin()&&s.primalBegin()>0)events.add(Event.PRIMAL);
        return events;
    }
    public void reset(){previous=null;admittedJump=admittedBarrier=0;}
}
