package lab.owmcguest;

/** One hit per original 00fe:69/70 TrackTargets window (only 100ms long).
 * A completed window between polls is valid; an attached old window is not. */
public final class WinstonFistPhase {
    private long previous=-1;private boolean active,suppressEnd;
    public long observe(long tick,boolean running){
        if(tick<0)throw new IllegalArgumentException("native fist tick");
        if(previous<0||tick<previous){previous=tick;active=running;suppressEnd=running;return 0;}
        long token=0;
        if(tick>previous){
            if(running){token=tick;suppressEnd=false;}
            else if(!active&&!suppressEnd)token=tick;
            if(!running)suppressEnd=false;
        }
        previous=tick;active=running;return token;
    }
    public void reset(){previous=-1;active=suppressEnd=false;}
}
