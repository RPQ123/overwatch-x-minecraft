package lab.owmcguest;

import java.util.UUID;
import com.google.gson.JsonObject;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.util.math.*;
import net.minecraft.util.hit.*;
import net.minecraft.world.RaycastContext;
import net.minecraft.block.Blocks;
import net.minecraft.particle.ParticleTypes;

/** MC owns the real35m ground query/teleport, while original confirm and
 * departure/arrival animations own admission/timing. No key-created warp. */
public final class NativeShadowRuntime {
    public record Scope(UUID owner,long world,long source,long model){}
    public record Phase(Scope scope,long aim,boolean aiming,long confirm,long out,boolean departing,long in,boolean arriving,long wall){}
    public record View(Scope scope,long aim,long confirm,long wall,Vec3d destination,boolean valid,int phase){}
    public record Receipt(Scope scope,long aim,long confirm,long wall,int phase){}
    private record Pending(long aim,long confirm,long wall,Vec3d origin,Vec3d destination,boolean seenDeparture,boolean moved){}
    private static Scope observed;private static long lastConfirm,starts,moves,refused,cancelled;
    private static Phase source;private static Pending pending;
    public static volatile View view;public static volatile Receipt receipt;
    public static volatile String status="{\"aiming\":false,\"casting\":false}";
    private static boolean matches(ServerPlayerEntity p,Scope s){return s!=null&&p!=null&&p.isAlive()&&p.getUuid().equals(s.owner())
        &&NativeWorldIdentity.of(p.getServer(),p.getWorld().getRegistryKey())==s.world()
        &&NativeEliminationRuntime.sessionMatches(s.owner(),s.world(),NativeReaperRuntime.HERO,s.model(),s.source());}
    private static boolean safe(ServerPlayerEntity p,Vec3d at){
        var w=p.getServerWorld();var box=p.getBoundingBox().offset(at.subtract(p.getPos()));
        if(!w.getWorldBorder().contains(box)||at.y<w.getBottomY()||at.y+box.getLengthY()>w.getTopY()||!w.isSpaceEmpty(p,box))return false;
        for(int x=(int)Math.floor(box.minX)>>4;x<=(int)Math.floor(box.maxX)>>4;x++)for(int z=(int)Math.floor(box.minZ)>>4;z<=(int)Math.floor(box.maxZ)>>4;z++)if(!w.isChunkLoaded(new BlockPos(x<<4,(int)at.y,z<<4)))return false;
        var below=BlockPos.ofFloored(at.add(0,-.03,0));var floor=w.getBlockState(below);
        return !floor.getCollisionShape(w,below).isEmpty()&&floor.getFluidState().isEmpty()&&!floor.isOf(Blocks.MAGMA_BLOCK)&&!floor.isOf(Blocks.CACTUS)&&!floor.isOf(Blocks.CAMPFIRE)&&!floor.isOf(Blocks.SOUL_CAMPFIRE)&&!floor.isOf(Blocks.POWDER_SNOW);
    }
    private static Vec3d query(ServerPlayerEntity p){
        var w=p.getServerWorld();var eye=p.getEyePos();var end=eye.add(p.getRotationVec(1).multiply(35));
        var clip=LoadedRayPrefix.clip(new NativeShotProtocol.Vec(eye.x,eye.y,eye.z),new NativeShotProtocol.Vec(end.x,end.y,end.z),(x,z)->w.isChunkLoaded(new BlockPos(x<<4,0,z<<4)));
        var hit=w.raycast(new RaycastContext(eye,eye.lerp(end,clip.fraction()),RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
        if(hit.getType()!=HitResult.Type.BLOCK||hit.getSide()!=Direction.UP)return null;
        var at=hit.getPos().add(0,.01,0);return eye.squaredDistanceTo(at)<=35*35&&safe(p,at)?at:null;
    }
    public static void refresh(MinecraftServer server,Phase next){
        long now=System.currentTimeMillis();var p=server.getPlayerManager().getPlayer(next.scope().owner());
        if(!matches(p,next.scope())||now-next.wall()>150||next.wall()>now+50)return;
        if(!next.scope().equals(observed)){
            observed=next.scope();lastConfirm=next.confirm();pending=null;
            // A transient unknown pose cancels gameplay, but must not erase
            // this exact cast's terminal cleanup before its pawn returns.
            // A definite new world/model/source cannot use that old receipt.
            if(receipt!=null&&!receipt.scope().equals(observed))receipt=null;
            source=next;publish();return;
        }
        source=next;
        if(pending==null&&receipt!=null){
            if(next.aiming()&&next.aim()>receipt.confirm())receipt=null;
            else if(receipt.phase()>=2&&next.confirm()>=receipt.confirm()){
                // A blocked/finished MC result is a cleanup disposition. Keep
                // transporting it after a sharing violation, within this same
                // live scope. This cannot re-admit a warp: only phase1 admits
                // native departure, and only the pending MC record can move.
                receipt=new Receipt(observed,receipt.aim(),receipt.confirm(),now,receipt.phase());
            }
        }
        if(pending==null){
            var dest=next.aiming()?query(p):null;
            view=next.aiming()?new View(observed,next.aim(),0,now,dest,dest!=null,0):null;
            if(next.confirm()>lastConfirm){
                lastConfirm=next.confirm();
                if(next.aiming()&&next.confirm()>=next.aim()&&dest!=null){
                    pending=new Pending(next.aim(),next.confirm(),now,p.getPos(),dest,false,false);starts++;
                    receipt=new Receipt(observed,next.aim(),next.confirm(),now,1);
                    p.getServerWorld().spawnParticles(ParticleTypes.LARGE_SMOKE,p.getX(),p.getY()+.7,p.getZ(),15,.3,.5,.3,.025);
                }else refused++;
            }
        }
        if(pending!=null){
            var q=pending;
            if(next.departing()&&next.out()>=q.confirm())q=new Pending(q.aim(),q.confirm(),q.wall(),q.origin(),q.destination(),true,q.moved());
            // Actual departure animation End, after seeing this cast's Begin.
            if(!q.moved()&&q.seenDeparture()&&!next.departing()&&next.out()>=q.confirm()){
                if(p.getPos().squaredDistanceTo(q.origin())<4&&safe(p,q.destination())){
                    p.requestTeleport(q.destination().x,q.destination().y,q.destination().z);p.setVelocity(Vec3d.ZERO);p.fallDistance=0;moves++;
                    p.getServerWorld().spawnParticles(ParticleTypes.LARGE_SMOKE,p.getX(),p.getY()+.7,p.getZ(),25,.35,.6,.35,.03);
                    q=new Pending(q.aim(),q.confirm(),q.wall(),q.origin(),q.destination(),true,true);
                }else{cancelled++;pending=null;receipt=new Receipt(observed,q.aim(),q.confirm(),now,3);view=null;publish();return;}
            }
            pending=q;int phase=q.moved()?2:1;receipt=new Receipt(observed,q.aim(),q.confirm(),now,phase);
            view=new View(observed,q.aim(),q.confirm(),now,q.destination(),true,phase);
            if(q.moved()&&!next.arriving()&&next.in()>=q.confirm()){pending=null;view=null;}
        }
        publish();
    }
    public static void tick(MinecraftServer server){
        if(observed==null)return;long now=System.currentTimeMillis();var p=server.getPlayerManager().getPlayer(observed.owner());
        if(!matches(p,observed)){resetSession();return;}
        if(pending!=null&&now-pending.wall()>5000){var q=pending;pending=null;view=null;receipt=new Receipt(observed,q.aim(),q.confirm(),now,3);cancelled++;publish();}
        if(source==null||now-source.wall()>150){view=null;return;}
        if(pending==null&&view!=null&&view.valid()&&p.age%5==0){var at=view.destination();for(int i=0;i<8;i++){double a=i*Math.PI/4;p.getServerWorld().spawnParticles(ParticleTypes.SMOKE,at.x+Math.cos(a)*.5,at.y+.08,at.z+Math.sin(a)*.5,1,0,.02,0,0);}}
    }
    private static void publish(){var o=new JsonObject();o.addProperty("aiming",source!=null&&source.aiming());o.addProperty("casting",pending!=null);o.addProperty("valid",view!=null&&view.valid());o.addProperty("phase",view==null?0:view.phase());o.addProperty("receiptPhase",receipt==null?0:receipt.phase());o.addProperty("receiptWall",receipt==null?0:receipt.wall());o.addProperty("starts",starts);o.addProperty("moves",moves);o.addProperty("refused",refused);o.addProperty("cancelled",cancelled);o.addProperty("range",35);if(view!=null&&view.destination()!=null){o.addProperty("x",view.destination().x);o.addProperty("y",view.destination().y);o.addProperty("z",view.destination().z);}
        // integrator/models: only real state/geometry, never input-derived effects.
if(source!=null&&pending!=null&&source.scope().equals(observed)){
            var f=OriginalEffectFrames.frame(observed.owner(),observed.world(),observed.source(),observed.model(),source.wall());
            OriginalEffectFrames.body(f,pending.moved()?"reaper-shadow-end":"reaper-shadow-start",
                (pending.moved()?pending.destination():pending.origin()).add(0,.7,0),new Vec3d(1.2,1.2,1.2),.7f,true);
            o.add("models",f);
        }
        status=o.toString();}
    public static void resetSession(){
        if(pending!=null&&observed!=null){
            receipt=new Receipt(observed,pending.aim(),pending.confirm(),System.currentTimeMillis(),pending.moved()?2:3);
            if(!pending.moved())cancelled++;
        }
        observed=null;source=null;pending=null;view=null;lastConfirm=0;publish();
    }
    /** Hard stop/test cleanup cannot retain a disposition for another server. */
    public static void clear(){observed=null;source=null;pending=null;view=null;receipt=null;lastConfirm=0;publish();}
}
