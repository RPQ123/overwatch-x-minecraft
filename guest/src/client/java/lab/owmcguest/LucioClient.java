package lab.owmcguest;

import com.google.gson.*;
import java.nio.file.*;
import java.util.*;
import net.minecraft.client.MinecraftClient;
import net.minecraft.util.math.*;
import net.fabricmc.fabric.api.client.rendering.v1.*;
import net.minecraft.client.render.WorldRenderer;

/** 原版多发窗口 + existing emission16 的真实逐发工厂诊断。不安装回调、不改共享 ACK。
 * 校准开关使用现有creation保护文件；只撤销本实例创建且内容仍相同的开关，不改其他采集者的开关。
 * 工厂采集未就绪/缺失/过期时拒绝子发，绝不按Volley补造固定四发。 */
public final class LucioClient implements HeroClientModule {
    static{
        NativeSkillReader.register("lucioWeapon",new NativeSkillReader.Spec(LucioServer.HERO,0x0580000000000776L,Map.of("volley",36,"boop",65,"boopCommit",29)));
        NativeSkillReader.register("lucioSong",new NativeSkillReader.Spec(LucioServer.HERO,0x0580000000000266L,Map.of("songCommit",9)));
        NativeSkillReader.register("lucioAmp",new NativeSkillReader.Spec(LucioServer.HERO,0x0580000000000277L,Map.of("ampCast",6,"ampWindow",11)));
        NativeSkillReader.register("lucioBarrier",new NativeSkillReader.Spec(LucioServer.HERO,0x058000000000073aL,Map.of("barrier",0)));
        NativeSkillReader.register("lucioWall",new NativeSkillReader.Spec(LucioServer.HERO,0x0580000000000263L,Map.of("wallMove",25)));
    }
    public static final LucioClient INSTANCE=new LucioClient();
    private final List<NativeSkillReader> readers=List.of(new NativeSkillReader("lucioWeapon"),new NativeSkillReader("lucioSong"),new NativeSkillReader("lucioAmp"),new NativeSkillReader("lucioBarrier"),new NativeSkillReader("lucioWall"));
    private final List<Map<String,NativeSkillReader.Entry>> previous=new ArrayList<>(Arrays.asList(null,null,null,null,null));
    private final SupportNativeGate boopGate=new SupportNativeGate(),wallGate=new SupportNativeGate();
    private static final class Window {long begin,start,end;Window(long b,long t){begin=b;start=t;}}
    private final List<Window> windows=new ArrayList<>();private final LinkedHashSet<String> seen=new LinkedHashSet<>();
    private LucioServer.Scope scope;private net.minecraft.server.MinecraftServer server;
    private long frame=-1,frameWall,factoryEpoch,creation;private boolean factoryBaseline,renderRegistered;
    private Path ownedSwitch;private String switchPayload;private volatile String problem="";
    private LucioClient(){}
    @Override public void tick(MinecraftClient c){
        var h=HostPoseReader.INSTANCE.latest();long model=NativeLocomotionController.INSTANCE.modelId();
        if(h==null||h.flags()!=1||model==0||c.player==null||!c.player.isAlive()||c.world==null||c.getServer()==null||NativeLocomotionController.INSTANCE.hero()!=LucioServer.HERO){resetSession();return;}
        long now=System.currentTimeMillis();if(h.frame()!=frame){frame=h.frame();frameWall=now;}
        if(now-frameWall>150){resetSession();problem="native source stale; baseline discarded";return;}
        var next=new LucioServer.Scope(c.player.getUuid(),NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey()),h.generation(),model);
        if(!next.equals(scope)){resetSession();scope=next;server=c.getServer();}
        var srv=server;var own=scope;srv.execute(()->LucioServer.INSTANCE.heartbeat(srv,own,now));problem="";
        for(int i=0;i<readers.size();i++){
            var r=readers.get(i);var state=r.poll(h,model,LucioServer.HERO);
            if(state==null){String why=r.error;resetSession();problem=why;return;}
            var old=previous.get(i);previous.set(i,state.entries());
            for(String node:new String[]{"boopCommit","wallMove"}){
                var e=state.entries().get(node);if(e==null)continue;
                var gate=node.equals("wallMove")?wallGate:boopGate;var edge=gate.sample(e.tick(),e.active(),false);
                if(edge==SupportNativeGate.Edge.RESET){resetSession();problem="native support tick regressed";return;}
                if(edge==SupportNativeGate.Edge.BEGIN||edge==SupportNativeGate.Edge.END)
                    srv.execute(()->LucioServer.INSTANCE.signal(srv,own,node,e.tick(),edge==SupportNativeGate.Edge.BEGIN,now));
            }
            if(old==null)continue;
            for(var row:state.entries().entrySet()){
                String node=row.getKey();var e=row.getValue();var before=old.get(node);if(e.equals(before))continue;
                if(node.equals("boopCommit")||node.equals("wallMove"))continue;
                if(e.tick()<before.tick()){resetSession();problem="native tick regressed";return;}
                if(e.tick()<=0)continue;
                if(node.equals("volley")){
                    if(e.active()&&!before.active()){windows.add(new Window(e.tick(),now));}
                    else if(!e.active()&&before.active()&&!windows.isEmpty())windows.get(windows.size()-1).end=now;
                }
                // Begin/End同一轮只从约定相位计数；重复active样本不重开窗口。
                if(e.active()!=before.active()||e.tick()>before.tick())srv.execute(()->LucioServer.INSTANCE.signal(srv,own,node,e.tick(),e.active(),now));
            }
        }
        try{factories(c,h,now);}catch(Exception failure){factoryBaseline=false;seen.clear();problem=failure.toString();}
    }
    private static long n(JsonObject o,String key){return Long.parseUnsignedLong(o.get(key).getAsString());}
    private void factories(MinecraftClient c,HostPoseReader.Pose h,long now)throws Exception{
        String dir=System.getProperty("owmc.nativeEventsDirectory","");if(dir.isBlank())throw new IllegalStateException("factory directory missing");var root=Path.of(dir);
        var path=root.resolve("native-emissions-"+h.pid()+".json");if(Files.size(path)>524288)throw new IllegalStateException("factory report too large");
        var d=JsonParser.parseString(Files.readString(path)).getAsJsonObject();long heartbeat=n(d,"heartbeat");
        if(d.get("probeVersion").getAsInt()!=16||d.get("protocol").getAsInt()!=3||n(d,"pid")!=Integer.toUnsignedLong(h.pid())||n(d,"hostGeneration")!=h.generation()
            ||n(d,"hero")!=LucioServer.HERO||n(d,"modelId")!=scope.model()||!d.get("enabled").getAsBoolean()||d.get("restored").getAsBoolean()
            ||d.get("failures").getAsInt()!=0||d.get("overflow").getAsBoolean()||now-heartbeat>150||heartbeat>now+50)throw new IllegalStateException("factory source identity/freshness");
        if(d.get("combatReady").getAsBoolean()||d.get("armoryVariants").getAsInt()!=0)throw new IllegalStateException("Lucio authoritative journal path present; diagnostic consumer refuses double admission");
        // 此binding刚由NativeSkillReader校验过真实进程creation、owner及graph；再次关联报告。
        var b=JsonParser.parseString(Files.readString(root.resolve("native-lucioWeapon-request-"+h.pid()+".json"))).getAsJsonObject();
        if(n(b,"pid")!=Integer.toUnsignedLong(h.pid())||n(b,"modelId")!=scope.model()||n(b,"hero")!=LucioServer.HERO||n(b,"creation")!=n(d,"creation"))throw new IllegalStateException("factory creation mismatch");
        creation=n(d,"creation");var flag=root.resolve("native-factory-calibration-"+h.pid()+".txt");String payload=creation+"\n";
        if(!Files.exists(flag)){
            // CREATE_NEW避免覆盖同时启动的其他采集者。仅使用现有owner提供的诊断开关。
            Files.writeString(flag,payload,StandardOpenOption.CREATE_NEW);ownedSwitch=flag;switchPayload=payload;
        }else if(!Files.readString(flag).equals(payload))throw new IllegalStateException("factory calibration owned by another creation");
        if(!d.get("factoryCalibration").getAsBoolean())throw new IllegalStateException("waiting for existing owner factory capture");
        long epoch=n(d,"epoch");if(epoch==0)throw new IllegalStateException("factory epoch missing");
        if(epoch!=factoryEpoch){factoryEpoch=epoch;factoryBaseline=false;seen.clear();}
        var rows=d.getAsJsonArray("factoryObservations");if(rows.size()>256)throw new IllegalStateException("factory observation bounds");
        var own=scope;var srv=server;boolean baseline=!factoryBaseline;
        for(var value:rows){var r=value.getAsJsonObject();
            if(n(r,"owner")!=scope.model()||n(r,"hero")!=LucioServer.HERO||n(r,"resource")!=0x04000000000005ffL)continue;
            long tick=n(r,"tick"),shot=n(r,"shot"),pellet=n(r,"pellet"),captured=n(r,"wallMs");
            String id=epoch+":"+n(r,"owner")+":"+Long.toUnsignedString(n(r,"volley"))+":"+tick+":"+shot+":"+pellet;
            if(!seen.add(id))continue;
            if(baseline||now-captured>150||captured>now+50)continue;
            if(tick<=0||shot>65535||pellet>255||n(r,"volley")==0||n(r,"result")==0||r.get("status").getAsInt()!=0||r.get("type").getAsInt()!=3
                ||r.get("speed").getAsDouble()!=40||r.get("lifetime").getAsDouble()!=5||r.get("range").getAsDouble()!=100)continue;
            var a=r.getAsJsonArray("direction");if(a.size()!=3)continue;var direction=new Vec3d(a.get(0).getAsDouble(),a.get(1).getAsDouble(),a.get(2).getAsDouble());
            if(!Double.isFinite(direction.lengthSquared())||Math.abs(direction.lengthSquared()-1)>.01)continue;
            Window match=null;for(var w:windows)if(captured>=w.start-50&&(w.end==0||captured<=w.end+50))match=w;
            if(match==null)continue;long begin=match.begin;srv.execute(()->LucioServer.INSTANCE.factory(srv,own,id,begin,captured,direction,now));
        }
        factoryBaseline=true;while(seen.size()>1024)seen.remove(seen.iterator().next());windows.removeIf(w->w.end!=0&&now-w.end>500);
    }
    @Override public void resetSession(){
        if(server!=null&&scope!=null)server.execute(LucioServer.INSTANCE::resetSession);
        for(var r:readers)r.close();boopGate.clear();wallGate.clear();Collections.fill(previous,null);windows.clear();seen.clear();factoryBaseline=false;factoryEpoch=creation=0;scope=null;server=null;problem="";
        if(ownedSwitch!=null){try{if(Files.exists(ownedSwitch)&&Files.readString(ownedSwitch).equals(switchPayload))Files.delete(ownedSwitch);}catch(Exception e){problem="factory switch cleanup: "+e;}ownedSwitch=null;switchPayload=null;}
    }
    @Override public String errorKey(){return "lucioError";}
    @Override public String error(){return problem;}
    /** Shared mixin integration is listed in handoff; no MC wall/key can start native WallMove. */
    public boolean travel(MinecraftClient c){
        long now=System.currentTimeMillis();var h=HostPoseReader.INSTANCE.latest();
        if(!wallGate.active()||scope==null||c.player==null||!scope.owner().equals(c.player.getUuid())||c.world==null||c.getServer()==null
                ||scope.world()!=NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey())||h==null||h.flags()!=1||h.generation()!=scope.source()
                ||NativeLocomotionController.INSTANCE.hero()!=LucioServer.HERO||NativeLocomotionController.INSTANCE.modelId()!=scope.model()
                ||now-frameWall<0||now-frameWall>150||c.player.isOnGround()||c.player.isTouchingWater()||c.player.isInLava())return false;
        Vec3d normal=null;
        for(var n:new Vec3d[]{new Vec3d(1,0,0),new Vec3d(-1,0,0),new Vec3d(0,0,1),new Vec3d(0,0,-1)})
            if(!c.world.isSpaceEmpty(c.player,c.player.getBoundingBox().contract(.01).offset(n.multiply(.12)))){normal=n;break;}
        if(normal==null)return false;
        var forward=c.player.getRotationVec(1);var tangent=new Vec3d(forward.x,0,forward.z);tangent=tangent.subtract(normal.multiply(tangent.dotProduct(normal)));
        if(tangent.lengthSquared()<1e-6)return false;
        var motion=tangent.normalize().multiply(.3).add(0,Math.max(-.05,Math.min(.05,c.player.getVelocity().y)),0);
        c.player.setVelocity(Vec3d.ZERO);c.player.move(net.minecraft.entity.MovementType.SELF,motion);c.player.fallDistance=0;return true;
    }
    @Override public void registerRender(){if(!renderRegistered){WorldRenderEvents.AFTER_ENTITIES.register(this::render);renderRegistered=true;}}
    private void render(WorldRenderContext ctx){
        var c=MinecraftClient.getInstance();if(!Boolean.getBoolean("owmc.frameExport")||c.world==null||c.getServer()==null||ctx.matrixStack()==null)return;
        // integrator/models: actual 19f2/19b6 templates; missing installed packs still draw nothing.
        if(!Files.isRegularFile(PrivateAssetPaths.meshes().resolve("lucio-sonic/pack.json")))return;
        var pack=OriginalMeshPack.get("lucio-sonic");if(pack==null)return;long world=NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey()),now=System.currentTimeMillis();
        for(var v:LucioServer.INSTANCE.views){if(v.world()!=world||now-v.wall()>200||!c.world.isChunkLoaded(BlockPos.ofFloored(v.at())))continue;
            OriginalWorldRenderer.mesh(ctx,"lucio-sonic",v.at(),null,true,.28f,.28f,.28f,1);
            OriginalWorldRenderer.mesh(ctx,"lucio-sonic-glow",v.at(),null,true,.28f,.28f,.28f,1);}
    }
}
