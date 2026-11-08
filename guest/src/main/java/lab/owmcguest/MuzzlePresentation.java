package lab.owmcguest;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.LongAdder;
import com.google.gson.*;
import lab.owmcguest.NativeShotProtocol.Vec;

/** One visual-only launch plane for all native weapons. The authoritative Shot,
 * traces, collision times, velocity and damage are never modified. A launch's
 * camera basis is immutable; looking around cannot drag a projectile with it. */
public final class MuzzlePresentation {
    public static volatile boolean nativeReferenceOnly;
    /** Opt-in disposable-lab object-ID colour, geometry/physics unchanged. */
    public static volatile boolean measurementMask;
    public record Scope(UUID owner,long world,long model,long source){}
    public record Profile(String name,double x,double y,double depth,double converge){}
    public record Basis(Vec forward,Vec right,Vec up){}
    private static final class Launch {
        final Scope scope;final String id;final long hero,wall;final Vec start;volatile Vec visualStart,forward,offset;final double converge;
        volatile long visualEpoch;
        volatile Vec contact;
        Launch(Scope scope,String id,long hero,long wall,Vec start,Vec offset,double converge){this.scope=scope;this.id=id;this.hero=hero;this.wall=wall;this.visualEpoch=wall;this.start=start;this.visualStart=start;this.offset=offset;this.converge=converge;}
    }
    private static final Map<String,Launch> launches=new ConcurrentHashMap<>();
    private static final Map<Long,LongAdder> remembered=new ConcurrentHashMap<>(),corrected=new ConcurrentHashMap<>();
    private static volatile Scope scope;private static long retiredBefore;
    private static volatile Vec lastStart,lastMuzzle,lastReal,lastVisual;private static volatile long lastHero;
    private static final ArrayDeque<JsonObject> anchors=new ArrayDeque<>();
    private MuzzlePresentation(){}
    public static Profile profile(long hero,long resource,long alternate){
        int id=(int)(hero&0xffff);double side=(alternate&1)==0?-1:1;
        if(resource==0x0400000000000052L)return new Profile("Pharah/Barrage shoulders",side*.29,-.16,.7,6);
        if(resource==0x040000000000072cL)return new Profile("Soldier76/Helix",.13,-.15,.9,6);
        if(resource==0x04000000000003ceL)return new Profile("Bastion/Tank barrel",0,-.13,.8,6);
        if(resource==-1)return new Profile("original throw hand",-.23,-.25,.65,4);
        return switch(id){
            case 0x29->new Profile("Genji fingers",.10,-.12,.65,6);
            case 0x42->new Profile("McCree revolver",.10,-.14,.7,6);
            case 8->new Profile("Pharah launcher",.068,-.166,.9,6);
            case 2->new Profile("Reaper dual shotguns",side*.40,-.25,.7,6);
            case 0x6e->new Profile("Soldier76 rifle",.17,-.17,.75,6);
            case 3->new Profile("Tracer dual pistols",side*.36,-.21,.65,6);
            case 0x15->new Profile("Bastion recon barrel",.19,-.17,.75,6);
            case 5->new Profile("Hanzo arrow tip",.02,-.13,.8,6);
            case 0x65->new Profile("Junkrat launcher",.19,-.18,.75,6);
            case 0xdd->new Profile("Mei nozzle",.18,-.16,.75,6);
            case 10->new Profile("Widowmaker barrel",.16,-.15,.75,6);
            case 6->new Profile("Torbjorn rivet muzzle",.16,-.18,.7,6);
            case 0x40->new Profile("Roadhog scrap muzzle",.17,-.18,.85,6);
            case 9->new Profile("Winston Tesla aperture",.18,-.20,.8,6);
            default->null;
        };
    }
    public static Vec offset(Profile p,Basis b,double fov,double aspect){
        if(p==null||b==null||!Double.isFinite(fov)||fov<20||fov>140||!Double.isFinite(aspect)||aspect<=0)throw new IllegalArgumentException("muzzle lens");
        double half=p.depth()*Math.tan(Math.toRadians(fov)/2);
        return b.forward().multiply(p.depth()).add(b.right().multiply(p.x()*half*aspect)).add(b.up().multiply(p.y()*half));
    }
    public static synchronized void remember(Scope next,String id,long hero,long wall,Vec start,Vec delta,Profile p){
        if(next==null||next.owner()==null||next.world()==0||next.model()==0||next.source()==0||id==null||p==null||wall<=retiredBefore)return;
        if(!next.equals(scope)){launches.clear();scope=next;}
        if(launches.containsKey(id))return;
        if(launches.size()>=2048)launches.entrySet().removeIf(e->wall-e.getValue().wall>6000);
        if(launches.size()>=2048)return;
        launches.put(id,new Launch(next,id,hero,wall,start,delta,p.converge()));remembered.computeIfAbsent(hero,k->new LongAdder()).increment();
        lastStart=start;lastMuzzle=start.add(delta);lastHero=hero;
    }
    public static void contact(String id,Vec point){var f=launches.get(id);if(f!=null&&f.scope.equals(scope))f.contact=point;}
    public static void alias(String from,String to){var f=launches.get(from);if(f!=null&&f.scope.equals(scope))launches.putIfAbsent(to,f);}
    public static String launchKey(String id){var f=launches.get(id);return f==null?id:f.id;}
    public static void reanchor(String id,Vec delta,long now){var f=launches.get(id);if(f!=null&&f.scope.equals(scope)){f.offset=delta;f.visualEpoch=now;lastStart=f.start;lastMuzzle=f.start.add(delta);lastHero=f.hero;}}
    /** The tank shell can already be metres along its unchanged physical ray
     * when its first render arrives. Start that first visible sample at the
     * aperture, then converge forward to the real ray/contact. Earlier trail
     * samples collapse onto that launch plane rather than piercing the body. */
    public static void reanchorVisible(String id,Vec firstVisible,Vec muzzle,Vec direction,long now){
        var f=launches.get(id);double length=Math.sqrt(direction.lengthSquared());
        if(f!=null&&f.scope.equals(scope)&&Double.isFinite(length)&&length>1e-7){
            f.visualStart=firstVisible;f.forward=direction.multiply(1/length);f.offset=muzzle.subtract(firstVisible);f.visualEpoch=now;
            lastStart=f.start;lastMuzzle=muzzle;lastHero=f.hero;
        }
    }
    public static synchronized void noteAnchor(String id,long hero,long resource,long nativeWall,long visualWall,double x,double y,double width,double height){
        var row=new JsonObject();row.addProperty("id",id);row.addProperty("hero",Long.toUnsignedString(hero,16));row.addProperty("resource",Long.toUnsignedString(resource,16));row.addProperty("nativeWall",nativeWall);row.addProperty("visualWall",visualWall);row.addProperty("phaseMs",visualWall-nativeWall);row.addProperty("x",x);row.addProperty("y",y);row.addProperty("width",width);row.addProperty("height",height);
        if(anchors.size()>=64)anchors.removeFirst();anchors.addLast(row);
    }
    public static Vec position(String id,Vec actual){
        return position(id,actual,System.currentTimeMillis());
    }
    public static Vec position(String id,Vec actual,long now){
        var f=launches.get(id);if(f==null||!f.scope.equals(scope))return actual;
        double age=Math.max(0,(now-f.visualEpoch)/1000.);if(age>=.26)return actual;
        double time=Math.clamp((age-.04)/.22,0,1),timeWeight=1-time*time*(3-2*time);
        var base=actual;double distance=Math.sqrt(actual.subtract(f.visualStart).lengthSquared()),end=f.converge,scale=1;
        if(f.forward!=null){
            var relative=actual.subtract(f.visualStart);double along=relative.x()*f.forward.x()+relative.y()*f.forward.y()+relative.z()*f.forward.z();
            distance=Math.max(0,along);if(along<0)base=actual.subtract(f.forward.multiply(along));
        }
        if(f.contact!=null){
            var relative=f.contact.subtract(f.visualStart);double hit=f.forward==null?Math.sqrt(relative.lengthSquared()):Math.max(0,relative.x()*f.forward.x()+relative.y()*f.forward.y()+relative.z()*f.forward.z());
            end=Math.min(end,hit);
            double ahead=f.forward==null?Math.sqrt(f.offset.lengthSquared()):Math.max(0,f.offset.x()*f.forward.x()+f.offset.y()*f.forward.y()+f.offset.z()*f.forward.z());
            scale=Math.min(1,hit/Math.max(.001,ahead*2));
        }
        if(end<1e-7||distance>=end)return actual;
        double t=Math.max(0,Math.min(1,distance/end)),weight=(1-t*t*(3-2*t))*scale*timeWeight;
        var visual=base.add(f.offset.multiply(weight));
        corrected.computeIfAbsent(f.hero,k->new LongAdder()).increment();lastReal=actual;lastVisual=visual;return visual;
    }
    public static synchronized void retire(long wall){retiredBefore=Math.max(retiredBefore,wall);launches.clear();scope=null;nativeReferenceOnly=measurementMask=false;}
    public static JsonObject diagnostics(){
        var o=new JsonObject();o.addProperty("nativeReferenceOnly",nativeReferenceOnly);o.addProperty("measurementMask",measurementMask);var rows=new JsonArray();for(long suffix:new long[]{0x29,0x42,8,2,0x6e,3,0x15,5,0x65,0xdd,10,6}){
            long hero=0x02e0000000000000L+suffix;var p=profile(hero,0,0);var row=new JsonObject();row.addProperty("hero",Long.toUnsignedString(hero,16));row.addProperty("profile",p.name());
            row.addProperty("x",p.x());row.addProperty("y",p.y());row.addProperty("depth",p.depth());row.addProperty("remembered",remembered.containsKey(hero)?remembered.get(hero).sum():0);row.addProperty("corrected",corrected.containsKey(hero)?corrected.get(hero).sum():0);rows.add(row);
        }o.add("heroes",rows);o.addProperty("activeLaunches",launches.size());o.addProperty("lastHero",Long.toUnsignedString(lastHero,16));
        synchronized(MuzzlePresentation.class){o.add("anchors",new Gson().toJsonTree(anchors));}
        o.add("calibration",MuzzleCalibration.diagnostics());
        var gson=new Gson();if(lastStart!=null){o.add("lastStart",gson.toJsonTree(lastStart));o.add("lastMuzzle",gson.toJsonTree(lastMuzzle));}if(lastReal!=null){o.add("lastReal",gson.toJsonTree(lastReal));o.add("lastVisual",gson.toJsonTree(lastVisual));}return o;
    }
}
