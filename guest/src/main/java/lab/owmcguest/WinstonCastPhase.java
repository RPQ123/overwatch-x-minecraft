package lab.owmcguest;

/** Native cast logger edge, including a short cast whose End was sampled first.
 * Initial/rollback samples are baselines; repeated active snapshots are inert. */
public final class WinstonCastPhase {
    private long previous=-1;private boolean suppressWindow;
    public long observe(long tick){return observe(tick,false);}
    public long observe(long tick,boolean active){
        if(tick<0)throw new IllegalArgumentException("Winston cast clock");
        if(previous<0||tick<previous){previous=tick;suppressWindow=active;return 0;}
        if(tick==previous){if(!active)suppressWindow=false;return 0;}
        previous=tick;if(suppressWindow){if(!active)suppressWindow=false;return 0;}return tick;
    }
    public void reset(){previous=-1;suppressWindow=false;}
}
