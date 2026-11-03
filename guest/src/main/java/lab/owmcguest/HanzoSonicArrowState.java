package lab.owmcguest;

import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.UUID;

/** Pure Sonic lifecycle. Only an already accepted original projectile may arm it.
 * Beta c3 declares10 seconds/10 range. Sphere selection and a fixed impact anchor
 * are MC policy, not a claim of original server shape or later target attachment. */
public final class HanzoSonicArrowState {
    public static final long HERO=0x02e0000000000005L;
    public static final long STRONG=0x0400000000000149L,WEAK=0x040000000000020dL;
    public static final int DURATION_TICKS=200;
    public static final double RADIUS=10;
    public record Scope(UUID owner,long world,long generation,long model) {
        public boolean valid(){return owner!=null&&world!=0&&generation!=0&&model!=0;}
    }
    public record Point(double x,double y,double z) {
        public boolean valid(){return Double.isFinite(x)&&Double.isFinite(y)&&Double.isFinite(z)
            &&Math.abs(x)<=30000000&&Math.abs(y)<=30000000&&Math.abs(z)<=30000000;}
        public double squaredDistance(Point p){double a=x-p.x,b=y-p.y,c=z-p.z;return a*a+b*b+c*c;}
    }
    public record Pulse(String identity,Point at,long began,long expires) {}
    private final LinkedHashMap<String,Long> flights=new LinkedHashMap<>();
    private final LinkedHashMap<String,Pulse> pulses=new LinkedHashMap<>();
    private final HashSet<String> seen=new HashSet<>();
    private Scope scope;
    private long lastTick=Long.MIN_VALUE;
    public long admitted,impacts,refused,duplicates,expired;
    public static boolean sonicResource(long resource){return resource==STRONG||resource==WEAK;}
    public void configure(Scope next){
        if(next==null||!next.valid()){clear();return;}
        if(!next.equals(scope)){clear();scope=next;}
    }
    private boolean current(Scope expected,long tick){
        if(scope==null||!scope.equals(expected)||tick<0||tick<lastTick)return false;
        lastTick=tick;return true;
    }
    /** Must be called from the accepted NativeShotSimulation admissions, never keys/logger snapshots. */
    public boolean admit(Scope expected,String identity,long resource,long wall,double lifetime,long now,long tick){
        if(!current(expected,tick)||identity==null||identity.isBlank()||identity.length()>256
            ||!sonicResource(resource)||now-wall>500||wall-now>100||!Double.isFinite(lifetime)
            ||lifetime!=5){refused++;return false;}
        if(seen.contains(identity)){duplicates++;return false;}
        if(seen.size()>=4096||flights.size()>=16||pulses.size()>=16){refused++;return false;}
        seen.add(identity);
        long remaining=(long)Math.ceil(Math.max(0,lifetime-Math.max(0,now-wall)/1000.)*20);
        if(remaining==0){refused++;return false;}
        flights.put(identity,tick+remaining);admitted++;return true;
    }
    /** The actual MC sweep resolves once. An unloaded contact consumes and refuses it. */
    public boolean impact(Scope expected,String identity,Point point,boolean loaded,long tick){
        if(!current(expected,tick)){refused++;return false;}
        Long until=flights.remove(identity);
        if(until==null||tick>until||!loaded||point==null||!point.valid()){refused++;return false;}
        pulses.put(identity,new Pulse(identity,point,tick,tick+DURATION_TICKS));impacts++;return true;
    }
    public void advance(Scope expected,long tick){
        if(!current(expected,tick)){clear();return;}
        flights.entrySet().removeIf(e->tick>e.getValue());
        var iterator=pulses.values().iterator();
        while(iterator.hasNext())if(tick>=iterator.next().expires()){iterator.remove();expired++;}
    }
    public boolean reveals(Point point){
        if(point==null||!point.valid())return false;
        return pulses.values().stream().anyMatch(p->p.at().squaredDistance(point)<=RADIUS*RADIUS);
    }
    public List<Pulse> pulses(){return List.copyOf(pulses.values());}
    public int flights(){return flights.size();}
    public Scope scope(){return scope;}
    public void clear(){flights.clear();pulses.clear();seen.clear();scope=null;lastTick=Long.MIN_VALUE;}
}
