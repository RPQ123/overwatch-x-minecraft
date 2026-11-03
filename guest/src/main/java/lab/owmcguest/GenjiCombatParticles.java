package lab.owmcguest;

import com.google.gson.JsonObject;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.Vec3d;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicLong;

/** Cosmetic vanilla MC feedback, admitted by the existing native combat guards.
 * Client sword presentation and server dash trail; neither admits damage. */
public final class GenjiCombatParticles {
    private static final AtomicLong swordEvents=new AtomicLong(),dashSegments=new AtomicLong(),particles=new AtomicLong();
    private static volatile long lastAnimationNode,lastAnimationTick,lastVisualQueueMs;
    public static volatile String status="{}";
    public record SwordPoint(Vec3d at,boolean spark){}
    public static List<SwordPoint> swordGeometry(Vec3d eye,Vec3d forward,Vec3d right,int node){
        if(node!=47&&node!=48)throw new IllegalArgumentException("original sword animation node");
        var points=new ArrayList<SwordPoint>(10);
        // User-approved vanilla white slash, with three staggered depths.
        // No colored dust. Opposite offset for the native alternating swings.
        for(int layer=0;layer<3;layer++){
            var at=eye.add(forward.multiply(1.6+layer*.4))
                .add(right.multiply((node==47?1:-1)*(layer-1)*.38)).add(0,-layer*.12,0);
            points.add(new SwordPoint(at,false));
        }
        // A few brief white sparks outline the cut without filling the view.
        for(int i=0;i<=6;i++){
            double t=i/6.0,angle=(t-.5)*1.65;
            var at=eye.add(forward.multiply(1.8*Math.cos(angle)))
                .add(right.multiply(1.8*Math.sin(angle)))
                .add(0,(node==47?1:-1)*(.5-t)*1.15,0);
            points.add(new SwordPoint(at,true));
        }
        return points;
    }
    public static void swordPresented(int count,int node,long tick,long queueMs){
        lastAnimationNode=node;lastAnimationTick=tick;lastVisualQueueMs=queueMs;
        swordEvents.incrementAndGet();particles.addAndGet(count);publish();
    }
    public static void dash(ServerWorld world,Vec3d from,Vec3d to){
        // The caller supplies only the bounded, actually traversed MC segment.
        int steps=Math.min(16,Math.max(1,(int)Math.ceil(from.distanceTo(to)/.5)));
        for(int i=1;i<=steps;i++){
            var at=from.lerp(to,i/(double)steps);
            world.spawnParticles(ParticleTypes.CLOUD,at.x,at.y,at.z,1,.06,.09,.06,.005);particles.incrementAndGet();
        }
        dashSegments.incrementAndGet();publish();
    }
    private static void publish(){
        var out=new JsonObject();out.addProperty("swordEvents",swordEvents.get());out.addProperty("dashSegments",dashSegments.get());
        out.addProperty("style","white-layered-sweep-v3-animation");out.addProperty("lastAnimationNode",lastAnimationNode);
        out.addProperty("lastAnimationTick",lastAnimationTick);out.addProperty("lastVisualQueueMs",lastVisualQueueMs);
        out.addProperty("particlesSent",particles.get());status=out.toString();
    }
    private GenjiCombatParticles(){}
}
