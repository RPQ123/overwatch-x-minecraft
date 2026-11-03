package lab.owmcguest;

import net.minecraft.client.MinecraftClient;
/** Compatibility lifecycle only. All portal construction is now selected in F8. */
public final class NativePortalController implements AutoCloseable {
    public static final NativePortalController INSTANCE=new NativePortalController();
    public static volatile String error="";
    public void tick(MinecraftClient client){}
    @Override public void close(){error="";}
    void resetSession(){close();error="native session transition";}
}
