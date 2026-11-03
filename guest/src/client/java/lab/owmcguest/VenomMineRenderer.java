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

/** Original 24919 Venom Mine mesh/textures (private pack from tools/venom_mine_assets.py) drawn at the
 * MC-owned mine position. +Y is the mine's top; its base sits on y=0, so it lies on the hit face. */
final class VenomMineRenderer {
    static long frames;
    static volatile boolean ready;
    static volatile String error="original Venom Mine assets not loaded";
    private static boolean attempted;
    private static final Identifier BODY=Identifier.of("owmcguest","private/venom-body");
    private static final Identifier EMISSION=Identifier.of("owmcguest","private/venom-emission");
    private static float[] positions,normals,uv;
    private static int[] indices;

    private static void load(MinecraftClient client)throws Exception {
        var root=PrivateAssetPaths.assets().resolve("owmc-venom-mine").toRealPath();
        var proof=JsonParser.parseString(Files.readString(root.resolve("provenance.json"))).getAsJsonObject();
        if(!proof.get("clientBuild").getAsString().equals("0.8.0.24919")||!proof.get("model").getAsString().equals("0d000000000006f2")
            ||!proof.get("entity").getAsString().equals("04000000000000af"))throw new IllegalArgumentException("Venom source identity");
        var files=proof.getAsJsonObject("files");
        for(String name:List.of("venom.json","body.png","emission.png")){
            var path=root.resolve(name).toRealPath();
            if(!path.startsWith(root)||Files.size(path)<=0||Files.size(path)>4*1024*1024)throw new IllegalArgumentException("Venom asset path/size");
            var hash=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path)));
            if(!hash.equals(files.get(name).getAsString()))throw new IllegalArgumentException("Venom asset hash: "+name);
        }
        var data=JsonParser.parseString(Files.readString(root.resolve("venom.json"))).getAsJsonObject();
        if(data.get("schema").getAsInt()!=1||!data.get("model").getAsString().equals("0d000000000006f2")
            ||!data.get("units").getAsString().equals("meters")||!data.get("upAxis").getAsString().equals("+Y"))throw new IllegalArgumentException("Venom mesh identity");
        var gson=new Gson();
        var p=gson.fromJson(data.get("positions"),float[].class);var n=gson.fromJson(data.get("normals"),float[].class);
        var t=gson.fromJson(data.get("uv"),float[].class);var ids=gson.fromJson(data.get("indices"),int[].class);
        int count=p.length/3;
        if(count!=1079||n.length!=p.length||t.length!=count*2||ids.length!=1236*3)throw new IllegalArgumentException("Venom mesh counts");
        for(float x:p)if(!Float.isFinite(x)||Math.abs(x)>.3)throw new IllegalArgumentException("Venom position");
        for(float x:t)if(!Float.isFinite(x)||x<0||x>1)throw new IllegalArgumentException("Venom UV");
        for(int i:ids)if(i<0||i>=count)throw new IllegalArgumentException("Venom triangle index");
        try(var in=Files.newInputStream(root.resolve("body.png"))){client.getTextureManager().registerTexture(BODY,new NativeImageBackedTexture(NativeImage.read(in)));}
        try(var in=Files.newInputStream(root.resolve("emission.png"))){client.getTextureManager().registerTexture(EMISSION,new NativeImageBackedTexture(NativeImage.read(in)));}
        positions=p;normals=n;uv=t;indices=ids;ready=true;error="";
    }

    private static void mesh(VertexConsumer consumer,MatrixStack.Entry entry,int light){
        for(int triangle=0;triangle<indices.length;triangle+=3)for(int corner:new int[]{0,1,2,2}){
            int i=indices[triangle+corner];
            consumer.vertex(entry.getPositionMatrix(),positions[i*3],positions[i*3+1],positions[i*3+2])
                .color(255,255,255,255).texture(uv[i*2],uv[i*2+1]).overlay(OverlayTexture.DEFAULT_UV)
                .light(light).normal(entry,normals[i*3],normals[i*3+1],normals[i*3+2]);
        }
    }

    static void register(){WidowSpiderRenderer.register();WorldRenderEvents.AFTER_ENTITIES.register(VenomMineRenderer::render);}
    private static void render(WorldRenderContext ctx){
        var client=MinecraftClient.getInstance();
        if(!Boolean.getBoolean("owmc.frameExport"))return;
        var v=NativeVenomRuntime.view;long now=System.currentTimeMillis();
        if(v==null||client.player==null||client.world==null||client.getServer()==null||ctx.matrixStack()==null
            ||!v.owner().equals(client.player.getUuid())||v.world()!=NativeWorldIdentity.of(client.getServer(),client.world.getRegistryKey())
            ||now-v.wall()>250)return;
        var at=v.at();if(!client.world.isChunkLoaded(BlockPos.ofFloored(at)))return;
        if(v.spider()){WidowSpiderRenderer.renderFlying(ctx,v);return;}
        if(!attempted){attempted=true;try{load(client);}catch(Exception failure){error=failure.toString();System.err.println("OWMC original Venom Mine model unavailable: "+error);}}
        if(!ready)return;
        var normal=v.normal().normalize();
        var matrices=ctx.matrixStack();var camera=ctx.camera().getPos();matrices.push();
        matrices.translate(at.x-camera.x,at.y-camera.y,at.z-camera.z);
        matrices.multiply(new Quaternionf().rotationTo(0,1,0,(float)normal.x,(float)normal.y,(float)normal.z));
        // Facing follows the throw; while flying the mine tumbles slowly (presentation only).
        matrices.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(-v.yaw()+(v.stuck()?0:v.age()*24f)));
        var buffers=client.getBufferBuilders().getEntityVertexConsumers();var body=RenderLayer.getEntityCutoutNoCull(BODY);var emission=RenderLayer.getEyes(EMISSION);
        mesh(buffers.getBuffer(body),matrices.peek(),WorldRenderer.getLightmapCoordinates(client.world,BlockPos.ofFloored(at.add(normal.multiply(.2)))));
        mesh(buffers.getBuffer(emission),matrices.peek(),LightmapTextureManager.MAX_LIGHT_COORDINATE);
        matrices.pop();buffers.draw(body);buffers.draw(emission);frames++;
    }
}
