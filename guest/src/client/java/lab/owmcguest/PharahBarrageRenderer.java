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
import org.joml.Quaternionf;

/** Restored 2026-10-24 mini-rocket/sprites, enlarged 25% (MC adaptation). */
final class PharahBarrageRenderer {
    private static final Map<String,Identifier> TEXTURES=new LinkedHashMap<>();
    static{for(String n:List.of("body","trail","flame","flare","glow"))TEXTURES.put(n,Identifier.of("owmcguest","private/barrage-"+n));}
    private static float[] positions,normals,uv;private static int[] indices,colors;
    private static boolean attempted,ready;
    private static String error="waiting for independent Barrage assets";
    private static final Set<String> shown=new HashSet<>(),impacts=new HashSet<>();
    private static long frames,models,blasts;
    static volatile String status="{}";
    static void register(){WorldRenderEvents.AFTER_ENTITIES.register(PharahBarrageRenderer::render);}
    static boolean accepts(MinecraftClient c,HostPoseReader.Pose h,PharahBarragePresentation.View v){
        return Boolean.getBoolean("owmc.frameExport")&&c.world!=null&&c.player!=null&&c.player.isAlive()&&c.getServer()!=null&&h!=null&&h.inputActive()&&h.flags()==1&&v!=null
            &&v.source().pid()==h.pid()&&v.source().hostGeneration()==h.generation()&&v.player().equals(c.player.getUuid())
            &&v.model()==NativeLocomotionController.INSTANCE.modelId()&&NativeLocomotionController.INSTANCE.hero()==0x02e0000000000008L
            &&v.world()==NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey());
    }
    private static void load(MinecraftClient c)throws Exception{
        var root=PrivateAssetPaths.assets().resolve("owmc-pharah-barrage");
        var files=JsonParser.parseString(Files.readString(root.resolve("provenance.json"))).getAsJsonObject().getAsJsonObject("files");
        for(String n:List.of("barrage.json","body.png","trail.png","flame.png","flare.png","glow.png")){
            var p=root.resolve(n);if(Files.size(p)>4*1024*1024)throw new IllegalArgumentException("Barrage asset size");
            var hash=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(p)));
            if(!hash.equals(files.get(n).getAsString()))throw new IllegalArgumentException("Barrage asset hash: "+n);
        }
        var d=JsonParser.parseString(Files.readString(root.resolve("barrage.json"))).getAsJsonObject();
        if(d.get("schema").getAsInt()!=1||!d.get("resource").getAsString().equals("0400000000000052")||!d.get("model").getAsString().equals("mc-barrage-mini-v1"))throw new IllegalArgumentException("Independent Barrage identity");
        var gson=new Gson();positions=gson.fromJson(d.get("positions"),float[].class);normals=gson.fromJson(d.get("normals"),float[].class);uv=gson.fromJson(d.get("uv"),float[].class);indices=gson.fromJson(d.get("indices"),int[].class);colors=gson.fromJson(d.get("colors"),int[].class);
        if(positions.length<9||positions.length>12000||positions.length%3!=0||normals.length!=positions.length||colors.length!=positions.length||uv.length!=positions.length/3*2||indices.length>24000||indices.length%3!=0)throw new IllegalArgumentException("Barrage mesh bounds");
        for(float x:positions)if(!Float.isFinite(x)||Math.abs(x)>.2)throw new IllegalArgumentException("Barrage mesh position");
        for(float x:normals)if(!Float.isFinite(x)||Math.abs(x)>1.001)throw new IllegalArgumentException("Barrage normal");
        for(float x:uv)if(!Float.isFinite(x)||Math.abs(x)>16)throw new IllegalArgumentException("Barrage UV");
        for(int x:indices)if(x<0||x>=positions.length/3)throw new IllegalArgumentException("Barrage index");
        for(int x:colors)if(x<0||x>255)throw new IllegalArgumentException("Barrage color");
        for(var e:TEXTURES.entrySet())try(var in=Files.newInputStream(root.resolve(e.getKey()+".png"))){c.getTextureManager().registerTexture(e.getValue(),new NativeImageBackedTexture(NativeImage.read(in)));}
        ready=true;error="";
    }
    private static void effect(VertexConsumer v,MatrixStack.Entry m,float x,float y,float z,float u,float w,int r,int g,int b,int a){
        // Eyes uses ONE/ONE. Fade RGB as well as alpha to avoid a glowing box
        // and an abrupt disappearance when a blast reaches the end of its life.
        v.vertex(m.getPositionMatrix(),x,y,z).color(r*a/255,g*a/255,b*a/255,a).texture(u,w).overlay(OverlayTexture.DEFAULT_UV).light(LightmapTextureManager.MAX_LIGHT_COORDINATE).normal(m,0,0,1);
    }
    private static void sprite(MatrixStack m,VertexConsumer v,WorldRenderContext ctx,Vec3d at,float radius,int frame,int r,int g,int b,int a){
        var cam=ctx.camera().getPos();m.push();m.translate(at.x-cam.x,at.y-cam.y,at.z-cam.z);m.multiply(ctx.camera().getRotation());var e=m.peek();
        float l=frame<0?0:frame/4f,rr=frame<0?1:(frame+1)/4f;
        effect(v,e,-radius,-radius,0,l,1,r,g,b,a);effect(v,e,radius,-radius,0,rr,1,r,g,b,a);effect(v,e,radius,radius,0,rr,0,r,g,b,a);effect(v,e,-radius,radius,0,l,0,r,g,b,a);m.pop();
    }
    private static Vec3d vec(NativeShotProtocol.Vec p){return new Vec3d(p.x(),p.y(),p.z());}
    private static void render(WorldRenderContext ctx){
        var c=MinecraftClient.getInstance();if(!Boolean.getBoolean("owmc.frameExport"))return;
        if(!attempted){attempted=true;try{load(c);}catch(Exception e){error=e.toString();}}
        var view=PharahBarragePresentation.view;var host=HostPoseReader.INSTANCE.latest();
        if(!ready||!accepts(c,host,view)){publish();return;}
        var m=ctx.matrixStack();if(m==null)return;
        var flights=NativeCombatRuntime.rocketView;var buffers=c.getBufferBuilders().getEntityVertexConsumers();var cam=ctx.camera().getPos();long now=System.currentTimeMillis();boolean drew=false;
        var bodyLayer=RenderLayer.getEntityCutoutNoCull(TEXTURES.get("body"));var trailLayer=RenderLayer.getEyes(TEXTURES.get("trail"));var flameLayer=RenderLayer.getEyes(TEXTURES.get("flame"));var glowLayer=RenderLayer.getEyes(TEXTURES.get("glow"));var flareLayer=RenderLayer.getEyes(TEXTURES.get("flare"));
        if(flights!=null&&flights.source().equals(view.source())&&flights.world()==view.world()&&flights.model()==view.model()&&flights.player().equals(view.player()))for(var shot:flights.shots()){
            if(!shot.barrage())continue;double age=(now-shot.wallMs())/1000.;if(age<0||age>shot.lifetime())continue;
            var at=vec(PharahBarrageMotion.position(shot,age));if(!c.world.isChunkLoaded(BlockPos.ofFloored(at)))continue;
            var direction=vec(PharahBarrageMotion.direction(shot,age)).normalize();
            // The beta factory originates at the eye. Hide solid geometry in
            // the near camera region instead of drawing huge clipped rocket
            // faces. Its authoritative position and hit remain untouched.
            boolean drawBody=at.squaredDistanceTo(cam)>=4;
            m.push();m.translate(at.x-cam.x,at.y-cam.y,at.z-cam.z);m.multiply(new Quaternionf().rotationTo(0,1,0,(float)direction.x,(float)direction.y,(float)direction.z));m.scale(.75f,.75f,.75f);var e=m.peek();var body=buffers.getBuffer(bodyLayer);int light=WorldRenderer.getLightmapCoordinates(c.world,BlockPos.ofFloored(at));
            if(drawBody)for(int t=0;t<indices.length;t+=3)for(int corner:new int[]{0,1,2,2}){int i=indices[t+corner];body.vertex(e.getPositionMatrix(),positions[i*3],positions[i*3+1],positions[i*3+2]).color(colors[i*3],colors[i*3+1],colors[i*3+2],255).texture(uv[i*2],uv[i*2+1]).overlay(OverlayTexture.DEFAULT_UV).light(light).normal(e,normals[i*3],normals[i*3+1],normals[i*3+2]);}
            m.pop();
            // Short curved pale ribbon, sampled from the SAME native Wave path.
            // It cannot cut across a curve as the old straight exhaust did.
            var tail=buffers.getBuffer(trailLayer);var entry=m.peek();int pieces=12;
            for(int i=0;i<pieces;i++){
                double a=Math.max(0,age-i*.012),b=Math.max(0,age-(i+1)*.012);if(a==b)break;
                var p=vec(PharahBarrageMotion.position(shot,a));var q=vec(PharahBarrageMotion.position(shot,b));
                var cross=q.subtract(p).crossProduct(cam.subtract(p));if(cross.lengthSquared()<1e-10)continue;var side=cross.normalize().multiply(.02375*(1-i/(double)pieces));
                var pa=p.add(side).subtract(cam);var pb=p.subtract(side).subtract(cam);var qa=q.add(side).subtract(cam);var qb=q.subtract(side).subtract(cam);int alpha=(int)(155*(1-i/(double)pieces));
                effect(tail,entry,(float)pa.x,(float)pa.y,(float)pa.z,0,0,210,222,240,alpha);effect(tail,entry,(float)pb.x,(float)pb.y,(float)pb.z,1,0,210,222,240,alpha);effect(tail,entry,(float)qb.x,(float)qb.y,(float)qb.z,1,1,210,222,240,alpha);effect(tail,entry,(float)qa.x,(float)qa.y,(float)qa.z,0,1,210,222,240,alpha);
            }
            var exhaust=at.subtract(direction.multiply(.10));sprite(m,buffers.getBuffer(flareLayer),ctx,exhaust,.14375f,-1,255,165,35,230);sprite(m,buffers.getBuffer(glowLayer),ctx,exhaust,.06875f,-1,255,242,170,240);
            String id=view.source()+":"+shot.id();if(shown.add(id)){models++;NativeCombatRuntime.rocketModelsShown++;}drew=true;
        }
        for(var cue:view.impacts()){
            double age=(now-cue.wallMs())/1000.;if(age<0||age>.32)continue;var at=vec(cue.point());if(cue.normal()!=null)at=at.add(vec(cue.normal()).multiply(.045));
            float t=(float)(age/.32),radius=.17f+.68f*(float)Math.sin(t*Math.PI*.75),fade=(1-t)*(1-t);int frame=Math.min(3,(int)(t*4));
            sprite(m,buffers.getBuffer(glowLayer),ctx,at,radius*.85f,-1,255,98,16,(int)(145*fade));
            sprite(m,buffers.getBuffer(flameLayer),ctx,at,radius,frame,255,184,80,(int)(235*fade));
            if(age<.07)sprite(m,buffers.getBuffer(flareLayer),ctx,at,.22f,-1,255,242,175,(int)(250*(1-age/.07)));
            String id=view.source()+":"+cue.sequence();if(impacts.add(id))blasts++;drew=true;
        }
        if(shown.size()>8192)shown.clear();if(impacts.size()>8192)impacts.clear();
        if(drew){for(var layer:List.of(bodyLayer,trailLayer,flameLayer,glowLayer,flareLayer))buffers.draw(layer);frames++;NativeCombatRuntime.rocketRenderFrames++;}publish();
    }
    private static void publish(){var o=new JsonObject();o.addProperty("ready",ready);o.addProperty("model","mc-barrage-mini-v1");o.addProperty("originalMeshExport",false);o.addProperty("models",models);o.addProperty("impacts",blasts);o.addProperty("frames",frames);o.addProperty("error",error);status=o.toString();}
}
