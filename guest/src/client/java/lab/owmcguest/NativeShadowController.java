package lab.owmcguest;
import net.minecraft.client.MinecraftClient;

/** Current original E query/confirm and actual native departure/arrival phases. */
final class NativeShadowController implements AutoCloseable {
    static final NativeShadowController INSTANCE=new NativeShadowController();
    private final NativeSkillReader reader=new NativeSkillReader("shadow");
    private final NativeAbilityContinuationGate gate=new NativeAbilityContinuationGate();
    private long frame,lastFrameWall,lastWrite;
    static volatile String error="";
    static boolean casting(){
        var f=NativeShadowRuntime.view;var c=MinecraftClient.getInstance();var h=HostPoseReader.INSTANCE.latest();
        return f!=null&&f.phase()>0&&h!=null&&c.player!=null&&c.world!=null&&c.getServer()!=null&&c.player.isAlive()
            &&NativeLocomotionController.INSTANCE.hero()==NativeReaperRuntime.HERO&&f.scope().model()==NativeLocomotionController.INSTANCE.modelId()
            &&f.scope().world()==NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey())&&f.scope().source()==h.generation()&&System.currentTimeMillis()-f.wall()<=150;
    }
    void tick(MinecraftClient c){
        var h=HostPoseReader.INSTANCE.latest();long hero=NativeLocomotionController.INSTANCE.hero(),model=NativeLocomotionController.INSTANCE.modelId();
        if(h==null||h.flags()!=1||c.player==null||!c.player.isAlive()||c.world==null||c.getServer()==null||hero!=NativeReaperRuntime.HERO){resetSession();return;}
        long now=System.currentTimeMillis();if(h.frame()!=frame){frame=h.frame();lastFrameWall=now;}if(now-lastFrameWall>150)return;
        var state=reader.poll(h,model,hero);if(state==null){error=reader.error;return;}error="";
        long world=NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey());var aim=state.entries().get("aim");var out=state.entries().get("out");var in=state.entries().get("in");
        boolean aiming=gate.observe(new NativeAbilityContinuationGate.Scope(h.generation(),world,model),aim.tick(),aim.active(),h.inputActive(),now);
        var scope=new NativeShadowRuntime.Scope(c.player.getUuid(),world,h.generation(),model);
        var next=new NativeShadowRuntime.Phase(scope,aim.tick(),aiming,state.entries().get("confirm").tick(),out.tick(),out.active(),in.tick(),in.active(),now);
        var server=c.getServer();server.execute(()->NativeShadowRuntime.refresh(server,next));
        var result=NativeShadowRuntime.receipt;
        if(result!=null&&result.scope().equals(scope)&&now-result.wall()<=250&&now-lastWrite>=50){
            try{
                var path=java.nio.file.Path.of(System.getProperty("owmc.nativeEventsDirectory")).resolve("native-shadow-ack-"+h.pid()+".bin");var tmp=path.resolveSibling(path.getFileName()+".tmp");
                java.nio.file.Files.write(tmp,reader.shadowReceipt(result));java.nio.file.Files.move(tmp,path,java.nio.file.StandardCopyOption.REPLACE_EXISTING);lastWrite=now;
            }catch(java.io.IOException e){error="Shadow Step transport retry: "+e;}
            catch(RuntimeException e){error="Shadow Step owner unavailable: "+e;}
        }
    }
    void resetSession(){reader.close();gate.reset();frame=lastFrameWall=lastWrite=0;error="";}
    @Override public void close(){resetSession();}
}
