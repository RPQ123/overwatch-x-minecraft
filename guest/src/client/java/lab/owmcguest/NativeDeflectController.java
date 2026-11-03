package lab.owmcguest;
import net.minecraft.client.MinecraftClient;
import net.minecraft.util.math.Vec3d;

/** Native E state controls admission; no key or copied duration starts Deflect. */
final class NativeDeflectController implements AutoCloseable {
    static final NativeDeflectController INSTANCE=new NativeDeflectController();
    private final NativeSkillReader reader=new NativeSkillReader();
    static volatile String error="waiting for native Deflect";
    void tick(MinecraftClient client){
        var host=HostPoseReader.INSTANCE.latest();var p=client.player;long hero=NativeLocomotionController.INSTANCE.hero();
        if(p==null||!p.isAlive()||client.world==null||client.getServer()==null||host==null||host.flags()!=1||hero!=0x02e0000000000029L)return;
        var state=reader.poll(host,NativeLocomotionController.INSTANCE.modelId(),hero);error=reader.error;if(state==null)return;
        var phase=state.entries().get("deflect");var boxes=phase.active()?reader.deflectBoxes():java.util.List.<double[]>of();
        if(boxes==null){error=reader.error;return;}
        var f=new org.joml.Vector3f(0,0,-1).rotate(host.rotation());var r=new org.joml.Vector3f(1,0,0).rotate(host.rotation());var u=new org.joml.Vector3f(0,1,0).rotate(host.rotation());
        var forward=new Vec3d(f.x,f.y,f.z).normalize();var right=new Vec3d(r.x,r.y,r.z).normalize();var up=new Vec3d(u.x,u.y,u.z).normalize();
        var server=client.getServer();var owner=p.getUuid();var eye=p.getEyePos();long world=NativeWorldIdentity.of(server,client.world.getRegistryKey()),wall=System.currentTimeMillis();
        server.execute(()->NativeDeflectRuntime.refresh(owner,world,host.generation(),state.model(),phase.tick(),phase.active(),eye,forward,right,up,boxes,wall));error="";
    }
    @Override public void close(){reader.close();error="";}
    void resetSession(){close();error="native session transition";}
}
