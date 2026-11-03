package lab.owmcguest;

import java.util.UUID;
import com.google.gson.JsonObject;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.damage.DamageSource;
import net.minecraft.registry.RegistryKey;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.util.Identifier;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.RaycastContext;
import lab.owmcguest.NativeShotProtocol.*;

/** All game effects run on the integrated server; journal admission is the only shot source. */
public final class NativeCombatRuntime {
    private static final NativeShotSimulation simulation=new NativeShotSimulation();
    private static UUID owner;
    private static long worldId;
    private static long modelId;
    private static Batch lastBatch;
    private static Shot lastShot;
    private static JsonObject flashModels;
    public static volatile String status="{}";
    public record RocketView(long world,UUID player,Source source,long model,java.util.List<Shot> shots,java.util.List<Shot> flashes){}
    private static Source flashSource;
    private static final java.util.ArrayDeque<Shot> flashes=new java.util.ArrayDeque<>();
    public static volatile RocketView rocketView;
    public static volatile RocketView flashbangView;
    public static volatile RocketView concussiveView;
    public record Cue(UUID player,long world,Source source,Shot shot){}
    public static volatile Cue flashbangCue;
    public static volatile boolean rocketVisualsReady;
    public static volatile String rocketVisualsError="waiting for original Pharah assets";
    public static volatile long rocketModelsShown,rocketRenderFrames,muzzleFlashesShown,muzzleRenderFrames;
    public static volatile long helixModelsShown,helixRenderFrames;
    public static volatile long tankShellModelsShown,tankShellRenderFrames;
    private static Vec3d point(Vec v){return new Vec3d(v.x(),v.y(),v.z());}
    private static Vec vector(Vec3d v){return new Vec(v.x,v.y,v.z);}
    public static long accept(MinecraftServer server,UUID player,long expectedWorld,long nativeModel,Batch batch){
        var p=server.getPlayerManager().getPlayer(player);
        if(p==null||!p.isAlive()||NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())!=expectedWorld)throw new IllegalArgumentException("server world/player changed");
        if(owner!=null&&(!owner.equals(player)||worldId!=expectedWorld||modelId!=nativeModel)){simulation.clear();flashes.clear();flashSource=null;flashModels=null;HanzoSonicArrowRuntime.resetSession();HanzoArrowPresentation.reset();PharahBarragePresentation.reset();PharahRocketImpacts.reset();PharahConcussiveBursts.reset();}
        owner=player;worldId=expectedWorld;modelId=nativeModel;if(!batch.entries().isEmpty())lastBatch=batch;
        for(var entry:batch.entries())if(entry.shot()!=null)lastShot=entry.shot();
        if(!batch.source().equals(flashSource)){flashModels=null;flashes.clear();HanzoSonicArrowRuntime.resetSession();PharahBarragePresentation.reset();PharahRocketImpacts.reset();PharahConcussiveBursts.reset();flashSource=batch.source();}
        long cursor=simulation.admit(RocketFlightTuning.adapt(batch));
        var sonicScope=new HanzoSonicArrowState.Scope(owner,worldId,batch.source().hostGeneration(),modelId);
        for(var shot:simulation.admissions())HanzoSonicArrowRuntime.admit(server,sonicScope,shot);
        for(var shot:simulation.admissions())PharahBarragePresentation.launch(shot);
        for(var shot:simulation.admissions())if(shot.rocket()||shot.helix()){if(flashes.size()>=16)flashes.removeFirst();flashes.addLast(shot);}
        for(var shot:simulation.admissions())if(shot.effect()!=null&&shot.effect().kind()==2)flashbangCue=new Cue(owner,worldId,batch.source(),shot);
        tick(server);return cursor;
    }
    public static void replay(MinecraftServer server){if(lastBatch!=null)accept(server,owner,worldId,modelId,lastBatch);}
    public static void tick(MinecraftServer server){
        NativeFlashbangRuntime.tick(server);
        NativeDeadeyeRuntime.tick(server);
        final JsonObject[] beamModels={null};
        var p=owner==null?null:server.getPlayerManager().getPlayer(owner);
        if(p!=null&&p.isAlive()&&NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())==worldId){
            var world=p.getServerWorld();
            simulation.tick(new NativeShotSimulation.WorldAccess(){
                public void impact(Shot shot,NativeShotSimulation.Hit hit){
                    if(lastBatch!=null&&HanzoSonicArrowRuntime.isSonic(shot))HanzoSonicArrowRuntime.impact(server,
                        new HanzoSonicArrowState.Scope(owner,worldId,lastBatch.source().hostGeneration(),modelId),shot,hit);
                }
                public void present(Shot shot,Vec from,Vec to,NativeShotSimulation.Hit hit){
                    if(lastBatch!=null)HanzoArrowPresentation.segment(new HanzoArrowPresentation.Scope(owner,worldId,modelId,lastBatch.source()),shot,from,to,hit,server.getTicks());
                    if(shot.beam()&&lastBatch!=null){
                        var start=point(from);var end=point(to);
                        if(hit==null){
                            var clip=LoadedRayPrefix.clip(from,to,(x,z)->world.isChunkLoaded(new net.minecraft.util.math.BlockPos(x<<4,0,z<<4)));
                            end=start.lerp(end,clip.fraction());
                            var block=world.raycast(new RaycastContext(start,end,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
                            if(block.getType()!=HitResult.Type.MISS)end=block.getPos();
                        }
                        if(beamModels[0]==null)beamModels[0]=OriginalEffectFrames.frame(owner,worldId,lastBatch.source().hostGeneration(),modelId,shot.wallMs());
                        beamModels[0].addProperty("wall",Math.min(beamModels[0].get("wall").getAsLong(),shot.wallMs()));
                        if(beamModels[0].getAsJsonArray("effects").size()<128)OriginalEffectFrames.beam(beamModels[0],"winston-tesla",start,end,.08f,.8f);
                    }
                }
                public Vec aim(Shot shot){return NativeVisorRuntime.aim(p,worldId,lastBatch.source(),shot);}
                public java.util.List<NativeShotSimulation.Hit> beam(Vec origin,Vec direction,double range){
                    var start=point(origin);var forward=point(direction);var hits=new java.util.ArrayList<NativeShotSimulation.Hit>();
                    var seen=new java.util.HashSet<java.util.UUID>();
                    for(var entity:NativeDamageTargets.in(world,p,new Box(start,start).expand(range))){
                        var target=entity.getBoundingBox().getCenter();var delta=target.subtract(start);double distance=delta.length();
                        // Original TrackTargets: radius8 and cosine(fullAngle40/2).
                        if(distance>range||distance<1e-6||delta.dotProduct(forward)/distance<Math.cos(Math.toRadians(20)))continue;
                        if(!world.isChunkLoaded(entity.getBlockPos()))continue;
                        var wall=world.raycast(new RaycastContext(start,target,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
                        boolean blocked=wall.getType()!=HitResult.Type.MISS&&start.squaredDistanceTo(wall.getPos())+1e-5<start.squaredDistanceTo(target);
                        if(!blocked&&!seen.add(NativeDamageTargets.owner(entity).getUuid()))continue;
                        hits.add(new NativeShotSimulation.Hit(blocked,blocked?0:entity.getId(),vector(blocked?wall.getPos():target)));
                    }
                    return hits;
                }
                public NativeShotSimulation.Hit trace(Vec a,Vec b){
                    var start=point(a);var end=point(b);
                    // An unavailable far chunk cannot hide a nearer creature
                    // or wall. Clip the loaded prefix first, then resolve its
                    // nearest real collision without generating any chunk.
                    var clip=LoadedRayPrefix.clip(a,b,(x,z)->world.isChunkLoaded(new net.minecraft.util.math.BlockPos(x<<4,0,z<<4)));
                    if(clip.fraction()==0)return new NativeShotSimulation.Hit(true,0,a,false);
                    end=start.lerp(end,clip.fraction());
                    var block=world.raycast(new RaycastContext(start,end,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
                    double nearest=block.getType()==HitResult.Type.MISS?Double.POSITIVE_INFINITY:start.squaredDistanceTo(block.getPos());
                    var normal=block.getSide().getVector();
                    NativeShotSimulation.Hit result=block.getType()==HitResult.Type.MISS?null:new NativeShotSimulation.Hit(true,0,vector(block.getPos()),true,new Vec(normal.getX(),normal.getY(),normal.getZ()));
                    for(var entity:NativeDamageTargets.in(world,p,new Box(start,end).expand(.01))){
                        var box=entity.getBoundingBox();var intercept=box.contains(start)?java.util.Optional.of(start):box.raycast(start,end);
                        if(intercept.isPresent()&&start.squaredDistanceTo(intercept.get())<nearest){nearest=start.squaredDistanceTo(intercept.get());result=new NativeShotSimulation.Hit(false,entity.getId(),vector(intercept.get()));}
                    }
                    return result!=null?result:clip.complete()?null:new NativeShotSimulation.Hit(true,0,vector(end),false);
                }
                public double damage(NativeShotSimulation.Hit hit,double amount,long nativeEntity){
                    var result=NativeDamageTargets.projectileDamage(world,NativeDamageTargets.resolve(world,(int)hit.target()),p,amount);
                    NativeUltimateRuntime.credit(result.healthLost());return result.healthLost();
                }
                public double beamDamage(NativeShotSimulation.Hit hit,double amount){
                    var result=NativeDamageTargets.beamDamage(world,NativeDamageTargets.resolve(world,(int)hit.target()),p,amount);
                    NativeUltimateRuntime.credit(result.healthLost());return result.healthLost();
                }
                public double explode(Shot shot,NativeShotSimulation.Hit hit){
    if(lastBatch!=null)NativeRocketSelfImpulse.INSTANCE.impact(world,p,shot,hit,lastBatch.source(),modelId);
    double lost=NativeRocketExplosion.explode(world,p,shot,hit);
    PharahBarragePresentation.impact(shot,hit);
    PharahRocketImpacts.impact(shot,hit);
    NativeUltimateRuntime.credit(lost);
    return lost;
}
                public double armoryExplosion(Shot shot,NativeShotSimulation.Hit hit){return explode(shot,hit);}
                public double controlImpact(Shot shot,NativeShotSimulation.Hit hit){double lost=shot.effect().kind()==3?NativeConcussiveRuntime.detonate(world,p,shot,hit,lastBatch.source()):NativeFlashbangRuntime.detonate(world,p,shot,hit);if(shot.effect().kind()==2&&hit.loaded()&&lastBatch!=null){
                        flashModels=OriginalEffectFrames.frame(owner,worldId,lastBatch.source().hostGeneration(),modelId,System.currentTimeMillis());
                        OriginalEffectFrames.body(flashModels,"mccree-flash-impact",point(hit.point()),new Vec3d(1.2,1.2,1.2),.85f,true);
                    }
                    NativeUltimateRuntime.credit(lost);return lost;}
                public double weaponHit(Shot shot,NativeShotSimulation.Hit hit){
                    var entity=NativeDamageTargets.resolve(world,(int)hit.target());
                    boolean spray=NativeMeiFreezeRuntime.spray(shot);
                    var beforePosition=entity==null?null:entity.getPos();var beforeVelocity=entity==null?null:entity.getVelocity();
                    var result=NativeDamageTargets.projectileDamage(world,entity,p,shot.nativeDamage()*NativeShotSimulation.HP_SCALE);
                    // Continuous frost is not an ordinary MC bullet impulse.
                    // Preserve real teleport/removal reactions and existing motion.
                    if(spray&&entity!=null&&entity.isAlive()&&!entity.isRemoved()&&entity.getWorld()==world&&entity.getPos().squaredDistanceTo(beforePosition)<1e-8){entity.setVelocity(beforeVelocity);entity.velocityModified=true;}
                    NativeUltimateRuntime.credit(result.healthLost());
                    if(result.applied()&&lastBatch!=null)NativeMeiFreezeRuntime.contact(p,worldId,modelId,lastBatch.source().hostGeneration(),shot,entity);
                    return result.healthLost();
                }
            },System.currentTimeMillis());
        }else if(owner!=null){simulation.clear();owner=null;}
        var out=new JsonObject();out.addProperty("admitted",simulation.admitted);out.addProperty("rejected",simulation.rejected);out.addProperty("duplicates",simulation.duplicates);out.addProperty("blockHits",simulation.blockHits);out.addProperty("entityHits",simulation.entityHits);out.addProperty("damageApplied",simulation.damageApplied);out.addProperty("active",simulation.active());out.addProperty("cursor",simulation.cursor());
        if(lastShot!=null)out.add("lastShot",new com.google.gson.Gson().toJsonTree(lastShot));
        out.addProperty("lastShotRejection",simulation.lastRejection);
        if(p!=null){out.addProperty("eyeHeight",p.getEyeHeight(p.getPose()));out.addProperty("yaw",p.getYaw());out.addProperty("pitch",p.getPitch());}
        out.addProperty("crystalsDestroyed",NativeDamageTargets.crystalsDestroyed);
        out.add("flashbang",com.google.gson.JsonParser.parseString(NativeFlashbangRuntime.status));
        out.add("concussive",com.google.gson.JsonParser.parseString(NativeConcussiveRuntime.status));
        out.add("deadeye",com.google.gson.JsonParser.parseString(NativeDeadeyeRuntime.status));
        out.add("multipart",com.google.gson.JsonParser.parseString(OptionalMultipartTargets.status()));
        out.add("sonic",com.google.gson.JsonParser.parseString(HanzoSonicArrowRuntime.status));
        out.add("meiFreeze",com.google.gson.JsonParser.parseString(NativeMeiFreezeRuntime.status));
        out.addProperty("rocketExplosions",NativeRocketExplosion.detonations);
        out.addProperty("rocketBlocksDestroyed",NativeRocketExplosion.blocksDestroyed);
        out.addProperty("rocketDirectHealthLost",NativeRocketExplosion.directHealthLost);
        out.addProperty("rocketSplashHealthLost",NativeRocketExplosion.splashHealthLost);
        out.addProperty("tankShellExplosions",NativeRocketExplosion.tankDetonations);
        out.addProperty("genjiEliminations",NativeEliminationRuntime.eliminations);
        out.addProperty("visorLocks",NativeVisorRuntime.locks);
        out.addProperty("dashResetRequests",NativeEliminationRuntime.requests);
        out.addProperty("dashResetsApplied",NativeEliminationRuntime.applied);
        // Only actual admitted factory flights supply these cosmetic views.
        long visualNow=System.currentTimeMillis();flashes.removeIf(s->visualNow-s.wallMs()>180||visualNow<s.wallMs());
        rocketView=p!=null&&owner!=null&&lastBatch!=null?new RocketView(worldId,owner,lastBatch.source(),modelId,simulation.activeProjectiles().stream().filter(s->s.rocket()||s.barrage()||s.helix()||s.tankShell()).toList(),java.util.List.copyOf(flashes)):null;
        if(p!=null&&owner!=null&&lastBatch!=null)HanzoArrowPresentation.publish(new HanzoArrowPresentation.Scope(owner,worldId,modelId,lastBatch.source()),simulation.activeProjectiles(),server.getTicks(),visualNow);
        if(p!=null&&owner!=null&&lastBatch!=null){PharahBarragePresentation.publish(worldId,owner,lastBatch.source(),modelId,visualNow);PharahRocketImpacts.publish(worldId,owner,lastBatch.source(),modelId,visualNow);PharahConcussiveBursts.publish(worldId,owner,lastBatch.source(),modelId,visualNow);}else{PharahBarragePresentation.reset();PharahRocketImpacts.reset();PharahConcussiveBursts.reset();}
        out.addProperty("barragePresentationLaunches",PharahBarragePresentation.admitted);out.addProperty("barragePresentationImpacts",PharahBarragePresentation.detonated);
        flashbangView=p!=null&&owner!=null&&lastBatch!=null?new RocketView(worldId,owner,lastBatch.source(),modelId,simulation.activeProjectiles().stream().filter(s->s.effect()!=null&&s.effect().kind()==2).toList(),java.util.List.of()):null;
        concussiveView=p!=null&&owner!=null&&lastBatch!=null?new RocketView(worldId,owner,lastBatch.source(),modelId,simulation.activeProjectiles().stream().filter(s->s.effect()!=null&&s.effect().kind()==3).toList(),java.util.List.of()):null;
        out.addProperty("presentationMode",rocketVisualsReady?"pharah-original-model-and-effect-sprites":"pharah-original-assets-pending");
        out.addProperty("muzzleFlashesShown",muzzleFlashesShown);out.addProperty("muzzleRenderFrames",muzzleRenderFrames);
        out.addProperty("projectileModelsShown",rocketModelsShown);
        out.addProperty("projectileRenderFrames",rocketRenderFrames);
        out.addProperty("helixModelsShown",helixModelsShown);out.addProperty("helixRenderFrames",helixRenderFrames);
        out.addProperty("tankShellModelsShown",tankShellModelsShown);out.addProperty("tankShellRenderFrames",tankShellRenderFrames);
        out.addProperty("tankShellPresentation","restored-silver-shell/MC-size-and-speed-adapter; composed pixels pending");
        out.addProperty("pharahVisualError",rocketVisualsError);
        out.addProperty("originalEffectGraph",false);
        out.addProperty("projectileEntitiesSpawned",0);
        out.addProperty("projectileEntitiesActive",0);
        out.addProperty("tracersShown",0);
        out.addProperty("beamVisualSegments",0);
        out.add("boss",com.google.gson.JsonParser.parseString(NativeBossRuntime.status()));
        // Actual accepted beam segments/impact points only; no UI-time lease refresh.
        if(beamModels[0]!=null)out.add("models",beamModels[0]);
        else if(flashModels!=null&&owner!=null&&flashModels.get("owner").getAsString().equals(owner.toString())
            &&flashModels.get("world").getAsLong()==worldId&&flashModels.get("model").getAsLong()==modelId
            &&visualNow>=flashModels.get("wall").getAsLong()&&visualNow-flashModels.get("wall").getAsLong()<=200)out.add("models",flashModels);
        NativeCombatScene.addStatus(server,out);status=out.toString();
    }
    public static void close(){HanzoSonicArrowRuntime.resetSession();HanzoArrowPresentation.reset();PharahBarragePresentation.reset();PharahRocketImpacts.reset();PharahConcussiveBursts.reset();concussiveView=null;NativeConcussiveRuntime.resetSession();flashbangCue=null;flashbangView=null;NativeFlashbangRuntime.resetSession();NativeDeadeyeRuntime.resetSession();NativeBuildersLab.cleanup();NativeCombatScene.cleanup();OptionalMultipartTargets.reset();simulation.clear();owner=null;lastBatch=null;rocketView=null;flashes.clear();flashSource=null;flashModels=null;}
    public static void resetSession(){HanzoSonicArrowRuntime.resetSession();HanzoArrowPresentation.reset();PharahBarragePresentation.reset();PharahRocketImpacts.reset();PharahConcussiveBursts.reset();concussiveView=null;NativeConcussiveRuntime.resetSession();flashbangCue=null;flashbangView=null;rocketView=null;simulation.clear();owner=null;worldId=0;lastBatch=null;lastShot=null;flashes.clear();flashSource=null;flashModels=null;status="{\"admitted\":0,\"rejected\":0,\"duplicates\":0,\"blockHits\":0,\"entityHits\":0,\"damageApplied\":0.0,\"active\":false,\"cursor\":0}";}
}
