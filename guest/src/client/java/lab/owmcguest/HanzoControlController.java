package lab.owmcguest;

import com.sun.jna.*;
import com.sun.jna.win32.StdCallLibrary;
import net.minecraft.client.MinecraftClient;
import org.joml.Quaternionf;

/** Original Q Begin/End and same-cast arrow release; never admits an attack from a key. */
public final class HanzoControlController {
    private interface Win extends StdCallLibrary {
        Win API=Native.load("user32",Win.class);
        Pointer GetForegroundWindow();int GetWindowThreadProcessId(Pointer w,int[] pid);boolean GetCursorInfo(Pointer info);
    }
    private static final HanzoControlProof gate=new HanzoControlProof();
    private static volatile HanzoControlProof.Request request;
    private static Quaternionf frozen;private static float frozenYaw,frozenPitch;
    private static long locks,lockFrames,runtimeEpoch;private static boolean ready;
    // 用户要求：整个原版 Q 施法期间（Begin→End）都不能移动；视角锁仍到龙释放为止。
    private static volatile long castActiveWall,castStartWall;
    // 用户要求（2026-10-27）：半藏放龙期间全部不锁（视角与移动都自由）。改回 true 即恢复锁定。
    public static final boolean LOCK_ENABLED=false;
    public static volatile String status="{\"ready\":false,\"locked\":false}";
    private static boolean foreground(int pid){
        var w=Win.API.GetForegroundWindow();if(w==null)return false;int[] actual={0};Win.API.GetWindowThreadProcessId(w,actual);
        try(var cursor=new Memory(Native.POINTER_SIZE==8?24:20)){cursor.clear();cursor.setInt(0,(int)cursor.size());
            return actual[0]==pid&&Win.API.GetCursorInfo(cursor)&&(cursor.getInt(4)&1)==0;}
    }
    private static HanzoControlProof.Scope scope(MinecraftClient c,HostPoseReader.Pose h){
        return new HanzoControlProof.Scope(c.player.getUuid(),h.pid(),h.generation(),NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey()),NativeLocomotionController.INSTANCE.modelId());
    }
    private static boolean eligible(MinecraftClient c,HostPoseReader.Pose h){
        return Boolean.getBoolean("owmc.frameExport")&&Boolean.getBoolean("owmc.hostMovement")
            &&c.player!=null&&c.player.isAlive()&&c.world!=null&&c.getServer()!=null&&c.currentScreen==null&&!c.isPaused()
            &&h!=null&&h.flags()==1&&NativeLocomotionController.INSTANCE.hero()==HanzoControlProof.HERO
            &&HanzoControlCapability.available(h.pid(),h.generation(),h.frame(),System.currentTimeMillis())&&foreground(h.pid());
    }
    static void refresh(MinecraftClient c,HostPoseReader.Pose h,NativeSkillReader.State cast,NativeSkillReader.State weapon){
        if(runtimeEpoch!=NativeHanzoSkillRuntime.controlsEpoch)reset();
        long now=System.currentTimeMillis();boolean cap=h!=null&&HanzoControlCapability.available(h.pid(),h.generation(),h.frame(),now);
        ready=cast!=null&&weapon!=null&&eligible(c,h);
        long oldBegin=gate.begin();var entry=cast==null?null:cast.entries().get("cast");
        if(entry!=null&&entry.active()&&NativeLocomotionController.INSTANCE.hero()==HanzoControlProof.HERO){
            if(now-castActiveWall>300)castStartWall=now;castActiveWall=now;
        }
        long begin=entry!=null&&entry.active()?entry.tick():oldBegin;
        long volley=weapon==null?0:weapon.entries().get("dragon").tick();
        var flight=NativeHanzoSkillRuntime.dragonFlight;
        boolean same=flight!=null&&c.player!=null&&c.world!=null&&c.getServer()!=null&&h!=null
            &&flight.scope().owner().equals(c.player.getUuid())&&flight.scope().source()==h.generation()
            &&flight.scope().world()==NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey())
            &&flight.scope().model()==NativeLocomotionController.INSTANCE.modelId()&&flight.begin()==begin;
        boolean wasLocked=request!=null;
        request=gate.observe(ready?scope(c,h):null,NativeLocomotionController.INSTANCE.hero(),h==null?0:h.frame(),h!=null&&h.inputActive(),ready,
            entry==null?null:new HanzoControlProof.Phase(entry.tick(),entry.active()),begin>0&&volley>=begin,same&&flight.released(),now);
        if(!LOCK_ENABLED)request=null; // 全部不锁：不冻结视角/速度，也不向原版发送锁定请求
        if(request!=null){
            if(!wasLocked||oldBegin!=request.begin()){
                frozen=new Quaternionf(h.rotation());var f=new org.joml.Vector3f(0,0,-1).rotate(frozen);
                frozenYaw=(float)Math.toDegrees(Math.atan2(-f.x,f.z));frozenPitch=(float)Math.toDegrees(Math.atan2(-f.y,Math.hypot(f.x,f.z)));locks++;
            }
            hold(c);lockFrames++;
        }else frozen=null;
        var o=new com.google.gson.JsonObject();o.addProperty("ready",ready);o.addProperty("locked",request!=null);o.addProperty("locks",locks);o.addProperty("lockFrames",lockFrames);
        o.addProperty("nativeCapability",cap);o.addProperty("protocol","HNZ2");o.addProperty("nativeBegin",gate.begin());o.addProperty("startedWall",gate.startedWall());
        o.addProperty("nativeEndWall",gate.endedWall());o.addProperty("releasedWall",gate.releasedWall());o.addProperty("lockMillis",gate.duration(now));
        o.addProperty("nativeEnd",gate.nativeEnd());o.addProperty("nativeCastMillis",gate.nativeEnd()>0?gate.nativeEnd()-gate.begin():0);
        o.addProperty("nativeCastActive",entry!=null&&entry.active());o.addProperty("dragonReleased",same&&flight.released());o.addProperty("reason",ready?gate.reason():"binding/capability/focus/session unavailable");
        o.addProperty("adaptation","MC ???????");status=o.toString();
    }
    public static HanzoControlProof.Request current(MinecraftClient c,HostPoseReader.Pose h){
        if(!LOCK_ENABLED)return null;
        if(runtimeEpoch!=NativeHanzoSkillRuntime.controlsEpoch){reset();return null;}
        var held=request;
        if(held!=null&&gate.holding(System.currentTimeMillis())&&c.player!=null&&c.player.isAlive()
            &&NativeLocomotionController.INSTANCE.hero()==HanzoControlProof.HERO)return held; // 短暂失焦/帧抖动不解锁
        if(!eligible(c,h)){reset();return null;}
        var r=request;if(!HanzoControlProof.current(r,scope(c,h),h.frame(),System.currentTimeMillis())){
            if(r!=null)reset();return null;
        }return r;
    }
    private static boolean castMoveHold(MinecraftClient c){
        if(!LOCK_ENABLED)return false;
        long now=System.currentTimeMillis();
        return c.player!=null&&c.player.isAlive()&&NativeLocomotionController.INSTANCE.hero()==HanzoControlProof.HERO
            &&now-castActiveWall<=200&&now-castStartWall<=HanzoControlProof.MAX_LOCK_MS;
    }
    public static boolean movementLocked(){
        var c=MinecraftClient.getInstance();
        return current(c,HostPoseReader.INSTANCE.latest())!=null||castMoveHold(c);
    }
    public static boolean holdMotion(){
        var c=MinecraftClient.getInstance();if(!movementLocked())return false;
        NativeRollController.INSTANCE.discardMotion();NativeMotorController.INSTANCE.discardMotion();hold(c);return true;
    }
    public static int movementBits(MinecraftClient c,HostPoseReader.Pose h,int ordinary){return current(c,h)==null&&!castMoveHold(c)?ordinary:ordinary&~0x7f;}
    /** HNZ1 speed recovery is retired. Preserve ordinary native limits after unlock. */
    public static double[] movementSpeeds(MinecraftClient c,HostPoseReader.Pose h,double[] computed,double[] base){return computed;}
    public static Quaternionf cameraRotation(HostPoseReader.Pose h){
        return current(MinecraftClient.getInstance(),h)!=null&&frozen!=null?new Quaternionf(frozen):h.rotation();
    }
    private static void hold(MinecraftClient c){
        if(c.player==null)return;var v=c.player.getVelocity();c.player.setVelocity(0,Math.min(0,v.y),0); // 只清水平/上升速度，保留下落
        if(frozen==null)return; // 施法后段只锁移动，不再锁视角
        c.player.setYaw(frozenYaw);c.player.setPitch(frozenPitch);c.player.prevYaw=frozenYaw;c.player.prevPitch=frozenPitch;
    }
    static long nativeBegin(){return gate.begin();}
    static void reset(){runtimeEpoch=NativeHanzoSkillRuntime.controlsEpoch;gate.reset();request=null;frozen=null;ready=false;status="{\"ready\":false,\"locked\":false,\"reason\":\"scope reset\"}";}
}
