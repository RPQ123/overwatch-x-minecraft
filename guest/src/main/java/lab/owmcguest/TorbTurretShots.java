package lab.owmcguest;
import java.util.*;
import net.minecraft.util.math.Vec3d;
/** Cosmetic-only shots after the real turret's existing instantaneous damage. */
public final class TorbTurretShots {
    public static final double SPEED=35;
    public record Shot(long id,Vec3d from,Vec3d to,long wall,int level){}
    public record View(NativeTorbjornRuntime.Scope scope,long wall,List<Shot> shots){}
    private static final List<Shot> shots=new ArrayList<>();private static long sequence;
    public static volatile View view;
    public static void launch(NativeTorbjornRuntime.Scope scope,Vec3d from,Vec3d to,int level){
        long now=System.currentTimeMillis();if(shots.size()>=128)shots.removeFirst();shots.add(new Shot(++sequence,from,to,now,level));publish(scope,now);
    }
    public static void publish(NativeTorbjornRuntime.Scope scope,long now){
        shots.removeIf(s->now-s.wall()>(s.from().distanceTo(s.to())/SPEED*1000)+330);
        view=scope==null?null:new View(scope,now,List.copyOf(shots));
    }
    public static void reset(){shots.clear();view=null;}
}
