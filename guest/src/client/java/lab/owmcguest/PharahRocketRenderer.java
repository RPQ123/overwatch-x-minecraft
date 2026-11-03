package lab.owmcguest;

import com.google.gson.*;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import net.fabricmc.fabric.api.client.rendering.v1.*;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.*;
import net.minecraft.client.texture.*;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.*;
import net.minecraft.world.RaycastContext;
import org.joml.Quaternionf;

/** Restored 2026-10-24 private OW mesh/sprites; 25% larger body is an MC adaptation. */
final class PharahRocketRenderer {
    private static final Identifier BODY=Identifier.of("owmcguest","private/pharah-body"),TAIL=Identifier.of("owmcguest","private/pharah-exhaust");
    private static final Identifier FLAME=Identifier.of("owmcguest","private/pharah-flame"),FLARE=Identifier.of("owmcguest","private/pharah-flare"),GLOW=Identifier.of("owmcguest","private/pharah-glow");
    private static float[] positions,normals,uv;private static int[] indices;
    private static boolean attempted;private static NativeShotProtocol.Source source;private static final Set<Long> seen=new HashSet<>();
    private static final Set<Long> flashed=new HashSet<>();
    private record LaunchFrame(PharahRocketPresentation.Basis basis,double fov,double aspect){}
    private static final Map<Long,LaunchFrame> launches=new HashMap<>();
    private static long launchWorld,launchModel;
    static void register(){WorldRenderEvents.AFTER_ENTITIES.register(PharahRocketRenderer::render);}
    private static void load(MinecraftClient client)throws Exception{
        var root=PrivateAssetPaths.assets().resolve("owmc-pharah-projectile");
        var manifest=JsonParser.parseString(Files.readString(root.resolve("provenance.json"))).getAsJsonObject().getAsJsonObject("files");
        for(String name:List.of("rocket.json","body.png","exhaust.png","flame.png","flare.png","glow.png")){
            var file=root.resolve(name);if(Files.size(file)>4*1024*1024)throw new IllegalArgumentException("rocket asset size");
            var hash=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(file)));
            if(!hash.equals(manifest.get(name).getAsString()))throw new IllegalArgumentException("rocket asset hash: "+name);
        }
        var data=JsonParser.parseString(Files.readString(root.resolve("rocket.json"))).getAsJsonObject();
        if(data.get("schema").getAsInt()!=1||!data.get("resource").getAsString().equals("0400000000000033")||!data.get("model").getAsString().equals("00000000084C.00C"))throw new IllegalArgumentException("original rocket identity");
        var gson=new Gson();positions=gson.fromJson(data.get("positions"),float[].class);normals=gson.fromJson(data.get("normals"),float[].class);uv=gson.fromJson(data.get("uv"),float[].class);indices=gson.fromJson(data.get("indices"),int[].class);
        if(positions.length<3||positions.length>12000||positions.length%3!=0||normals.length!=positions.length||uv.length!=positions.length/3*2||indices.length>24000||indices.length%3!=0)throw new IllegalArgumentException("rocket mesh bounds");
        for(float x:positions)if(!Float.isFinite(x)||Math.abs(x)>.2)throw new IllegalArgumentException("unscaled rocket position");
        for(float x:normals)if(!Float.isFinite(x)||Math.abs(x)>1.001)throw new IllegalArgumentException("rocket normal");
        for(float x:uv)if(!Float.isFinite(x)||Math.abs(x)>16)throw new IllegalArgumentException("rocket UV");
        for(int x:indices)if(x<0||x>=positions.length/3)throw new IllegalArgumentException("rocket index");
        try(var in=Files.newInputStream(root.resolve("body.png"))){client.getTextureManager().registerTexture(BODY,new NativeImageBackedTexture(NativeImage.read(in)));}
        try(var in=Files.newInputStream(root.resolve("exhaust.png"))){client.getTextureManager().registerTexture(TAIL,new NativeImageBackedTexture(NativeImage.read(in)));}
        for(var asset:Map.of("flame.png",FLAME,"flare.png",FLARE,"glow.png",GLOW).entrySet())try(var in=Files.newInputStream(root.resolve(asset.getKey()))){client.getTextureManager().registerTexture(asset.getValue(),new NativeImageBackedTexture(NativeImage.read(in)));}
        NativeCombatRuntime.rocketVisualsReady=true;NativeCombatRuntime.rocketVisualsError="";
    }
    private static void vertex(VertexConsumer v,MatrixStack.Entry m,float x,float y,float z,float u,float w,float nx,float ny,float nz,int light){
        v.vertex(m.getPositionMatrix(),x,y,z).color(255,255,255,255).texture(u,w).overlay(OverlayTexture.DEFAULT_UV).light(light).normal(m,nx,ny,nz);
    }
    private static void effectVertex(VertexConsumer v,MatrixStack.Entry m,float x,float y,float z,float u,float w,int r,int g,int b,int a){
        v.vertex(m.getPositionMatrix(),x,y,z).color(r*a/255,g*a/255,b*a/255,a).texture(u,w).overlay(OverlayTexture.DEFAULT_UV).light(LightmapTextureManager.MAX_LIGHT_COORDINATE).normal(m,0,0,1);
    }
    private static void billboard(MatrixStack matrices,VertexConsumer buffer,WorldRenderContext ctx,Vec3d at,float radius,int r,int g,int b,int a){
        var camera=ctx.camera().getPos();matrices.push();matrices.translate(at.x-camera.x,at.y-camera.y,at.z-camera.z);matrices.multiply(ctx.camera().getRotation());var m=matrices.peek();
        effectVertex(buffer,m,-radius,-radius,0,0,1,r,g,b,a);effectVertex(buffer,m,radius,-radius,0,1,1,r,g,b,a);effectVertex(buffer,m,radius,radius,0,1,0,r,g,b,a);effectVertex(buffer,m,-radius,radius,0,0,0,r,g,b,a);matrices.pop();
    }
    private static void render(WorldRenderContext ctx){
        var client=MinecraftClient.getInstance();
        if(!Boolean.getBoolean("owmc.frameExport"))return;
        if(!attempted){attempted=true;try{load(client);}catch(Exception e){NativeCombatRuntime.rocketVisualsError=e.toString();}}
        var view=NativeCombatRuntime.rocketView;var host=HostPoseReader.INSTANCE.latest();
        if(!NativeCombatRuntime.rocketVisualsReady||client.world==null||client.player==null||client.getServer()==null||view==null||host==null||!host.inputActive()||host.flags()!=1||!client.player.isAlive()||view.source().pid()!=host.pid()||view.source().hostGeneration()!=host.generation()||!client.player.getUuid().equals(view.player())||NativeLocomotionController.INSTANCE.hero()!=0x02e0000000000008L||view.world()!=NativeWorldIdentity.of(client.getServer(),client.world.getRegistryKey()))return;
        long model=NativeLocomotionController.INSTANCE.modelId();if(view.model()!=model)return;
        if(!view.source().equals(source)||launchWorld!=view.world()||launchModel!=model){source=view.source();launchWorld=view.world();launchModel=model;seen.clear();flashed.clear();launches.clear();}
        var matrices=ctx.matrixStack();if(matrices==null)return;
        // OW effect sprites use additive light. Ordinary alpha blending made
        // the bright narrow star look like a muddy orange dot over terrain.
        var buffers=client.getBufferBuilders().getEntityVertexConsumers();var bodyLayer=RenderLayer.getEntityCutoutNoCull(BODY);var tailLayer=RenderLayer.getEyes(TAIL);var flameLayer=RenderLayer.getEyes(FLAME);var flareLayer=RenderLayer.getEyes(FLARE);var glowLayer=RenderLayer.getEyes(GLOW);
        var camera=ctx.camera().getPos();long now=System.currentTimeMillis();boolean drew=false;
        // A real admitted native shot owns the flash, even if its flight hit a
        // nearby wall in the same server tick. Never infer a shot from LMB.
        var rotation=ctx.camera().getRotation();var f=new org.joml.Vector3f(0,0,-1).rotate(rotation);var rr=new org.joml.Vector3f(1,0,0).rotate(rotation);var uu=new org.joml.Vector3f(0,1,0).rotate(rotation);
        var forward=new Vec3d(f.x,f.y,f.z);var right=new Vec3d(rr.x,rr.y,rr.z);var up=new Vec3d(uu.x,uu.y,uu.z);
        double aspect=(double)client.getWindow().getFramebufferWidth()/client.getWindow().getFramebufferHeight();
        var launch=PharahRocketPresentation.launch(0,host.fov(),aspect);
        var muzzle=camera.add(forward.multiply(launch.forward())).add(right.multiply(launch.right())).add(up.multiply(launch.up()));
        boolean flashDrew=false;
        for(var shot:view.flashes()){
            double age=(now-shot.wallMs())/1000.0;if(age<0||age>.13)continue;
            int alpha=(int)(230*Math.pow(1-age/.13,.65));
            billboard(matrices,buffers.getBuffer(glowLayer),ctx,muzzle,.12f,255,125,24,alpha/2);
            billboard(matrices,buffers.getBuffer(flareLayer),ctx,muzzle,.095f,255,210,105,alpha);
            billboard(matrices,buffers.getBuffer(glowLayer),ctx,muzzle,.035f,255,250,220,alpha);
            if(flashed.size()>4096)flashed.clear();if(flashed.add(shot.id()))NativeCombatRuntime.muzzleFlashesShown++;
            flashDrew=true;drew=true;
        }
        for(var shot:view.shots()){
            if(shot.barrage())continue; // Independent Barrage renderer owns Q.
            double age=(now-shot.wallMs())/1000.0,speed=Math.sqrt(shot.velocity().lengthSquared());
            if(age<0||age>shot.lifetime()||age*speed>=shot.range()||speed<1)continue;
            var start=new Vec3d(shot.start().x(),shot.start().y(),shot.start().z());var velocity=new Vec3d(shot.velocity().x(),shot.velocity().y(),shot.velocity().z());var path=PharahBarrageMotion.position(shot,age);var at=new Vec3d(path.x(),path.y(),path.z());
            if(shot.barrage()){var tangent=PharahBarrageMotion.direction(shot,age);velocity=new Vec3d(tangent.x(),tangent.y(),tangent.z()).normalize().multiply(speed);}
            // The beta's damage ray starts at the eye. Only the visible body
            // converges from the launcher to that unchanged authoritative ray.
            var direction=velocity.normalize();
            // Freeze the camera plane/FOV for this launch. Looking around after
            // firing must not move a rocket's early convergence sideways.
            var frame=launches.get(shot.id());
            if(frame==null&&age<.16){
                try{frame=new LaunchFrame(PharahRocketPresentation.basis(shot.velocity(),new NativeShotProtocol.Vec(right.x,right.y,right.z)),host.fov(),aspect);launches.put(shot.id(),frame);}
                catch(IllegalArgumentException invalid){continue;}
            }
            var offset=PharahRocketPresentation.launch(age,frame==null?host.fov():frame.fov(),frame==null?aspect:frame.aspect());
            var basis=frame==null?null:frame.basis();
            var side=basis==null?Vec3d.ZERO:new Vec3d(basis.right().x(),basis.right().y(),basis.right().z());
            var lift=basis==null?Vec3d.ZERO:new Vec3d(basis.up().x(),basis.up().y(),basis.up().z());
            if(!shot.barrage())at=at.add(direction.multiply(offset.forward())).add(side.multiply(offset.right())).add(lift.multiply(offset.up()));
            if(!client.world.isChunkLoaded(BlockPos.ofFloored(at)))continue;
            if(!shot.barrage()){
                var hit=client.world.raycast(new RaycastContext(start,at,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,client.player));
                if(hit.getType()!=net.minecraft.util.hit.HitResult.Type.MISS)continue;
            }
            matrices.push();matrices.translate(at.x-camera.x,at.y-camera.y,at.z-camera.z);matrices.multiply(new Quaternionf().rotationTo(0,1,0,(float)(velocity.x/speed),(float)(velocity.y/speed),(float)(velocity.z/speed)));var entry=matrices.peek();
            var body=buffers.getBuffer(bodyLayer);int light=WorldRenderer.getLightmapCoordinates(client.world,BlockPos.ofFloored(at));
            matrices.push();float modelScale=shot.barrage()?.7f:2.5f;matrices.scale(modelScale,modelScale,modelScale);entry=matrices.peek();
            for(int triangle=0;triangle<indices.length;triangle+=3)for(int corner:new int[]{0,1,2,2}){int i=indices[triangle+corner];vertex(body,entry,positions[i*3],positions[i*3+1],positions[i*3+2],uv[i*2],uv[i*2+1],normals[i*3],normals[i*3+1],normals[i*3+2],light);}
            matrices.pop();entry=matrices.peek();
            var tail=buffers.getBuffer(tailLayer);
            for(int axis=0;axis<2;axis++)for(int corner=0;corner<4;corner++){
                float width=corner<2?.095f:.035f,edge=corner==0||corner==3?-width:width,y=corner<2?-.09f:(float)-Math.min(1.35,Math.max(.10,age*speed-.25));
                effectVertex(tail,entry,axis==0?edge:0,y,axis==0?0:edge,corner==0||corner==3?0:1,corner<2?0:1,255,255,255,180);
            }
            var flame=buffers.getBuffer(flameLayer);int spriteFrame=(int)(age*36)%4;
            for(int axis=0;axis<2;axis++)for(int corner=0;corner<4;corner++){
                float width=corner<2?.11f:.05f,edge=corner==0||corner==3?-width:width,y=corner<2?-.09f:(float)-Math.min(.70,Math.max(.10,age*speed-.25));
                effectVertex(flame,entry,axis==0?edge:0,y,axis==0?0:edge,(spriteFrame+(corner==0||corner==3?0:1))/4f,corner<2?0:1,255,185,80,220);
            }
            matrices.pop();
            // Official Rocket Launcher demonstration has a sharp luminous star
            // around the body, not only a dim circular exhaust. Original private
            // sprites preserve its angular silhouette; no invented MC particles.
            var exhaust=at.subtract(direction.multiply(.12));float effectScale=shot.barrage()?.45f:1.25f;
            billboard(matrices,buffers.getBuffer(glowLayer),ctx,exhaust,.24f*effectScale,255,157,30,175);
            billboard(matrices,buffers.getBuffer(flareLayer),ctx,exhaust,.25f*effectScale,255,205,70,245);
            billboard(matrices,buffers.getBuffer(glowLayer),ctx,exhaust,.065f*effectScale,255,250,220,255);
            drew=true;if(seen.size()>4096)seen.clear();if(seen.add(shot.id()))NativeCombatRuntime.rocketModelsShown++;
        }
        var impacts=PharahRocketImpacts.view;
        if(impacts!=null&&impacts.source().equals(view.source())&&impacts.world()==view.world()&&impacts.model()==model&&impacts.player().equals(client.player.getUuid()))for(var impact:impacts.impacts()){
            double age=(now-impact.wall())/1000.;if(age<0||age>.35)continue;
            var p=impact.point();var at=new Vec3d(p.x(),p.y(),p.z());var n=impact.normal();if(n!=null)at=at.add(n.x()*.045,n.y()*.045,n.z()*.045);
            if(!client.world.isChunkLoaded(BlockPos.ofFloored(at)))continue;
            float t=(float)(age/.35),radius=.22f+.95f*(float)Math.sin(t*Math.PI*.75),fade=(1-t)*(1-t);
            billboard(matrices,buffers.getBuffer(glowLayer),ctx,at,radius*.9f,255,100,18,(int)(160*fade));
            // Original four-frame retail flame atlas, not an invented particle.
            matrices.push();matrices.translate(at.x-camera.x,at.y-camera.y,at.z-camera.z);matrices.multiply(ctx.camera().getRotation());var m=matrices.peek();var v=buffers.getBuffer(flameLayer);int frame=Math.min(3,(int)(t*4));
            effectVertex(v,m,-radius,-radius,0,frame/4f,1,255,185,80,(int)(240*fade));effectVertex(v,m,radius,-radius,0,(frame+1)/4f,1,255,185,80,(int)(240*fade));effectVertex(v,m,radius,radius,0,(frame+1)/4f,0,255,185,80,(int)(240*fade));effectVertex(v,m,-radius,radius,0,frame/4f,0,255,185,80,(int)(240*fade));matrices.pop();
            if(age<.075)billboard(matrices,buffers.getBuffer(flareLayer),ctx,at,.30f,255,242,175,(int)(250*(1-age/.075)));drew=true;
        }
        launches.keySet().removeIf(id->view.shots().stream().noneMatch(s->s.id()==id));
        if(drew){buffers.draw(bodyLayer);buffers.draw(tailLayer);buffers.draw(flameLayer);buffers.draw(glowLayer);buffers.draw(flareLayer);NativeCombatRuntime.rocketRenderFrames++;}
        if(flashDrew)NativeCombatRuntime.muzzleRenderFrames++;
    }
}
