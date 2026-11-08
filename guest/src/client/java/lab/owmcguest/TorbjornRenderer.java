package lab.owmcguest;

import java.util.*;
import com.google.gson.JsonObject;
import net.fabricmc.fabric.api.client.rendering.v1.*;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.*;
import net.minecraft.util.math.*;
import org.joml.Quaternionf;

/** Original private Torbjorn meshes and depth-tested volumetric tracking beams.
 * Flight positions come exclusively from accepted server sweep histories. */
final class TorbjornRenderer {
    private static final RenderLayer BEAM=RenderLayer.getLightning();
    private static final Set<String> seen=new HashSet<>();private static Object source;
    private static long primaryFrames,pelletFrames,packFrames,landedFrames,laserFrames,turretFrames,previewFrames,scrapFrames;
    private static float lastPackYaw;private static double lastPackLift;
    private static final Map<String,Long> visualEpochs=new HashMap<>();private static final Map<Long,Long> turretEpochs=new HashMap<>();
    private static Object turretSource;private static long turretBulletFrames,fireFrames;private static double lastVisualSpeed;
    private static final long[] laserLevels=new long[4];private static long modelsShown,errors;
    private static String error="";private static long phaseWall;private static int activePrimary,activePellets,activePacks,activeLaser,lastLevel;
    private static double lastSpeed,lastDelay;private static Vec3d lastAt,lastLaserStart,lastLaserEnd;
    static void register(){WorldRenderEvents.AFTER_ENTITIES.register(TorbjornRenderer::render);}
    static long turretFrames(){return turretFrames;}
    private static boolean current(MinecraftClient c,UUID owner,long world,long model,long generation,long wall){
        var h=HostPoseReader.INSTANCE.latest();var loc=NativeLocomotionController.INSTANCE;long now=System.currentTimeMillis();
        return c.world!=null&&c.player!=null&&c.player.isAlive()&&c.getServer()!=null&&owner.equals(c.player.getUuid())
            &&loc.hero()==TorbRivetPresentation.HERO&&loc.modelId()==model&&h!=null&&h.flags()==1&&h.inputActive()
            &&h.generation()==generation&&now-wall>=-50&&now-wall<=250&&NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey())==world;
    }
    private static Vec3d point(NativeShotProtocol.Vec p){return new Vec3d(p.x(),p.y(),p.z());}
    private static void render(WorldRenderContext ctx){
        if(!Boolean.getBoolean("owmc.frameExport")||ctx.matrixStack()==null)return;
        var c=MinecraftClient.getInstance();int primary=0,pellets=0,packs=0,laser=0,level=0;boolean trace=false;
        if(c.world==null||c.player==null)return;
        var m=ctx.matrixStack();var cam=ctx.camera().getPos();var buffers=c.getBufferBuilders().getEntityVertexConsumers();
        try{
            var flightView=TorbRivetPresentation.view;
            if(flightView!=null){var s=flightView.scope();
                if(current(c,s.owner(),s.world(),s.model(),s.source().hostGeneration(),flightView.wall())){
                    if(!s.equals(source)){source=s;seen.clear();visualEpochs.clear();}
                    var body=OriginalMeshPack.get("torb-rivet");
                    if(body!=null&&!MuzzlePresentation.nativeReferenceOnly)for(var f:flightView.flights()){
                        long now=System.currentTimeMillis();long epoch=visualEpochs.computeIfAbsent(f.id(),k->now);
                        var sample=TorbRivetPresentation.sample(f,now,epoch);if(sample==null)continue;
                        var at=point(sample.at());if(!c.world.isChunkLoaded(BlockPos.ofFloored(at)))continue;
                        var dir=sample.direction();float scale=f.kind()==TorbRivetPresentation.Kind.PELLET?T3VisualTuning.PELLET_SCALE:T3VisualTuning.RIVET_SCALE;
                        for(var position:TorbRivetPresentation.bodies(f,sample)){var bodyAt=NativeMuzzleOrigins.at(f.id(),point(position));
                        m.push();try{m.translate(bodyAt.x-cam.x,bodyAt.y-cam.y,bodyAt.z-cam.z);
                            m.multiply(new Quaternionf().rotationTo(1,0,0,(float)dir.x(),(float)dir.y(),(float)dir.z()));
                            m.scale(scale,scale,scale);m.translate(0,-.0238885768,0); // center the original D0D's Y bounds
                            if(MuzzlePresentation.measurementMask)body.drawObjectId(buffers,m.peek());
                            else body.draw(buffers,m.peek(),LightmapTextureManager.MAX_LIGHT_COORDINATE);
                        }finally{m.pop();}}
                        var shown=NativeMuzzleOrigins.at(f.id(),at);var direction=point(dir);
                        if(!MuzzlePresentation.measurementMask){
                            if(PharahProjectileGlow.draw(ctx,shown,direction,sample.age(),T3VisualTuning.FIRE_SCALE))fireFrames++;
                            if(sample.age()<.07){var first=f.segments().getFirst().from();PharahProjectileGlow.draw(ctx,NativeMuzzleOrigins.at(f.id(),point(first)),direction,sample.age(),.45f);}
                            trace|=beam(ctx,buffers,NativeMuzzleOrigins.at(f.id(),point(sample.trailFrom())),shown,.012,255,153,48,165);
                        }
                        if(f.kind()==TorbRivetPresentation.Kind.RIVET){primary++;primaryFrames++;}else{pellets++;pelletFrames++;}
                        if(seen.add(f.id()))modelsShown++;lastAt=shown;lastSpeed=sample.nativeSpeed();lastVisualSpeed=sample.visualSpeed();lastDelay=epoch-f.nativeWall();
                    }
                    visualEpochs.keySet().retainAll(flightView.flights().stream().map(TorbRivetPresentation.Flight::id).toList());
                }
            }
            var v=NativeTorbjornRuntime.visualView;
            if(v!=null){var s=v.scope();if(current(c,s.owner(),s.world(),s.model(),s.source(),v.wall())){
                var preview=NativeTorbjornRuntime.previewView;
                if(preview!=null&&System.currentTimeMillis()-preview.wall()<=250){var body=OriginalMeshPack.get("torb-turret-1");if(body!=null){
                    m.push();try{m.translate(preview.at().x-cam.x,preview.at().y-cam.y,preview.at().z-cam.z);m.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(-preview.yaw()));
                        body.draw(buffers,m.peek(),LightmapTextureManager.MAX_LIGHT_COORDINATE,preview.valid()?.2f:1,.75f,preview.valid()?1:.2f,.55f);
                        previewFrames++;
                    }finally{m.pop();}
                }}
                var t=v.turret();if(t!=null){level=t.level();var body=OriginalMeshPack.get("torb-turret-"+level);
                    if(body!=null){m.push();try{m.translate(t.at().x-cam.x,t.at().y-cam.y,t.at().z-cam.z);
                        m.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(-t.yaw()));body.draw(buffers,m.peek(),WorldRenderer.getLightmapCoordinates(c.world,BlockPos.ofFloored(t.at()).up()));
                    }finally{m.pop();}turretFrames++;}
                    if(t.target()!=null&&t.muzzle()!=null&&t.targetId()!=null){
                        trace|=beam(ctx,buffers,t.muzzle(),t.target(),.026,255,15,10,40);
                        trace|=beam(ctx,buffers,t.muzzle(),t.target(),.010,255,32,20,235);
                        laser=1;laserFrames++;laserLevels[level]++;lastLaserStart=t.muzzle();lastLaserEnd=t.target();
                    }
                }
                if(!v.packs().isEmpty()){var body=OriginalMeshPack.get("torb-armor");if(body!=null)for(var p:v.packs()){
                    long now=System.currentTimeMillis();var at=PickupRenderMotion.at(p.previous(),p.at(),p.motionWall(),now);var motion=PickupKinematics.pose(p.landed(),p.attracting(),p.age(),p.motionWall(),now);
                    lastPackYaw=(float)motion.yaw();lastPackLift=motion.lift();
                    var shown=p.landed()||p.attracting()?at:NativeMuzzleOrigins.at(p.visualId(),at);
                    m.push();try{m.translate(shown.x-cam.x,shown.y-cam.y+.02+motion.lift(),shown.z-cam.z);
                        m.multiply(RotationAxis.POSITIVE_Y.rotationDegrees((float)motion.yaw()));
                        body.draw(buffers,m.peek(),LightmapTextureManager.MAX_LIGHT_COORDINATE);
                    }finally{m.pop();}packs++;packFrames++;if(p.landed())landedFrames++;
                }}
                if(!v.scrap().isEmpty()){var body=OriginalMeshPack.get("torb-scrap");if(body!=null)for(var drop:v.scrap()){
                    long now=System.currentTimeMillis();var at=PickupRenderMotion.at(drop.previous(),drop.at(),drop.motionWall(),now);
                    var pose=PickupKinematics.pose(drop.landed(),drop.attracting(),drop.age(),drop.motionWall(),now);
                    m.push();try{m.translate(at.x-cam.x,at.y-cam.y+pose.lift(),at.z-cam.z);m.multiply(RotationAxis.POSITIVE_Y.rotationDegrees((float)pose.yaw()));
                        body.draw(buffers,m.peek(),LightmapTextureManager.MAX_LIGHT_COORDINATE);
                        scrapFrames++;
                    }finally{m.pop();}
                }}
            }}
            var bullets=TorbTurretShots.view;
            if(bullets!=null){var s=bullets.scope();if(current(c,s.owner(),s.world(),s.model(),s.source(),bullets.wall())){
                if(!s.equals(turretSource)){turretSource=s;turretEpochs.clear();}var body=OriginalMeshPack.get("torb-rivet");
                if(body!=null)for(var shot:bullets.shots()){
                    long now=System.currentTimeMillis();long epoch=turretEpochs.computeIfAbsent(shot.id(),k->now);double age=(now-epoch)/1000.,length=shot.from().distanceTo(shot.to());
                    if(length<.01||age>length/TorbTurretShots.SPEED+.08)continue;var direction=shot.to().subtract(shot.from()).normalize();
                    var at=shot.from().add(direction.multiply(Math.min(length,age*TorbTurretShots.SPEED)));
                    if(!c.world.isChunkLoaded(BlockPos.ofFloored(at)))continue;m.push();try{m.translate(at.x-cam.x,at.y-cam.y,at.z-cam.z);
                        m.multiply(new Quaternionf().rotationTo(1,0,0,(float)direction.x,(float)direction.y,(float)direction.z));m.scale(T3VisualTuning.TURRET_SCALE,T3VisualTuning.TURRET_SCALE,T3VisualTuning.TURRET_SCALE);m.translate(0,-.0238885768,0);
                        body.draw(buffers,m.peek(),LightmapTextureManager.MAX_LIGHT_COORDINATE);
                    }finally{m.pop();}turretBulletFrames++;
                    if(PharahProjectileGlow.draw(ctx,at,direction,age,T3VisualTuning.FIRE_SCALE))fireFrames++;
                    var tail=shot.from().add(direction.multiply(Math.max(0,age*TorbTurretShots.SPEED-.8)));trace|=beam(ctx,buffers,tail,at,.012,255,153,48,165);
                }turretEpochs.keySet().retainAll(bullets.shots().stream().map(TorbTurretShots.Shot::id).toList());
            }}
            if(trace)buffers.draw(BEAM);error="";
        }catch(RuntimeException e){errors++;error=e.toString();}
        activePrimary=primary;activePellets=pellets;activePacks=packs;activeLaser=laser;lastLevel=level;phaseWall=System.currentTimeMillis();
    }
    private static boolean beam(WorldRenderContext ctx,VertexConsumerProvider.Immediate buffers,Vec3d from,Vec3d to,double radius,int r,int g,int b,int alpha){
        var d=to.subtract(from);if(d.lengthSquared()<1e-10)return false;d=d.normalize();
        var side=d.crossProduct(new Vec3d(0,1,0));if(side.lengthSquared()<1e-8)side=d.crossProduct(new Vec3d(1,0,0));side=side.normalize().multiply(radius);
        var up=d.crossProduct(side).normalize().multiply(radius);var cam=ctx.camera().getPos();var start=from.subtract(cam);var end=to.subtract(cam);
        var corners=List.of(side.add(up),side.negate().add(up),side.negate().subtract(up),side.subtract(up));
        var v=buffers.getBuffer(BEAM);var matrix=ctx.matrixStack().peek().getPositionMatrix();
        for(int i=0;i<4;i++)for(var p:List.of(start.add(corners.get(i)),end.add(corners.get(i)),end.add(corners.get((i+1)%4)),start.add(corners.get((i+1)%4))))
            v.vertex(matrix,(float)p.x,(float)p.y,(float)p.z).color(r,g,b,alpha);
        return true;
    }
    static JsonObject diagnostics(){
        var o=new JsonObject();o.addProperty("primaryFrames",primaryFrames);o.addProperty("pelletFrames",pelletFrames);o.addProperty("modelsShown",modelsShown);
        o.addProperty("packFrames",packFrames);o.addProperty("landedFrames",landedFrames);o.addProperty("turretFrames",turretFrames);o.addProperty("laserFrames",laserFrames);
        o.addProperty("previewFrames",previewFrames);o.addProperty("lastPackYaw",lastPackYaw);o.addProperty("lastPackLift",lastPackLift);
        o.addProperty("turretBulletFrames",turretBulletFrames);o.addProperty("fireFrames",fireFrames);o.addProperty("lastVisualSpeed",lastVisualSpeed);o.addProperty("fireError",PharahProjectileGlow.error);
        for(int i=1;i<=3;i++)o.addProperty("laserLevel"+i,laserLevels[i]);o.addProperty("phaseWall",phaseWall);
        o.addProperty("activePrimary",activePrimary);o.addProperty("activePellets",activePellets);o.addProperty("activePacks",activePacks);o.addProperty("activeLaser",activeLaser);o.addProperty("level",lastLevel);
        o.addProperty("lastSegmentSpeed",lastSpeed);o.addProperty("presentationDelayMs",lastDelay);o.addProperty("segments",TorbRivetPresentation.segments);o.addProperty("contacts",TorbRivetPresentation.contacts);
        o.addProperty("errors",errors);o.addProperty("error",error);o.addProperty("refused",TorbRivetPresentation.refused);
        if(lastAt!=null)o.add("lastProjectilePosition",new com.google.gson.Gson().toJsonTree(new double[]{lastAt.x,lastAt.y,lastAt.z}));
        if(lastLaserStart!=null){o.add("laserStart",new com.google.gson.Gson().toJsonTree(new double[]{lastLaserStart.x,lastLaserStart.y,lastLaserStart.z}));o.add("laserEnd",new com.google.gson.Gson().toJsonTree(new double[]{lastLaserEnd.x,lastLaserEnd.y,lastLaserEnd.z}));}
        o.addProperty("scrapFrames",scrapFrames);o.addProperty("pickupFullbright",true);o.addProperty("pickupLight",LightmapTextureManager.MAX_LIGHT_COORDINATE);
        for(var name:List.of("torb-rivet","torb-armor","torb-scrap","torb-turret-1","torb-turret-2","torb-turret-3"))o.add(name,OriginalMeshPack.diagnostics(name));
        return o;
    }
}
