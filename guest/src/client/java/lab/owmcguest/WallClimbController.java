package lab.owmcguest;

import net.minecraft.client.MinecraftClient;
import net.minecraft.entity.MovementType;
import net.minecraft.util.math.Direction;
import net.minecraft.util.math.Vec3d;

/** Original window supplies intent; MC supplies wall shapes and final movement. */
public final class WallClimbController {
    public static final WallClimbController INSTANCE=new WallClimbController();
    private final WallClimbPhase phase=new WallClimbPhase();
    private long starts,ticks,blocked;
    private double distance;
    private int contactAge=-1;
    private long contactModel;
    private String diagnostics="";
    private boolean mantling;
    private double mantleDistance;
    private double mantleLift;
    private int lastBits;
    public long nativeClimbModel(MinecraftClient client){
        return client.player!=null&&phase.active()&&client.player.age==contactAge
            &&NativeLocomotionController.INSTANCE.wallClimbReady()&&NativeLocomotionController.INSTANCE.modelId()==contactModel?contactModel:0;
    }
    public static volatile String status="{\"active\":false}";
    void resetSession(){phase.invalidate();mantling=false;contactAge=-1;contactModel=0;mantleDistance=0;mantleLift=0;diagnostics="\"sessionTransition\":true";publish(false,false);}
    public boolean travel(MinecraftClient client){
        contactAge=-1;contactModel=0;
        var p=client.player;var host=HostPoseReader.INSTANCE.latest();
        if(p==null||client.world==null||host==null||host.flags()!=1||!host.inputActive()){
            phase.invalidate();mantling=false;mantleDistance=0;publish(false,false);return false;
        }
        int bits=host.movementBits();lastBits=bits;boolean request=(bits&17)==17&&(bits&32)==0;
        NativeLocomotionController.INSTANCE.tick(client);
        var direction=new org.joml.Vector3f(0,0,-1).rotate(host.rotation());
        var forward=new Vec3d(direction.x,0,direction.z).normalize();
        var body=p.getBoundingBox();
        var sweep=body.stretch(forward.multiply(.36)).expand(.015,0,.015);
        boolean contact=forward.lengthSquared()>.5&&client.world.getBlockCollisions(p,sweep).iterator().hasNext();
        // A one-block ledge is ordinary step-up terrain, not a climbable wall.
        // Sample above the player's actual feet so fractional block heights work.
        var probe=net.minecraft.util.math.BlockPos.ofFloored(p.getPos().add(forward.multiply(.34)));
        var upper=net.minecraft.util.math.BlockPos.ofFloored(p.getPos().add(forward.multiply(.34)).add(0,1.0,0));
        boolean upperShape=!client.world.getBlockState(upper).getCollisionShape(client.world,upper).isEmpty();
        boolean was=phase.active();
        boolean wall=WallClimbPhase.wallAdmission(contact,upperShape,was);
        boolean eligible=p.isAlive()&&!p.isSpectator()&&!p.getAbilities().flying
            &&!p.isTouchingWater()&&!p.isInLava()&&client.currentScreen==null
            &&NativeLocomotionController.INSTANCE.wallClimbReady()
            &&(NativeLocomotionController.INSTANCE.hero()!=0x02e0000000000029L||(NativeDashController.INSTANCE.heroReady()&&NativeDashController.INSTANCE.motion()==null));
        diagnostics="\"bits\":"+bits+",\"eligible\":"+eligible+",\"feetY\":"+p.getY()
            +",\"forwardX\":"+forward.x+",\"forwardZ\":"+forward.z+",\"probe\":\""+probe.getX()+","+probe.getY()+","+probe.getZ()
            +"\",\"upperShape\":"+upperShape;
        if(mantling){
            if(!request||!eligible){mantling=false;phase.blocked();publish(wall,request);return false;}
            return mantle(client,p,forward,wall,request);
        }
        double topLift=was&&request&&eligible&&!wall?mantleSurface(client,p,forward):Double.NaN;
        if(Double.isFinite(topLift)){
            mantling=true;mantleDistance=0;
            mantleLift=topLift;
            return mantle(client,p,forward,wall,request);
        }
        double rise=phase.step(host.generation(),p.age,p.isOnGround(),request,wall,eligible,p.getY());
        if(rise<=0){publish(wall,request);return false;}
        if(!was)starts++;
        double before=p.getY();
        p.setVelocity(Vec3d.ZERO);
        // Entity.move performs vanilla swept block collision, including ceilings.
        p.move(MovementType.SELF,forward.multiply(.04).add(0,rise,0));
        NativeMotorController.INSTANCE.discardMotion();
        double actual=p.getY()-before;distance+=Math.max(0,actual);ticks++;p.fallDistance=0;
        if(actual+1e-5<rise){phase.blocked();blocked++;}
        if(phase.active()){contactAge=p.age;contactModel=NativeLocomotionController.INSTANCE.modelId();}
        publish(wall,request);return true;
    }
    private double mantleSurface(MinecraftClient client,net.minecraft.client.network.ClientPlayerEntity p,Vec3d forward){
        var target=p.getPos().add(forward.multiply(.68));
        int minY=net.minecraft.util.math.MathHelper.floor(p.getY()-1.0);
        int maxY=net.minecraft.util.math.MathHelper.floor(p.getY()+.25);
        for(int y=minY;y<=maxY;y++){
            var pos=net.minecraft.util.math.BlockPos.ofFloored(target.x,y,target.z);
            var shape=client.world.getBlockState(pos).getCollisionShape(client.world,pos);
            if(shape.isEmpty())continue;
            double top=pos.getY()+shape.getMax(Direction.Axis.Y);
            double rise=top-p.getY();
            if(rise<-.35||rise>.25)continue;
            var landing=p.getBoundingBox().offset(forward.multiply(.68)).offset(0,rise,0);
            if(client.world.isSpaceEmpty(p,landing))return rise;
        }
        return Double.NaN;
    }
    private boolean mantle(MinecraftClient client,net.minecraft.client.network.ClientPlayerEntity p,Vec3d forward,
                           boolean wall,boolean request){
        double before=p.getX();double beforeZ=p.getZ();double beforeY=p.getY();
        p.setVelocity(Vec3d.ZERO);
        if(mantleLift>1e-5){
            double lift=mantleLift;mantleLift=0;
            p.move(MovementType.SELF,new Vec3d(0,lift,0));
            if(p.getY()-beforeY+1e-5<lift){mantling=false;phase.blocked();publish(wall,request);return false;}
        }
        p.move(MovementType.SELF,forward.multiply(.32));
        NativeMotorController.INSTANCE.discardMotion();
        double advanced=Math.hypot(p.getX()-before,p.getZ()-beforeZ);
        mantleDistance+=advanced;
        ticks++;p.fallDistance=0;
        if(advanced<.30-1e-5||mantleDistance>=.96){
            mantling=false;phase.blocked();
        }else if(phase.active()){
            contactAge=p.age;contactModel=NativeLocomotionController.INSTANCE.modelId();
        }
        diagnostics="\"bits\":"+lastBits+",\"eligible\":true,\"mantle\":true,\"mantleDistance\":"+mantleDistance;
        publish(wall,request);return advanced>0;
    }
    private void publish(boolean wall,boolean request){
        status="{\"active\":"+phase.active()+",\"wallContact\":"+wall+",\"requested\":"+request
            +",\"starts\":"+starts+",\"ticks\":"+ticks+",\"distance\":"+distance+",\"ceilingStops\":"+blocked
            +",\"nativeAnimationRequested\":"+(contactModel!=0)+","+diagnostics+"}";
    }
}
