package lab.owmcguest;

import net.minecraft.client.MinecraftClient;

/** 托比昂：原版 graph f4 的ghost22授权预览，实际LMB新边沿确认MC地面放置。
 * 不再把预览成形动画29结束视作确认；原版仍拥有预览/取消/换武器动画。
 * 原版 graph 01cc WeaponVolley5 新 tick → 投出护甲包。首个样本只作基线。 */
public final class NativeTorbjornController implements AutoCloseable {
    static final long HERO=0x02e0000000000006L;
    static{NativeSkillReader.register("torbHammer",new NativeSkillReader.Spec(HERO,0x05800000000000f3L,java.util.Map.of("strike",24,"swing",29,"repair",10)));}
    public static final NativeTorbjornController INSTANCE=new NativeTorbjornController();
    private final NativeSkillReader turret=new NativeSkillReader("torbTurret"),armor=new NativeSkillReader("torbArmor"),hammer=new NativeSkillReader("torbHammer"),core=new NativeSkillReader();
    private long lastThrow=-1,scopeSource,scopeModel,scopeWorld,frame,frameWall;
    private long lastStrike=-1;private final NativeTorbjornCoreBegin coreBegin=new NativeTorbjornCoreBegin();
    private NativeTorbjornRuntime.Scope activeScope;private net.minecraft.server.MinecraftServer activeServer;
    private final TorbPlacementInput placement=new TorbPlacementInput();private final NativeTorbPlacementInput placementKeys=new NativeTorbPlacementInput();
    private boolean cancelNative;private static long nativeCancelRequests,nativeCancelMessages;
    private final NativeScrapClient scrapClient=new NativeScrapClient();
    private final NativePlacementActionClient placementActions=new NativePlacementActionClient(2);
    private long previewToken,lastPreviewWall;
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
        scrapClient.tick(c,h,scope);
        var signals=new com.google.gson.JsonObject();signals.addProperty("ready",true);signals.addProperty("model",model);signals.addProperty("source",h.generation());signals.addProperty("world",world);
        var t=turret.poll(h,model,hero);
        signals.add("turret",snapshot(t,turret.error));
        int buttons=placementKeys.keys(c,h);
        if(t==null){error=turret.error;placement.reset();server.execute(()->NativeTorbjornRuntime.preview(server,scope,0,false));}
        else{
            var ghost=t.entries().get("ghost");boolean preview=t.active("ghost");
            placementActions.tick(c,h,turret,NativeTorbjornRuntime.cooldown(scope));
            double remaining;try{remaining=turret.placementRemaining(2);}catch(Exception invalid){remaining=Double.NaN;}
            if(preview&&remaining<=.001){previewToken=ghost.tick();lastPreviewWall=now;}
            boolean closing=(buttons&1)!=0&&placement.preview()&&now-lastPreviewWall<=150;
            boolean admitted=(preview&&remaining<=.001)||closing;
            var action=placement.sample(placementKeys.permitted(),admitted,true,previewToken,buttons);
            long token=previewToken;
            if(action==TorbPlacementInput.Action.CONFIRM){deployRequests++;
                server.execute(()->{boolean accepted=NativeTorbjornRuntime.confirm(server,scope,token);c.execute(()->{
                    if(scope.equals(activeScope))placement.confirmed(accepted);
                });});
            }else{boolean visible=placement.preview();server.execute(()->NativeTorbjornRuntime.preview(server,scope,token,visible));}
            if(action==TorbPlacementInput.Action.CANCEL&&(buttons&4)==0||preview&&!admitted)cancelNative=true;
            if(cancelNative){
                if(preview){nativeCancelRequests++;if(placementKeys.cancel(h))nativeCancelMessages++;}
                cancelNative=false;
            }
        }
        var a=armor.poll(h,model,hero);
        signals.add("armor",snapshot(a,armor.error));
        if(a==null){lastThrow=-1;}else{long k=a.entries().get("throw").tick();if(lastThrow<0)lastThrow=k;else if(k>lastThrow){lastThrow=k;String launch="torb-pack:"+h.generation()+":"+model+":"+k;
            NativeMuzzleOrigins.thrown(c,h,launch,hero,c.player.getEyePos(),true);server.execute(()->NativeTorbjornRuntime.throwPack(server,scope,launch));}}
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
        signals.addProperty("deployRequests",deployRequests);signals.addProperty("hammerRequests",hammerRequests);signals.addProperty("nativeCancelRequests",nativeCancelRequests);signals.addProperty("nativeCancelMessages",nativeCancelMessages);NativeTorbjornRuntime.nativeSignals=signals.toString();
    }
    void resetSession(){
        if(activeScope!=null&&activeServer!=null){var s=activeScope;activeServer.execute(()->NativeTorbjornRuntime.cancel(s));}
        activeScope=null;activeServer=null;turret.close();armor.close();hammer.close();core.close();lastStrike=lastThrow=-1;
        scrapClient.close();placementActions.close();previewToken=lastPreviewWall=0;
        coreBegin.missing();frame=frameWall=0;scopeSource=scopeModel=scopeWorld=0;error="";
        placement.reset();cancelNative=false;
        NativeTorbjornRuntime.nativeSignals="{\"ready\":false,\"error\":\"native controller scope reset\"}";
    }
    @Override public void close(){resetSession();}
}
