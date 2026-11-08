package lab.owmcguest;

import com.google.gson.JsonParser;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import net.fabricmc.fabric.api.client.rendering.v1.WorldRenderContext;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.*;
import net.minecraft.client.texture.*;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.Vec3d;

/** Reuses Pharah's verified private additive flare/glow/flame sprites.
 * Fullbright emitting body and crossed animated exhaust are MC presentation;
 * no temporary light blocks, extra projectiles or damage are created. */
final class PharahProjectileGlow {
    private static final Map<String,Identifier> TEXTURES=new LinkedHashMap<>();
    static{for(String name:List.of("flare","glow","flame"))TEXTURES.put(name,Identifier.of("owmcguest","private/shared-rocket-"+name));}
    private static boolean attempted;
    static boolean ready;
    static String error="waiting for private Pharah glow sprites";
    private static void load(MinecraftClient client)throws Exception{
        var local=PrivateAssetPaths.meshes().resolve("projectile-fire-fx");
        var root=Files.isRegularFile(local.resolve("provenance.json"))?local:PrivateAssetPaths.assets().resolve("owmc-pharah-projectile");
        var files=JsonParser.parseString(Files.readString(root.resolve("provenance.json"))).getAsJsonObject().getAsJsonObject("files");
        // Validate every sprite before registering any of them.
        for(String name:TEXTURES.keySet()){
            var file=root.resolve(name+".png");if(Files.size(file)>4*1024*1024)throw new IllegalArgumentException("rocket glow size");
            var hash=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(file)));
            if(!hash.equals(files.get(name+".png").getAsString()))throw new IllegalArgumentException("rocket glow hash: "+name);
        }
        for(var t:TEXTURES.entrySet())try(var in=Files.newInputStream(root.resolve(t.getKey()+".png"))){
            client.getTextureManager().registerTexture(t.getValue(),new NativeImageBackedTexture(NativeImage.read(in)));
        }
        ready=true;error="";
    }
    private static void vertex(VertexConsumer v,MatrixStack.Entry e,float x,float y,float z,float u,float w,int r,int g,int b,int alpha){
        // RenderLayer.getEyes uses additive blending: RGB must fade too.
        v.vertex(e.getPositionMatrix(),x,y,z).color(r*alpha/255,g*alpha/255,b*alpha/255,alpha).texture(u,w)
            .overlay(OverlayTexture.DEFAULT_UV).light(LightmapTextureManager.MAX_LIGHT_COORDINATE).normal(e,0,0,1);
    }
    private static void billboard(WorldRenderContext ctx,VertexConsumer v,Vec3d at,float radius,int r,int g,int b,int alpha){
        var m=ctx.matrixStack();var camera=ctx.camera().getPos();m.push();m.translate(at.x-camera.x,at.y-camera.y,at.z-camera.z);m.multiply(ctx.camera().getRotation());var e=m.peek();
        vertex(v,e,-radius,-radius,0,0,1,r,g,b,alpha);vertex(v,e,radius,-radius,0,1,1,r,g,b,alpha);
        vertex(v,e,radius,radius,0,1,0,r,g,b,alpha);vertex(v,e,-radius,radius,0,0,0,r,g,b,alpha);m.pop();
    }
    static boolean draw(WorldRenderContext ctx,Vec3d at,Vec3d direction,double age){
        return draw(ctx,at,direction,age,1);
    }
    static boolean draw(WorldRenderContext ctx,Vec3d at,Vec3d direction,double age,float size){
        var client=MinecraftClient.getInstance();
        if(!attempted){attempted=true;try{load(client);}catch(Exception failure){error=failure.toString();}}
        if(!ready||ctx.matrixStack()==null)return false;
        var buffers=client.getBufferBuilders().getEntityVertexConsumers();
        var flare=RenderLayer.getEyes(TEXTURES.get("flare"));var glow=RenderLayer.getEyes(TEXTURES.get("glow"));var flame=RenderLayer.getEyes(TEXTURES.get("flame"));
        var exhaust=at.subtract(direction.multiply(BastionTankPresentation.LENGTH*.42*size));
        billboard(ctx,buffers.getBuffer(glow),at,.24f*size,255,150,32,135);
        billboard(ctx,buffers.getBuffer(flare),exhaust,.29f*size,255,205,90,225);
        billboard(ctx,buffers.getBuffer(glow),exhaust,.09f*size,255,248,215,245);
        var axis=Math.abs(direction.y)<.9?new Vec3d(0,1,0):new Vec3d(1,0,0);
        var right=direction.crossProduct(axis).normalize();var up=right.crossProduct(direction).normalize();
        var camera=ctx.camera().getPos();var m=ctx.matrixStack().peek();var v=buffers.getBuffer(flame);int frame=(int)(age*36)%4;
        for(var side:List.of(right,up))for(int corner=0;corner<4;corner++){
            boolean near=corner<2;double width=(near?.12:.035)*size,sign=corner==0||corner==3?-1:1;
            var p=exhaust.add(side.multiply(sign*width)).subtract(direction.multiply(near?0:.65*size)).subtract(camera);
            vertex(v,m,(float)p.x,(float)p.y,(float)p.z,(frame+(corner==0||corner==3?0:1))/4f,near?0:1,255,185,65,near?220:85);
        }
        for(var layer:List.of(flare,glow,flame))buffers.draw(layer);
        return true;
    }
}
