package lab.owmcguest;

import java.util.UUID;
import com.google.gson.JsonObject;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.util.math.*;
import net.minecraft.world.RaycastContext;
import net.minecraft.util.hit.HitResult;
import net.minecraft.particle.ParticleTypes;

/** Original Death Blossom phase to real MC area damage.8m/3s are pinned beta
 * declarations.170OW HP/s is an explicit historical-rules adapter, corroborated
 * by Blizzard's pre-March2024 value, not claimed extracted2015 server damage. */
public final class NativeReaperRuntime {
    public static final long HERO=0x02e0000000000002L;
    public record Scope(UUID owner,long world,long source,long model){}
    public record Phase(Scope scope,long begin,long wall,boolean active,double radius,double seconds){}
    public record View(Scope scope,long begin,long wall,Vec3d at){}
    private static Phase phase;private static Scope observed;private static long baseline,lastBegin,started;
    private static int ticks;private static long starts,ended,contacts;private static double damage;
    public static volatile View view;
    public static volatile String status="{\"active\":false}";
    private static boolean matches(ServerPlayerEntity p,Scope s){return s!=null&&p!=null&&p.isAlive()&&p.getUuid().equals(s.owner())
        &&NativeWorldIdentity.of(p.getServer(),p.getWorld().getRegistryKey())==s.world()
        &&NativeEliminationRuntime.sessionMatches(s.owner(),s.world(),HERO,s.model(),s.source());}
    public static void refresh(MinecraftServer server,Phase next){
        long now=System.currentTimeMillis();var s=next.scope();var p=server.getPlayerManager().getPlayer(s.owner());
        if(!matches(p,s)||now-next.wall()>150||next.wall()>now+50||next.radius()!=8||next.seconds()!=3)return;
        if(!s.equals(observed)){observed=s;baseline=lastBegin=next.begin();phase=null;publish();return;}
        if(!next.active()){if(phase!=null){ended++;phase=null;publish();}return;}
        if(next.begin()>lastBegin){lastBegin=next.begin();started=now;ticks=0;starts++;phase=next;}
        else if(phase!=null&&next.begin()==phase.begin())phase=next;
        publish();
    }
    public static void tick(MinecraftServer server){
        var f=phase;if(f==null)return;long now=System.currentTimeMillis();var p=server.getPlayerManager().getPlayer(f.scope().owner());
        if(!matches(p,f.scope())||now-started>3100||ticks>=60){ended++;phase=null;publish();return;}
        if(now-f.wall()>150)return; // Pause, never catch up damage after a source stall.
        var w=p.getServerWorld();var origin=p.getPos().add(0,1,0);ticks++;
        var seen=new java.util.HashSet<UUID>();
        for(var part:NativeDamageTargets.in(w,p,p.getBoundingBox().expand(8))){
            var victim=NativeDamageTargets.owner(part);if(seen.contains(victim.getUuid())||!w.isChunkLoaded(part.getBlockPos()))continue;
            var box=part.getBoundingBox();var closest=new Vec3d(Math.clamp(origin.x,box.minX,box.maxX),Math.clamp(origin.y,box.minY,box.maxY),Math.clamp(origin.z,box.minZ,box.maxZ));
            if(closest.squaredDistanceTo(origin)>64)continue;
            boolean visible=false;
            for(double y:new double[]{.2,.5,.8}){
                var at=new Vec3d((box.minX+box.maxX)*.5,box.minY+box.getLengthY()*y,(box.minZ+box.maxZ)*.5);
                var clip=LoadedRayPrefix.clip(new NativeShotProtocol.Vec(origin.x,origin.y,origin.z),new NativeShotProtocol.Vec(at.x,at.y,at.z),(x,z)->w.isChunkLoaded(new BlockPos(x<<4,0,z<<4)));
                if(clip.complete()&&w.raycast(new RaycastContext(origin,at,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p)).getType()==HitResult.Type.MISS){visible=true;break;}
            }
            if(!visible)continue;seen.add(victim.getUuid());
            double actual=NativeDamageTargets.beamDamage(w,part,p,.85).healthLost();damage+=actual;
            if(actual>0){contacts++;if(ticks%4==0)w.spawnParticles(ParticleTypes.CRIT,closest.x,closest.y,closest.z,2,.08,.1,.08,0);}
        }
        // Sparse gray spiral, not an opaque smoke wall or fake damage source.
        if(ticks%3==0)for(int i=0;i<5;i++){double a=ticks*.4+i*Math.PI*2/5,r=.5+ticks%6*.12;w.spawnParticles(ParticleTypes.ASH,p.getX()+Math.cos(a)*r,p.getY()+.5+i*.12,p.getZ()+Math.sin(a)*r,1,.01,.03,.01,0);}
        // Q damage never credits the next Q, including delayed final contacts.
        view=new View(f.scope(),f.begin(),now,p.getPos());publish();
    }
    private static void publish(){var o=new JsonObject();o.addProperty("active",phase!=null);o.addProperty("starts",starts);o.addProperty("ended",ended);o.addProperty("contacts",contacts);o.addProperty("damage",damage);o.addProperty("ticks",ticks);o.addProperty("radius",8);o.addProperty("damagePerSecondMc",17);o.addProperty("damagePolicy","historical170OW/s compatibility, not extracted2015 server damage");if(phase==null)view=null;
        // integrator/models: only real state/geometry, never input-derived effects.
if(phase!=null&&view!=null&&phase.scope().equals(view.scope())){
            var s=phase.scope();var f=OriginalEffectFrames.frame(s.owner(),s.world(),s.source(),s.model(),Math.min(phase.wall(),view.wall()));
            OriginalEffectFrames.body(f,"reaper-blossom",view.at().add(0,.9,0),new Vec3d(2,2,2),.65f,true);o.add("models",f);
        }
        status=o.toString();}
    public static void resetSession(){phase=null;observed=null;baseline=lastBegin=0;publish();}
}
