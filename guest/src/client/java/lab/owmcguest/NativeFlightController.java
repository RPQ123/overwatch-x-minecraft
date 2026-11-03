package lab.owmcguest;

import net.minecraft.client.MinecraftClient;
import net.minecraft.entity.MovementType;
import net.minecraft.util.math.Vec3d;

/** Original Pharah physics resolves against actual MC blocks, including ceilings. */
public final class NativeFlightController implements AutoCloseable {
    public static final NativeFlightController INSTANCE=new NativeFlightController();
    private final NativeFlightReader reader=new NativeFlightReader();
    private final NativeSkillReader skills=new NativeSkillReader();
    private double[] previous;private long sequence,world,model;private int blocked;
    public static volatile String status="{\"ready\":false}";
    public boolean requested(MinecraftClient client){
        var p=client.player;var host=HostPoseReader.INSTANCE.latest();
        return p!=null&&client.world!=null&&client.getServer()!=null&&p.isAlive()&&!p.getAbilities().flying&&!p.hasVehicle()&&!p.isTouchingWater()&&!p.isInLava()&&!p.isFallFlying()
            &&host!=null&&host.flags()==1&&NativeLocomotionController.INSTANCE.hero()==0x02e0000000000008L&&NativeLocomotionController.INSTANCE.modelId()!=0;
    }
    public int blockedAxes(){return blocked;}
    public boolean travel(MinecraftClient client){
        if(!requested(client)){resetSession();return false;}
        long nextWorld=NativeWorldIdentity.of(client.getServer(),client.world.getRegistryKey()),nextModel=NativeLocomotionController.INSTANCE.modelId();
        if(world!=nextWorld||model!=nextModel){previous=null;sequence=0;blocked=0;world=nextWorld;model=nextModel;}
        var motion=reader.poll(HostPoseReader.INSTANCE.latest(),world,model);
        if(motion==null){previous=null;status="{\"ready\":false,\"error\":"+new com.google.gson.Gson().toJson(reader.error)+"}";return true;}
        var p=client.player;
        if(previous==null){previous=motion.total().clone();sequence=motion.sequence();return true;}
        if(motion.sequence()==sequence)return true;
        var delta=new Vec3d(motion.total()[0]-previous[0],motion.total()[1]-previous[1],motion.total()[2]-previous[2]);previous=motion.total().clone();sequence=motion.sequence();
        if(delta.lengthSquared()>25){previous=null;blocked=0;return true;}
        // The supplied offline mover retains horizontal drift after Jump Jet
        // even with a zero movement command. Keep the already verified native
        // directional speed/input adapter; import original vertical integration.
        var host=HostPoseReader.INSTANCE.latest();
        boolean heldSpace=host!=null&&host.inputActive()&&(host.movementBits()&16)!=0;
        double lifted=NativeHoverLift.apply(delta.y,motion.velocity()[1],heldSpace);
        boolean boosted=lifted!=delta.y;
        delta=NativeLocomotionController.INSTANCE.movement(new Vec3d(0,lifted,0));
        var phase=skills.poll(HostPoseReader.INSTANCE.latest(),model,0x02e0000000000008L);
        boolean barrage=phase!=null&&(phase.active("barrage")||phase.active("windup")||phase.active("firing"));
        if(barrage)delta=Vec3d.ZERO;
        delta=delta.add(NativeConcussiveController.INSTANCE.motion(client));
        var rocketJump=NativeRocketSelfImpulseClient.INSTANCE.pharahMotion(client);
        delta=delta.add(rocketJump);
        var before=p.getPos();p.setVelocity(Vec3d.ZERO);p.move(MovementType.SELF,delta);var actual=p.getPos().subtract(before);
        blocked=(Math.abs(actual.x-delta.x)>1e-5?1:0)|(Math.abs(actual.y-delta.y)>1e-5?2:0)|(Math.abs(actual.z-delta.z)>1e-5?4:0);
        NativeRocketSelfImpulseClient.INSTANCE.pharahBlocked(blocked);
        var velocity=motion.velocity();p.setVelocity((blocked&1)!=0?0:delta.x,(blocked&2)!=0?0:(boosted||rocketJump.lengthSquared()>1e-10)?actual.y:velocity[1]/20,(blocked&4)!=0?0:delta.z);p.fallDistance=0;
        status="{\"ready\":true,\"sequence\":"+sequence+",\"blockedAxes\":"+blocked+",\"barrage\":"+barrage+",\"heldSpaceLift\":"+boosted+",\"appliedVerticalSpeed\":"+(actual.y*20)+",\"nativeVelocity\":"+new com.google.gson.Gson().toJson(velocity)+"}";
        return true;
    }
    @Override public void close(){reader.close();skills.close();previous=null;sequence=world=model=0;blocked=0;}
    void resetSession(){close();status="{\"ready\":false}";}
}
