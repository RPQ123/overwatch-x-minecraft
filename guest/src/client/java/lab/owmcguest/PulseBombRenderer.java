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

/** Private original24919 Pulse geometry/textures; MC material/pose adaptation. */
final class PulseBombRenderer {
    static long frames;
    static volatile boolean ready;
    static volatile String error="original Pulse assets not loaded";
    private static boolean attempted;
    private static final String MODEL_SHA="f90dee3ea70c5ff84ba8c516dc83feb1bce2a49bd599c6a65630769f2cb6dd37";
    private static final Identifier BODY=Identifier.of("owmcguest","private/pulse-body");
    private static final Identifier EMISSION=Identifier.of("owmcguest","private/pulse-emission");
    private static float[] positions,normals,uv;
    private static int[] indices;
    private static double halfThickness;

    private static void load(MinecraftClient client)throws Exception {
        var root=PrivateAssetPaths.assets().resolve("owmc-pulse-bomb").toRealPath();
        var proofPath=root.resolve("provenance.json").toRealPath();
        if(!proofPath.startsWith(root)||Files.size(proofPath)<=0||Files.size(proofPath)>65536)throw new IllegalArgumentException("Pulse provenance path/size");
        var proof=JsonParser.parseString(Files.readString(proofPath)).getAsJsonObject();
        if(!proof.get("clientBuild").getAsString().equals("0.8.0.24919")
            ||!proof.get("originalModelSha256").getAsString().equals(MODEL_SHA)
            ||!proof.get("model").getAsString().equals("0d00000000000b2c"))throw new IllegalArgumentException("Pulse source identity");
        var files=proof.getAsJsonObject("files");
        for(String name:List.of("pulse.json","body.png","emission.png")){
            var path=root.resolve(name).toRealPath();
            if(!path.startsWith(root)||Files.size(path)<=0||Files.size(path)>4*1024*1024)throw new IllegalArgumentException("Pulse asset path/size");
            var hash=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path)));
            if(!hash.equals(files.get(name).getAsString()))throw new IllegalArgumentException("Pulse asset hash: "+name);
        }
        var data=JsonParser.parseString(Files.readString(root.resolve("pulse.json"))).getAsJsonObject();
        if(data.get("schema").getAsInt()!=1||!data.get("resource").getAsString().equals("0400000000000045")
            ||!data.get("model").getAsString().equals("0d00000000000b2c")
            ||!data.get("originalModelSha256").getAsString().equals(MODEL_SHA)
            ||!data.get("geometry").getAsString().equals("original-beta24919-flat-model-v1")
            ||!data.get("units").getAsString().equals("meters")||!data.get("frontAxis").getAsString().equals("+Y"))throw new IllegalArgumentException("Pulse mesh identity");
        var gson=new Gson();
        var p=gson.fromJson(data.get("positions"),float[].class);var n=gson.fromJson(data.get("normals"),float[].class);
        var t=gson.fromJson(data.get("uv"),float[].class);var ids=gson.fromJson(data.get("indices"),int[].class);
        double half=data.get("halfThickness").getAsDouble();
        if(p.length!=731*3||n.length!=p.length||t.length!=731*2||ids.length!=868*3||!Double.isFinite(half)||Math.abs(half-.050670683384)>.000001)throw new IllegalArgumentException("Pulse mesh counts/thickness");
        for(float x:p)if(!Float.isFinite(x)||Math.abs(x)>.2)throw new IllegalArgumentException("Pulse unscaled position");
        for(float x:n)if(!Float.isFinite(x)||Math.abs(x)>1.001)throw new IllegalArgumentException("Pulse normal");
        for(float x:t)if(!Float.isFinite(x)||x<0||x>1)throw new IllegalArgumentException("Pulse UV");
        for(int i:ids)if(i<0||i>=731)throw new IllegalArgumentException("Pulse triangle index");
        try(var in=Files.newInputStream(root.resolve("body.png"))){client.getTextureManager().registerTexture(BODY,new NativeImageBackedTexture(NativeImage.read(in)));}
        try(var in=Files.newInputStream(root.resolve("emission.png"))){client.getTextureManager().registerTexture(EMISSION,new NativeImageBackedTexture(NativeImage.read(in)));}
        positions=p;normals=n;uv=t;indices=ids;halfThickness=half;ready=true;error="";
    }

    private static void mesh(VertexConsumer consumer,MatrixStack.Entry entry,int light){
        for(int triangle=0;triangle<indices.length;triangle+=3)for(int corner:new int[]{0,1,2,2}){
            int i=indices[triangle+corner];
            consumer.vertex(entry.getPositionMatrix(),positions[i*3],positions[i*3+1],positions[i*3+2])
                .color(255,255,255,255).texture(uv[i*2],uv[i*2+1]).overlay(OverlayTexture.DEFAULT_UV)
                .light(light).normal(entry,normals[i*3],normals[i*3+1],normals[i*3+2]);
        }
    }

    static void register(){WorldRenderEvents.AFTER_ENTITIES.register(PulseBombRenderer::render);}
    private static void render(WorldRenderContext ctx){
        var client=MinecraftClient.getInstance();
        if(!Boolean.getBoolean("owmc.frameExport"))return;
        PulseBurstRenderer.render(ctx);
        if(!attempted){attempted=true;try{load(client);}catch(Exception failure){error=failure.toString();System.err.println("OWMC original Pulse model unavailable: "+error);}}
        var host=HostPoseReader.INSTANCE.latest();var view=NativePulseRuntime.view;long now=System.currentTimeMillis();
        if(!ready||view==null||host==null||client.player==null||client.world==null||client.getServer()==null||ctx.matrixStack()==null
            ||!host.inputActive()||view.source()!=host.generation()||view.model()!=NativeLocomotionController.INSTANCE.modelId()
            ||NativeLocomotionController.INSTANCE.hero()!=NativePulseRuntime.HERO
            ||view.world()!=NativeWorldIdentity.of(client.getServer(),client.world.getRegistryKey())
            ||!view.owner().equals(client.player.getUuid())||now<view.wall()||now-view.wall()>250
            ||now<view.launchedWall()||now-view.launchedWall()>6500)return;
        var normal=view.normal();if(normal==null||!Double.isFinite(normal.lengthSquared())||normal.lengthSquared()<.0001)return;
        normal=normal.normalize();
        var at=view.at().add(normal.multiply(PulseBombPresentation.contactOffset(halfThickness*T3VisualTuning.PULSE_SCALE,view.attached(),view.blockAttached())));
        if(!view.attached())at=NativeMuzzleOrigins.at("pulse:"+view.source()+":"+view.model()+":"+view.nativeTick(),at);
        if(!Double.isFinite(at.x)||!Double.isFinite(at.y)||!Double.isFinite(at.z)||!client.world.isChunkLoaded(BlockPos.ofFloored(at)))return;
        var matrices=ctx.matrixStack();var camera=ctx.camera().getPos();matrices.push();
        matrices.translate(at.x-camera.x,at.y-camera.y,at.z-camera.z);
        matrices.scale(T3VisualTuning.PULSE_SCALE,T3VisualTuning.PULSE_SCALE,T3VisualTuning.PULSE_SCALE);
        // The original white/LED face is +Y. Only visuals move outward; runtime
        // attachment, fuse, damage and contact coordinates are unchanged.
        matrices.multiply(new Quaternionf().rotationTo(0,1,0,(float)normal.x,(float)normal.y,(float)normal.z));
        if(!view.attached())matrices.multiply(RotationAxis.POSITIVE_X.rotationDegrees((float)PulseBombPresentation.spinDegrees(now,view.launchedWall(),false)));
        var buffers=client.getBufferBuilders().getEntityVertexConsumers();var body=RenderLayer.getEntityCutoutNoCull(BODY);var emission=RenderLayer.getEyes(EMISSION);
        mesh(buffers.getBuffer(body),matrices.peek(),WorldRenderer.getLightmapCoordinates(client.world,BlockPos.ofFloored(at)));
        mesh(buffers.getBuffer(emission),matrices.peek(),LightmapTextureManager.MAX_LIGHT_COORDINATE);
        matrices.pop();buffers.draw(body);buffers.draw(emission);frames++;
    }
}
