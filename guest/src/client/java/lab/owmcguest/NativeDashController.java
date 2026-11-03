package lab.owmcguest;

import net.minecraft.client.MinecraftClient;
import net.minecraft.util.math.Vec3d;

public final class NativeDashController implements AutoCloseable {
    public static final NativeDashController INSTANCE=new NativeDashController();
    private final NativeAbilityReader reader=new NativeAbilityReader();
    private final NativeDashPhase phase=new NativeDashPhase();
    private Vec3d direction=Vec3d.ZERO;
    private double speed;
    private long heroVerifiedAt,modelId;
    private NativeEliminationRuntime.Reset pendingReset;
    public boolean heroReady(){return heroVerifiedAt!=0&&System.currentTimeMillis()-heroVerifiedAt<=150;}
    public long modelId(){return heroReady()?modelId:0;}
    public static volatile String error="waiting for native ability";
    public static volatile String bindingStatus="{\"ready\":false}";
    public void tick(MinecraftClient client){
        var host=HostPoseReader.INSTANCE.latest();var state=reader.poll(host);long now=System.currentTimeMillis();
        error=reader.error;
        heroVerifiedAt=host!=null&&host.flags()==1&&error.isEmpty()?now:0;
        modelId=state==null?0:state.model();
        if(state==null||client.player==null||client.world==null||client.getServer()==null||!client.player.isAlive()) {bindingStatus="{\"ready\":false}";phase.invalidate();return;}
        var server=client.getServer();var id=client.player.getUuid();
        long world=NativeWorldIdentity.of(server,client.world.getRegistryKey());
        bindingStatus="{\"ready\":true,\"modelId\":"+state.model()+",\"worldId\":"+world+",\"hostGeneration\":"+state.source()+",\"observedTick\":"+state.tick()+",\"executing\":"+state.active()+"}";
        NativeEliminationRuntime.Reset reset;while((reset=NativeEliminationRuntime.poll())!=null)pendingReset=reset;
        if(pendingReset!=null){
            var ticket=pendingReset;
            if(ticket.generation()!=state.source()||ticket.model()!=state.model()||ticket.world()!=world||now-ticket.wallMs()>2000||now<ticket.wallMs())pendingReset=null;
            else if(!state.active()){
                try{if(reader.resetCooldown(state)){NativeEliminationRuntime.applied++;pendingReset=null;}}
                catch(Exception failure){error=failure.toString();reader.close();}
            }
        }
        boolean begin=phase.observe(state.source(),state.model(),state.tick(),state.active(),now);
        if(begin){
            var f=new org.joml.Vector3f(0,0,-1).rotate(host.rotation());direction=new Vec3d(f.x,f.y,f.z).normalize();speed=state.speed();
            server.execute(()->NativeDashRuntime.begin(server,id,world,state.source(),state.model(),state.tick(),state.damage()));
        }
        boolean active=phase.active(now);long tick=phase.tick();
        server.execute(()->NativeDashRuntime.refresh(id,state.source(),state.model(),tick,active));
    }
    public Vec3d motion(){return phase.active(System.currentTimeMillis())?direction.multiply(speed/20):null;}
    @Override public void close(){heroVerifiedAt=0;pendingReset=null;phase.invalidate();reader.close();}
    void resetSession(){close();modelId=0;bindingStatus="{\"ready\":false}";error="native session transition";}
}
