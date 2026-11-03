package lab.owmcguest;

import com.google.gson.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;
import net.fabricmc.fabric.api.client.rendering.v1.WorldRenderEvents;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.WorldRenderer;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Vec3d;

/** Native phase reader plus read-only, already-owned emission16 factory observations.
 * No callback owner, journal acknowledgement, calibration switch, input-derived shot,
 * fixed charge count or synthetic per-orb timer is installed here.
 * Diagnostic factory rows have no MC-world tag: only rows AFTER the current world/model
 * baseline, within a newly observed release B and <=150ms old may enter this MC adaptation.
 * Logger/transport interruptions rebuild emission baselines without invalidating native
 * projectiles already handed to MC; only confirmed identity/lifecycle transitions revoke those.
 */
public final class ZenyattaClient implements HeroClientModule {
    static {
        NativeSkillReader.register("zenWeapon",new NativeSkillReader.Spec(ZenyattaServer.HERO,0x0580000000000164L,Map.of("primary",28,"release",32)));
        NativeSkillReader.register("zenHarmony",new NativeSkillReader.Spec(ZenyattaServer.HERO,0x05800000000002f3L,Map.of("search",46,"heal",11)));
        NativeSkillReader.register("zenDiscord",new NativeSkillReader.Spec(ZenyattaServer.HERO,0x0580000000000176L,Map.of("search",41,"aura",6)));
        NativeSkillReader.register("zenTranscendence",new NativeSkillReader.Spec(ZenyattaServer.HERO,0x058000000000017bL,Map.of("windup",19,"heal",17,"aura",30)));
    }
    public static final ZenyattaClient INSTANCE=new ZenyattaClient();
    private final NativeSkillReader weapon=new NativeSkillReader("zenWeapon"),harmony=new NativeSkillReader("zenHarmony"),
        discord=new NativeSkillReader("zenDiscord"),transcendence=new NativeSkillReader("zenTranscendence");
    private final Map<String,NativeSkillReader.Entry> previous=new HashMap<>();
    private final Map<String,SupportNativeGate> supportGates=new HashMap<>();
    private final Set<String> seenFactories=new HashSet<>();
    private ZenyattaServer.Scope scope;
    private long serial,frame,frameWall,frameSource,scopeStart,primaryFired,release,releaseEndedWall,epoch,dropped;
    private boolean releasing,renderRegistered;
    private String error="",factoryError="waiting for scoped emission16 factory observations";
    public volatile long renderFrames;
    private ZenyattaClient(){}
    @Override public void tick(MinecraftClient c){
        var h=HostPoseReader.INSTANCE.latest();var server=c.getServer();long now=System.currentTimeMillis();
        long hero=NativeLocomotionController.INSTANCE.hero(),model=NativeLocomotionController.INSTANCE.modelId();
        if(c.player==null||!c.player.isAlive()||c.world==null||server==null){resetSession();return;}
        if(hero!=0&&hero!=ZenyattaServer.HERO){resetSession();return;}
        if(h==null||h.flags()!=1||hero==0||model==0){interruptTracking(c,"native transport/locomotion identity temporarily unavailable");return;}
        if(h.generation()!=frameSource||h.frame()!=frame){frameSource=h.generation();frame=h.frame();frameWall=now;}
        if(now<frameWall||now-frameWall>150){interruptTracking(c,"native frame stale; admission baseline revoked");return;}
        long world=NativeWorldIdentity.of(server,c.world.getRegistryKey());
        if(scope==null||scope.source()!=h.generation()||scope.model()!=model||scope.world()!=world||!scope.owner().equals(c.player.getUuid())){
            if(scope!=null)resetSession();
            scope=new ZenyattaServer.Scope(c.player.getUuid(),world,h.generation(),model,++serial);
            scopeStart=now;
        }
        var s=scope;ZenyattaServer.INSTANCE.permit(s,now);error="";
        var state=weapon.poll(h,model,hero);
        if(state==null){interruptTracking(c,weapon.error);return;}
        var p=state.entries().get("primary");var old=previous.put("primary",p);
        if(old==null)primaryFired=p.tick();
        else if(p.tick()<old.tick()){interruptTracking(c,"native primary tick regressed");return;}
        else if(!p.active()&&p.tick()>primaryFired){
            primaryFired=p.tick();server.execute(()->ZenyattaServer.INSTANCE.primary(server,s,p.tick(),now));
        }
        var r=state.entries().get("release");old=previous.put("release",r);
        if(old!=null){
            if(r.tick()<old.tick()){interruptTracking(c,"native release tick regressed");return;}
            if(r.tick()>0&&!r.equals(old)){
                if(r.active()){
                    release=r.tick();releasing=true;releaseEndedWall=0;server.execute(()->ZenyattaServer.INSTANCE.release(server,s,r.tick(),true,now));
                }else{
                    if(releasing)releaseEndedWall=now;releasing=false;server.execute(()->ZenyattaServer.INSTANCE.release(server,s,r.tick(),false,now));
                }
            }
        }
        factories(c,h,model,now);
        attempt(c,h,model,hero,harmony,"harmony","search",false);
        attempt(c,h,model,hero,discord,"discord","search",false);
        attempt(c,h,model,hero,transcendence,"transcendence","windup",true);
    }
    private void attempt(MinecraftClient c,HostPoseReader.Pose h,long model,long hero,NativeSkillReader reader,String kind,String node,boolean begin){
        var state=reader.poll(h,model,hero);
        if(state==null){previous.remove(kind);supportGates.clear();var s=scope;
            c.getServer().execute(()->ZenyattaServer.INSTANCE.stopSupport(s));if(error.isEmpty())error=reader.error;return;}
        var e=state.entries().get(node);var old=previous.put(kind,e);var s=scope;var server=c.getServer();
        long wall=System.currentTimeMillis();
        if(old!=null&&e.tick()>old.tick()&&e.active()==begin)server.execute(()->ZenyattaServer.INSTANCE.attempt(server,s,kind,e.tick(),wall));
        if(kind.equals("harmony"))support(c,state,"harmony","heal",wall);
        else if(kind.equals("discord"))support(c,state,"discord","aura",wall);
        else{support(c,state,"transcendence","heal",wall);support(c,state,"transcendenceAura","aura",wall);}
    }
    private void support(MinecraftClient c,NativeSkillReader.State state,String kind,String node,long now){
        var e=state.entries().get(node);var gate=supportGates.computeIfAbsent(kind,key->new SupportNativeGate());
        var edge=gate.sample(e.tick(),e.active(),false);var s=scope;var server=c.getServer();
        if(edge==SupportNativeGate.Edge.RESET){supportGates.clear();server.execute(()->ZenyattaServer.INSTANCE.stopSupport(s));return;}
        if(edge==SupportNativeGate.Edge.BEGIN||edge==SupportNativeGate.Edge.END)
            server.execute(()->ZenyattaServer.INSTANCE.support(server,s,kind,e.tick(),edge==SupportNativeGate.Edge.BEGIN,now));
    }
    private static long n(JsonObject o,String key){return Long.parseUnsignedLong(o.get(key).getAsString());}
    private static Vec3d direction(JsonObject row){
        var a=row.getAsJsonArray("direction");if(a==null||a.size()!=3)throw new IllegalArgumentException("orb direction shape");
        var v=new Vec3d(a.get(0).getAsDouble(),a.get(1).getAsDouble(),a.get(2).getAsDouble());
        if(!Double.isFinite(v.lengthSquared())||Math.abs(v.lengthSquared()-1)>.01)throw new IllegalArgumentException("orb direction bounds");return v;
    }
    private static String identity(JsonObject row){
        return row.get("volley").getAsString()+":"+row.get("tick").getAsString()+":"+row.get("shot").getAsString()+":"+row.get("pellet").getAsString();
    }
    private void factories(MinecraftClient c,HostPoseReader.Pose h,long model,long now){
        try{
            String dir=System.getProperty("owmc.nativeEventsDirectory","");if(dir.isBlank())throw new IllegalArgumentException("native events directory absent");
            var path=Path.of(dir).resolve("native-emissions-"+h.pid()+".json");
            var binding=Path.of(dir).resolve("native-zenWeapon-request-"+h.pid()+".json");
            if(!Files.isRegularFile(path)||Files.size(path)>524288||!Files.isRegularFile(binding)||Files.size(binding)>8192)
                throw new IllegalArgumentException("bounded factory/binding file unavailable");
            var root=JsonParser.parseString(Files.readString(path)).getAsJsonObject();
            var proof=JsonParser.parseString(Files.readString(binding)).getAsJsonObject();
            long heartbeat=n(root,"heartbeat"),newEpoch=n(root,"epoch");
            if(n(root,"pid")!=Integer.toUnsignedLong(h.pid())||n(root,"hostGeneration")!=h.generation()
                    ||n(root,"hero")!=ZenyattaServer.HERO||n(root,"modelId")!=model||n(root,"creation")!=n(proof,"creation")
                    ||n(proof,"pid")!=Integer.toUnsignedLong(h.pid())||n(proof,"hero")!=ZenyattaServer.HERO||n(proof,"modelId")!=model
                    ||root.get("probeVersion").getAsInt()!=16||root.get("protocol").getAsInt()!=3||newEpoch<=0
                    ||!root.get("enabled").getAsBoolean()||root.get("failures").getAsInt()!=0||root.get("overflow").getAsBoolean()
                    ||now-heartbeat<0||now-heartbeat>150||!root.get("factoryCalibration").getAsBoolean())
                throw new IllegalArgumentException("waiting for fresh, scoped emission16 factoryCalibration (module never enables it)");
            var rows=root.getAsJsonArray("factoryObservations");if(rows==null||rows.size()>256)throw new IllegalArgumentException("factory row bounds");
            if(epoch!=newEpoch){
                epoch=newEpoch;dropped=n(root,"factoryDropped");seenFactories.clear();
                for(var v:rows)seenFactories.add(identity(v.getAsJsonObject()));
                cancelRelease(c);
                factoryError="";return; // current snapshot is a baseline, never a replay
            }
            if(n(root,"factoryDropped")!=dropped)throw new IllegalArgumentException("factory observations dropped; rebaseline required");
            for(var v:rows){
                var row=v.getAsJsonObject();String id=identity(row);
                if(seenFactories.contains(id))continue;
                long wall=n(row,"wallMs"),age=now-wall;
                if(age<0||age>150||wall<scopeStart){seenFactories.add(id);continue;}
                // Wait for the matching freshly observed B, including a row published just before B was sampled.
                if(release==0||(!releasing&&(releaseEndedWall==0||wall>releaseEndedWall)))continue;
                if(n(row,"hero")!=ZenyattaServer.HERO||n(row,"owner")!=model||n(row,"resource")!=0x0400000000000261L
                        ||row.get("type").getAsInt()!=3||row.get("status").getAsInt()!=0||n(row,"result")==0
                        ||n(row,"tick")==0||n(row,"tick")>0xffffffffL||n(row,"shot")>65535||n(row,"pellet")>255
                        ||row.get("speed").getAsDouble()!=90||row.get("lifetime").getAsDouble()!=3||row.get("range").getAsDouble()!=180){
                    seenFactories.add(id);continue;
                }
                var d=direction(row);var server=c.getServer();var s=scope;long cast=release;
                seenFactories.add(id);server.execute(()->ZenyattaServer.INSTANCE.secondary(server,s,cast,id,d,wall));
            }
            if(seenFactories.size()>4096)throw new IllegalArgumentException("factory identity capacity reached; session rebaseline required");
            factoryError="";
        }catch(Exception failure){
            epoch=0;seenFactories.clear();cancelRelease(c);factoryError=failure.toString();
        }
    }
    private void cancelRelease(MinecraftClient c){
        if(releasing&&scope!=null){var s=scope;long tick=release,wall=System.currentTimeMillis();var server=c.getServer();
            server.execute(()->ZenyattaServer.INSTANCE.release(server,s,tick,false,wall));}
        releasing=false;release=releaseEndedWall=0;
    }
    @Override public void registerRender(){
        if(renderRegistered)return;renderRegistered=true;
        WorldRenderEvents.AFTER_ENTITIES.register(ctx->{
            var c=MinecraftClient.getInstance();long now=System.currentTimeMillis();
            if(!Boolean.getBoolean("owmc.frameExport")||c.world==null||c.player==null||c.getServer()==null||ctx.matrixStack()==null)return;
            long world=NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey());
            for(var v:ZenyattaServer.INSTANCE.views){
                if(scope==null||!scope.sameFlightIdentity(v.scope())||v.scope().world()!=world||!v.scope().owner().equals(c.player.getUuid())||now-v.wall()<0||now-v.wall()>150)continue;
                var body=OriginalMeshPack.get(v.secondary()?"zenyatta-secondary-core":"zenyatta-primary-core");
                var glow=OriginalMeshPack.get(v.secondary()?"zenyatta-secondary-glow":"zenyatta-primary-glow");
                if(body==null||glow==null||!c.world.isChunkLoaded(BlockPos.ofFloored(v.at())))continue;
                var m=ctx.matrixStack();var cam=ctx.camera().getPos();
                var buffers=c.getBufferBuilders().getEntityVertexConsumers();
                m.push();
                try{
                    m.translate(v.at().x-cam.x,v.at().y-cam.y,v.at().z-cam.z);
                    m.multiply(ctx.camera().getRotation()); // 两个原版模板均为片，需要 billboard
                    m.scale(.24f,.24f,.24f); // MC适配直径；原版 emitter 尺寸/曲线未解，不是物理半径
                    m.push();m.translate(0,-.50142765,0);
                    body.draw(buffers,m.peek(),net.minecraft.client.render.LightmapTextureManager.MAX_LIGHT_COORDINATE);
                    m.pop();
                    m.push();m.translate(0,-.5,0);
                    glow.draw(buffers,m.peek(),net.minecraft.client.render.LightmapTextureManager.MAX_LIGHT_COORDINATE);
                    m.pop();
                }finally{m.pop();}
                renderFrames++;
            }
        });
    }
    private void interruptTracking(MinecraftClient c,String reason){
        // MC already owns accepted flights. Stop NEW admissions, preserve their verified
        // owner/world/source/model, and baseline the next logger sample instead of replaying it.
        boolean hadScope=scope!=null;
        ZenyattaServer.INSTANCE.suspendAdmission();clearTracking();error=reason;
        if(hadScope)c.getServer().execute(()->ZenyattaServer.INSTANCE.readInterrupted(reason));
    }
    private void clearTracking(){
        weapon.close();harmony.close();discord.close();transcendence.close();previous.clear();supportGates.clear();seenFactories.clear();
        scope=null;scopeStart=primaryFired=release=releaseEndedWall=epoch=dropped=0;releasing=false;error="";factoryError="waiting for scoped emission16 factory observations";
    }
    @Override public void resetSession(){
        ZenyattaServer.INSTANCE.revoke();clearTracking();
    }
    @Override public String errorKey(){return "zenyattaError";}
    @Override public String error(){return error.isEmpty()?factoryError:error+(factoryError.isEmpty()?"":"; "+factoryError);}
}
