package lab.owmcguest;

import net.minecraft.client.MinecraftClient;
import net.minecraft.util.math.Vec3d;

/** Only actual original quick-melee TrackTargets Begin can admit a swing. */
public final class NativeMeleeController implements AutoCloseable {
    public static final NativeMeleeController INSTANCE=new NativeMeleeController();
    public static volatile String error="";
    private final NativeSkillReader reader=new NativeSkillReader(true);
    private final NativeDashPhase phase=new NativeDashPhase();

    public void tick(MinecraftClient client){
        var pose=HostPoseReader.INSTANCE.latest();
        if(pose==null||pose.flags()!=1||client.player==null||client.world==null||client.getServer()==null||!client.player.isAlive()){phase.invalidate();return;}
        long hero=NativeLocomotionController.INSTANCE.hero();
        if(!NativeMeleeRuntime.supported(hero)){phase.invalidate();return;}
        var state=reader.poll(pose,NativeLocomotionController.INSTANCE.modelId(),hero);error=reader.error;
        if(state==null){phase.invalidate();return;}
        var strike=state.entries().get("strike");long wall=System.currentTimeMillis();
        if(!phase.observe(state.source(),state.model(),strike.tick(),strike.active(),wall))return;
        var f=new org.joml.Vector3f(0,0,-1).rotate(pose.rotation());
        var forward=new Vec3d(f.x,f.y,f.z).normalize();
        var server=client.getServer();var owner=client.player.getUuid();
        long world=NativeWorldIdentity.of(server,client.world.getRegistryKey());
        var eye=client.player.getEyePos();
        var geometry=state.geometry();var center=eye.add(forward.multiply(geometry.offset()[2])).add(0,geometry.offset()[1]-geometry.eye(),0);
        server.execute(()->NativeMeleeRuntime.swing(server,owner,world,pose.generation(),hero,state.model(),strike.tick(),wall,eye,center,geometry.damage(),geometry.radius()));
        error="";
    }
    @Override public void close(){reader.close();phase.invalidate();error="";}
    void resetSession(){close();error="native session transition";}
}
