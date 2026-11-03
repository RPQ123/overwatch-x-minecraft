package lab.owmcguest;

import net.minecraft.client.MinecraftClient;

/** Observe the original cast; native logic owner completes its actual Anim End. */
public final class NativeRecallController implements AutoCloseable {
    static final NativeRecallController INSTANCE=new NativeRecallController();
    private final NativeSkillReader reader=new NativeSkillReader("recall");
    private final UltimateCalloutGate gate=new UltimateCalloutGate();
    private long session,pending,acknowledged;private static volatile boolean casting;private static volatile long castingWall;
    static volatile String error="";
    public static boolean rewinding(){return casting&&System.currentTimeMillis()-castingWall<=200;}
    void tick(MinecraftClient c){
        var h=HostPoseReader.INSTANCE.latest();long hero=NativeLocomotionController.INSTANCE.hero(),model=NativeLocomotionController.INSTANCE.modelId();
        // Focus is required to ADMIT Recall, not to finish an already observed
        // original cast. Resetting pending on Alt-Tab lost the MC End receipt
        // and left original history state1 holding the guns indefinitely.
        if(h==null||h.flags()!=1||c.player==null||!c.player.isAlive()||c.world==null||c.getServer()==null||hero!=NativeRecallRuntime.HERO){resetSession();return;}
        var state=reader.poll(h,model,hero);if(state==null){error=reader.error;return;}error="";
        long world=NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey()),now=System.currentTimeMillis();var cast=state.entries().get("cast");casting=cast.active();castingWall=now;
        var scope=new NativeRecallRuntime.Scope(c.player.getUuid(),world,h.generation(),model);var server=c.getServer();
        if(gate.observe(session,h.generation(),model,world,h.inputActive()&&cast.active()?cast.tick():0)){
            pending=cast.tick();long begin=pending;
            RecallStartSound.begin(c,scope,begin,now);
            server.execute(()->NativeRecallRuntime.begin(server,scope,begin,now));
        }
        if(pending!=0&&!cast.active()&&cast.tick()>=pending){long begin=pending;pending=0;server.execute(()->NativeRecallRuntime.finish(server,scope,begin,cast.tick(),now));}
        var result=NativeRecallRuntime.completion;
        if(result!=null&&result.scope().equals(scope)&&result.begin()!=acknowledged&&!cast.active()&&cast.tick()>=result.begin()){
            try{
                var path=java.nio.file.Path.of(System.getProperty("owmc.nativeEventsDirectory")).resolve("native-recall-ack-"+h.pid()+".bin");var tmp=path.resolveSibling(path.getFileName()+".tmp");
                // Fresh observed original End + exact same scope authorizes a
                // terminal receipt retry, never another MC rewind/heal. phase3
                // also releases original history after a transient pose reset.
                var receipt=new NativeRecallRuntime.Completion(scope,result.begin(),now,result.moved());
                java.nio.file.Files.write(tmp,reader.recallCompletion(receipt));java.nio.file.Files.move(tmp,path,java.nio.file.StandardCopyOption.REPLACE_EXISTING);acknowledged=result.begin();
            }catch(java.io.IOException e){error="Recall completion transport retry: "+e;}
            catch(RuntimeException e){error="Recall completion owner unavailable: "+e;}
        }
    }
    void resetSession(){session++;reader.close();gate.reset();pending=acknowledged=0;casting=false;error="";}
    @Override public void close(){resetSession();}
}
