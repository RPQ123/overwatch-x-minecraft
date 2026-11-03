package lab.owmcguest;

import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.win32.StdCallLibrary;
import net.minecraft.client.MinecraftClient;
import org.lwjgl.glfw.GLFWNativeWin32;

/** A background MC terrain screen must not capture another foreground game's mouse. */
public final class HostMouseCaptureGuard {
    private interface User32 extends StdCallLibrary {Pointer GetForegroundWindow();}
    private static final class Windows {static final User32 API=Native.load("user32",User32.class);}
    private static long denied,allowed,lastForeground,lastWindow;
    public static boolean permit(MinecraftClient client){
        if(!Boolean.getBoolean("owmc.frameExport")||!Boolean.getBoolean("owmc.hostMovement")
                ||!System.getProperty("os.name","").startsWith("Windows"))return true;
        lastWindow=GLFWNativeWin32.glfwGetWin32Window(client.getWindow().getHandle());
        lastForeground=Pointer.nativeValue(Windows.API.GetForegroundWindow());
        boolean focused=lastWindow!=0&&lastForeground==lastWindow;
        if(focused)allowed++;else denied++;
        return focused;
    }
    public static String status(){
        return "{\"backgroundLocksDenied\":"+denied+",\"foregroundLocksAllowed\":"+allowed
            +",\"lastForegroundWindow\":"+lastForeground+",\"minecraftWindow\":"+lastWindow+"}";
    }
}
