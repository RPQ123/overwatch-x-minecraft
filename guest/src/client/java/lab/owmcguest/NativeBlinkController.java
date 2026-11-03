package lab.owmcguest;

import net.minecraft.client.MinecraftClient;
import net.minecraft.entity.MovementType;
import net.minecraft.util.math.Vec3d;

/** Original Tracer teleport execution; MC sweeps its own actual block shapes. */
public final class NativeBlinkController implements AutoCloseable {
    public static final NativeBlinkController INSTANCE=new NativeBlinkController();
    private final NativeFlightReader reader=new NativeFlightReader(2);
    private final NativeBlinkPhase phase=new NativeBlinkPhase();
    private long world,model,starts;private double requestedDistance,actualDistance;
    public static volatile String status="{\"ready\":false}";
    public boolean requested(MinecraftClient client){
        var p=client.player;var host=HostPoseReader.INSTANCE.latest();
        return p!=null&&client.world!=null&&client.getServer()!=null&&p.isAlive()&&!p.getAbilities().flying&&!p.hasVehicle()
            &&host!=null&&host.flags()==1&&NativeLocomotionController.INSTANCE.hero()==0x02e0000000000003L&&NativeLocomotionController.INSTANCE.modelId()!=0;
    }
    public void travel(MinecraftClient client){
        if(!requested(client)){resetSession();return;}
        long nextWorld=NativeWorldIdentity.of(client.getServer(),client.world.getRegistryKey()),nextModel=NativeLocomotionController.INSTANCE.modelId();
        if(world!=nextWorld||model!=nextModel){phase.reset();world=nextWorld;model=nextModel;}
        var motion=reader.poll(HostPoseReader.INSTANCE.latest(),world,model);
        if(motion==null){phase.reset();status="{\"ready\":false,\"error\":"+new com.google.gson.Gson().toJson(reader.error)+"}";return;}
        var delta=phase.observe(motion.total(),motion.captures(),motion.actionTick());
        if(delta!=null){
            var p=client.player;var before=p.getPos();var velocity=p.getVelocity();
            p.move(MovementType.SELF,new Vec3d(delta[0],0,delta[2]));p.setVelocity(velocity);
            starts++;requestedDistance=Math.hypot(delta[0],delta[2]);actualDistance=p.getPos().subtract(before).horizontalLength();
        }
        status="{\"ready\":true,\"starts\":"+starts+",\"nativeCaptures\":"+motion.captures()+",\"actionTick\":"+motion.actionTick()+",\"requestedDistance\":"+requestedDistance+",\"actualDistance\":"+actualDistance+"}";
    }
    @Override public void close(){reader.close();phase.reset();world=model=0;}
    void resetSession(){close();status="{\"ready\":false}";}
}
