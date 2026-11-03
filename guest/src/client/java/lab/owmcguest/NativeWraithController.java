package lab.owmcguest;
import net.minecraft.client.MinecraftClient;

/** Native event admission; the original logic owner releases the actual End. */
final class NativeWraithController implements AutoCloseable {
    static final NativeWraithController INSTANCE=new NativeWraithController();
    private final NativeSkillReader reader=new NativeSkillReader("wraith");
    private final NativeAbilityContinuationGate gate=new NativeAbilityContinuationGate();
    private long frame,lastFrameWall;
    static volatile String error="";
    static boolean active(){
        var f=NativeWraithRuntime.view;var c=MinecraftClient.getInstance();var h=HostPoseReader.INSTANCE.latest();
        return f!=null&&h!=null&&c.player!=null&&c.world!=null&&c.getServer()!=null&&c.player.isAlive()
            &&NativeLocomotionController.INSTANCE.hero()==NativeReaperRuntime.HERO&&f.scope().model()==NativeLocomotionController.INSTANCE.modelId()
            &&f.scope().world()==NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey())&&f.scope().source()==h.generation()&&System.currentTimeMillis()-f.wall()<=150;
    }
    void tick(MinecraftClient c){
        var h=HostPoseReader.INSTANCE.latest();long hero=NativeLocomotionController.INSTANCE.hero(),model=NativeLocomotionController.INSTANCE.modelId();
        if(h==null||h.flags()!=1||c.player==null||!c.player.isAlive()||c.world==null||c.getServer()==null||hero!=NativeReaperRuntime.HERO){resetSession();return;}
        long now=System.currentTimeMillis();if(h.frame()!=frame){frame=h.frame();lastFrameWall=now;}if(now-lastFrameWall>150)return;
        var state=reader.poll(h,model,hero);if(state==null){error=reader.error;return;}error="";
        long world=NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey());var root=state.entries().get("cast");
        boolean active=gate.observe(new NativeAbilityContinuationGate.Scope(h.generation(),world,model),root.tick(),root.active()&&state.active("animation"),h.inputActive(),now);
        var next=new NativeWraithRuntime.Phase(new NativeWraithRuntime.Scope(c.player.getUuid(),world,h.generation(),model),root.tick(),now,active);
        var server=c.getServer();server.execute(()->NativeWraithRuntime.refresh(server,next));
    }
    void resetSession(){reader.close();gate.reset();frame=lastFrameWall=0;error="";}
    @Override public void close(){resetSession();}
}
