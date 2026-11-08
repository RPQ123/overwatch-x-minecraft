package lab.owmcguest;

import com.sun.jna.*;
import com.sun.jna.ptr.IntByReference;
import com.sun.jna.win32.StdCallLibrary;
import net.minecraft.client.MinecraftClient;

/** Read only the native foreground window's Shift; never synthesize input.
 * User explicitly permits Jump Pack prediction before the native receipt. */
final class WinstonJumpInput {
    interface User extends StdCallLibrary {
        Pointer GetForegroundWindow();int GetWindowThreadProcessId(Pointer window,IntByReference pid);short GetAsyncKeyState(int key);
    }
    private final User user=Native.load("user32",User.class);
    /** -1 revokes input edges, 0 released, 1 pressed. */
    int sample(MinecraftClient c,HostPoseReader.Pose h){
        if(h==null||!h.inputActive()||h.flags()!=1||c.currentScreen!=null||PortalMenu.visible()||TwilightBossMenu.visible()
            ||SummonMenu.visible()||SurvivalMenu.visible()||WorldSettingsMenu.visible())return -1;
        var window=user.GetForegroundWindow();var pid=new IntByReference();user.GetWindowThreadProcessId(window,pid);
        if(window==null||pid.getValue()!=h.pid())return -1;
        return (user.GetAsyncKeyState(0x10)&0x8000)!=0?1:0;
    }
}
