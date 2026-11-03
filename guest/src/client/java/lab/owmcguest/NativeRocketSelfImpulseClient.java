package lab.owmcguest;

import net.minecraft.client.MinecraftClient;
import net.minecraft.util.math.Vec3d;
import lab.owmcguest.NativeShotProtocol.Vec;

/** Mirrors a scoped server impulse once, preserving native flight/hover/Shift.
 * Pharah receives a full displacement overlay. Other heroes retain vanilla
 * vertical momentum plus a horizontal overlay AFTER native speed import. */
public final class NativeRocketSelfImpulseClient implements HeroClientModule {
    public static final NativeRocketSelfImpulseClient INSTANCE=new NativeRocketSelfImpulseClient();
    private static final long PHARAH=0x02e0000000000008L;
    private final RocketImpulseMotion motion=new RocketImpulseMotion();
    private long consumed,world,model,generation,hero;
    private java.util.UUID owner;
    private NativeRocketSelfImpulseClient(){}
    @Override public void tick(MinecraftClient client){
        var p=client.player;var h=HostPoseReader.INSTANCE.latest();
        long latest=NativeRocketSelfImpulse.cues.stream().mapToLong(NativeRocketSelfImpulse.Cue::sequence).max().orElse(consumed);
        if(!Boolean.getBoolean("owmc.frameExport")||p==null||!p.isAlive()||p.isSpectator()||p.hasVehicle()||client.world==null
            ||client.getServer()==null||h==null||!h.inputActive()||h.flags()!=1){consumed=Math.max(consumed,latest);clear();return;}
        long w=NativeWorldIdentity.of(client.getServer(),client.world.getRegistryKey()),m=NativeLocomotionController.INSTANCE.modelId(),nextHero=NativeLocomotionController.INSTANCE.hero();
        if(owner!=null&&(!owner.equals(p.getUuid())||world!=w||model!=m||generation!=h.generation()||hero!=nextHero))clear();
        for(var c:NativeRocketSelfImpulse.cues){
            if(c.sequence()<=consumed)continue;consumed=c.sequence();long age=System.currentTimeMillis()-c.wall();
            if(c.nativePid()!=h.pid()||c.hostGeneration()!=h.generation()||c.world()!=w||c.model()!=m||c.hero()!=nextHero
                ||!c.owner().equals(p.getUuid())||age< -50||age>250)continue;
            owner=p.getUuid();world=w;model=m;generation=h.generation();hero=nextHero;
            var push=c.impulse();motion.add(new Vec(push.x,hero==PHARAH?push.y:0,push.z),p.age);
            if(hero!=PHARAH)p.setVelocity(p.getVelocity().add(0,push.y,0));
            p.fallDistance=0;
        }
    }
    /** Add to NativeFlightController's native delta before its swept move. */
    public Vec3d pharahMotion(MinecraftClient client){
        tick(client);if(hero!=PHARAH||client.player==null)return Vec3d.ZERO;
        var v=motion.sample(client.player.age);return new Vec3d(v.x(),v.y(),v.z());
    }
    public void pharahBlocked(int axes){if(hero==PHARAH)motion.blocked(axes);}
    /** Apply AFTER NativeLocomotionController.movement in the shared mixin. */
    public Vec3d vanillaMovement(MinecraftClient client,Vec3d imported){
        tick(client);if(hero==PHARAH||client.player==null)return imported;
        var v=motion.sample(client.player.age);return imported.add(v.x(),0,v.z());
    }
    /** Compatibility only: never suspend native flight. Integrator removes
     * the obsolete branch and adds pharahMotion instead. */
    @Deprecated public boolean useVanillaTravel(MinecraftClient client){tick(client);return false;}
    private void clear(){owner=null;world=model=generation=hero=0;motion.reset();}
    @Override public void resetSession(){clear();consumed=NativeRocketSelfImpulse.cues.stream().mapToLong(NativeRocketSelfImpulse.Cue::sequence).max().orElse(consumed);}
    @Override public String errorKey(){return "rocketSelfImpulseClientError";}
    @Override public String error(){return "";}
}
