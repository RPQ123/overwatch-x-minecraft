package lab.owmcguest;

/** Rare native Q actions persist in the original logger; establish a baseline
 * before accepting a new activation/fire, and never carry one across sessions. */
public final class NativeDeadeyeEvents {
    public record Event(boolean started,boolean fire,long activation){}
    private long source,model,world,begin,fire;private boolean initialized,armed,fired;
    public Event observe(long nextSource,long nextModel,long nextWorld,long nextBegin,boolean active,long nextFire){
        if(!initialized||source!=nextSource||model!=nextModel||world!=nextWorld){
            initialized=true;source=nextSource;model=nextModel;world=nextWorld;begin=nextBegin;fire=nextFire;armed=false;fired=false;return new Event(false,false,begin);
        }
        boolean started=nextBegin>begin&&active;
        if(started){begin=nextBegin;armed=true;fired=false;}
        boolean shooting=armed&&!fired&&active&&nextFire>fire&&nextFire>=begin;
        fire=Math.max(fire,nextFire);if(shooting)fired=true;if(!active)armed=false;
        return new Event(started,shooting,begin);
    }
    public boolean armed(){return armed&&!fired;}
    /** Confirmed native fire persists through the shot queue, until root End. */
    public boolean firing(){return armed&&fired;}
    public void reset(){initialized=false;armed=fired=false;source=model=world=begin=fire=0;}
}
