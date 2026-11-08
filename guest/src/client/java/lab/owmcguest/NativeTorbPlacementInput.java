package lab.owmcguest;

import com.sun.jna.*;
import com.sun.jna.ptr.IntByReference;
import com.sun.jna.win32.StdCallLibrary;
import net.minecraft.client.MinecraftClient;

/** Existing native preview still owns its animation. After an MC-confirmed
 * placement (or second Shift), use its ordinary RMB cancellation message path.
 * No native graph tick, animation or weapon state is written. */
final class NativeTorbPlacementInput {
    interface User extends StdCallLibrary{
        Pointer GetForegroundWindow();int GetWindowThreadProcessId(Pointer window,IntByReference pid);
        short GetAsyncKeyState(int key);boolean PostMessageW(Pointer window,int message,long w,long l);
    }
    private final User user=Native.load("user32",User.class);
    private final int activation,cancelKey;
    NativeTorbPlacementInput(){this(0x10,0x02);}
    NativeTorbPlacementInput(int activation,int cancelKey){this.activation=activation;this.cancelKey=cancelKey;}
    private Pointer window;private boolean permitted;
    int keys(MinecraftClient c,HostPoseReader.Pose h){
        window=user.GetForegroundWindow();var pid=new IntByReference();user.GetWindowThreadProcessId(window,pid);
        permitted=h!=null&&h.flags()==1&&h.inputActive()&&pid.getValue()==h.pid()&&c.currentScreen==null
            &&!PortalMenu.visible()&&!TwilightBossMenu.visible()&&!SummonMenu.visible()&&!SurvivalMenu.visible()&&!WorldSettingsMenu.visible();
        if(!permitted)return 0;int bits=0;
        if((user.GetAsyncKeyState(0x01)&0x8000)!=0)bits|=1;
        if((user.GetAsyncKeyState(activation)&0x8000)!=0)bits|=2;
        if((user.GetAsyncKeyState(0x02)&0x8000)!=0)bits|=4;
        if((user.GetAsyncKeyState(0x20)&0x8000)!=0)bits|=8;
        return bits;
    }
    boolean permitted(){return permitted;}
    boolean cancel(HostPoseReader.Pose h){
        if(!permitted||h==null||!h.inputActive())return false;
        var now=user.GetForegroundWindow();var pid=new IntByReference();user.GetWindowThreadProcessId(now,pid);
        if(pid.getValue()!=h.pid()||!now.equals(window))return false;
        if(cancelKey==0x02)return user.PostMessageW(now,0x204,2,0)&&user.PostMessageW(now,0x205,0,0);
        return user.PostMessageW(now,0x100,cancelKey,1)&&user.PostMessageW(now,0x101,cancelKey,0xc0000001L);
    }
}
