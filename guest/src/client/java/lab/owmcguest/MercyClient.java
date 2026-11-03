package lab.owmcguest;

import java.util.HashMap;
import java.util.Map;
import net.fabricmc.fabric.api.client.rendering.v1.WorldRenderEvents;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.WorldRenderer;
import net.minecraft.util.math.BlockPos;

/** Fresh native phases only. First sample/read failure/source, owner or world change
 * rebuilds baselines. E closes a channel even when it shares the B's native tick.
 * Search25/36 remain attempts. Pistol/MoveTo/passive paths need their own real
 * execution after baseline; old active states never acquire fresh authority. */
public final class MercyClient implements HeroClientModule {
    static {
        NativeSkillReader.register("mercyStaff",new NativeSkillReader.Spec(MercyServer.HERO,0x058000000000006bL,Map.of("heal",7,"boost",19)));
        NativeSkillReader.register("mercyPistol",new NativeSkillReader.Spec(MercyServer.HERO,0x058000000000006dL,Map.of("volley",10)));
        NativeSkillReader.register("mercyGuardian",new NativeSkillReader.Spec(MercyServer.HERO,0x058000000000006eL,Map.of("search",25,"move",2)));
        NativeSkillReader.register("mercyResurrect",new NativeSkillReader.Spec(MercyServer.HERO,0x05800000000000caL,Map.of("search",36,"wait",40)));
        NativeSkillReader.register("mercyPassive",new NativeSkillReader.Spec(MercyServer.HERO,0x0580000000000071L,Map.of("glide",2,"selfHeal",4)));
    }
    public static final MercyClient INSTANCE=new MercyClient();
    private final NativeSkillReader staff=new NativeSkillReader("mercyStaff"),pistol=new NativeSkillReader("mercyPistol"),
        guardian=new NativeSkillReader("mercyGuardian"),resurrect=new NativeSkillReader("mercyResurrect"),passive=new NativeSkillReader("mercyPassive");
    private final Map<String,NativeSkillReader.Entry> previous=new HashMap<>();
    private final Map<String,SupportNativeGate> gates=new HashMap<>();
    private MercyServer.Scope scope;
    private long serial,frame,frameWall,frameSource;
    private String error="";
    private boolean renderRegistered;
    private MercyClient(){}
    @Override public void tick(MinecraftClient c){
        var h=HostPoseReader.INSTANCE.latest();var server=c.getServer();
        long hero=NativeLocomotionController.INSTANCE.hero(),model=NativeLocomotionController.INSTANCE.modelId(),now=System.currentTimeMillis();
        if(h==null||h.flags()!=1||c.player==null||!c.player.isAlive()||c.world==null||server==null||hero!=MercyServer.HERO||model==0){resetSession();return;}
        if(h.generation()!=frameSource||h.frame()!=frame){frameSource=h.generation();frame=h.frame();frameWall=now;}
        if(now<frameWall||now-frameWall>150){resetSession();error="native frame stale; baseline revoked";return;}
        long world=NativeWorldIdentity.of(server,c.world.getRegistryKey());
        if(scope==null||scope.source()!=h.generation()||scope.model()!=model||scope.world()!=world||!scope.owner().equals(c.player.getUuid())){
            resetSession();scope=new MercyServer.Scope(c.player.getUuid(),world,h.generation(),model,++serial);
        }
        var s=scope;MercyServer.INSTANCE.permit(s,now);error="";
        var states=staff.poll(h,model,hero);
        if(states==null){
            previous.remove("heal");previous.remove("boost");error=staff.error;
            server.execute(()->MercyServer.INSTANCE.stopChannel(s));
        }else for(var kind:MercyServer.Channel.values()){
            String name=kind==MercyServer.Channel.HEAL?"heal":"boost";var e=states.entries().get(name);var old=previous.put(name,e);
            if(old==null)continue;
            if(e.tick()<old.tick()){previous.remove(name);server.execute(()->MercyServer.INSTANCE.stopChannel(s));continue;}
            if(e.tick()>0&&!e.equals(old))server.execute(()->MercyServer.INSTANCE.channel(server,s,kind,e.tick(),e.active(),now));
        }
        var gs=guardian.poll(h,model,hero);
        if(gs==null){clearSupport(c);if(error.isEmpty())error=guardian.error;}
        else{attemptState(c,gs,"guardian","search");phase(c,gs,"guardian","move",now);}
        attempt(c,h,model,hero,resurrect,"resurrect","search");
        var ps=pistol.poll(h,model,hero);
        var pg=gates.computeIfAbsent("pistol",key->new SupportNativeGate());
        if(ps==null){pg.clear();if(error.isEmpty())error=pistol.error;}
        else{var e=ps.entries().get("volley");if(pg.sample(e.tick(),e.active(),true)==SupportNativeGate.Edge.PULSE)
            server.execute(()->MercyServer.INSTANCE.pistol(server,s,e.tick(),now));}
        var passiveState=passive.poll(h,model,hero);
        if(passiveState==null){clearSupport(c);if(error.isEmpty())error=passive.error;}
        else{phase(c,passiveState,"glide","glide",now);phase(c,passiveState,"selfHeal","selfHeal",now);}
    }
    private void clearSupport(MinecraftClient c){
        previous.remove("guardian");
        for(String kind:new String[]{"guardian","glide","selfHeal"})gates.computeIfAbsent(kind,key->new SupportNativeGate()).clear();
        var s=scope;c.getServer().execute(()->MercyServer.INSTANCE.stopSupport(s));
    }
    private void phase(MinecraftClient c,NativeSkillReader.State state,String kind,String node,long now){
        var e=state.entries().get(node);var gate=gates.computeIfAbsent(kind,key->new SupportNativeGate());
        var edge=gate.sample(e.tick(),e.active(),false);var s=scope;var server=c.getServer();
        if(edge==SupportNativeGate.Edge.RESET){clearSupport(c);return;}
        if(edge==SupportNativeGate.Edge.BEGIN||edge==SupportNativeGate.Edge.END)
            server.execute(()->MercyServer.INSTANCE.support(server,s,kind,e.tick(),edge==SupportNativeGate.Edge.BEGIN,now));
    }
    private void attempt(MinecraftClient c,HostPoseReader.Pose h,long model,long hero,NativeSkillReader reader,String kind,String node){
        var state=reader.poll(h,model,hero);
        if(state==null){previous.remove(kind);if(error.isEmpty())error=reader.error;return;}
        attemptState(c,state,kind,node);
    }
    private void attemptState(MinecraftClient c,NativeSkillReader.State state,String kind,String node){
        var e=state.entries().get(node);var old=previous.put(kind,e);var s=scope;var server=c.getServer();
        long wall=System.currentTimeMillis();
        if(old!=null&&e.tick()>old.tick()&&!e.active())server.execute(()->MercyServer.INSTANCE.attempt(server,s,kind,e.tick(),wall));
    }
    /** Called by the shared travel mixin after integration; MC Entity.move resolves collision. */
    public boolean travel(MinecraftClient c){
        var h=HostPoseReader.INSTANCE.latest();long now=System.currentTimeMillis();
        if(c.player==null||c.world==null||c.getServer()==null||scope==null||!scope.owner().equals(c.player.getUuid())
                ||scope.world()!=NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey())||h==null||h.flags()!=1||now-frameWall<0||now-frameWall>150
                ||h.generation()!=scope.source()||NativeLocomotionController.INSTANCE.hero()!=MercyServer.HERO
                ||NativeLocomotionController.INSTANCE.modelId()!=scope.model())return false;
        var view=MercyServer.INSTANCE.guardianView;var gate=gates.get("guardian");
        if(gate!=null&&gate.active()&&view!=null&&scope.equals(view.scope())&&now-view.wall()>=0&&now-view.wall()<=150){
            var delta=view.destination().subtract(c.player.getPos());double length=delta.length();
            if(length>.8&&length<=15){var motion=delta.normalize().multiply(Math.min(.9,length-.8));
                c.player.setVelocity(net.minecraft.util.math.Vec3d.ZERO);c.player.move(net.minecraft.entity.MovementType.SELF,motion);c.player.fallDistance=0;return true;}
        }
        gate=gates.get("glide");
        if(gate!=null&&gate.active()&&!c.player.isOnGround()&&c.player.getVelocity().y<-.1){
            var v=c.player.getVelocity();c.player.setVelocity(v.x,-.1,v.z);c.player.fallDistance=0;
        }return false;
    }
    @Override public void registerRender(){
        if(renderRegistered)return;renderRegistered=true;
        WorldRenderEvents.AFTER_ENTITIES.register(ctx->{
            var c=MinecraftClient.getInstance();if(!Boolean.getBoolean("owmc.frameExport")||c.world==null||c.player==null||ctx.matrixStack()==null)return;
            // Only a newly executed original pistol Volley may populate these views.
            for(var v:MercyServer.INSTANCE.projectiles){
                if(scope==null||!scope.equals(v.scope())||System.currentTimeMillis()-v.wall()>150)continue;
                OriginalWorldRenderer.mesh(ctx,"mercy-pistol",v.at(),null,true,.12f,.12f,.12f,1);
            }
        });
    }
    @Override public void resetSession(){
        MercyServer.INSTANCE.revoke();staff.close();pistol.close();guardian.close();resurrect.close();passive.close();previous.clear();gates.clear();scope=null;error="";
    }
    @Override public String errorKey(){return "mercyError";}
    @Override public String error(){return error;}
}
