package lab.owmcguest;
import java.util.UUID;
import net.minecraft.util.math.Vec3d;
/** Published only after the existing real MC explosion has resolved. */
public final class PulseBurstPresentation {
    public record Cue(UUID owner,long world,long source,long model,long tick,Vec3d at,long wall){}
    public static volatile Cue cue;public static long emitted;
    public static void launch(NativePulseRuntime.Deployment d,Vec3d at){if(d!=null){cue=new Cue(d.owner(),d.world(),d.source(),d.model(),d.nativeTick(),at,System.currentTimeMillis());emitted++;}}
    public static void reset(){cue=null;}
}
