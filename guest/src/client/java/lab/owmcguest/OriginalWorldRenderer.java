package lab.owmcguest;

import com.google.gson.*;
import java.util.*;
import java.util.function.Supplier;
import net.fabricmc.fabric.api.client.rendering.v1.*;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.*;
import net.minecraft.util.math.*;
import org.joml.Quaternionf;

/** Original geometry only. Transforms, static UV0, fullbright and timing are MC
 * presentation adaptations. Never admits an attack or changes server physics.
 * Additional hero effects consume a scoped `models` snapshot in existing status
 * JSON; absent snapshots draw nothing. See handoff-20261026-models.md. */
final class OriginalWorldRenderer {
    static volatile long frames, submissions, rejected;
    static volatile String error="";
    private static boolean registered;
    private record Spec(float x,float y,float z,float width,float height,float depth){}
    // Generated from actual selected LOD0 bounds by tools/models_20261026_jobs.py.
    private static final Map<String,Spec> CENTERS=new HashMap<>();
    static {
        CENTERS.put("pharah-rocket",new Spec(0f,0.016057428f,0f,0.0321147554f,0.0321148559f,0.109399348f));
        CENTERS.put("pharah-flight-glow",new Spec(0f,0.5f,0f,1f,1f,2.34371475e-14f));
        CENTERS.put("pharah-impact",new Spec(0f,0.5f,0f,1f,1f,2.34371475e-14f));
        CENTERS.put("pharah-trail",new Spec(0f,0.5f,0f,1f,1f,1f));
        CENTERS.put("pharah-barrage",new Spec(0f,0.016057428f,0f,0.0321147554f,0.0321148559f,0.109399348f));
        CENTERS.put("pharah-barrage-trail",new Spec(0f,0.5f,0f,1f,1f,1f));
        CENTERS.put("pharah-barrage-impact",new Spec(0f,0.5f,0f,1f,1f,2.34371475e-14f));
        CENTERS.put("pharah-concussive",new Spec(0f,0.016057428f,0f,0.0321147554f,0.0321148559f,0.109399348f));
        CENTERS.put("pharah-concussive-trail",new Spec(0f,0.5f,0f,1f,1f,1f));
        CENTERS.put("pharah-concussive-impact",new Spec(0f,0.5f,0f,1f,1f,2.34371475e-14f));
        CENTERS.put("mccree-flashbang",new Spec(0f,0.126500815f,0f,0.0958804116f,0.25300163f,0.0798115283f));
        CENTERS.put("mccree-flash-impact",new Spec(0f,0.5f,0f,1f,1f,2.34371475e-14f));
        CENTERS.put("soldier-helix",new Spec(0f,0.0847280845f,0f,0.311655045f,0.169456169f,0.155553758f));
        CENTERS.put("soldier-helix-trail",new Spec(0f,0.5f,0f,1f,1f,2.34371475e-14f));
        CENTERS.put("soldier-biotic",new Spec(0f,0.116647944f,0f,0.13188076f,0.233295888f,0.13695848f));
        CENTERS.put("soldier-biotic-field",new Spec(0f,0.5f,0f,1f,1f,2.34371475e-14f));
        CENTERS.put("bastion-tank-shell",new Spec(0f,0.5f,0f,1f,1f,2.34371475e-14f));
        CENTERS.put("bastion-tank-trail",new Spec(0f,0.5f,0f,1f,1f,1f));
        CENTERS.put("winston-projector",new Spec(0f,0.112653881f,0f,0.788642645f,0.225307763f,0.762993693f));
        CENTERS.put("winston-barrier",new Spec(0f,5f,0f,9.99999809f,10f,9.99999619f));
        CENTERS.put("reinhardt-barrier",new Spec(0f,2.126441f,0f,6.78943348f,4.252882f,0.861928463f));
        CENTERS.put("zarya-barrier",new Spec(0f,1.5f,0f,2.99999952f,3f,2.99999857f));
        CENTERS.put("zarya-beam",new Spec(0f,0.5f,0f,1f,1f,1f));
        CENTERS.put("mercy-heal-beam",new Spec(0f,0.5f,0f,1f,1f,1f));
        CENTERS.put("mercy-target-glow",new Spec(0f,0.5f,0f,1f,1f,2.34371475e-14f));
        CENTERS.put("lucio-sound-barrier",new Spec(0f,0.334999919f,0f,0.941495538f,0.669999838f,0.94149518f));
        CENTERS.put("lucio-sonic",new Spec(0f,0.0195415914f,0f,0.252982169f,0.0390831828f,0.25298211f));
        CENTERS.put("lucio-sonic-glow",new Spec(0f,0.0688123405f,0f,0.137624681f,0.137624681f,0.0318746492f));
        CENTERS.put("winston-tesla",new Spec(0f,0.5f,0f,1f,1f,1f));
        CENTERS.put("widow-grapple-flash",new Spec(0f,0.5f,0f,1f,1f,2.34371475e-14f));
        CENTERS.put("symmetra-orb",new Spec(0f,0.5f,0f,1f,1f,2.34371475e-14f));
        CENTERS.put("reaper-shadow-start",new Spec(0f,0.5f,0f,1f,1f,2.34371475e-14f));
        CENTERS.put("reaper-shadow-end",new Spec(0f,0.5f,0f,1f,1f,2.34371475e-14f));
        CENTERS.put("reaper-wraith",new Spec(0f,0.5f,0f,1f,1f,2.34371475e-14f));
        CENTERS.put("reaper-blossom",new Spec(0f,0.5f,0f,1f,1f,2.34371475e-14f));
        CENTERS.put("widow-venom-gas",new Spec(0f,0.5f,0f,1f,1f,2.34371475e-14f));
        CENTERS.put("tracer-blink",new Spec(0f,0.5f,0f,1f,1f,2.34371475e-14f));
        CENTERS.put("genji-dash-wind",new Spec(0f,0.5f,0f,1f,1f,2.34371475e-14f));
        CENTERS.put("mei-freeze-snow",new Spec(0f,0.5f,0f,1f,1f,2.34371475e-14f));
        CENTERS.put("mei-blizzard-shard",new Spec(0f,0.0139621543f,0f,0.109927215f,0.0279243086f,0.109927215f));
        CENTERS.put("roadhog-hook",new Spec(0f,0.741913378f,0f,0.147499859f,1.48382676f,0.697494984f));
        CENTERS.put("widow-hook",new Spec(0f,0.131877512f,0f,0.263755023f,0.263755023f,0.403815806f));
        CENTERS.put("mercy-pistol",new Spec(0f,0.5f,0f,1f,1f,2.34371475e-14f));
        CENTERS.put("dva-pistol",new Spec(0f,0.5f,0f,1f,1f,2.34371475e-14f));
        CENTERS.put("roadhog-scrap",new Spec(0f,0.5f,0f,1f,1f,1f));
        CENTERS.put("roadhog-secondary",new Spec(0f,0.20232895f,0f,0.452610135f,0.4046579f,0.372734189f));
        CENTERS.put("roadhog-whole-hog",new Spec(0f,0.5f,0f,1f,1f,2.34371475e-14f));
        CENTERS.put("symmetra-beam",new Spec(0f,0.5f,0f,1f,1f,1f));
        CENTERS.put("symmetra-shield",new Spec(0f,0.5f,0f,1f,1f,2.34371475e-14f));
        CENTERS.put("symmetra-turret",new Spec(0f,0.193053037f,0f,0.605816126f,0.386106074f,0.530117571f));
        CENTERS.put("symmetra-teleporter",new Spec(0f,0.182046458f,0f,2.18195057f,0.364092916f,1.91207719f));
        CENTERS.put("zenyatta-primary",new Spec(0f,0.5f,0f,1.00000012f,1f,1.00000024f));
        CENTERS.put("zenyatta-secondary",new Spec(0f,0.5f,0f,1.00000012f,1f,1.00000024f));
        CENTERS.put("zenyatta-primary-core",new Spec(0f,0.50142765f,0f,1.00285506f,1.0028553f,0f));
        CENTERS.put("zenyatta-secondary-core",new Spec(0f,0.50142765f,0f,1.00285506f,1.0028553f,0f));
        CENTERS.put("zenyatta-primary-glow",new Spec(0f,0.5f,0f,1f,1f,2.34371475e-14f));
        CENTERS.put("zenyatta-secondary-glow",new Spec(0f,0.5f,0f,1f,1f,2.34371475e-14f));
        CENTERS.put("zarya-grenade",new Spec(0f,0.500000238f,0f,1.00000024f,1.00000048f,0.486184955f));
        CENTERS.put("zarya-grenade-blue",new Spec(0f,0.500000238f,0f,1.00000024f,1.00000048f,0.486184955f));
        CENTERS.put("zarya-graviton",new Spec(0f,0.499487013f,0f,0.984724045f,0.998974025f,0.984724164f));
        CENTERS.put("zarya-graviton-red",new Spec(0f,0.499487013f,0f,0.984724045f,0.998974025f,0.984724164f));
    }
    private record Source(long hero,Supplier<String> status){}
    private static final List<Source> SOURCES=List.of(
        new Source(MercyServer.HERO,MercyServer.INSTANCE::status),
        new Source(LucioServer.HERO,LucioServer.INSTANCE::status),
        new Source(RoadhogServer.HERO,RoadhogServer.INSTANCE::status),
        new Source(ReinhardtServer.HERO,ReinhardtServer.INSTANCE::status),
        new Source(ZaryaServer.HERO,ZaryaServer.INSTANCE::status),
        new Source(SymmetraServer.HERO,SymmetraServer.INSTANCE::status),
        new Source(0x02e0000000000009L,()->NativeCombatRuntime.status),
        new Source(0x02e000000000000aL,()->NativeGrappleController.status),
        new Source(0x02e000000000000aL,()->NativeVenomRuntime.status),
        new Source(NativeReaperRuntime.HERO,()->NativeShadowRuntime.status),
        new Source(NativeReaperRuntime.HERO,()->NativeWraithRuntime.status),
        new Source(NativeReaperRuntime.HERO,()->NativeReaperRuntime.status),
        new Source(0x02e0000000000003L,()->NativeRecallRuntime.status),
        new Source(0x02e00000000000ddL,()->NativeBlizzardRuntime.status),
        new Source(0x02e0000000000029L,()->NativeDashRuntime.status),
        new Source(NativeDeadeyeRuntime.HERO,()->NativeCombatRuntime.status));

    static boolean mesh(WorldRenderContext ctx,String name,Vec3d at,Vec3d direction,
                        boolean billboard,float x,float y,float z,float alpha){
        return mesh(ctx,name,at,direction,billboard,x,y,z,alpha,1,1,1);
    }
    static boolean mesh(WorldRenderContext ctx,String name,Vec3d at,Vec3d direction,
                        boolean billboard,float x,float y,float z,float alpha,float r,float g,float b){
        var c=MinecraftClient.getInstance();
        if(c.world==null||ctx.matrixStack()==null||!finite(at)||at.squaredDistanceTo(ctx.camera().getPos())>256*256
            ||!c.world.isChunkLoaded(BlockPos.ofFloored(at))||!CENTERS.containsKey(name))return false;
        for(float v:new float[]{x,y,z})if(!Float.isFinite(v)||v<=0||v>128)return false;
        for(float v:new float[]{alpha,r,g,b})if(!Float.isFinite(v)||v<0||v>1)return false;
        var pack=OriginalMeshPack.get(name);if(pack==null)return false;
        var m=ctx.matrixStack();var camera=ctx.camera().getPos();var center=CENTERS.get(name);
        m.push();
        try{
            m.translate(at.x-camera.x,at.y-camera.y,at.z-camera.z);
            if(billboard)m.multiply(ctx.camera().getRotation());
            else if(direction!=null){
                if(!finite(direction)||direction.lengthSquared()<1e-10)return false;
                var d=direction.normalize();
                // Default source axis is +Y; callers rotate original +Z missiles
                // separately or provide their source direction through zMesh.
                m.multiply(new Quaternionf().rotationTo(0,1,0,(float)d.x,(float)d.y,(float)d.z));
            }
            m.scale(x,y,z);m.translate(-center.x,-center.y,-center.z);
            pack.draw(c.getBufferBuilders().getEntityVertexConsumers(),m.peek(),
                      WorldRenderer.getLightmapCoordinates(c.world,BlockPos.ofFloored(at)),r,g,b,alpha);
            submissions++;return true;
        }finally{m.pop();}
    }
    static boolean zMesh(WorldRenderContext ctx,String name,Vec3d at,Vec3d direction,float scale){
        return zMesh(ctx,name,at,direction,scale,scale,scale,1);
    }
    static boolean zMesh(WorldRenderContext ctx,String name,Vec3d at,Vec3d direction,float x,float y,float z,float alpha){
        if(!finite(direction)||direction.lengthSquared()<1e-10)return false;
        var m=ctx.matrixStack();if(m==null)return false;var d=direction.normalize();
        // A rotated local frame lets mesh keep its actual native +Z axis.
        var cam=ctx.camera().getPos();m.push();
        try{
            m.translate(at.x-cam.x,at.y-cam.y,at.z-cam.z);
            m.multiply(new Quaternionf().rotationTo(0,0,1,(float)d.x,(float)d.y,(float)d.z));
            m.translate(cam.x-at.x,cam.y-at.y,cam.z-at.z);
            return mesh(ctx,name,at,null,false,x,y,z,alpha);
        }finally{m.pop();}
    }
    static boolean beam(WorldRenderContext ctx,String name,Vec3d from,Vec3d to,float width,float alpha){
        if(!finite(from)||!finite(to))return false;var d=to.subtract(from);double length=d.length();
        var spec=CENTERS.get(name);if(length<.001||length>100||spec==null||spec.height<=1e-6)return false;
        return mesh(ctx,name,from.lerp(to,.5),d,false,width/Math.max(.001f,spec.width),
                    (float)length/spec.height,width/Math.max(1,spec.depth),alpha);
    }
    private static boolean finite(Vec3d v){return v!=null&&Double.isFinite(v.x)&&Double.isFinite(v.y)&&Double.isFinite(v.z);}
    private static Vec3d vector(JsonArray a){
        if(a==null||a.size()!=3)throw new IllegalArgumentException("models vector");
        var v=new Vec3d(a.get(0).getAsDouble(),a.get(1).getAsDouble(),a.get(2).getAsDouble());
        if(!finite(v))throw new IllegalArgumentException("models nonfinite");return v;
    }
    static void register(){if(registered)return;registered=true;WorldRenderEvents.AFTER_ENTITIES.register(ctx->{
        var c=MinecraftClient.getInstance();var h=HostPoseReader.INSTANCE.latest();
        if(!Boolean.getBoolean("owmc.frameExport")||c.world==null||c.player==null||!c.player.isAlive()||c.getServer()==null
            ||ctx.matrixStack()==null||h==null||!h.inputActive()||h.flags()!=1)return;
        long hero=NativeLocomotionController.INSTANCE.hero(),world=NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey());
        long now=System.currentTimeMillis();boolean drew=false;
        for(var source:SOURCES){
            if(hero!=source.hero)continue;
            try{
                var text=source.status.get();
                if(text==null||!text.contains("\"models\""))continue;
                if(text.length()>1_048_576)throw new IllegalArgumentException("models status bound");
                var status=JsonParser.parseString(text).getAsJsonObject();
                if(!status.has("models"))continue;var frame=status.getAsJsonObject("models");
                long age=now-frame.get("wall").getAsLong();
                if(age<0||age>200||frame.get("world").getAsLong()!=world||frame.get("source").getAsLong()!=h.generation()
                    ||frame.get("model").getAsLong()!=NativeLocomotionController.INSTANCE.modelId()
                    ||!frame.get("owner").getAsString().equals(c.player.getUuidAsString()))continue;
                var effects=frame.getAsJsonArray("effects");if(effects.size()>128)throw new IllegalArgumentException("models bound");
                for(var item:effects){
                    var effect=item.getAsJsonObject();String name=effect.get("mesh").getAsString();var at=vector(effect.getAsJsonArray("at"));
                    if(name.equals("winston-tesla")&&effect.has("launch"))at=NativeMuzzleOrigins.at(effect.get("launch").getAsString(),at);
                    float alpha=effect.has("alpha")?effect.get("alpha").getAsFloat():1;
                    if(effect.has("to"))drew|=beam(ctx,name,at,vector(effect.getAsJsonArray("to")),effect.get("width").getAsFloat(),alpha);
                    else{
                        var scale=vector(effect.getAsJsonArray("scale"));
                        var direction=effect.has("direction")?vector(effect.getAsJsonArray("direction")):null;
                        if(direction!=null&&effect.has("axis")&&effect.get("axis").getAsString().equals("z"))
                            drew|=zMesh(ctx,name,at,direction,(float)scale.x,(float)scale.y,(float)scale.z,alpha);
                        else drew|=mesh(ctx,name,at,direction,effect.has("billboard")&&effect.get("billboard").getAsBoolean(),
                                       (float)scale.x,(float)scale.y,(float)scale.z,alpha);
                    }
                }
            }catch(RuntimeException failure){rejected++;error=failure.toString();}
        }
        if(drew)frames++;
    });}
}
