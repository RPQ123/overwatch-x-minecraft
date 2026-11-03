package lab.owmcguest;

import net.minecraft.client.MinecraftClient;
import net.minecraft.util.math.Vec3d;

/** Keep the real E self push through Pharah's normal native flight import.
 * MC collision is still Entity.move; owner/world/focus changes clear impulses. */
public final class NativeConcussiveController {
    public static final NativeConcussiveController INSTANCE=new NativeConcussiveController();
    private NativeConcussiveRuntime.SelfCue current;private String consumed="";private int age=-1;
    private Vec3d velocity=Vec3d.ZERO;
    public Vec3d motion(MinecraftClient client){
        var host=HostPoseReader.INSTANCE.latest();var p=client.player;var cue=NativeConcussiveRuntime.selfCue;long now=System.currentTimeMillis();
        if(p==null||client.world==null||client.getServer()==null||host==null||!host.inputActive()||NativeLocomotionController.INSTANCE.hero()!=NativeConcussiveRuntime.HERO){reset();return Vec3d.ZERO;}
        long world=NativeWorldIdentity.of(client.getServer(),client.world.getRegistryKey()),model=NativeLocomotionController.INSTANCE.modelId();
        if(current!=null&&(current.world()!=world||current.model()!=model||current.source()!=host.generation()||!current.owner().equals(p.getUuid()))){reset();return Vec3d.ZERO;}
        String identity=cue==null?"":cue.source()+":"+cue.world()+":"+cue.model()+":"+cue.id();
        if(cue!=null&&!identity.equals(consumed)&&cue.world()==world&&cue.model()==model&&cue.source()==host.generation()&&cue.owner().equals(p.getUuid())&&now>=cue.wall()-50&&now-cue.wall()<=150){
            current=cue;consumed=identity;velocity=cue.velocity();
        }
        if(p.age==age)return Vec3d.ZERO;age=p.age;
        if(current==null||now-current.wall()>1500){velocity=Vec3d.ZERO;return velocity;}
        var result=velocity;velocity=velocity.multiply(.8);return result;
    }
    public void reset(){current=null;velocity=Vec3d.ZERO;age=-1;}
}
