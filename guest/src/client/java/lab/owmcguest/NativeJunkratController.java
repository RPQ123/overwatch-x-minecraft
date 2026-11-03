package lab.owmcguest;

import net.minecraft.client.MinecraftClient;

/** 狂鼠：原版主武器/Shift/E 的 WeaponVolley 新 tick 各准入一次 MC 投掷。首个样本只作基线。
 * 地雷引爆：原版引爆依赖服务端创建的地雷实体，本客户端观测不到任何引爆状态（junk-detonate-calibration1：右键/再按 Shift 均无变化），
 * 所以 MC 适配为：原版窗口在前台且输入有效时，右键按下沿引爆当前 MC 地雷。 */
public final class NativeJunkratController implements AutoCloseable {
    static final long HERO=0x02e0000000000065L;
    static{NativeSkillReader.register("junkTire",new NativeSkillReader.Spec(HERO,0x0580000000000232L,java.util.Map.of("create",32,"control",10,"view",11,"windup",7)));}
    public static final NativeJunkratController INSTANCE=new NativeJunkratController();
    private final NativeSkillReader primary=new NativeSkillReader("junkPrimary"),mine=new NativeSkillReader("junkMine"),trap=new NativeSkillReader("junkTrap"),tire=new NativeSkillReader("junkTire");
    private final long[] last={-1,-1,-1};
    private interface User32 extends com.sun.jna.win32.StdCallLibrary{com.sun.jna.Pointer GetForegroundWindow();int GetWindowThreadProcessId(com.sun.jna.Pointer w,com.sun.jna.ptr.IntByReference pid);short GetAsyncKeyState(int key);}
    private final User32 user=com.sun.jna.Native.load("user32",User32.class);private boolean rmb;static long detonateRequests;
    private long scopeSource,scopeModel,scopeWorld,frame,frameWall;
    private long lastCreate=-1;private NativeJunkratRuntime.Scope activeScope;private net.minecraft.server.MinecraftServer activeServer;
    private static long tireCreateEvents;
    static volatile String error="";
    void tick(MinecraftClient c){
        var h=HostPoseReader.INSTANCE.latest();long hero=NativeLocomotionController.INSTANCE.hero(),model=NativeLocomotionController.INSTANCE.modelId();
        if(c.player!=null&&!c.player.isAlive()&&hero==HERO&&c.world!=null&&c.getServer()!=null&&activeScope!=null){
            var captured=activeScope;var server=c.getServer();server.execute(()->NativeJunkratRuntime.observe(server,captured));return;
        }
        if(h==null||h.flags()!=1||c.player==null||c.world==null||c.getServer()==null||hero!=HERO){resetSession();return;}
        long now=System.currentTimeMillis();if(h.frame()!=frame){frame=h.frame();frameWall=now;}if(now-frameWall>150){resetSession();return;}
        long world=NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey());
        if(scopeSource!=h.generation()||scopeModel!=model||scopeWorld!=world){resetSession();scopeSource=h.generation();scopeModel=model;scopeWorld=world;}
        var scope=new NativeJunkratRuntime.Scope(c.player.getUuid(),world,h.generation(),model);var server=c.getServer();
        activeScope=scope;activeServer=server;server.execute(()->NativeJunkratRuntime.observe(server,scope));
        var diagnostic=new com.google.gson.JsonObject();diagnostic.addProperty("ready",true);diagnostic.addProperty("model",model);diagnostic.addProperty("hero",hero);
        diagnostic.addProperty("source",h.generation());diagnostic.addProperty("world",world);
        diagnostic.add("primary",poll(0,primary,"volley",h,model,hero,server,scope,NativeJunkratRuntime.Kind.GRENADE));
        diagnostic.add("mine",poll(1,mine,"throw",h,model,hero,server,scope,NativeJunkratRuntime.Kind.MINE));
        diagnostic.add("trap",poll(2,trap,"throw",h,model,hero,server,scope,NativeJunkratRuntime.Kind.TRAP));
        var q=tire.poll(h,model,hero);
        var qDiagnostic=new com.google.gson.JsonObject();qDiagnostic.addProperty("ready",q!=null);
        if(q==null){lastCreate=-1;error=tire.error;qDiagnostic.addProperty("error",tire.error);}else{
            long next=q.entries().get("create").tick();
            qDiagnostic.addProperty("tick",next);qDiagnostic.addProperty("active",q.active("create"));
            qDiagnostic.addProperty("control",q.active("control"));qDiagnostic.addProperty("view",q.active("view"));qDiagnostic.addProperty("windup",q.active("windup"));
            if(lastCreate<0)lastCreate=next;
            else if(next>lastCreate){lastCreate=next;tireCreateEvents++;server.execute(()->NativeJunkratTireRuntime.cast(server,scope));}
        }
        diagnostic.add("tireCreate",qDiagnostic);diagnostic.addProperty("tireCreateEvents",tireCreateEvents);
        NativeJunkratRuntime.nativeSignals=diagnostic.toString();
        var fg=new com.sun.jna.ptr.IntByReference();user.GetWindowThreadProcessId(user.GetForegroundWindow(),fg);
        boolean focused=fg.getValue()==h.pid();
        boolean down=focused&&h.inputActive()&&(user.GetAsyncKeyState(0x02)&0x8000)!=0;
        var tv=currentTireView();
        if(tv!=null){
            int bits=focused?(h.inputActive()?h.movementBits():keys()):0;
            var direction=new org.joml.Vector3f(0,0,-1).rotate(h.rotation());
            var forward=new net.minecraft.util.math.Vec3d(direction.x,0,direction.z);
            server.execute(()->NativeJunkratTireRuntime.input(scope,forward,bits,now));
            // 0233 尚无认证的引爆提交绑定；这里仅发送移动，不采样 M1 或请求伤害。
        }else if(down&&!rmb&&NativeJunkratRuntime.views.stream().anyMatch(v->v.kind()==NativeJunkratRuntime.Kind.MINE)){detonateRequests++;server.execute(()->NativeJunkratRuntime.detonateMine(server,scope));}
        rmb=down;
    }
    private int keys(){int b=0;int[] keys={0x57,0x53,0x41,0x44,0x20};for(int i=0;i<keys.length;i++)if((user.GetAsyncKeyState(keys[i])&0x8000)!=0)b|=1<<i;return b;}
    /** 同时用于移动锁/相机/呈现，旧世界或旧原版角色的快照即使很新也必须拒绝。 */
    public static NativeJunkratTireRuntime.View currentTireView(){
        var c=MinecraftClient.getInstance();var v=NativeJunkratTireRuntime.view;var own=INSTANCE.activeScope;
        if(v==null||v.identity()==null||own==null||c.player==null||!c.player.isAlive()||c.world==null||c.getServer()==null
            ||INSTANCE.activeServer!=c.getServer())return null;
        long now=System.currentTimeMillis();var h=HostPoseReader.INSTANCE.latest();
        if(h==null||h.flags()!=1||!NativeJunkratTireIdentity.fresh(v.wall(),INSTANCE.frame,INSTANCE.frameWall,h.frame(),now))return null;
        var loc=NativeLocomotionController.INSTANCE;long world=NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey());
        var identity=v.identity();
        if(v.world()!=identity.world()||!identity.equals(new NativeJunkratTireIdentity(own.owner(),own.world(),own.source(),own.model()))
            ||!identity.matches(c.player.getUuid(),loc.hero(),world,h.generation(),loc.modelId()))return null;
        return v;
    }
    public static boolean movementLocked(){return currentTireView()!=null;}
    private com.google.gson.JsonObject poll(int i,NativeSkillReader r,String node,HostPoseReader.Pose h,long model,long hero,net.minecraft.server.MinecraftServer server,NativeJunkratRuntime.Scope scope,NativeJunkratRuntime.Kind kind){
        var diagnostic=new com.google.gson.JsonObject();var s=r.poll(h,model,hero);diagnostic.addProperty("ready",s!=null);
        if(s==null){error=r.error;last[i]=-1;diagnostic.addProperty("error",r.error);return diagnostic;}
        var e=s.entries().get(node);diagnostic.addProperty("tick",e.tick());diagnostic.addProperty("active",e.active());
        if(last[i]<0){last[i]=e.tick();return diagnostic;}
        if(e.tick()>last[i]){last[i]=e.tick();long nativeTick=e.tick();int nativePid=h.pid();server.execute(()->NativeJunkratRuntime.cast(server,scope,kind,nativePid,nativeTick));}
        return diagnostic;
    }
    void resetSession(){
        if(activeScope!=null&&activeServer!=null){var s=activeScope;var server=activeServer;server.execute(()->NativeJunkratRuntime.cancel(s));}
        activeScope=null;activeServer=null;primary.close();mine.close();trap.close();tire.close();lastCreate=-1;rmb=false;
        java.util.Arrays.fill(last,-1);frame=frameWall=0;scopeSource=scopeModel=scopeWorld=0;error="";
        NativeJunkratRuntime.nativeSignals="{\"ready\":false,\"error\":\"native controller scope reset\"}";
    }
    @Override public void close(){resetSession();}
}
