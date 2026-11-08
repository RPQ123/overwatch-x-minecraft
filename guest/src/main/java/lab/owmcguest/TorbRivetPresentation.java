package lab.owmcguest;

import java.util.*;
import lab.owmcguest.NativeShotProtocol.*;
import lab.owmcguest.NativeShotSimulation.Hit;

/** Only accepted MC sweeps supply geometry and time intervals. No collision,
 * input, ballistic solver or damage here. The first received server sweep sets
 * a per-flight presentation epoch; T3 replays its exact traced intervals at
 *0.75x visual time. Native damage/physics never wait for the cosmetic replay. */
public final class TorbRivetPresentation {
    public static final double VISUAL_TIME_SCALE=.75,PELLET_VISUAL_SPEED=45;
    public static final long HERO=0x02e0000000000006L,PRIMARY=0x0400000000000157L,SECONDARY=0x04000000000002d0L;
    public enum Kind{RIVET,PELLET}
    public record Scope(UUID owner,long world,long model,Source source){}
    public record Segment(Vec from,Vec to,double begin,double end,boolean impact){}
    public record Flight(String id,Kind kind,long epoch,long nativeWall,List<Segment> segments,boolean terminal,boolean instant){}
    public record View(Scope scope,long wall,List<Flight> flights){}
    public record Sample(Vec at,Vec direction,Vec trailFrom,boolean impact,double age,double nativeSpeed,double visualSpeed){}
    private static final class Pending{String id;Kind kind;long epoch,nativeWall;boolean terminal,instant;List<Segment> segments=new ArrayList<>();}
    private static final LinkedHashMap<String,Pending> flights=new LinkedHashMap<>();
    private static final Set<String> retired=new HashSet<>();private static Scope scope;
    public static volatile View view;public static long segments,contacts,refused;private static long cleanupWall;
    private TorbRivetPresentation(){}
    public static Kind kind(Shot s){
        if(s==null||s.beam()||s.effect()==null||s.effect().hero()!=HERO)return null;
        return s.effect().resource()==PRIMARY?Kind.RIVET:s.effect().resource()==SECONDARY?Kind.PELLET:null;
    }
    private static boolean finite(Vec p){return p!=null&&Double.isFinite(p.x())&&Double.isFinite(p.y())&&Double.isFinite(p.z())
        &&Math.abs(p.x())<=30000000&&Math.abs(p.y())<=30000000&&Math.abs(p.z())<=30000000;}
    private static boolean configure(Scope next){
        if(next==null||next.owner()==null||next.world()==0||next.model()==0||next.source()==null||next.source().hostGeneration()==0)return false;
        if(!next.equals(scope)){reset();scope=next;}return true;
    }
    public static void segment(Scope next,Shot shot,Vec from,Vec to,Hit hit,double begin,double end,long wall){
        Kind kind=kind(shot);if(kind==null||shot.wallMs()<=cleanupWall)return;
        if(!configure(next)||!finite(from)||!finite(to)||!Double.isFinite(begin)||!Double.isFinite(end)||begin<0||end<begin||end>shot.lifetime()+.001){refused++;return;}
        var id=shot.identity();if(id==null||retired.contains(id))return;
        var f=flights.get(id);
        if(f==null){
            if(flights.size()>=256||wall-shot.wallMs()>1000||wall<shot.wallMs()-50){refused++;return;}
            f=new Pending();f.id=id;f.kind=kind;f.instant=shot.hitscan();f.nativeWall=shot.wallMs();f.epoch=wall-Math.round(begin*1000);flights.put(id,f);
        }
        if(f.terminal||f.segments.size()>=512){refused++;return;}
        f.segments.add(new Segment(from,to,begin,end,hit!=null&&hit.loaded()));segments++;
        if(hit!=null){f.terminal=true;retired.add(id);if(hit.loaded())contacts++;}
        if(f.instant){f.terminal=true;retired.add(id);}
    }
    public static void publish(Scope next,List<Shot> active,long wall){
        if(!configure(next)){reset();return;}
        var alive=new HashSet<String>();for(var shot:active)if(kind(shot)!=null)alive.add(shot.identity());
        flights.values().removeIf(f->{
            if(f.segments.isEmpty())return true;
            var end=f.segments.get(f.segments.size()-1);double seconds=f.instant?Math.sqrt(end.to().subtract(end.from()).lengthSquared())/PELLET_VISUAL_SPEED:end.end()/VISUAL_TIME_SCALE;
            long visualEnd=f.epoch+Math.round(seconds*1000)+330; // bounded client first-frame latency +80ms contact tail
            return wall>visualEnd&&(f.terminal||!alive.contains(f.id));
        });
        if(retired.size()>16384){flights.clear();retired.clear();refused++;}
        view=new View(scope,wall,flights.values().stream().map(f->new Flight(f.id,f.kind,f.epoch,f.nativeWall,List.copyOf(f.segments),f.terminal,f.instant)).toList());
    }
    /** Piecewise interpolation follows the exact traced segment, including the
     * clipped collision time. A terminal sample never travels beyond its hit. */
    public static Sample sample(Flight f,long now){
        return sample(f,now,f==null?0:f.epoch());
    }
    public static Sample sample(Flight f,long now,long visualEpoch){
        if(f==null||f.segments().isEmpty()||now<visualEpoch)return null;double visualAge=(now-visualEpoch)/1000.,age=visualAge*VISUAL_TIME_SCALE;
        if(f.instant()){
            var s=f.segments().getFirst();var delta=s.to().subtract(s.from());double length=Math.sqrt(delta.lengthSquared());if(length<1e-10||visualAge>length/PELLET_VISUAL_SPEED+.08)return null;
            double distance=Math.min(length,visualAge*PELLET_VISUAL_SPEED);var direction=delta.multiply(1/length);var at=s.from().add(direction.multiply(distance));
            return new Sample(at,direction,s.from().add(direction.multiply(Math.max(0,distance-.8))),s.impact()&&distance>=length,visualAge,0,PELLET_VISUAL_SPEED);
        }
        Segment chosen=null;for(var s:f.segments()){if(age>=s.begin()){chosen=s;if(age<=s.end())break;}}
        if(chosen==null)return null;
        var last=f.segments().get(f.segments().size()-1);
        if(f.terminal()&&visualAge>last.end()/VISUAL_TIME_SCALE+.08)return null;
        var delta=chosen.to().subtract(chosen.from());double length=Math.sqrt(delta.lengthSquared());
        if(length<1e-10)return null;
        double duration=chosen.end()-chosen.begin(),t=duration>1e-9?Math.max(0,Math.min(1,(age-chosen.begin())/duration)):1;
        var at=chosen.from().add(delta.multiply(t));var direction=delta.multiply(1/length);
        var trail=chosen.from().add(delta.multiply(Math.max(0,t-.8/length)));
        double nativeSpeed=duration>1e-9?length/duration:0;
        return new Sample(at,direction,trail,chosen.impact()&&t>=1,visualAge,nativeSpeed,nativeSpeed*VISUAL_TIME_SCALE);
    }
    /** T3 user-requested slow cosmetic replay of already resolved native rays.
     * Instant native damage still occurred in the original solver at time0. */
    public static List<Vec> bodies(Flight f,Sample s){
        return List.of(s.at());
    }
    public static void reset(){flights.clear();retired.clear();scope=null;view=null;}
    public static void retireForFixtureCleanup(long wall){cleanupWall=Math.max(cleanupWall,wall);reset();}
}
