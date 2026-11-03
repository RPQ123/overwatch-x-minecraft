package lab.owmcguest;

/** Native Begin/End authority plus a distance ceiling from original speed/timeout. */
public final class NativeRollPhase {
    private NativeDashPhase phase=new NativeDashPhase();
    private double speed,remaining,seconds;private long started;
    public boolean observe(long source,long model,long tick,boolean active,double rate,double duration,long now){
        if(!Double.isFinite(rate)||rate<=0||rate>100||!Double.isFinite(duration)||duration<=0||duration>2){invalidate();return false;}
        boolean begin=phase.observe(source,model,tick,active,now);
        if(begin){speed=rate;seconds=duration;remaining=rate*duration;started=now;}
        return begin;
    }
    public double step(long now){
        if(!active(now))return 0;
        double distance=Math.min(speed/20,remaining);remaining=Math.max(0,remaining-distance);return distance;
    }
    public boolean active(long now){return phase.active(now)&&now-started<=seconds*1000+50&&remaining>1e-6;}
    public void invalidate(){phase=new NativeDashPhase();remaining=0;}
    /** Consume pending distance while retaining this native Begin baseline. */
    public void discardMotion(){remaining=0;}
    public long tick(){return phase.tick();}
    /** Original formula: normalized forward*throttle.y - left*throttle.x. */
    public static double[] direction(int bits,boolean directional){
        if(!directional)return new double[]{0,1};
        int forward=((bits&1)!=0?1:0)-((bits&2)!=0?1:0);
        int right=((bits&8)!=0?1:0)-((bits&4)!=0?1:0);
        double length=Math.hypot(forward,right);
        return length==0?null:new double[]{right/length,forward/length};
    }
}
