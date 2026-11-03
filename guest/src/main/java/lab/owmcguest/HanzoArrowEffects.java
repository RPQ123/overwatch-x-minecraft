package lab.owmcguest;

import java.util.*;
import lab.owmcguest.NativeShotProtocol.Vec;

/** Cosmetic history of real loaded sweep segments. Never moves/damages an arrow.
 * Native emitter curves are unevaluated: the 120 ms trail and 80 ms contact
 * afterglow are explicit MC presentation approximations, not projectile lifetime. */
public final class HanzoArrowEffects {
    public enum Kind { PRIMARY, SONIC, SCATTER }
    public enum Contact { NONE, IMPACT, SPLIT, BOUNCE, STUCK }
    public record Scope(UUID owner,long world,long model,long generation) {}
    public record Point(Vec at,long nanos) {}
    public record Trail(String id,Kind kind,boolean child,List<Point> points,long expires) {}
    public record Flash(Kind kind,Vec at,Contact contact,long began,long expires) {}
    public record View(Scope scope,long wall,List<Trail> trails,List<Flash> flashes) {}
    public static final long TRAIL_NANOS=120_000_000L,FLASH_NANOS=80_000_000L;
    private static final class Track {Kind kind;boolean child;long expires;final ArrayDeque<Point> points=new ArrayDeque<>();}
    private static final LinkedHashMap<String,Track> tracks=new LinkedHashMap<>();
    private static final ArrayList<Flash> flashes=new ArrayList<>();
    private static Scope scope;
    public static volatile View view;
    public static volatile long segments,bounces,contacts;
    private HanzoArrowEffects(){}
    public static void segment(Scope next,String id,Kind kind,boolean child,Vec from,Vec to,Contact contact){
        if(next==null||next.owner()==null||next.world()==0||next.model()==0||next.generation()==0||id==null)return;
        if(!next.equals(scope)){reset();scope=next;}
        long now=System.nanoTime();var track=tracks.get(id);
        if(track==null){if(tracks.size()>=256)tracks.remove(tracks.keySet().iterator().next());track=new Track();track.kind=kind;track.child=child;tracks.put(id,track);}
        if(track.points.isEmpty()||track.points.getLast().at().subtract(from).lengthSquared()>1e-10)track.points.add(new Point(from,now));
        if(track.points.isEmpty()||track.points.getLast().at().subtract(to).lengthSquared()>1e-10)track.points.add(new Point(to,now));
        while(track.points.size()>32)track.points.removeFirst();
        track.expires=now+TRAIL_NANOS;segments++;
        if(contact!=Contact.NONE){
            contacts++;if(contact==Contact.BOUNCE)bounces++;
            if(flashes.size()>=128)flashes.remove(0);
            flashes.add(new Flash(kind,to,contact,now,now+FLASH_NANOS));
        }
    }
    /** Called by the existing Hanzo presentation publishers, never by a watcher. */
    public static void publish(){
        long now=System.nanoTime();tracks.values().removeIf(t->now>=t.expires);flashes.removeIf(f->now>=f.expires());
        var trails=new ArrayList<Trail>();
        for(var e:tracks.entrySet()){
            var t=e.getValue();while(t.points.size()>2&&now-t.points.getFirst().nanos()>TRAIL_NANOS)t.points.removeFirst();
            trails.add(new Trail(e.getKey(),t.kind,t.child,List.copyOf(t.points),t.expires));
        }
        view=scope==null?null:new View(scope,System.currentTimeMillis(),List.copyOf(trails),List.copyOf(flashes));
    }
    public static void reset(){tracks.clear();flashes.clear();scope=null;view=null;}
}
