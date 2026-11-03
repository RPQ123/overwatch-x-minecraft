package lab.owmcguest;

import java.util.*;
import lab.owmcguest.NativeShotProtocol.*;
import lab.owmcguest.NativeShotSimulation.Hit;

/** Cosmetic mirror of accepted MC sweep segments. No independent flight or damage.
 * MC adaptation: block-embedded arrows remain 200 server ticks; beta retention is
 * unverified. Sonic reveal still belongs exclusively to HanzoSonicArrowRuntime.
 * Feed segment/publish from NativeCombatRuntime, on its existing server thread. */
public final class HanzoArrowPresentation {
    public static final int STUCK_TICKS=200,MAX_ARROWS=256;
    public enum Kind { PRIMARY, SONIC }
    public record Scope(UUID owner,long world,long model,Source source) {}
    public record Arrow(String identity,Kind kind,Vec at,Vec direction,boolean stuck,int expires) {}
    public record View(Scope scope,long wall,List<Arrow> arrows) {}
    private static final LinkedHashMap<String,Arrow> arrows=new LinkedHashMap<>();
    private static final Set<String> retired=new HashSet<>();
    private static Scope scope;
    private static long retiredBeforeWall=Long.MIN_VALUE;
    public static volatile View view;
    public static long segments,embedded,refused;
    private HanzoArrowPresentation(){}

    public static Kind kind(Shot shot){
        if(shot==null||shot.hitscan()||shot.beam()||shot.effect()==null
            ||shot.effect().hero()!=HanzoSonicArrowState.HERO)return null;
        long resource=shot.effect().resource();
        if(resource==0x0400000000000144L||resource==0x040000000000020bL)return Kind.PRIMARY;
        return HanzoSonicArrowState.sonicResource(resource)?Kind.SONIC:null;
    }
    private static boolean configure(Scope next){
        if(next==null||next.owner()==null||next.world()==0||next.model()==0||next.source()==null
            ||next.source().hostGeneration()==0)return false;
        if(!next.equals(scope)){reset();scope=next;}
        return true;
    }
    private static boolean finite(Vec p){return p!=null&&Double.isFinite(p.x())&&Double.isFinite(p.y())&&Double.isFinite(p.z())
        &&Math.abs(p.x())<=30000000&&Math.abs(p.y())<=30000000&&Math.abs(p.z())<=30000000;}

    /** Only from WorldAccess.present AFTER a real trace; a refused/unloaded hit
     * retires the cosmetic arrow without creating an embedded arrow or pulse. */
    public static void segment(Scope next,Shot shot,Vec from,Vec to,Hit hit,int tick){
        Kind kind=kind(shot);if(kind==null)return;
        if(shot.wallMs()<=retiredBeforeWall)return;
        if(!configure(next)||!finite(from)||!finite(to)||tick<0){refused++;return;}
        String id=shot.identity();if(id==null||retired.contains(id))return;
        if(hit==null||hit.loaded())HanzoArrowEffects.segment(
            new HanzoArrowEffects.Scope(next.owner(),next.world(),next.model(),next.source().hostGeneration()),id,
            kind==Kind.SONIC?HanzoArrowEffects.Kind.SONIC:HanzoArrowEffects.Kind.PRIMARY,false,from,to,
            hit==null?HanzoArrowEffects.Contact.NONE:HanzoArrowEffects.Contact.IMPACT);
        Vec direction=to.subtract(from);
        if(direction.lengthSquared()<1e-12){var previous=arrows.get(id);direction=previous==null?shot.velocity():previous.direction();}
        if(!finite(direction)||direction.lengthSquared()<1e-12){refused++;return;}
        segments++;
        boolean stuck=hit!=null&&hit.block()&&hit.loaded();
        if(hit!=null){
            // Bounded history: fail closed on an exhausted cosmetic session.
            if(retired.size()>=8192){refused++;arrows.remove(id);return;}
            retired.add(id);
            if(!stuck){arrows.remove(id);return;}
            embedded++;
        }
        if(!arrows.containsKey(id)&&arrows.size()>=MAX_ARROWS)arrows.remove(arrows.keySet().iterator().next());
        arrows.put(id,new Arrow(id,kind,to,direction,stuck,stuck?tick+STUCK_TICKS:0));
    }
    /** Publish after simulation.tick, carrying its remaining active flights. */
    public static void publish(Scope next,List<Shot> active,int tick,long wall){
        if(!configure(next)){reset();return;}
        var flying=new HashSet<String>();for(var shot:active)if(kind(shot)!=null)flying.add(shot.identity());
        arrows.values().removeIf(a->a.stuck()?tick>=a.expires():!flying.contains(a.identity()));
        view=new View(scope,wall,List.copyOf(arrows.values()));
        HanzoArrowEffects.publish();
    }
    public static void reset(){arrows.clear();retired.clear();scope=null;view=null;HanzoArrowEffects.reset();}
    /** Diagnostic-fixture cleanup only: queued pre-cleanup sweeps cannot
     * recreate a floating model after the owned wall has been restored. */
    public static void retireForFixtureCleanup(long wall){retiredBeforeWall=Math.max(retiredBeforeWall,wall);reset();}
}
