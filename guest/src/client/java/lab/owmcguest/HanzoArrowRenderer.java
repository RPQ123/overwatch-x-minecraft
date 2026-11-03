package lab.owmcguest;

import java.util.*;
import net.fabricmc.fabric.api.client.rendering.v1.*;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.WorldRenderer;
import net.minecraft.util.math.*;

/** Original Hanzo arrow meshes at actual MC sweep positions. Reveal/glowing and
 * damage remain owned by their existing runtimes. No keyboard or logger source. */
final class HanzoArrowRenderer {
    static volatile long frames,errors,primaryFrames,sonicFrames,scatterParentFrames,scatterChildFrames,stuckFrames,pulseFrames;
    static volatile long glowFrames,trailFrames,scatterParentGlowFrames,scatterChildGlowFrames,bounceGlowFrames;
    static volatile int lastBodyLight;
    private record PhaseFrame(long wall,int primary,int sonic,int scatterParent,int scatterChild,int stuck){}
    private static volatile PhaseFrame phaseFrame=new PhaseFrame(0,0,0,0,0,0);
    private static volatile long lastBounceWall;
    private static volatile long lastPrimaryFlightWall,lastSonicFlightWall,lastScatterFlightWall;
    private static volatile int activeBounceAfterglows;
    static volatile String error="";
    private static boolean registered;
    private static final Map<HanzoArrowMesh.Kind,Long> retryAfter=new EnumMap<>(HanzoArrowMesh.Kind.class);
    private static final Map<String,Long> pulseRetryAfter=new HashMap<>();
    private static final Map<String,String> assetErrors=new TreeMap<>();
    private static volatile Map<String,String> errorSnapshot=Map.of();
    private static final Map<String,Long> assetErrorCounts=new java.util.concurrent.ConcurrentHashMap<>();
    private static void failed(String asset,Exception e){errors++;assetErrors.put(asset,e.toString());assetErrorCounts.merge(asset,1L,Long::sum);errorSnapshot=Map.copyOf(assetErrors);error=assetErrors.toString();}
    private static void ready(String asset){if(assetErrors.remove(asset)!=null){errorSnapshot=Map.copyOf(assetErrors);error=assetErrors.isEmpty()?"":assetErrors.toString();}}
    static void register(){if(!registered){registered=true;WorldRenderEvents.AFTER_ENTITIES.register(HanzoArrowRenderer::render);}}
    private static boolean current(MinecraftClient client,UUID owner,long world,long model,long generation,long wall){
        long now=System.currentTimeMillis();var loc=NativeLocomotionController.INSTANCE;var host=HostPoseReader.INSTANCE.latest();
        return client.world!=null&&client.player!=null&&client.player.isAlive()&&client.getServer()!=null
            &&client.player.getUuid().equals(owner)&&loc.hero()==HanzoSonicArrowState.HERO&&loc.modelId()==model
            &&host!=null&&host.inputActive()&&host.generation()==generation&&now-wall>=-50&&now-wall<=250
            &&NativeWorldIdentity.of(client.getServer(),client.world.getRegistryKey())==world;
    }
    private static Vec3d point(NativeShotProtocol.Vec p){return new Vec3d(p.x(),p.y(),p.z());}
    private static void render(WorldRenderContext ctx){
        if(!Boolean.getBoolean("owmc.frameExport")||ctx.matrixStack()==null)return;
        var client=MinecraftClient.getInstance();var v=HanzoArrowPresentation.view;
        int activePrimary=0,activeSonic=0,activeParent=0,activeChild=0,activeStuck=0;
        if(v!=null){var s=v.scope();
            if(current(client,s.owner(),s.world(),s.model(),s.source().hostGeneration(),v.wall()))for(var a:v.arrows()){
                var kind=a.kind()==HanzoArrowPresentation.Kind.SONIC?HanzoArrowMesh.Kind.SONIC:HanzoArrowMesh.Kind.PRIMARY;
                if(draw(ctx,client,point(a.at()),point(a.direction()),kind,a.stuck())){
                    if(a.kind()==HanzoArrowPresentation.Kind.SONIC)sonicFrames++;else primaryFrames++;
                    if(a.stuck())activeStuck++;else if(a.kind()==HanzoArrowPresentation.Kind.SONIC)activeSonic++;else activePrimary++;
                }
            }
        }
        for(var a:NativeHanzoSkillRuntime.arrowViews){var s=a.scope();
            if(!current(client,s.owner(),s.world(),s.model(),s.source(),a.wall()))continue;
            if(!a.scatter())continue; // Dragon presentation belongs to its separate renderer.
            if(draw(ctx,client,a.at(),a.vel(),HanzoArrowMesh.Kind.SCATTER,a.stuck())){
                if(a.child())scatterChildFrames++;else scatterParentFrames++;
                if(a.stuck())activeStuck++;else if(a.child())activeChild++;else activeParent++;
            }
        }
        renderLightEffects(ctx,client);
        renderSonicPulses(ctx,client);
        long frameWall=System.currentTimeMillis();
        if(activePrimary>0)lastPrimaryFlightWall=frameWall;if(activeSonic>0)lastSonicFlightWall=frameWall;if(activeParent>0)lastScatterFlightWall=frameWall;
        phaseFrame=new PhaseFrame(frameWall,activePrimary,activeSonic,activeParent,activeChild,activeStuck);
    }
    private static boolean draw(WorldRenderContext ctx,MinecraftClient client,Vec3d at,Vec3d dir,HanzoArrowMesh.Kind kind,boolean stuck){
        if(client.world==null||!client.world.isChunkLoaded(BlockPos.ofFloored(at))||dir.lengthSquared()<1e-12)return false;
        long now=System.currentTimeMillis();if(now<retryAfter.getOrDefault(kind,0L))return false;
        var matrices=ctx.matrixStack();matrices.push();
        try{
            var pack=HanzoArrowMesh.get(kind);var d=dir.normalize();var cam=ctx.camera().getPos();
            matrices.translate(at.x-cam.x,at.y-cam.y,at.z-cam.z);
            matrices.multiply(new org.joml.Quaternionf().rotationTo(0,0,1,(float)d.x,(float)d.y,(float)d.z));
            var lightAt=BlockPos.ofFloored(stuck?at.subtract(d.multiply(.15)):at);
            lastBodyLight=WorldRenderer.getLightmapCoordinates(client.world,lightAt);
            pack.draw(client.getBufferBuilders().getEntityVertexConsumers(),matrices,lastBodyLight);
            frames++;if(stuck)stuckFrames++;ready(kind.name());return true;
        }catch(Exception e){failed(kind.name(),e);retryAfter.put(kind,now+5000);return false;}
        finally{matrices.pop();}
    }
    /** WorldFrameExporter: diagnostic.add("hanzoArrowFx",HanzoArrowRenderer.diagnostics()); */
    static com.google.gson.JsonObject diagnostics(){
        var o=new com.google.gson.JsonObject();o.addProperty("glowFrames",glowFrames);o.addProperty("trailFrames",trailFrames);
        o.addProperty("scatterParentGlowFrames",scatterParentGlowFrames);o.addProperty("scatterChildGlowFrames",scatterChildGlowFrames);
        o.addProperty("bounceGlowFrames",bounceGlowFrames);o.addProperty("bounces",HanzoArrowEffects.bounces);o.addProperty("contacts",HanzoArrowEffects.contacts);
        o.addProperty("segments",HanzoArrowEffects.segments);o.addProperty("stuckFrames",stuckFrames);o.addProperty("errors",errors);o.addProperty("error",error);
        o.add("assetErrors",new com.google.gson.Gson().toJsonTree(errorSnapshot));o.add("assetErrorCounts",new com.google.gson.Gson().toJsonTree(assetErrorCounts));
        var phase=phaseFrame;o.addProperty("frameWall",phase.wall());o.addProperty("activePrimary",phase.primary());o.addProperty("activeSonic",phase.sonic());
        o.addProperty("activeScatterParent",phase.scatterParent());o.addProperty("activeScatterChild",phase.scatterChild());o.addProperty("activeStuck",phase.stuck());o.addProperty("lastBounceWall",lastBounceWall);
        o.addProperty("lastPrimaryFlightWall",lastPrimaryFlightWall);o.addProperty("lastSonicFlightWall",lastSonicFlightWall);o.addProperty("lastScatterFlightWall",lastScatterFlightWall);
        o.addProperty("activeBounceAfterglows",activeBounceAfterglows);var server=MinecraftClient.getInstance().getServer();if(server!=null)o.addProperty("serverTick",server.getTicks());
        var anchors=new com.google.gson.JsonArray();var arrows=HanzoArrowPresentation.view;
        if(arrows!=null)for(var arrow:arrows.arrows())if(arrow.stuck()){
            var anchor=new com.google.gson.JsonObject();anchor.addProperty("id",arrow.identity());anchor.addProperty("kind",arrow.kind().name());
            anchor.addProperty("x",arrow.at().x());anchor.addProperty("y",arrow.at().y());anchor.addProperty("z",arrow.at().z());anchor.addProperty("expiresTick",arrow.expires());anchors.add(anchor);
        }o.add("embeddedAnchors",anchors);
        o.addProperty("lastBodyLight",lastBodyLight);o.addProperty("fxLight",0x00f000f0);o.addProperty("bodyScale",1);
        o.add("bodyLengthsMeters",new com.google.gson.Gson().toJsonTree(HanzoArrowMesh.LENGTHS));
        o.addProperty("nativeColorVariablesResolved",false);o.addProperty("maskTint","approximate normalized original BLUE 12d1 RGB mean: 18,30,255");
        o.addProperty("trailMs",120);o.addProperty("contactAfterglowMs",80);return o;
    }
    private static void renderLightEffects(WorldRenderContext ctx,MinecraftClient client){
        activeBounceAfterglows=0;
        var v=HanzoArrowEffects.view;if(v==null)return;var s=v.scope();
        if(!current(client,s.owner(),s.world(),s.model(),s.generation(),v.wall()))return;
        long now=System.nanoTime();
        for(var trail:v.trails()){
            if(now>=trail.expires()||trail.points().isEmpty())continue;
            String kind=trail.kind().name().toLowerCase(Locale.ROOT);float fade=Math.min(1,(trail.expires()-now)/(float)HanzoArrowEffects.TRAIL_NANOS);
            var points=trail.points();var last=point(points.getLast().at());
            if(sprite(ctx,client,kind+"-glow",last,trail.kind()==HanzoArrowEffects.Kind.SCATTER?.20f:.16f,fade)){
                glowFrames++;if(trail.kind()==HanzoArrowEffects.Kind.SCATTER){if(trail.child())scatterChildGlowFrames++;else scatterParentGlowFrames++;}
            }
            for(int i=1;i<points.size();i++){
                var a=points.get(i-1);var b=points.get(i);if(now-a.nanos()>HanzoArrowEffects.TRAIL_NANOS)continue;
                float ageFade=Math.max(0,1-(now-a.nanos())/(float)HanzoArrowEffects.TRAIL_NANOS)*fade;
                if(trail.kind()==HanzoArrowEffects.Kind.SONIC){
                    // 0244 exposes a particle sprite, not a 075d trail. Keep
                    // original sprite geometry at real past sweep samples.
                    if(sprite(ctx,client,"sonic-glow",point(a.at()),.12f,ageFade*.65f))trailFrames++;
                }else{
                    if(ribbon(ctx,client,kind+"-trail",point(a.at()),point(b.at()),.045f,ageFade))trailFrames++;
                    ribbon(ctx,client,kind+"-trail",point(a.at()),point(b.at()),.12f,ageFade*.22f);
                }
            }
        }
        for(var flash:v.flashes()){
            if(now>=flash.expires())continue;float fade=(flash.expires()-now)/(float)HanzoArrowEffects.FLASH_NANOS;
            if(sprite(ctx,client,flash.kind().name().toLowerCase(Locale.ROOT)+"-glow",point(flash.at()),.20f,fade)){
                glowFrames++;if(flash.contact()==HanzoArrowEffects.Contact.BOUNCE){bounceGlowFrames++;activeBounceAfterglows++;lastBounceWall=System.currentTimeMillis();}
            }
        }
    }
    private static boolean sprite(WorldRenderContext ctx,MinecraftClient client,String role,Vec3d at,float size,float opacity){
        return lightMesh(ctx,client,role,at,null,size,opacity);
    }
    private static boolean ribbon(WorldRenderContext ctx,MinecraftClient client,String role,Vec3d from,Vec3d to,float width,float opacity){
        if(from.squaredDistanceTo(to)<1e-10)return false;return lightMesh(ctx,client,role,from,to,width,opacity);
    }
    private static boolean lightMesh(WorldRenderContext ctx,MinecraftClient client,String role,Vec3d at,Vec3d end,float width,float opacity){
        if(opacity<=.001||client.world==null||!client.world.isChunkLoaded(BlockPos.ofFloored(at))||(end!=null&&!client.world.isChunkLoaded(BlockPos.ofFloored(end))))return false;
        var camera=ctx.camera().getPos();
        if(at.squaredDistanceTo(camera)<.25){
            if(end==null||end.squaredDistanceTo(camera)<.25)return false;
            // Clip only cosmetic geometry next to the camera; keep the rest on
            // its actual swept segment instead of a star at the eye/near plane.
            var delta=end.subtract(at);double length=delta.length();if(length<=.5)return false;at=at.add(delta.multiply(.5/length));
        }
        String key="fx-"+role;long now=System.currentTimeMillis();if(now<pulseRetryAfter.getOrDefault(key,0L))return false;
        var matrices=ctx.matrixStack();matrices.push();
        try{
            var pack=HanzoArrowFxMesh.get(role);var cam=ctx.camera().getPos();matrices.translate(at.x-cam.x,at.y-cam.y,at.z-cam.z);
            if(end==null){matrices.multiply(ctx.camera().getRotation());matrices.scale(width,width,width);matrices.translate(0,-.5,0);}
            else{var d=end.subtract(at);float length=(float)d.length();d=d.normalize();matrices.multiply(new org.joml.Quaternionf().rotationTo(0,1,0,(float)d.x,(float)d.y,(float)d.z));matrices.scale(width,length,width);}
            pack.draw(client.getBufferBuilders().getEntityVertexConsumers(),matrices,Math.min(1,opacity));frames++;ready(key);return true;
        }catch(Exception e){failed(key,e);pulseRetryAfter.put(key,now+5000);return false;}finally{matrices.pop();}
    }
    private static void renderSonicPulses(WorldRenderContext ctx,MinecraftClient client){
        var v=HanzoSonicArrowRuntime.view;
        if(v==null||!current(client,v.owner(),v.world(),v.model(),v.generation(),v.wall()))return;
        int tick=client.getServer().getTicks();
        for(var pulse:v.pulses()){
            if(tick<pulse.began()||tick>=pulse.expires())continue;
            var p=pulse.at();var at=new Vec3d(p.x(),p.y(),p.z());
            if(!client.world.isChunkLoaded(BlockPos.ofFloored(at)))continue;
            // Explicit MC visual policy: one expanding pulse/second, cyan tint;
            // c3's exact curves/color/period are not authenticated by this port.
            float age=tick-pulse.began()+Math.min(1,Math.max(0,(System.currentTimeMillis()-v.wall())/50f));
            float phase=(age%20)/20f,radius=.1f+phase*(float)(HanzoSonicArrowState.RADIUS-.1);
            for(String name:new String[]{"hanzo-sonic-pulse","hanzo-sonic-sense"}){
                long now=System.currentTimeMillis();if(now<pulseRetryAfter.getOrDefault(name,0L))continue;
                var matrices=ctx.matrixStack();matrices.push();
                try{var pack=HanzoSonicPulseMesh.get(name);var cam=ctx.camera().getPos();matrices.translate(at.x-cam.x,at.y-cam.y,at.z-cam.z);
                    pack.draw(client.getBufferBuilders().getEntityVertexConsumers(),matrices,radius,(int)(32*(1-phase)));
                    frames++;pulseFrames++;ready(name);
                }catch(Exception e){failed(name,e);pulseRetryAfter.put(name,now+5000);}finally{matrices.pop();}
            }
        }
    }
}
