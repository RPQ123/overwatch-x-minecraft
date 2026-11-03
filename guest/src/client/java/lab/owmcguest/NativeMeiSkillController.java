package lab.owmcguest;

import net.minecraft.client.MinecraftClient;

/** 美 Q 暴雪（以及后续冰墙）：原版 graph064a WeaponVolley10 的新 tick 准入一次 MC 投掷。首个样本只作基线。 */
public final class NativeMeiSkillController implements AutoCloseable {
    public static final NativeMeiSkillController INSTANCE=new NativeMeiSkillController();
    private final NativeSkillReader blizzard=new NativeSkillReader("blizzard"),wall=new NativeSkillReader("iceWall");
    private long lastConfirm=-1,lastPreviewWall;
    private long lastVolley=-1,scopeSource,scopeModel,scopeWorld,frame,frameWall;
    static volatile String error="";
    void tick(MinecraftClient c){
        var h=HostPoseReader.INSTANCE.latest();long hero=NativeLocomotionController.INSTANCE.hero(),model=NativeLocomotionController.INSTANCE.modelId();
        if(h==null||h.flags()!=1||c.player==null||!c.player.isAlive()||c.world==null||c.getServer()==null||hero!=NativeMeiFreezeRuntime.HERO){resetSession();return;}
        long now=System.currentTimeMillis();if(h.frame()!=frame){frame=h.frame();frameWall=now;}if(now-frameWall>150)return;
        long world=NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey());
        if(scopeSource!=h.generation()||scopeModel!=model||scopeWorld!=world){resetSession();scopeSource=h.generation();scopeModel=model;scopeWorld=world;}
        var server0=c.getServer();var wallScope=new NativeIceWallRuntime.Scope(c.player.getUuid(),world,h.generation(),model);
        var e=wall.poll(h,model,hero);
        if(e!=null){boolean preview=e.active("preview");if(preview)lastPreviewWall=now;server0.execute(()->NativeIceWallRuntime.preview(server0,wallScope,preview));
            long cf=e.entries().get("confirm").tick();
            if(lastConfirm<0)lastConfirm=cf;
            else if(cf>lastConfirm){lastConfirm=cf;if(now-lastPreviewWall<=1000)server0.execute(()->NativeIceWallRuntime.confirm(server0,wallScope));}}
        else {error=wall.error;lastConfirm=-1;}
        var q=blizzard.poll(h,model,hero);if(q==null){error=blizzard.error;lastVolley=-1;return;}error="";
        var v=q.entries().get("volley");
        if(lastVolley<0){lastVolley=v.tick();return;}
        if(v.tick()>lastVolley){lastVolley=v.tick();var server=c.getServer();
            var scope=new NativeBlizzardRuntime.Scope(c.player.getUuid(),world,h.generation(),model);server.execute(()->NativeBlizzardRuntime.cast(server,scope));}
    }
    void resetSession(){blizzard.close();wall.close();lastVolley=-1;lastConfirm=-1;lastPreviewWall=0;frame=frameWall=0;scopeSource=scopeModel=scopeWorld=0;error="";}
    @Override public void close(){resetSession();}
}
