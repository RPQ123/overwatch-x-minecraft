package lab.owmcguest;

import java.util.*;
import net.minecraft.client.MinecraftClient;
import net.fabricmc.fabric.api.client.rendering.v1.*;
import net.minecraft.client.render.WorldRenderer;
import net.minecraft.util.math.BlockPos;

/** 四张原版graph全部校验后原子派发；不读按键，不将预览升级为提交。
 * 声明成功分支需未来实机观测；失败/身份变化/过期后丢弃基线与授权，不重播旧事件。 */
public final class SymmetraClient implements HeroClientModule {
    static{
        NativeSkillReader.register("symmetraWeapon",new NativeSkillReader.Spec(SymmetraServer.HERO,0x0580000000000139L,Map.of("beam",77,"charge",18,"orb",116,"nativeDamage16",16,"nativeDamage89",89,"nativeDamage107",107)));
        NativeSkillReader.register("symmetraTurret",new NativeSkillReader.Spec(SymmetraServer.HERO,0x058000000000017eL,Map.of("turretPreview",32,"turretGhost",35,"turretPlace",2,"turretCommit",47)));
        NativeSkillReader.register("symmetraShield",new NativeSkillReader.Spec(SymmetraServer.HERO,0x05800000000001c3L,Map.of("shieldAttempt",27,"shieldWindup",16,"shieldCommit",3)));
        NativeSkillReader.register("symmetraPortal",new NativeSkillReader.Spec(SymmetraServer.HERO,0x0580000000000169L,Map.of("portalPreview",42,"portalGhost",74,"portalPlace",2,"portalCommit",66)));
    }
    public static final SymmetraClient INSTANCE=new SymmetraClient();
    private final List<NativeSkillReader> readers=List.of(new NativeSkillReader("symmetraWeapon"),new NativeSkillReader("symmetraTurret"),new NativeSkillReader("symmetraShield"),new NativeSkillReader("symmetraPortal"));
    private final List<Map<String,NativeSkillReader.Entry>> previous=new ArrayList<>(Arrays.asList(null,null,null,null));
    private SymmetraServer.Scope scope;private net.minecraft.server.MinecraftServer server;
    private long frame=-1,frameWall,serial;private boolean renderRegistered;private volatile String problem="";
    private record Event(String node,long tick,boolean active){}
    private static int priority(Event e){
        if(e.active())return 0;
        if(e.node().equals("orb")||e.node().endsWith("Commit"))return 1;
        return 2;
    }
    private SymmetraClient(){}
    @Override public void tick(MinecraftClient c){
        var h=HostPoseReader.INSTANCE.latest();long model=NativeLocomotionController.INSTANCE.modelId();
        if(h==null||h.flags()!=1||model==0||c.player==null||!c.player.isAlive()||c.world==null||c.getServer()==null||NativeLocomotionController.INSTANCE.hero()!=SymmetraServer.HERO){resetSession();return;}
        long now=System.currentTimeMillis();if(h.frame()!=frame){frame=h.frame();frameWall=now;}
        if(now-frameWall>150){resetSession();problem="native source stale; baseline discarded";return;}
        long world=NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey());
        if(scope==null||!scope.owner().equals(c.player.getUuid())||scope.world()!=world||scope.source()!=h.generation()||scope.model()!=model){
            resetSession();scope=new SymmetraServer.Scope(c.player.getUuid(),world,h.generation(),model,++serial);server=c.getServer();
        }
        var srv=server;var own=scope;problem="";
        boolean failed=false;
        var snapshots=new ArrayList<Map<String,NativeSkillReader.Entry>>();var events=new ArrayList<Event>();
        for(int i=0;i<readers.size();i++){
            var r=readers.get(i);var state=r.poll(h,model,SymmetraServer.HERO);
            if(state==null){failed=true;problem=r.error;break;}
            snapshots.add(state.entries());var old=previous.get(i);if(old==null)continue;
            for(String node:state.entries().keySet()){var e=state.entries().get(node);var before=old.get(node);
                if(e.equals(before))continue;if(e.tick()<before.tick()){failed=true;problem="native Symmetra tick regressed; baseline discarded";break;}
                if(e.tick()>0&&(e.active()!=before.active()||e.tick()>before.tick()))events.add(new Event(node,e.tick(),e.active()));
            }
            if(failed)break;
        }
        if(failed){String why=problem;resetSession();problem=why;return;}
        for(int i=0;i<snapshots.size();i++)previous.set(i,snapshots.get(i));
        events.sort(Comparator.comparingLong(Event::tick).thenComparingInt(SymmetraClient::priority).thenComparing(Event::node));
        SymmetraServer.INSTANCE.permit(own,now);
        srv.execute(()->{SymmetraServer.INSTANCE.heartbeat(srv,own,now);for(var e:events)SymmetraServer.INSTANCE.signal(srv,own,e.node(),e.tick(),e.active(),now);});
    }
    @Override public void resetSession(){
        SymmetraServer.INSTANCE.revoke();
        if(server!=null&&scope!=null){var old=scope;server.execute(()->SymmetraServer.INSTANCE.release(old));}
        for(var r:readers)r.close();Collections.fill(previous,null);scope=null;server=null;problem="";
        // 保留最后 frame，过期帧不能在 reset 后重新获得150ms信用。
    }
    @Override public String errorKey(){return "symmetraError";}
    @Override public String error(){return problem;}
    @Override public void registerRender(){if(!renderRegistered){WorldRenderEvents.AFTER_ENTITIES.register(this::render);renderRegistered=true;}}
    private void render(WorldRenderContext ctx){
        var c=MinecraftClient.getInstance();if(!Boolean.getBoolean("owmc.frameExport")||c.world==null||c.getServer()==null||ctx.matrixStack()==null)return;
        long world=NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey()),now=System.currentTimeMillis();
        for(var v:SymmetraServer.INSTANCE.views){
            if(v.world()!=world||now-v.wall()>200||!c.world.isChunkLoaded(BlockPos.ofFloored(v.at())))continue;
            if(v.mesh().equals("symmetra-orb")){
                OriginalWorldRenderer.mesh(ctx,"symmetra-orb",v.at(),null,true,.35f,.35f,.35f,1);
                continue;
            }
            if(v.mesh().equals("symmetra-beam")){
                if(OriginalWorldRenderer.beam(ctx,"symmetra-beam",v.at(),
                    v.at().add(v.direction().normalize().multiply(v.scale())),.08f,1))
                    SymmetraServer.INSTANCE.beamMeshFrames++;
                continue;
            }
            if(v.mesh().equals("symmetra-shield")){
                if(OriginalWorldRenderer.mesh(ctx,"symmetra-shield",v.at(),null,true,.8f,.8f,.8f,.5f))
                    SymmetraServer.INSTANCE.shieldMeshFrames++;
                continue;
            }
            var pack=OriginalMeshPack.get(v.mesh());if(pack==null)continue;
            var m=ctx.matrixStack();var camera=ctx.camera().getPos();m.push();
            try{
                m.translate(v.at().x-camera.x,v.at().y-camera.y,v.at().z-camera.z);
                if(v.mesh().equals("symmetra-beam")){
                    // MC适配：8cm宽、沿本地+Z拉伸到MC目标；不声称复刻原版粒子系统。
                    var d=v.direction().normalize();m.multiply(new org.joml.Quaternionf().rotationTo(new org.joml.Vector3f(0,0,1),new org.joml.Vector3f((float)d.x,(float)d.y,(float)d.z)));
                    m.scale(.08f,.08f,v.scale());
                }else m.scale(v.scale(),v.scale(),v.scale());
                if(v.mesh().equals("symmetra-beam")||v.mesh().equals("symmetra-shield")){
                    pack.drawEffect(c.getBufferBuilders().getEntityVertexConsumers(),m.peek(),(position,normal)->{},Float.NEGATIVE_INFINITY);
                    if(v.mesh().equals("symmetra-beam"))SymmetraServer.INSTANCE.beamMeshFrames++;else SymmetraServer.INSTANCE.shieldMeshFrames++;
                }else pack.draw(c.getBufferBuilders().getEntityVertexConsumers(),m.peek(),WorldRenderer.getLightmapCoordinates(c.world,BlockPos.ofFloored(v.at())));
            }finally{m.pop();}
        }
    }
}
