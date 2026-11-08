package lab.owmcguest;

import net.minecraft.client.MinecraftClient;

/** 美 Q 暴雪（以及后续冰墙）：原版 graph064a WeaponVolley10 的新 tick 准入一次 MC 投掷。首个样本只作基线。 */
public final class NativeMeiSkillController implements AutoCloseable {
    public static final NativeMeiSkillController INSTANCE=new NativeMeiSkillController();
    private final NativeSkillReader blizzard=new NativeSkillReader("blizzard"),wall=new NativeSkillReader("iceWall");
    private long previewToken,lastPreviewWall;
    private final TorbPlacementInput placement=new TorbPlacementInput();
    private final NativeTorbPlacementInput keys=new NativeTorbPlacementInput(0x45,0x45);
    private final NativePlacementActionClient actions=new NativePlacementActionClient(1);
    private NativeIceWallRuntime.Scope activeScope;private net.minecraft.server.MinecraftServer activeServer;
    private long lastVolley=-1,scopeSource,scopeModel,scopeWorld,frame,frameWall;
    static volatile String error="";
    void tick(MinecraftClient c){
        var h=HostPoseReader.INSTANCE.latest();long hero=NativeLocomotionController.INSTANCE.hero(),model=NativeLocomotionController.INSTANCE.modelId();
        if(h==null||h.flags()!=1||c.player==null||!c.player.isAlive()||c.world==null||c.getServer()==null||hero!=NativeMeiFreezeRuntime.HERO){resetSession();return;}
        long now=System.currentTimeMillis();if(h.frame()!=frame){frame=h.frame();frameWall=now;}if(now-frameWall>150){resetSession();return;}
        long world=NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey());
        if(scopeSource!=h.generation()||scopeModel!=model||scopeWorld!=world){resetSession();scopeSource=h.generation();scopeModel=model;scopeWorld=world;}
        var server0=c.getServer();var wallScope=new NativeIceWallRuntime.Scope(c.player.getUuid(),world,h.generation(),model);
        activeScope=wallScope;activeServer=server0;
        var e=wall.poll(h,model,hero);
        if(e!=null){
            actions.tick(c,h,wall,NativeIceWallRuntime.cooldown(wallScope));
            int buttons=keys.keys(c,h);boolean nativePreview=e.active("preview");
            double remaining;try{remaining=wall.placementRemaining(1);}catch(Exception invalid){remaining=Double.NaN;}
            if(nativePreview&&remaining<=.001){previewToken=e.entries().get("preview").tick();lastPreviewWall=now;}
            // Original FindGround2 can end in the very frame LMB confirms. Use
            // only the already visible plan for that edge, never a late animation.
            boolean closing=(buttons&1)!=0&&placement.preview()&&now-lastPreviewWall<=150;
            boolean admitted=(nativePreview&&remaining<=.001)||closing;
            var action=placement.sample(keys.permitted(),admitted,true,previewToken,buttons);
            if(action==TorbPlacementInput.Action.CONFIRM){long token=previewToken;
                server0.execute(()->{boolean accepted=NativeIceWallRuntime.request(server0,wallScope,token);c.execute(()->{if(wallScope.equals(activeScope))placement.confirmed(accepted);});});
            }else{boolean visible=placement.preview();long token=previewToken;server0.execute(()->NativeIceWallRuntime.preview(server0,wallScope,token,visible));}
            // Physical E already travels through the original input owner.
            // Sending E again here toggles the native preview twice. A pending
            // placement also closes through the body mailbox; do not flood E
            // every tick while its real cooldown is positive.
            if(nativePreview&&action==TorbPlacementInput.Action.CANCEL&&(buttons&2)==0)keys.cancel(h);
        }else {error=wall.error;placement.reset();server0.execute(()->NativeIceWallRuntime.preview(server0,wallScope,0,false));}
        var q=blizzard.poll(h,model,hero);if(q==null){error=blizzard.error;lastVolley=-1;return;}error="";
        var v=q.entries().get("volley");
        if(lastVolley<0){lastVolley=v.tick();return;}
        if(v.tick()>lastVolley){lastVolley=v.tick();var server=c.getServer();
            var scope=new NativeBlizzardRuntime.Scope(c.player.getUuid(),world,h.generation(),model);String launch="blizzard:"+h.generation()+":"+model+":"+v.tick();
            NativeMuzzleOrigins.thrown(c,h,launch,hero,c.player.getEyePos().add(c.player.getRotationVec(1).multiply(.6)),true);server.execute(()->NativeBlizzardRuntime.cast(server,scope,launch));}
    }
    void resetSession(){if(activeScope!=null&&activeServer!=null){var old=activeScope;activeServer.execute(()->NativeIceWallRuntime.cancel(old));}activeScope=null;activeServer=null;actions.close();placement.reset();blizzard.close();wall.close();lastVolley=-1;previewToken=lastPreviewWall=0;frame=frameWall=0;scopeSource=scopeModel=scopeWorld=0;error="";}
    @Override public void close(){resetSession();}
}
