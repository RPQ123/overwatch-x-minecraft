package lab.owmcguest;
import java.util.*;
import java.util.concurrent.atomic.AtomicLong;
import net.minecraft.server.MinecraftServer;
/** The native cooldown is authoritative. A real placement waits for its
 * original assignment/readback, then commits the already validated MC plan. */
public final class PlacementCooldowns {
    public record Scope(UUID owner,long world,long source,long model,int kind){}
    public record Pending(Scope scope,long sequence,long token,long wall){}
    private record Bound(double remaining,long wall){}
    private record Entry(Pending view,Runnable commit){}
    private static final Map<Scope,Bound> observed=new HashMap<>();private static final Map<Scope,Entry> pending=new HashMap<>();
    private static final AtomicLong sequences=new AtomicLong(System.currentTimeMillis()*1024);
    public static volatile List<Pending> requests=List.of();public static volatile String status="{}";
    private static long commits,failures,timeouts;
    public static long nextSequence(){return sequences.updateAndGet(n->Math.max(n+1,System.currentTimeMillis()*1024));}
    public static void observe(Scope scope,double remaining,long wall){if(!Double.isFinite(remaining)||remaining<0||remaining>120)return;observed.put(scope,new Bound(remaining,wall));publish();}
    public static boolean available(Scope scope){var b=observed.get(scope);return b!=null&&System.currentTimeMillis()-b.wall()<=500&&b.remaining()<=.001&&!pending.containsKey(scope);}
    public static boolean request(Scope scope,long token,Runnable commit){
        if(token<=0||pending.containsKey(scope)||pending.size()>=4)return false;
        var view=new Pending(scope,nextSequence(),token,System.currentTimeMillis());pending.put(scope,new Entry(view,commit));publish();return true;
    }
    public static void receipt(Scope scope,PlacementActionProtocol.Receipt receipt){
        var e=pending.get(scope);if(e==null||e.view().sequence()!=receipt.sequence()||receipt.kind()!=scope.kind())return;
        pending.remove(scope);if(receipt.phase()==1){observe(scope,receipt.remaining(),receipt.wall());e.commit().run();commits++;}else failures++;publish();
    }
    public static void cancel(Scope scope){pending.remove(scope);observed.remove(scope);publish();}
    public static void tick(MinecraftServer server){long now=System.currentTimeMillis();pending.entrySet().removeIf(e->{if(now-e.getValue().view().wall()>1000){timeouts++;return true;}return false;});observed.entrySet().removeIf(e->now-e.getValue().wall()>2000);publish();}
    public static void reset(){pending.clear();observed.clear();publish();}
    private static void publish(){requests=pending.values().stream().map(Entry::view).toList();var o=new com.google.gson.JsonObject();o.addProperty("pending",pending.size());o.addProperty("committed",commits);o.addProperty("failures",failures);o.addProperty("timeouts",timeouts);o.addProperty("meiSeconds",10);o.addProperty("torbSeconds",8);status=o.toString();}
}
