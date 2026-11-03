package lab.owmcguest;

import java.util.UUID;
import com.google.gson.JsonObject;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.entity.Entity;
import net.minecraft.particle.ParticleTypes;

/** Clean MC Wraith adapter. Original cast/Anim End own the lifecycle. Early
 *25% speed is separate from the later2018 increase to50%; no legacy lab. */
public final class NativeWraithRuntime {
    public record Scope(UUID owner,long world,long source,long model){}
    public record Phase(Scope scope,long begin,long wall,boolean active){}
    private static Scope observed;private static long lastBegin,started,starts,ended,protectedHits;
    private static Phase phase;
    private static net.minecraft.util.math.Vec3d modelAt;
    public static volatile Phase view;
    public static volatile String status="{\"active\":false}";
    private static boolean matches(ServerPlayerEntity p,Scope s){return s!=null&&p!=null&&p.isAlive()&&p.getUuid().equals(s.owner())
        &&NativeWorldIdentity.of(p.getServer(),p.getWorld().getRegistryKey())==s.world()
        &&NativeEliminationRuntime.sessionMatches(s.owner(),s.world(),NativeReaperRuntime.HERO,s.model(),s.source());}
    public static void refresh(MinecraftServer server,Phase next){
        long now=System.currentTimeMillis();var s=next.scope();var p=server.getPlayerManager().getPlayer(s.owner());
        if(!matches(p,s)||now-next.wall()>150||next.wall()>now+50)return;
        if(!s.equals(observed)){observed=s;lastBegin=next.begin();phase=null;publish();return;}
        if(!next.active()){if(phase!=null){ended++;phase=null;publish();}return;}
        if(next.begin()>lastBegin){lastBegin=next.begin();started=now;starts++;phase=next;}
        else if(phase!=null&&next.begin()==phase.begin())phase=next;
        publish();
    }
    public static boolean protects(Entity e){
        var f=phase;long now=System.currentTimeMillis();boolean protectedNow=e instanceof ServerPlayerEntity p&&f!=null&&matches(p,f.scope())&&now-f.wall()<=150&&now-started<=3300;
        if(protectedNow){protectedHits++;publish();}return protectedNow;
    }
    public static void tick(MinecraftServer server){
        var f=phase;if(f==null)return;long now=System.currentTimeMillis();var p=server.getPlayerManager().getPlayer(f.scope().owner());
        if(!matches(p,f.scope())||now-started>3300){ended++;phase=null;publish();return;}
        if(now-f.wall()>150)return;
        modelAt=p.getPos().add(0,.7,0);p.fallDistance=0;
        if(p.age%3==0)p.getServerWorld().spawnParticles(ParticleTypes.SMOKE,p.getX(),p.getY()+.35,p.getZ(),4,.2,.3,.2,.015);
        view=f;publish();
    }
    private static void publish(){view=phase;var o=new JsonObject();o.addProperty("active",phase!=null);o.addProperty("starts",starts);o.addProperty("ended",ended);o.addProperty("protectedHits",protectedHits);o.addProperty("speedMultiplier",1.25);o.addProperty("nativeBegin",phase==null?0:phase.begin());
        // integrator/models: only real state/geometry, never input-derived effects.
if(phase==null)modelAt=null;
        if(phase!=null&&modelAt!=null){
            var s=phase.scope();var f=OriginalEffectFrames.frame(s.owner(),s.world(),s.source(),s.model(),phase.wall());
            OriginalEffectFrames.body(f,"reaper-wraith",modelAt,new net.minecraft.util.math.Vec3d(1.3,1.3,1.3),.6f,true);o.add("models",f);
        }
        status=o.toString();}
    public static void resetSession(){phase=null;observed=null;lastBegin=0;publish();}
}
