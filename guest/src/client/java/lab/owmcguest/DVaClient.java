package lab.owmcguest;

import com.google.gson.*;
import java.nio.file.*;
import java.util.*;
import net.fabricmc.fabric.api.client.rendering.v1.*;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.WorldRenderer;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Vec3d;

/** Pilot-only native evidence. A B/E channel is not a per-tick bullet source.
 * Reads existing emission16 factory diagnostics; never installs a callback owner,
 * writes a control/ack file, reads buttons or fabricates a mech-form ability.
 * Production lossless factory routing still requires integration by Claude.
 */
public final class DVaClient implements HeroClientModule {
    static {
        NativeSkillReader.register("dvaPistol",new NativeSkillReader.Spec(DVaServer.HERO,0x05800000000002b8L,Map.of("firing",12)));
        NativeSkillReader.register("dvaCallMech",new NativeSkillReader.Spec(DVaServer.HERO,0x058000000000026aL,Map.of("attempt",41,"switch",25,"write",109,"enterAnim",50,"exitAnim",77,"move96",96,"move107",107,"health17",17,"health39",39)));
    }
    public static final DVaClient INSTANCE=new DVaClient();
    private final NativeSkillReader pistol=new NativeSkillReader("dvaPistol"),call=new NativeSkillReader("dvaCallMech");
    private final Phase firing=new Phase(),attempt=new Phase();
    private final TanksNodeEvidence evidence=new TanksNodeEvidence();
    private final Set<String> seen=new HashSet<>();private String tail="",error="";
    private DVaServer.Scope scope;private net.minecraft.server.MinecraftServer server;
    private long frame,frameSource,frameWall,lastWall,boundary,creation,epoch,calls,fireBeginWall;private boolean factoryBaseline,renderRegistered,wasFiring;
    private DVaClient(){}
    @Override public String errorKey(){return "dvaError";}
    @Override public String error(){return error;}
    static final class Phase {
        private NativeSkillReader.Entry previous;private long token;
        long update(NativeSkillReader.Entry e){
            if(e==null)throw new IllegalArgumentException("phase absent");
            if(previous==null||e.tick()<previous.tick()){previous=e;token=0;return 0;}
            if(!e.active())token=0;else if(!previous.active()&&e.tick()>previous.tick())token=e.tick();
            previous=e;return token;
        }
        void reset(){previous=null;token=0;}
    }
    @Override public void tick(MinecraftClient c){
        var h=HostPoseReader.INSTANCE.latest();long hero=NativeLocomotionController.INSTANCE.hero(),model=NativeLocomotionController.INSTANCE.modelId();
        if(h==null||h.flags()!=1||model==0||c.player==null||!c.player.isAlive()||c.world==null||c.getServer()==null){resetSession();return;}
        long now=System.currentTimeMillis();if(lastWall>0&&now-lastWall>150)resetSession();lastWall=now;
        if(h.frame()!=frame||h.generation()!=frameSource){frame=h.frame();frameSource=h.generation();frameWall=now;}
        if(now-frameWall>150){resetSession();error="native frame stale; baseline discarded";return;}
        long world=NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey());var current=new DVaServer.Scope(c.player.getUuid(),world,h.generation(),model);
        // Observe a changed hero/model BEFORE rejecting old bindings. This is a
        // raw identity observation, never proof that Call Mech succeeded.
        if(scope!=null&&server==c.getServer()&&scope.owner().equals(current.owner())&&scope.world()==world&&scope.source()==h.generation()){
            var expected=scope;var srv=server;
            srv.execute(()->DVaServer.INSTANCE.observeIdentity(srv,expected,now,hero,model));
        }
        if(hero!=DVaServer.HERO){resetSession();return;}
        if(!current.equals(scope)){resetSession();scope=current;server=c.getServer();boundary=lastWall=now;}
        var p=pistol.poll(h,model,hero);var a=call.poll(h,model,hero);
        if(p==null||a==null){String failure=p==null?pistol.error:call.error;resetSession();error=failure;return;}
        long fire=firing.update(p.entries().get("firing")),q=attempt.update(a.entries().get("attempt"));
        p.entries().forEach((name,e)->evidence.observe("pistol."+name,e.tick(),e.active()));
        a.entries().forEach((name,e)->evidence.observe("call."+name,e.tick(),e.active()));
        if(fire>0&&!wasFiring)fireBeginWall=Math.max(boundary,now-150);wasFiring=fire>0;
        var s=scope;var srv=server;var diagnostics=evidence.snapshot();
        srv.execute(()->{DVaServer.INSTANCE.refresh(srv,s,now,fire,q);DVaServer.INSTANCE.observeCandidates(s,now,diagnostics);});
        try{var rows=factories(h,fire,now);if(!rows.isEmpty())srv.execute(()->DVaServer.INSTANCE.pellets(srv,s,rows));error="";}
        catch(RuntimeException|java.io.IOException failure){factoryBaseline=false;seen.clear();tail="";error=failure.getMessage();}
    }
    private static long n(JsonObject o,String key){return Long.parseUnsignedLong(o.get(key).getAsString());}
    private static double scalar(JsonObject o,String key){double x=o.get(key).getAsDouble();if(!Double.isFinite(x))throw new IllegalArgumentException("nonfinite factory "+key);return x;}
    private static String identity(JsonObject r){return r.get("hero")+":"+r.get("owner")+":"+r.get("resource")+":"+r.get("volley")+":"+r.get("tick")+":"+r.get("shot")+":"+r.get("pellet");}
    private List<DVaServer.Pellet> factories(HostPoseReader.Pose h,long fire,long now)throws java.io.IOException{
        String dir=System.getProperty("owmc.nativeEventsDirectory","");if(dir.isBlank())throw new IllegalArgumentException("native events directory missing");
        var root=Path.of(dir);var path=root.resolve("native-emissions-"+h.pid()+".json");
        if(!Files.isRegularFile(path)||Files.size(path)>524288)throw new IllegalArgumentException("factory snapshot missing/oversized");
        var report=JsonParser.parseString(Files.readString(path)).getAsJsonObject();
        if(creation==0){var binding=JsonParser.parseString(Files.readString(root.resolve("native-dvaPistol-request-"+h.pid()+".json"))).getAsJsonObject();
            if(n(binding,"pid")!=Integer.toUnsignedLong(h.pid())||n(binding,"hero")!=DVaServer.HERO||n(binding,"modelId")!=scope.model())throw new IllegalArgumentException("factory binding identity");creation=n(binding,"creation");}
        long age=now-n(report,"heartbeat");
        if(n(report,"pid")!=Integer.toUnsignedLong(h.pid())||n(report,"creation")!=creation||n(report,"hostGeneration")!=h.generation()||n(report,"hero")!=DVaServer.HERO||n(report,"modelId")!=scope.model()
                ||n(report,"probeVersion")!=16||n(report,"protocol")!=3||n(report,"failures")!=0||!report.get("enabled").getAsBoolean()||report.get("restored").getAsBoolean()||report.get("overflow").getAsBoolean()||age< -50||age>150)
            throw new IllegalArgumentException("factory owner/status/freshness mismatch");
        if(!report.get("factoryCalibration").getAsBoolean())throw new IllegalArgumentException("factoryCalibration disabled; no per-bullet transport");
        if(n(report,"armoryVariants")>0)throw new IllegalArgumentException("shared armory active; refuse duplicate factory damage");
        long nextEpoch=n(report,"epoch"),nextCalls=n(report,"factoryCalls");if(nextEpoch<=0)throw new IllegalArgumentException("factory epoch missing");
        var all=report.getAsJsonArray("factoryObservations");if(all.size()>256)throw new IllegalArgumentException("factory snapshot bounds");
        var keys=new HashSet<String>();for(var e:all)keys.add(identity(e.getAsJsonObject()));
        boolean gap=factoryBaseline&&(epoch!=nextEpoch||nextCalls<calls||!tail.isEmpty()&&!keys.contains(tail));
        if(!factoryBaseline||gap){if(gap){var s=scope;server.execute(()->DVaServer.INSTANCE.gap(s));}seen.clear();seen.addAll(keys);factoryBaseline=true;boundary=now;tail="";}
        epoch=nextEpoch;calls=nextCalls;var result=new ArrayList<DVaServer.Pellet>();
        for(var value:all){var row=value.getAsJsonObject();String key=identity(row);tail=key;
            if(!seen.add(key))continue;if(seen.size()>65536)throw new IllegalArgumentException("factory identity capacity; rebaseline");
            long wall=n(row,"wallMs");
            if(fire==0||wall<fireBeginWall||wall<=boundary||now-wall>150||wall-now>50||n(row,"hero")!=DVaServer.HERO||n(row,"owner")!=scope.model()||n(row,"resource")!=DVaServer.PISTOL)continue;
            int type=row.get("type").getAsInt(),status=row.get("status").getAsInt();
            if(n(row,"volley")==0||n(row,"tick")==0||n(row,"tick")>0xffffffffL||n(row,"shot")>65535||n(row,"pellet")>255||type!=3||status!=0||n(row,"result")==0)continue;
            if(Math.abs(scalar(row,"speed")-50)>.001||Math.abs(scalar(row,"lifetime")-5)>.001||scalar(row,"range")!=100)continue;
            var a=row.getAsJsonArray("direction");if(a.size()!=3)continue;var d=new Vec3d(a.get(0).getAsDouble(),a.get(1).getAsDouble(),a.get(2).getAsDouble());
            if(!Double.isFinite(d.x)||!Double.isFinite(d.y)||!Double.isFinite(d.z)||Math.abs(d.lengthSquared()-1)>.02)continue;
            result.add(new DVaServer.Pellet(epoch+":"+key,d.normalize(),wall));
        }return List.copyOf(result);
    }
    @Override public void resetSession(){
        if(scope!=null&&server!=null){var old=scope;server.execute(()->DVaServer.INSTANCE.suspend(old));}
        pistol.close();call.close();firing.reset();attempt.reset();scope=null;server=null;
        // Preserve host frame/source freshness across reset: an unchanged frame
        // must not become fresh again just because a binding read failed.
        lastWall=boundary=creation=epoch=calls=fireBeginWall=0;factoryBaseline=wasFiring=false;seen.clear();evidence.clear();tail="";error="";
    }
    @Override public void registerRender(){if(!renderRegistered){renderRegistered=true;WorldRenderEvents.AFTER_ENTITIES.register(this::render);}}
    private void render(WorldRenderContext ctx){
        if(!Boolean.getBoolean("owmc.frameExport"))return;var c=MinecraftClient.getInstance();if(c.world==null||c.getServer()==null||ctx.matrixStack()==null||scope==null)return;
        var file=PrivateAssetPaths.meshes().resolve("dva-pistol/pack.json");if(!Files.isRegularFile(file))return;
        var pack=OriginalMeshPack.get("dva-pistol");if(pack==null)return;long world=NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey());var m=ctx.matrixStack();var cam=ctx.camera().getPos();
        for(var v:DVaServer.INSTANCE.views){if(v.world()!=world||v.source()!=scope.source()||v.model()!=scope.model()||System.currentTimeMillis()-v.wall()>150||!c.world.isChunkLoaded(BlockPos.ofFloored(v.at())))continue;
            OriginalWorldRenderer.mesh(ctx,"dva-pistol",v.at(),null,true,.12f,.12f,.12f,1);
        }
    }
}
