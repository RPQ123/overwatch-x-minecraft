package lab.owmcguest;
import net.minecraft.client.MinecraftClient;

/** Read actual ModifyHealth Begin/End; no keyboard-triggered healing. */
final class NativeSustainController implements AutoCloseable {
    static final NativeSustainController INSTANCE=new NativeSustainController();
    private final NativeSkillReader reader=new NativeSkillReader("sustain");
    static volatile String error="";
    void tick(MinecraftClient client){
        var host=HostPoseReader.INSTANCE.latest();long hero=NativeLocomotionController.INSTANCE.hero();
        if(host==null||host.flags()!=1||client.player==null||!client.player.isAlive()||client.world==null||client.getServer()==null||!NativeSustainRuntime.supported(hero)){reader.close();error="";return;}
        var s=reader.poll(host,NativeLocomotionController.INSTANCE.modelId(),hero);
        if(s==null){error=reader.error;return;}
        var value=reader.healing();if(value==null){error=reader.error;return;}error="";
        var phase=s.entries().get("heal");var server=client.getServer();var owner=client.player.getUuid();long world=NativeWorldIdentity.of(server,client.world.getRegistryKey()),wall=System.currentTimeMillis();
        server.execute(()->NativeSustainRuntime.refresh(owner,world,s.source(),s.model(),hero,phase.tick(),phase.active(),value.amount(),value.interval(),wall));
    }
    void resetSession(){reader.close();error="";}
    @Override public void close(){resetSession();}
}
