package lab.owmcguest;
import net.minecraft.client.MinecraftClient;
import net.minecraft.util.math.Vec3d;

/** Current input and original computed speed limits; MC owns actual collision. */
public final class NativeMotorController implements AutoCloseable {
    public static final NativeMotorController INSTANCE=new NativeMotorController();
    private final NativeSkillReader skills=new NativeSkillReader();
    public static volatile String status="{\"ready\":false}";
    /** Actual Sentry/transform state, never the Shift key or a guessed timer. */
    public boolean jumpLocked(){
        if(NativeRecallController.rewinding()||NativeShadowController.casting())return true;
        var loc=NativeLocomotionController.INSTANCE;var host=HostPoseReader.INSTANCE.latest();
        if(loc.hero()!=0x02e0000000000015L||loc.modelId()==0||host==null||!host.inputActive())return false;
        var state=skills.poll(host,loc.modelId(),loc.hero());
        return NativeMotorIntent.bastionRooted(state!=null&&state.active("recon"),state!=null&&state.active("sentry"),state!=null&&state.active("tank"));
    }
    public boolean requested(MinecraftClient client){
        var p=client.player;var host=HostPoseReader.INSTANCE.latest();
        return p!=null&&client.world!=null&&client.getServer()!=null&&p.isAlive()&&!p.getAbilities().flying&&!p.hasVehicle()&&!p.isTouchingWater()&&!p.isInLava()&&!p.isFallFlying()
            &&host!=null&&host.flags()==1&&NativeMotorIntent.hero(NativeLocomotionController.INSTANCE.hero())&&NativeLocomotionController.INSTANCE.modelId()!=0;
    }
    public Vec3d movement(MinecraftClient client,Vec3d vanilla){
        if(!requested(client)){resetSession();return null;}
        var host=HostPoseReader.INSTANCE.latest();var loc=NativeLocomotionController.INSTANCE;
        // 原版姿态短暂缺失（切英雄/重载/读失败）时不接管移动；以前这里空指针会让 MC 客户端崩溃。
        if(host==null){resetSession();return null;}
        Vec3d result=loc.baseMovement(vanilla);
        // Original Q selects its cinematic camera, so the generic first-person
        // pose intentionally clears input. A confirmed same-scope Q may still
        // walk at the original computed limits. Read only WASD in its exact
        // foreground window; no hook, synthetic input or renderer mutation.
        int bits=host.inputActive()?host.movementBits():0;
        bits=HanzoControlController.movementBits(client,host,bits);
        if(NativeReaperController.active()){bits=NativeReaperController.movementBits();result=loc.directionalMovement(vanilla,bits);}
        if(NativeRecallController.rewinding()||NativeShadowController.casting())result=Vec3d.ZERO;
        String form="";
        if(NativeLocomotionController.INSTANCE.hero()==0x02e0000000000015L){
            var state=skills.poll(host,loc.modelId(),0x02e0000000000015L);
            boolean recon=state!=null&&state.active("recon"),sentry=state!=null&&state.active("sentry"),tank=state!=null&&state.active("tank");
            form=NativeMotorIntent.bastionForm(recon,sentry,tank);
            if(!form.equals("recon")&&!form.equals("tank"))result=new Vec3d(0,vanilla.y,0);
        }
        status="{\"ready\":true,\"nativeVelocity\":"+new com.google.gson.Gson().toJson(loc.nativeVelocity())+",\"inputBits\":"+bits+",\"responsive\":true,\"speedSource\":\"native-computed-directional-limits\",\"form\":\""+form+"\",\"horizontalSpeed\":"+(Math.hypot(result.x,result.z)*20)+"}";
        return result;
    }
    // No cumulative native displacement remains queued after a climb or collision.
    void discardMotion(){}
    @Override public void close(){skills.close();}
    void resetSession(){close();status="{\"ready\":false}";}
}
