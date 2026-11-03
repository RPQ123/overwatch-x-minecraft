package lab.owmcguest;

import net.minecraft.client.MinecraftClient;

/** 托比昂：原版 graph f4 的放置动画29 结束（Shift 预览成形）→ MC 在准星指向的真实地面放炮台；
 * 原版的放置确认依赖隐藏 OW 地图的地面，本 beta 中观测不到确认节点（torb-place-calibration1/2），这是 MC 适配。
 * 原版 graph 01cc WeaponVolley5 新 tick → 投出护甲包。首个样本只作基线。 */
public final class NativeTorbjornController implements AutoCloseable {
    static final long HERO=0x02e0000000000006L;
    static{NativeSkillReader.register("torbHammer",new NativeSkillReader.Spec(HERO,0x05800000000000f3L,java.util.Map.of("strike",24,"swing",29,"repair",10)));}
    public static final NativeTorbjornController INSTANCE=new NativeTorbjornController();
    private final NativeSkillReader turret=new NativeSkillReader("torbTurret"),armor=new NativeSkillReader("torbArmor"),hammer=new NativeSkillReader("torbHammer"),core=new NativeSkillReader();
    private long lastAnimEnd=-1,lastThrow=-1,scopeSource,scopeModel,scopeWorld,frame,frameWall;private boolean animActive;
    private long lastStrike=-1;private final NativeTorbjornCoreBegin coreBegin=new NativeTorbjornCoreBegin();
    private NativeTorbjornRuntime.Scope activeScope;private net.minecraft.server.MinecraftServer activeServer;
    private static long deployRequests,hammerRequests;
    private static com.google.gson.JsonObject snapshot(NativeSkillReader.State state,String error){
        var out=new com.google.gson.JsonObject();out.addProperty("ready",state!=null);
        if(state==null)out.addProperty("error",error);else for(var field:state.entries().entrySet()){
            var entry=new com.google.gson.JsonObject();entry.addProperty("tick",field.getValue().tick());entry.addProperty("active",field.getValue().active());out.add(field.getKey(),entry);
        }return out;
    }
    static volatile String error="";
    void tick(MinecraftClient c){
        var h=HostPoseReader.INSTANCE.latest();long hero=NativeLocomotionController.INSTANCE.hero(),model=NativeLocomotionController.INSTANCE.modelId();
        if(h==null||h.flags()!=1||c.player==null||!c.player.isAlive()||c.world==null||c.getServer()==null||hero!=HERO){resetSession();return;}
        long now=System.currentTimeMillis();if(h.frame()!=frame){frame=h.frame();frameWall=now;}if(now-frameWall>150){resetSession();return;}
        long world=NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey());
        if(scopeSource!=h.generation()||scopeModel!=model||scopeWorld!=world){resetSession();scopeSource=h.generation();scopeModel=model;scopeWorld=world;}
        var scope=new NativeTorbjornRuntime.Scope(c.player.getUuid(),world,h.generation(),model);var server=c.getServer();
        activeScope=scope;activeServer=server;server.execute(()->NativeTorbjornRuntime.observe(server,scope));
        var signals=new com.google.gson.JsonObject();signals.addProperty("ready",true);signals.addProperty("model",model);signals.addProperty("source",h.generation());signals.addProperty("world",world);
        var t=turret.poll(h,model,hero);
        signals.add("turret",snapshot(t,turret.error));
        if(t==null){error=turret.error;lastAnimEnd=-1;}else{var anim=t.entries().get("anim");
            if(lastAnimEnd<0){lastAnimEnd=anim.tick();animActive=anim.active();}
            else{if(animActive&&!anim.active()&&anim.tick()>lastAnimEnd&&t.active("ghost")){deployRequests++;server.execute(()->NativeTorbjornRuntime.deploy(server,scope));}
                if(!anim.active())lastAnimEnd=anim.tick();animActive=anim.active();}}
        var a=armor.poll(h,model,hero);
        signals.add("armor",snapshot(a,armor.error));
        if(a==null){lastThrow=-1;}else{long k=a.entries().get("throw").tick();if(lastThrow<0)lastThrow=k;else if(k>lastThrow){lastThrow=k;server.execute(()->NativeTorbjornRuntime.throwPack(server,scope));}}
        var strike=hammer.poll(h,model,hero);
        signals.add("hammer",snapshot(strike,hammer.error));
        if(strike==null){lastStrike=-1;error=hammer.error;}else{
            long k=strike.entries().get("strike").tick();
            if(lastStrike<0)lastStrike=k;
            else if(k>lastStrike){lastStrike=k;if(strike.active("swing")||strike.active("repair")){hammerRequests++;server.execute(()->NativeTorbjornRuntime.hammer(server,scope));}}
        }
        var q=core.poll(h,model,hero);
        signals.add("core",snapshot(q,core.error));
        if(q==null){coreBegin.missing();error=core.error;server.execute(()->NativeTorbjornRuntime.core(server,scope,false,0,now));}
        else{
            boolean active=q.active("coreArmor")||q.active("coreEffect")||q.active("coreTimer");
            var armorState=q.entries().get("coreArmor");long cycle=coreBegin.observe(armorState.tick(),armorState.active(),active);
            boolean apply=active&&cycle>0;server.execute(()->NativeTorbjornRuntime.core(server,scope,apply,cycle,now));
        }
        signals.addProperty("deployRequests",deployRequests);signals.addProperty("hammerRequests",hammerRequests);NativeTorbjornRuntime.nativeSignals=signals.toString();
    }
    void resetSession(){
        if(activeScope!=null&&activeServer!=null){var s=activeScope;activeServer.execute(()->NativeTorbjornRuntime.cancel(s));}
        activeScope=null;activeServer=null;turret.close();armor.close();hammer.close();core.close();lastStrike=lastAnimEnd=lastThrow=-1;
        coreBegin.missing();animActive=false;frame=frameWall=0;scopeSource=scopeModel=scopeWorld=0;error="";
        NativeTorbjornRuntime.nativeSignals="{\"ready\":false,\"error\":\"native controller scope reset\"}";
    }
    @Override public void close(){resetSession();}
}
