package lab.owmcguest;
import java.util.*;
import lab.owmcguest.NativeShotProtocol.*;
import lab.owmcguest.NativeShotSimulation.Hit;
/** The authenticated05e6 Volley ->108b ->2817 icicle follows accepted MC
 * sweep intervals, including the final clipped impact. No damage code here. */
public final class MeiIciclePresentation {
    public static final long HERO=0x02e00000000000ddL,RESOURCE=0x040000000000108bL;
    public record Scope(UUID owner,long world,long model,Source source){}
    public record Segment(Vec from,Vec to,double begin,double end){}
    public static final int STUCK_TICKS=HanzoArrowPresentation.STUCK_TICKS,FADE_TICKS=20;
    public record Flight(String id,long epoch,List<Segment> path,boolean terminal,boolean embedded,int impactTick){}
    public record View(Scope scope,long wall,int tick,List<Flight> flights){}
    public record Sample(Vec at,Vec direction){}
    private static final class Pending {long epoch;boolean terminal,embedded;int impactTick;final List<Segment> path=new ArrayList<>();}
    private static final Map<String,Pending> flights=new LinkedHashMap<>();private static Scope scope;
    public static volatile View view;public static long traced,contacts,embedded;
    public static boolean isIcicle(Shot s){return s!=null&&!s.beam()&&s.effect()!=null&&s.effect().hero()==HERO&&s.effect().resource()==RESOURCE;}
    private static boolean configure(Scope next){if(next==null||next.owner()==null||next.source()==null||next.world()==0||next.model()==0)return false;if(!next.equals(scope)){reset();scope=next;}return true;}
    public static void segment(Scope next,Shot shot,Vec from,Vec to,Hit hit,double begin,double end,long wall,int tick){
        if(!isIcicle(shot)||!configure(next)||!finite(from)||!finite(to)||tick<0||!Double.isFinite(begin)||!Double.isFinite(end)||begin<0||end<begin||end>shot.lifetime()+.001)return;
        if(flights.size()>=256&&!flights.containsKey(shot.identity()))return;
        var p=flights.computeIfAbsent(shot.identity(),id->{var item=new Pending();item.epoch=wall-Math.round(begin*1000);return item;});
        if(p.terminal||p.path.size()>=512)return;p.path.add(new Segment(from,to,begin,end));p.terminal=hit!=null||shot.hitscan();traced++;if(hit!=null&&hit.loaded())contacts++;
        if(hit!=null&&hit.loaded()&&hit.block()){p.embedded=true;p.impactTick=tick;embedded++;}
    }
    private static boolean finite(Vec p){return p!=null&&Double.isFinite(p.x())&&Double.isFinite(p.y())&&Double.isFinite(p.z());}
    public static void publish(Scope next,List<Shot> active,long wall,int tick){
        if(!configure(next)){reset();return;}
        var alive=new HashSet<String>();for(var s:active)if(isIcicle(s))alive.add(s.identity());
        flights.entrySet().removeIf(e->{var p=e.getValue();return p.path.isEmpty()||(p.embedded?tick>=p.impactTick+STUCK_TICKS:wall>p.epoch+Math.round(p.path.getLast().end()*1000)+750&&(p.terminal||!alive.contains(e.getKey())));});
        view=new View(scope,wall,tick,flights.entrySet().stream().map(e->new Flight(e.getKey(),e.getValue().epoch,List.copyOf(e.getValue().path),e.getValue().terminal,e.getValue().embedded,e.getValue().impactTick)).toList());
    }
    public static Sample sample(Flight f,long now,long epoch){
        if(f==null||f.path().isEmpty()||now<epoch)return null;double age=(now-epoch)/1000.;var last=f.path().getLast();if(f.terminal()&&!f.embedded()&&age>last.end()+.1)return null;
        Segment chosen=f.path().getFirst();for(var p:f.path())if(age>=p.begin()){chosen=p;if(age<=p.end())break;}
        var delta=chosen.to().subtract(chosen.from());double length=Math.sqrt(delta.lengthSquared());if(length<1e-8)return null;
        double duration=chosen.end()-chosen.begin(),fraction=duration>1e-8?Math.clamp((age-chosen.begin())/duration,0,1):1;
        return new Sample(chosen.from().add(delta.multiply(fraction)),delta.multiply(1/length));
    }
    public static boolean stuck(Flight f,long now,long epoch){return f.embedded()&&(now-epoch)/1000.>=f.path().getLast().end();}
    public static float opacity(Flight f,double tick){return f.embedded()?(float)Math.clamp((f.impactTick()+STUCK_TICKS-tick)/FADE_TICKS,0,1):1;}
    public static void reset(){flights.clear();view=null;scope=null;}
    private MeiIciclePresentation(){}
}
