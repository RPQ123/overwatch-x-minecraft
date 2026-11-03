package lab.owmcguest;

import net.minecraft.client.MinecraftClient;
import net.minecraft.util.math.Vec3d;

public final class NativeRollController implements AutoCloseable {
    public static final NativeRollController INSTANCE=new NativeRollController();
    private final NativeRollReader reader=new NativeRollReader();
    private final NativeRollPhase phase=new NativeRollPhase();
    private Vec3d direction=Vec3d.ZERO;private long starts;private double requestedDistance;
    public static volatile String status="{\"ready\":false}";
    public void tick(MinecraftClient client){
        var host=HostPoseReader.INSTANCE.latest();var state=reader.poll(host);long now=System.currentTimeMillis();
        var p=client.player;
        if(state==null||p==null||client.world==null||!p.isAlive()||p.getAbilities().flying||p.hasVehicle())phase.invalidate();
        else if(phase.observe(state.source(),state.model(),state.tick(),state.active(),state.speed(),state.seconds(),now)){
            var local=NativeRollPhase.direction(host.inputActive()?host.movementBits():0,state.directional());
            var f=new org.joml.Vector3f(0,0,-1).rotate(host.rotation());
            var forward=new Vec3d(f.x,0,f.z).normalize();var right=new Vec3d(-forward.z,0,forward.x);
            if(local==null||forward.lengthSquared()<.99)phase.invalidate();
            else {direction=right.multiply(local[0]).add(forward.multiply(local[1]));starts++;requestedDistance=0;}
        }
        if(NativeDeadeyeController.movementLocked())discardMotion();
        var data=new com.google.gson.JsonObject();data.addProperty("ready",state!=null);data.addProperty("active",phase.active(now));
        data.addProperty("starts",starts);data.addProperty("requestedDistance",requestedDistance);data.addProperty("nativeTick",phase.tick());
        if(state!=null){data.addProperty("modelId",state.model());data.addProperty("speed",state.speed());data.addProperty("seconds",state.seconds());data.addProperty("directional",state.directional());}
        data.addProperty("error",reader.error);status=data.toString();
    }
    public Vec3d movement(Vec3d vanilla){
        if(NativeDeadeyeController.movementLocked()){discardMotion();return null;}
        double distance=phase.step(System.currentTimeMillis());if(distance==0)return null;
        requestedDistance+=distance;var v=direction.multiply(distance);
        // Preserve vanilla gravity and Entity.move's complete block-shape sweep.
        return new Vec3d(v.x,vanilla.y,v.z);
    }
    void discardMotion(){phase.discardMotion();direction=Vec3d.ZERO;}
    @Override public void close(){phase.invalidate();reader.close();}
    void resetSession(){close();status="{\"ready\":false,\"active\":false,\"error\":\"native session transition\"}";}
}
