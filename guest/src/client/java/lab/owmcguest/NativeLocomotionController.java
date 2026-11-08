package lab.owmcguest;

import net.minecraft.client.MinecraftClient;
import net.minecraft.util.math.Vec3d;

public final class NativeLocomotionController implements AutoCloseable {
    public static final NativeLocomotionController INSTANCE=new NativeLocomotionController();
    private final NativeLocomotionReader reader=new NativeLocomotionReader();
    private int age=-1;private Object player;private double[] speeds;
    private long verifiedAt;
    public static volatile String status="{\"ready\":false}";
    public boolean isGenji(){return reader.genji();}
    public long hero(){return reader.hero();}
    public long modelId(){return reader.modelId();}
    public static String mouseCaptureStatus(){return HostMouseCaptureGuard.status();}
    double[] nativeVelocity(){return reader.nativeVelocity();}
    public boolean wallClimbReady(){return speeds!=null&&verifiedAt!=0&&System.currentTimeMillis()-verifiedAt<=150&&WallClimbPhase.hero(hero())&&modelId()!=0;}
    public void tick(MinecraftClient client){
        var p=client.player;
        if(p==null){close();status="{\"ready\":false}";return;}
        if(!Boolean.getBoolean("owmc.hostMovement")||!Boolean.getBoolean("owmc.frameExport"))return;
        // Water and stationary travel may skip the movement injection. Binding
        // readiness must recover on ordinary ticks without requiring a keypress.
        if(player!=p||age!=p.age){player=p;age=p.age;speeds=reader.poll(HostPoseReader.INSTANCE.latest());
            verifiedAt=speeds==null?0:System.currentTimeMillis();
            long world=client.world!=null&&client.getServer()!=null?NativeWorldIdentity.of(client.getServer(),client.world.getRegistryKey()):0;
            status="{\"ready\":"+(speeds!=null)+",\"hero\":"+hero()+",\"modelId\":"+modelId()+",\"worldId\":"+world+",\"baseSpeeds\":"+new com.google.gson.Gson().toJson(reader.baseSpeeds())+",\"effectiveSpeeds\":"+new com.google.gson.Gson().toJson(speeds)+",\"speedSource\":\"native-computed-directional-limits\",\"mouseCapture\":"+mouseCaptureStatus()+",\"error\":"+new com.google.gson.Gson().toJson(reader.error)+"}";
        }
    }
    public Vec3d movement(Vec3d vanilla){
        var client=MinecraftClient.getInstance();var p=client.player;
        if(p==null||!Boolean.getBoolean("owmc.hostMovement")||!Boolean.getBoolean("owmc.frameExport"))return vanilla;
        var host=HostPoseReader.INSTANCE.latest();
        tick(client);
        // MC 适配：用户第六次要求；Q Begin 起锁，施法 End 与同次龙 released 均到达才解锁。
        if(HanzoControlController.movementLocked()){
            NativeRollController.INSTANCE.discardMotion();NativeMotorController.INSTANCE.discardMotion();
            p.setVelocity(Vec3d.ZERO);return Vec3d.ZERO;
        }
        if(NativeDeadeyeController.movementLocked()||RoadhogClient.breatherLocked()){
            NativeRollController.INSTANCE.discardMotion();NativeMotorController.INSTANCE.discardMotion();
            return new Vec3d(0,p.getAbilities().flying?0:vanilla.y,0);
        }
        if(p.getAbilities().flying||p.isTouchingWater()||p.isInLava()||p.hasVehicle()||p.isFallFlying())return vanilla;
        var winstonMomentum=WinstonClient.INSTANCE.momentumMovement(client,vanilla);if(winstonMomentum!=null)return winstonMomentum;
        var grappleMomentum=NativeGrappleController.INSTANCE.momentumMovement(client,vanilla);if(grappleMomentum!=null)return grappleMomentum;
        var roll=NativeRollController.INSTANCE.movement(vanilla);if(roll!=null)return roll;
        var motor=NativeMotorController.INSTANCE.movement(client,vanilla);if(motor!=null)return motor;
        return baseMovement(vanilla);
    }
    /** Shared direct-input direction; no motor recursion or native inertia. */
    Vec3d baseMovement(Vec3d vanilla){
        var host=HostPoseReader.INSTANCE.latest();
        int bits=host!=null&&host.inputActive()?host.movementBits():0;
        bits=HanzoControlController.movementBits(MinecraftClient.getInstance(),host,bits);
        return directionalMovement(vanilla,bits);
    }
    Vec3d directionalMovement(Vec3d vanilla,int bits){
        var host=HostPoseReader.INSTANCE.latest();
        var local=NativeWalkSpeed.local(bits,speeds);
        if(host==null)return new Vec3d(0,vanilla.y,0);
        var f=new org.joml.Vector3f(0,0,-1).rotate(host.rotation());
        var forward=new Vec3d(f.x,0,f.z).normalize();var right=new Vec3d(-forward.z,0,forward.x);
        var horizontal=right.multiply(local[0]).add(forward.multiply(local[1]));
        // Keep vanilla vertical movement/gravity and let Entity.move resolve all block shapes.
        return new Vec3d(horizontal.x,vanilla.y,horizontal.z);
    }
    double baseRunSpeed(){return speeds==null?0:Math.max(speeds[0],Math.max(speeds[1],speeds[2]));}
    @Override public void close(){reader.close();player=null;age=-1;speeds=null;verifiedAt=0;}
    void resetSession(){close();status="{\"ready\":false,\"error\":\"native session transition\"}";}
}
