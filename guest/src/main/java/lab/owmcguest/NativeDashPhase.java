package lab.owmcguest;

/** Native execution timestamps, never keyboard edges, identify a dash. */
public final class NativeDashPhase {
    private long source,model,lastTick,activeTick,started,refreshed;
    private boolean initialized,active;
    public boolean observe(long origin,long owner,long tick,boolean executing,long now){
        if(!initialized||source!=origin||model!=owner){initialized=true;source=origin;model=owner;lastTick=tick;active=false;return false;}
        boolean begin=executing&&tick>lastTick;
        if(begin){active=true;activeTick=tick;started=now;}
        if(!executing||tick!=activeTick)active=false;
        lastTick=Math.max(lastTick,tick);refreshed=now;return begin;
    }
    public boolean active(long now){return active&&now-refreshed<=100&&now-started<=750;}
    public long tick(){return activeTick;}
    public void invalidate(){active=false;}
}
