package lab.owmcguest;
import java.util.*;
/** Retire only pre-travel bars; original server ADD is the re-admission oracle. */
public final class BossHudTravelScope {
    private static final Set<UUID> retired=new HashSet<>(),pending=new HashSet<>();
    private static volatile long epoch;
    public static long epoch(){return epoch;}
    public static boolean visible(UUID id){return !retired.contains(id);}
    public static void begin(Collection<UUID> bars){
        pending.clear();for(var id:bars)if(retired.add(id))pending.add(id);epoch++;
    }
    public static void finish(boolean success){if(!success)retired.removeAll(pending);pending.clear();epoch++;}
    public static void added(UUID id){retired.remove(id);pending.remove(id);epoch++;}
    public static void removed(UUID id){retired.remove(id);pending.remove(id);epoch++;}
    public static int retired(){return retired.size();}
    public static void reset(){retired.clear();pending.clear();epoch++;}
}
