package lab.owmcguest;

import com.sun.jna.*;
import com.sun.jna.ptr.IntByReference;
import com.sun.jna.win32.StdCallLibrary;
import net.minecraft.client.MinecraftClient;

/** Missing offline-server completion: after a confirmed MC volley, use the
 * original native cancel/recovery input once. This never admits an attack.
 * No focus stealing, input in another app, hook, native call or stuck button. */
final class NativeDeadeyeFinish {
    private interface User32 extends StdCallLibrary {
        Pointer GetForegroundWindow();int GetWindowThreadProcessId(Pointer hwnd,IntByReference pid);short GetAsyncKeyState(int key);
        void mouse_event(int flags,int dx,int dy,int data,Pointer extra);
    }
    private final User32 user=Native.load("user32",User32.class);
    private String consumed="";private boolean pressed;private long pressedAt;
    static volatile long requests;
    void releaseDue(){if(pressed&&System.currentTimeMillis()-pressedAt>=35)release();}
    private void release(){if(pressed){user.mouse_event(0x10,0,0,0,null);pressed=false;}}
    void complete(MinecraftClient client,HostPoseReader.Pose host,long model,long world,long begin,long observed,boolean nativeActive){
        releaseDue();var f=NativeDeadeyeRuntime.completion;long now=System.currentTimeMillis();
        if(f==null||client.player==null||host==null||host.flags()!=1||!host.inputActive()||now-observed>100||now<f.wall()||now-f.wall()>250||!f.owner().equals(client.player.getUuid())||f.world()!=world||f.source()!=host.generation()||f.model()!=model||f.begin()!=begin||NativeLocomotionController.INSTANCE.hero()!=NativeDeadeyeRuntime.HERO)return;
        String identity=f.source()+":"+model+":"+world+":"+begin;if(identity.equals(consumed))return;
        if(!nativeActive){consumed=identity;return;}
        var window=user.GetForegroundWindow();var pid=new IntByReference();user.GetWindowThreadProcessId(window,pid);
        if(pid.getValue()!=host.pid()||!java.util.Objects.equals(window,user.GetForegroundWindow()))return;
        consumed=identity;
        // A human's already-held RMB is itself the original cancellation.
        if((user.GetAsyncKeyState(0x02)&0x8000)!=0)return;
        user.mouse_event(0x08,0,0,0,null);pressed=true;pressedAt=now;requests++;
    }
    void reset(){release();consumed="";}
}
