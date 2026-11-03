package lab.owmcguest;
import net.minecraft.client.MinecraftClient;

/** Original Q firing phase owns the MC adapter; no keyboard-generated attacks. */
final class NativeReaperController implements AutoCloseable {
    private interface Windows extends com.sun.jna.win32.StdCallLibrary {
        com.sun.jna.Pointer GetForegroundWindow();int GetWindowThreadProcessId(com.sun.jna.Pointer window,com.sun.jna.ptr.IntByReference pid);short GetAsyncKeyState(int key);
        boolean GetCursorInfo(Cursor cursor);
    }
    @com.sun.jna.Structure.FieldOrder({"size","flags","cursor","x","y"})
    public static class Cursor extends com.sun.jna.Structure {public int size,flags;public com.sun.jna.Pointer cursor;public int x,y;public Cursor(){size=size();}}
    private static final Windows windows=com.sun.jna.Native.load("user32",Windows.class);
    static final NativeReaperController INSTANCE=new NativeReaperController();
    private final NativeSkillReader reader=new NativeSkillReader();
    private final NativeAbilityContinuationGate gate=new NativeAbilityContinuationGate();
    private long frame,lastFrameWall;
    static volatile String error="";
    static boolean active(){
        var f=NativeReaperRuntime.view;if(f==null)return false;var c=MinecraftClient.getInstance();var h=HostPoseReader.INSTANCE.latest();
        return f!=null&&h!=null&&c.player!=null&&c.player.isAlive()&&c.currentScreen==null&&c.world!=null&&c.getServer()!=null&&System.currentTimeMillis()-f.wall()<=150
            &&f.scope().owner().equals(c.player.getUuid())&&f.scope().source()==h.generation()&&f.scope().model()==NativeLocomotionController.INSTANCE.modelId()
            &&NativeLocomotionController.INSTANCE.hero()==NativeReaperRuntime.HERO&&f.scope().world()==NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey());
    }
    static int movementBits(){
        if(!active())return 0;var h=HostPoseReader.INSTANCE.latest();if(h==null)return 0;var window=windows.GetForegroundWindow();var pid=new com.sun.jna.ptr.IntByReference();windows.GetWindowThreadProcessId(window,pid);
        var cursor=new Cursor();if(pid.getValue()!=h.pid()||!windows.GetCursorInfo(cursor)||(cursor.flags&1)!=0)return 0;
        int bits=0;int[] keys={0x57,0x53,0x41,0x44};for(int i=0;i<4;i++)if((windows.GetAsyncKeyState(keys[i])&0x8000)!=0)bits|=1<<i;
        return java.util.Objects.equals(window,windows.GetForegroundWindow())?bits:0;
    }
    void tick(MinecraftClient c){
        var h=HostPoseReader.INSTANCE.latest();long hero=NativeLocomotionController.INSTANCE.hero(),model=NativeLocomotionController.INSTANCE.modelId();
        if(h==null||h.flags()!=1||c.player==null||!c.player.isAlive()||c.world==null||c.getServer()==null||hero!=NativeReaperRuntime.HERO){resetSession();return;}
        long now=System.currentTimeMillis();if(h.frame()!=frame){frame=h.frame();lastFrameWall=now;}
        if(now-lastFrameWall>150)return; // A cinematic is not permission to refresh a stalled pose.
        var state=reader.poll(h,model,hero);if(state==null){error=reader.error;return;}var values=reader.reaperParameters();if(values==null){error=reader.error;return;}error="";
        long world=NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey());var root=state.entries().get("ultimate");
        boolean active=gate.observe(new NativeAbilityContinuationGate.Scope(h.generation(),world,model),root.tick(),state.active("ultimate")&&state.active("firing")&&state.active("animation"),h.inputActive(),now);
        var phase=new NativeReaperRuntime.Phase(new NativeReaperRuntime.Scope(c.player.getUuid(),world,h.generation(),model),root.tick(),now,active,values[0],values[1]);
        var server=c.getServer();server.execute(()->NativeReaperRuntime.refresh(server,phase));
    }
    void resetSession(){reader.close();gate.reset();frame=lastFrameWall=0;error="";}
    @Override public void close(){resetSession();}
}
