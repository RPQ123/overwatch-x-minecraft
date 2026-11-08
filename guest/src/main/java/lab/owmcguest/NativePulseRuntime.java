package lab.owmcguest;

import java.util.UUID;
import com.google.gson.JsonObject;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.entity.Entity;
import net.minecraft.util.math.*;
import net.minecraft.util.hit.HitResult;
import net.minecraft.world.RaycastContext;
import net.minecraft.world.explosion.Explosion;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.sound.*;

/** MC sticky/fuse adapter: original beta15m/s,30m/s²,5impact,400blast/2-4m.
 * One second AFTER contact is a documented compatibility policy, not an
 * authenticated meaning of the beta's anonymous explosion field. */
public final class NativePulseRuntime {
    public static final long HERO=0x02e0000000000003L;
    public record Deployment(UUID owner,long world,long source,long model,long nativeTick,long wall,Vec3d at,Vec3d velocity){}
    public record View(UUID owner,long world,long source,long model,long nativeTick,Vec3d at,boolean attached,int remaining,long wall,Vec3d normal,long launchedWall,boolean blockAttached){}
    private static Deployment active;
    private static Deployment lastDeployment;
    private static boolean suspended;
    private static long suspendedWall;
    private static Vec3d at,velocity,offset;
    private static Vec3d attachmentNormal=new Vec3d(0,1,0);
    private static Entity target;
    private static boolean attached,blockAttached;
    private static int age,fuse;
    private static long lastTick,launches,sticks,explosions,cancelled,refused;
    private static double damage;private static long terrainBursts,terrainBlocks;private static String terrainError="";
    public static volatile View view;
    public static volatile String status="{\"active\":false}";
    private static boolean matches(MinecraftServer server,Deployment d){
        var p=server.getPlayerManager().getPlayer(d.owner());return p!=null&&p.isAlive()
            &&NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())==d.world()
            &&NativeEliminationRuntime.sessionMatches(d.owner(),d.world(),HERO,d.model(),d.source());
    }
    public static void deploy(MinecraftServer server,Deployment d){
        long now=System.currentTimeMillis();
        if(d==null||!matches(server,d)||now-d.wall()>150||d.wall()>now+50||d.nativeTick()<=lastTick
            ||Math.abs(d.velocity().lengthSquared()-225)>.001||!Double.isFinite(d.at().lengthSquared())){refused++;return;}
        var p=server.getPlayerManager().getPlayer(d.owner());
        if(p.getEyePos().squaredDistanceTo(d.at())>4||!p.getServerWorld().isChunkLoaded(BlockPos.ofFloored(d.at()))){refused++;return;}
        active=lastDeployment=d;lastTick=d.nativeTick();suspended=false;at=d.at();velocity=d.velocity();attachmentNormal=velocity.normalize().multiply(-1);attached=false;blockAttached=false;target=null;age=fuse=0;launches++;publish();
    }
    /** Server thread, AFTER NativeEliminationRuntime.configure. Same-pawn input
     * confirmation preserves a real in-flight bomb and its anti-replay cursor.
     * Definitive identity changes still cancel; unknown identity only suspends
     * for the existing 150ms freshness budget, without advancing damage/fuse.
     */
    public static void revalidateSession(UUID owner,long world,long hero,long model,long source){
        if(owner==null||world==0||hero==0||model==0||source==0){
            if(!suspended){suspended=true;suspendedWall=System.currentTimeMillis();}view=null;publish();return;
        }
        var last=lastDeployment;
        if(last!=null&&(!last.owner().equals(owner)||last.world()!=world||hero!=HERO||last.model()!=model||last.source()!=source))resetSession();
        suspended=false;publish();
    }
    public static void tick(MinecraftServer server){
        var d=active;if(d==null)return;
        if(suspended){if(System.currentTimeMillis()-suspendedWall>150)clear(true);return;}
        if(!matches(server,d)){clear(true);return;}
        var p=server.getPlayerManager().getPlayer(d.owner());var w=p.getServerWorld();age++;
        if(!w.isChunkLoaded(BlockPos.ofFloored(at))||at.y<w.getBottomY()||age>120){clear(true);return;}
        if(attached){
            if(target!=null){
                var next=target.getPos().add(offset);
                // Death/removal detaches at the last loaded point; a teleport
                // never drags an old explosion into another world or chunk.
                if(target.isRemoved()||!target.isAlive()||target.getWorld()!=w||next.squaredDistanceTo(at)>256)target=null;
                else at=next;
            }
            if(--fuse<=0){detonate(p);clear(false);return;}
            if(fuse%5==0){w.spawnParticles(ParticleTypes.ELECTRIC_SPARK,at.x,at.y,at.z,3,.08,.08,.08,.01);w.playSound(null,at.x,at.y,at.z,SoundEvents.BLOCK_NOTE_BLOCK_HAT.value(),SoundCategory.PLAYERS,.7f,1.2f+(20-fuse)*.04f);}
        }else{
            // Four swept substeps per server tick avoid tunnelling at15m/s.
            for(int i=0;i<4&&!attached;i++){
                var next=at.add(velocity.multiply(.0125)).add(0,-.5*30*.0125*.0125,0);
                if(!w.isChunkLoaded(BlockPos.ofFloored(next))){clear(true);return;}
                var block=w.raycast(new RaycastContext(at,next,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
                Vec3d hit=block.getType()==HitResult.Type.MISS?null:block.getPos();double distance=hit==null?Double.POSITIVE_INFINITY:at.squaredDistanceTo(hit);Entity victim=null;
                for(var e:NativeDamageTargets.in(w,p,new Box(at,next).expand(.12))){
                    if(!w.isChunkLoaded(e.getBlockPos()))continue;
                    var box=e.getBoundingBox().expand(.08);var contact=box.contains(at)?java.util.Optional.of(at):box.raycast(at,next);
                    if(contact.isPresent()&&at.squaredDistanceTo(contact.get())<distance){hit=contact.get();distance=at.squaredDistanceTo(hit);victim=e;}
                }
                velocity=velocity.add(0,-30*.0125,0);
                if(hit!=null){
                    attached=true;fuse=20;sticks++;at=hit;
                    if(victim!=null){
                        target=victim;blockAttached=false;offset=hit.subtract(victim.getPos());attachmentNormal=velocity.normalize().multiply(-1);
                        double actual=NativeDamageTargets.projectileDamage(w,victim,p,.5).healthLost();damage+=actual;
                    }else{blockAttached=true;attachmentNormal=Vec3d.of(block.getSide().getVector());at=at.add(attachmentNormal.multiply(.04));}
                    w.playSound(null,at.x,at.y,at.z,SoundEvents.BLOCK_RESPAWN_ANCHOR_CHARGE,SoundCategory.PLAYERS,.6f,1.6f);
                }else at=next;
            }
            if(!attached&&age>=100){clear(true);return;}
        }
        publish();
    }
    private static void detonate(ServerPlayerEntity p){
        var w=p.getServerWorld();double actual=0;var victims=new java.util.LinkedHashMap<Entity,Double>();
        for(int x=(int)Math.floor(at.x-4)>>4;x<=((int)Math.floor(at.x+4)>>4);x++)
            for(int z=(int)Math.floor(at.z-4)>>4;z<=((int)Math.floor(at.z+4)>>4);z++)
                if(!w.isChunkLoaded(new BlockPos(x<<4,(int)at.y,z<<4))){refused++;return;}
        for(var e:NativeDamageTargets.in(w,p,new Box(at,at).expand(4))){
            if(!w.isChunkLoaded(e.getBlockPos()))continue;var b=e.getBoundingBox();
            var closest=new Vec3d(Math.clamp(at.x,b.minX,b.maxX),Math.clamp(at.y,b.minY,b.maxY),Math.clamp(at.z,b.minZ,b.maxZ));
            double scale=NativeBlastFalloff.scale(closest.distanceTo(at),2,4,.2);if(scale<=0)continue;
            // A normal swept first contact can sit on an entity surface;
            // vanilla exposure handles partial and full solid cover.
            double amount=40*scale*Explosion.getExposure(at,e);if(amount<=0)continue;
            var owner=NativeDamageTargets.owner(e);var old=victims.keySet().stream().filter(v->NativeDamageTargets.owner(v)==owner).findFirst();
            if(old.isPresent())victims.merge(old.get(),amount,Math::max);else victims.put(e,amount);
        }
        for(var e:victims.entrySet())actual+=NativeDamageTargets.explosionDamage(w,e.getKey(),p,e.getValue()).healthLost();
        // Respect normal creative invulnerability. Survival self damage is
        // real MC damage; no blanket creative health overwrite is introduced.
        if(!p.isCreative()&&p.getPos().squaredDistanceTo(at)<16)NativeDamageTargets.explosionDamage(w,p,p,40*NativeBlastFalloff.scale(p.getBoundingBox().getCenter().distanceTo(at),2,4,.2)*Explosion.getExposure(at,p));
        // Ultimate damage never earns the next ultimate, even when the short
        // native throw animation ended before this delayed detonation.
        damage+=actual;explosions++;
        PulseBurstPresentation.launch(active,at);
        // Keep original cover/self damage decisions before the user-custom hole.
        var terrain=NativeTerrainBurst.explode(w,p,at,NativeExplosionTerrain.PULSE);
        if(terrain.applied()){terrainBursts++;terrainBlocks+=terrain.blocksDestroyed();}terrainError=terrain.rejection();
        w.spawnParticles(ParticleTypes.EXPLOSION_EMITTER,at.x,at.y,at.z,1,0,0,0,0);
        w.spawnParticles(ParticleTypes.ELECTRIC_SPARK,at.x,at.y,at.z,65,.7,.7,.7,.3);
        w.playSound(null,at.x,at.y,at.z,SoundEvents.ENTITY_GENERIC_EXPLODE,SoundCategory.PLAYERS,1.2f,1.3f);
    }
    private static void publish(){
        var d=active;var o=new JsonObject();o.addProperty("active",d!=null);o.addProperty("launches",launches);o.addProperty("sticks",sticks);o.addProperty("explosions",explosions);o.addProperty("cancelled",cancelled);o.addProperty("refused",refused);o.addProperty("damage",damage);o.addProperty("terrainBursts",terrainBursts);o.addProperty("terrainBlocks",terrainBlocks);o.addProperty("terrainStrength",NativeExplosionTerrain.PULSE);o.addProperty("terrainError",terrainError);o.addProperty("attached",attached);o.addProperty("remainingTicks",fuse);o.addProperty("ageTicks",age);
        o.addProperty("suspended",suspended);
        if(d!=null){o.addProperty("nativeTick",d.nativeTick());o.addProperty("x",at.x);o.addProperty("y",at.y);o.addProperty("z",at.z);o.addProperty("target",target==null?0:target.getId());view=suspended?null:new View(d.owner(),d.world(),d.source(),d.model(),d.nativeTick(),at,attached,fuse,System.currentTimeMillis(),attachmentNormal,d.wall(),blockAttached);}else view=null;
        status=o.toString();
    }
    private static void clear(boolean cancel){if(cancel)cancelled++;active=null;target=null;attached=false;fuse=0;publish();}
    public static void resetSession(){if(active!=null)clear(true);PulseBurstPresentation.reset();lastTick=0;lastDeployment=null;suspended=false;publish();}
}
