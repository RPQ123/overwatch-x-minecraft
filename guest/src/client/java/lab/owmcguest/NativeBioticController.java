package lab.owmcguest;

import net.minecraft.client.MinecraftClient;

/** Join a newly observed original cast with its actual Volley before deploying. */
final class NativeBioticController implements AutoCloseable {
    static final NativeBioticController INSTANCE=new NativeBioticController();
    private final NativeSkillReader reader=new NativeSkillReader("biotic");
    private final NativeDeploymentGate gate=new NativeDeploymentGate();
    static volatile String error="";
    void tick(MinecraftClient client){
        var host=HostPoseReader.INSTANCE.latest();long hero=NativeLocomotionController.INSTANCE.hero(),model=NativeLocomotionController.INSTANCE.modelId();
        if(host==null||!host.inputActive()||client.player==null||!client.player.isAlive()||client.world==null||client.getServer()==null||hero!=NativeBioticRuntime.HERO){resetSession();return;}
        var state=reader.poll(host,model,hero);if(state==null){error=reader.error;return;}
        var parameters=reader.bioticParameters();if(parameters==null){error=reader.error;return;}
        long world=NativeWorldIdentity.of(client.getServer(),client.world.getRegistryKey()),now=System.currentTimeMillis();
        var cast=state.entries().get("cast");var deploy=state.entries().get("deploy");error="";
        if(!gate.observe(new NativeDeploymentGate.Scope(host.generation(),world,model),cast.tick(),cast.active(),deploy.tick(),now))return;
        var server=client.getServer();var owner=client.player.getUuid();var forward=client.player.getRotationVec(1).multiply(1,0,1).normalize();
        var right=new net.minecraft.util.math.Vec3d(-forward.z,0,forward.x);
        var at=client.player.getPos().add(forward.multiply(.35)).add(right.multiply(-.22)).add(0,1.15,0);
        var command=new NativeBioticRuntime.Deployment(owner,world,host.generation(),model,deploy.tick(),now,at,parameters[0],parameters[1],parameters[2]);
        server.execute(()->NativeBioticRuntime.deploy(server,command));
    }
    void resetSession(){reader.close();gate.reset();error="";}
    @Override public void close(){resetSession();}
}
