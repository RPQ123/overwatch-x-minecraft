package lab.owmcguest;

import com.google.gson.*;
import java.nio.file.*;
import java.util.*;
import net.fabricmc.fabric.api.client.rendering.v1.*;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.WorldRenderer;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Vec3d;

/** Read-only native phases and per-factory pellet identities; never reads buttons.
 * Existing emission16 diagnostics must already be enabled by the lab controller.
 * This reader creates no callback owner, control file or journal acknowledgment.
 * A snapshot gap is counted and baselined; missing factories are never synthesized.
 */
public final class RoadhogClient implements HeroClientModule {
    static {
        NativeSkillReader.register("roadhogWeapon",new NativeSkillReader.Spec(RoadhogServer.HERO,0x05800000000001c6L,Map.of("primary",30,"secondary",34,"wholeHog",37)));
        NativeSkillReader.register("roadhogHook",new NativeSkillReader.Spec(RoadhogServer.HERO,0x05800000000001c8L,Map.of("cast",11,"search",19,"damage",21)));
        NativeSkillReader.register("roadhogHeal",new NativeSkillReader.Spec(RoadhogServer.HERO,0x0580000000000240L,Map.of("heal",23)));
    }
    public static final RoadhogClient INSTANCE=new RoadhogClient();
    private final NativeSkillReader weapon=new NativeSkillReader("roadhogWeapon"),hook=new NativeSkillReader("roadhogHook"),heal=new NativeSkillReader("roadhogHeal");
    private final Phase q=new Phase(),cast=new Phase(),search=new Phase(),breather=new Phase();
    private final TanksNodeEvidence evidence=new TanksNodeEvidence();
    private final Set<String> seen=new HashSet<>();private String tail="",error="";
    private RoadhogServer.Scope scope;private net.minecraft.server.MinecraftServer server;
    private long frame,frameSource,frameWall,lastWall,boundary,creation,epoch,calls;private boolean factoryBaseline,renderRegistered;
    private boolean qWasActive;private long qBeginWall;
    private RoadhogClient(){}
    @Override public String errorKey(){return "roadhogError";}
    @Override public String error(){return error;}
    /** B/E of one continuous state opens/closes ONE token; first active sample never replays. */
    static final class Phase {
        private NativeSkillReader.Entry previous;private long token;
        long update(NativeSkillReader.Entry e){
            if(e==null)throw new IllegalArgumentException("phase absent");
            if(previous==null||e.tick()<previous.tick()){previous=e;token=0;return 0;}
            if(!e.active())token=0;
            else if(!previous.active()&&e.tick()>previous.tick())token=e.tick();
            previous=e;return token;
        }
        void reset(){previous=null;token=0;}
    }
    @Override public void tick(MinecraftClient c){
        var h=HostPoseReader.INSTANCE.latest();long hero=NativeLocomotionController.INSTANCE.hero(),model=NativeLocomotionController.INSTANCE.modelId();
        if(h==null||h.flags()!=1||hero!=RoadhogServer.HERO||model==0||c.player==null||!c.player.isAlive()||c.world==null||c.getServer()==null){resetSession();return;}
        long now=System.currentTimeMillis();if(lastWall>0&&now-lastWall>150)resetSession();lastWall=now;
        if(h.frame()!=frame||h.generation()!=frameSource){frame=h.frame();frameSource=h.generation();frameWall=now;}
        if(now-frameWall>150){resetSession();error="native frame stale; baseline discarded";return;}
        long world=NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey());
        var current=new RoadhogServer.Scope(c.player.getUuid(),world,h.generation(),model);
        if(!current.equals(scope)){resetSession();scope=current;server=c.getServer();boundary=lastWall=now;}
        var w=weapon.poll(h,model,hero);var k=hook.poll(h,model,hero);var b=heal.poll(h,model,hero);
        if(w==null||k==null||b==null){String failure=w==null?weapon.error:k==null?hook.error:heal.error;resetSession();error=failure;return;}
        long whole=q.update(w.entries().get("wholeHog")),hc=cast.update(k.entries().get("cast")),hs=search.update(k.entries().get("search")),hb=breather.update(b.entries().get("heal"));
        w.entries().forEach((name,e)->evidence.observe("weapon."+name,e.tick(),e.active()));
        k.entries().forEach((name,e)->evidence.observe("hook."+name,e.tick(),e.active()));
        b.entries().forEach((name,e)->evidence.observe("breather."+name,e.tick(),e.active()));
        if(whole>0&&!qWasActive)qBeginWall=Math.max(boundary,now-150);qWasActive=whole>0;
        var s=scope;var srv=server;var sample=new RoadhogServer.Sample(hc,hs,hb,whole);
        var diagnostics=evidence.snapshot();
        srv.execute(()->{RoadhogServer.INSTANCE.refresh(srv,s,now,sample);RoadhogServer.INSTANCE.observeCandidates(s,now,diagnostics);});
        try{var rows=factories(h,w,whole,now);if(!rows.isEmpty())srv.execute(()->RoadhogServer.INSTANCE.pellets(srv,s,rows));error="";}
        catch(RuntimeException|java.io.IOException failure){factoryBaseline=false;seen.clear();tail="";error=failure.getMessage();}
    }
    private static long n(JsonObject o,String key){return Long.parseUnsignedLong(o.get(key).getAsString());}
    private static double scalar(JsonObject o,String key){double x=o.get(key).getAsDouble();if(!Double.isFinite(x))throw new IllegalArgumentException("nonfinite factory "+key);return x;}
    private static String identity(JsonObject r){return r.get("hero")+":"+r.get("owner")+":"+r.get("resource")+":"+r.get("volley")+":"+r.get("tick")+":"+r.get("shot")+":"+r.get("pellet");}
    private List<RoadhogServer.Pellet> factories(HostPoseReader.Pose h,NativeSkillReader.State state,long whole,long now)throws java.io.IOException{
        String dir=System.getProperty("owmc.nativeEventsDirectory","");if(dir.isBlank())throw new IllegalArgumentException("native events directory missing");
        var root=Path.of(dir);var path=root.resolve("native-emissions-"+h.pid()+".json");
        if(!Files.isRegularFile(path)||Files.size(path)>524288)throw new IllegalArgumentException("factory snapshot missing/oversized");
        var report=JsonParser.parseString(Files.readString(path)).getAsJsonObject();
        if(creation==0){var binding=JsonParser.parseString(Files.readString(root.resolve("native-roadhogWeapon-request-"+h.pid()+".json"))).getAsJsonObject();
            if(n(binding,"pid")!=Integer.toUnsignedLong(h.pid())||n(binding,"hero")!=RoadhogServer.HERO||n(binding,"modelId")!=scope.model())throw new IllegalArgumentException("factory binding identity");creation=n(binding,"creation");}
        long age=now-n(report,"heartbeat");
        if(n(report,"pid")!=Integer.toUnsignedLong(h.pid())||n(report,"creation")!=creation||n(report,"hostGeneration")!=h.generation()||n(report,"hero")!=RoadhogServer.HERO||n(report,"modelId")!=scope.model()
                ||n(report,"probeVersion")!=16||n(report,"protocol")!=3||n(report,"failures")!=0||!report.get("enabled").getAsBoolean()||report.get("restored").getAsBoolean()||report.get("overflow").getAsBoolean()||age< -50||age>150)
            throw new IllegalArgumentException("factory owner/status/freshness mismatch");
        if(!report.get("factoryCalibration").getAsBoolean())throw new IllegalArgumentException("factoryCalibration disabled; no per-pellet transport");
        if(n(report,"armoryVariants")>0)throw new IllegalArgumentException("shared armory active; refuse duplicate factory damage");
        long nextEpoch=n(report,"epoch"),nextCalls=n(report,"factoryCalls");if(nextEpoch<=0)throw new IllegalArgumentException("factory epoch missing");
        var all=report.getAsJsonArray("factoryObservations");if(all.size()>256)throw new IllegalArgumentException("factory snapshot bounds");
        var keys=new HashSet<String>();for(var e:all)keys.add(identity(e.getAsJsonObject()));
        boolean gap=factoryBaseline&&(epoch!=nextEpoch||nextCalls<calls||!tail.isEmpty()&&!keys.contains(tail));
        if(!factoryBaseline||gap){if(gap){var s=scope;server.execute(()->RoadhogServer.INSTANCE.gap(s));}seen.clear();seen.addAll(keys);factoryBaseline=true;boundary=now;tail="";}
        epoch=nextEpoch;calls=nextCalls;var result=new ArrayList<RoadhogServer.Pellet>();var resources=new HashMap<Long,Long>();
        for(var value:all){var row=value.getAsJsonObject();String key=identity(row);tail=key;
            if(!seen.add(key))continue;if(seen.size()>65536)throw new IllegalArgumentException("factory identity capacity; rebaseline");
            long wall=n(row,"wallMs"),resource=n(row,"resource");
            if(wall<=boundary||now-wall>150||wall-now>50||n(row,"hero")!=RoadhogServer.HERO||n(row,"owner")!=scope.model())continue;
            // Unknown resources are evidence for later parent/child calibration,
            // never permission to create a pellet or count a successful split.
            resources.merge(resource,1L,Long::sum);
            if(resource!=RoadhogServer.SCRAP&&resource!=RoadhogServer.SECONDARY&&resource!=RoadhogServer.WHOLE_HOG)continue;
            int type=row.get("type").getAsInt(),status=row.get("status").getAsInt();
            int expectedType=resource==RoadhogServer.SCRAP?2:resource==RoadhogServer.SECONDARY?1:3;
            int expectedStatus=resource==RoadhogServer.SECONDARY?8:0;
            if(n(row,"volley")==0||n(row,"tick")==0||n(row,"tick")>0xffffffffL||n(row,"shot")>65535||n(row,"pellet")>255||type!=expectedType||status!=expectedStatus||status==0&&n(row,"result")==0)continue;
            boolean qResource=resource==RoadhogServer.WHOLE_HOG;
            var node=state.entries().get(resource==RoadhogServer.SCRAP?"primary":resource==RoadhogServer.SECONDARY?"secondary":"wholeHog");
            // An actual factory is necessary even for instantaneous volleys; a stale node is insufficient.
            if(node.tick()<=0||qResource&&(whole==0||wall<qBeginWall))continue;
            double speed=scalar(row,"speed"),life=scalar(row,"lifetime"),range=scalar(row,"range");
            if(range!=100||!qResource&&(Math.abs(speed-(resource==RoadhogServer.SCRAP?80:60))>.001||Math.abs(life-(resource==RoadhogServer.SCRAP?5:.15))>.001))continue;
            // Q's observed zero speed/lifetime are NOT promoted to original ballistics.
            if(qResource&&(speed!=0||life!=0))continue;
            var a=row.getAsJsonArray("direction");if(a.size()!=3)continue;
            var d=new Vec3d(a.get(0).getAsDouble(),a.get(1).getAsDouble(),a.get(2).getAsDouble());
            if(!Double.isFinite(d.x)||!Double.isFinite(d.y)||!Double.isFinite(d.z)||Math.abs(d.lengthSquared()-1)>.02)continue;
            result.add(new RoadhogServer.Pellet(epoch+":"+key,epoch+":"+resource+":"+row.get("volley")+":"+row.get("tick"),resource,d.normalize(),wall));
        }
        if(!resources.isEmpty()){var s=scope;var counts=Map.copyOf(resources);server.execute(()->RoadhogServer.INSTANCE.observeResources(s,now,counts));}
        return List.copyOf(result);
    }
    @Override public void resetSession(){
        if(scope!=null&&server!=null){var old=scope;server.execute(()->RoadhogServer.INSTANCE.suspend(old));}
        weapon.close();hook.close();heal.close();q.reset();cast.reset();search.reset();breather.reset();scope=null;server=null;
        lastWall=boundary=creation=epoch=calls=0;factoryBaseline=qWasActive=false;qBeginWall=0;seen.clear();evidence.clear();tail="";error="";
    }
    @Override public void registerRender(){if(!renderRegistered){renderRegistered=true;WorldRenderEvents.AFTER_ENTITIES.register(this::render);}}
    private void render(WorldRenderContext ctx){
        if(!Boolean.getBoolean("owmc.frameExport"))return;var c=MinecraftClient.getInstance();if(c.world==null||c.getServer()==null||ctx.matrixStack()==null||scope==null)return;
        long world=NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey());var m=ctx.matrixStack();var cam=ctx.camera().getPos();
        for(var v:RoadhogServer.INSTANCE.views){if(v.world()!=world||v.source()!=scope.source()||v.model()!=scope.model()||System.currentTimeMillis()-v.wall()>150||!c.world.isChunkLoaded(BlockPos.ofFloored(v.at())))continue;
            String name=v.resource()==RoadhogServer.SCRAP?"roadhog-scrap":v.resource()==RoadhogServer.WHOLE_HOG?"roadhog-whole-hog":"roadhog-secondary";
            // integrator/models: center real bounds; thin templates are MC-size billboards.
            if(v.resource()==RoadhogServer.SECONDARY)
                OriginalWorldRenderer.zMesh(ctx,name,v.at(),v.direction(),1);
            else OriginalWorldRenderer.mesh(ctx,name,v.at(),null,true,.12f,.12f,.12f,1);
        }
    }
}
