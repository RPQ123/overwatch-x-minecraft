package lab.owmcguest;

import net.minecraft.client.MinecraftClient;

/** 半藏：原版 graph b9 的 Volley26（散射）/Volley76（龙击）新 tick 各准入一次 MC 实现。首个样本只作基线。 */
public final class NativeHanzoSkillController implements AutoCloseable {
    public static final NativeHanzoSkillController INSTANCE=new NativeHanzoSkillController();
    static final long HERO=0x02e0000000000005L;
    private final NativeSkillReader reader=new NativeSkillReader("hanzoSkills");
    private final HanzoQCastReader qCast=new HanzoQCastReader();
    private final HanzoScatterContextReader scatterContext=new HanzoScatterContextReader();
    private long lastScatter=-1,lastDragon=-1,scopeSource,scopeModel,scopeWorld,frame,frameWall;
    static volatile String error="";
    void tick(MinecraftClient c){
        var h=HostPoseReader.INSTANCE.latest();long hero=NativeLocomotionController.INSTANCE.hero(),model=NativeLocomotionController.INSTANCE.modelId();
        if(h==null||h.flags()!=1||c.player==null||!c.player.isAlive()||c.world==null||c.getServer()==null||hero!=HERO){resetSession();return;}
        long now=System.currentTimeMillis();if(h.frame()!=frame){frame=h.frame();frameWall=now;}if(now-frameWall>150){HanzoControlController.reset();return;}
        long world=NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey());
        if(scopeSource!=h.generation()||scopeModel!=model||scopeWorld!=world){resetSession();scopeSource=h.generation();scopeModel=model;scopeWorld=world;}
        var s=reader.poll(h,model,hero);var q=qCast.poll(h,model);HanzoControlController.refresh(c,h,q,s);if(s==null){error=reader.error;lastScatter=lastDragon=-1;return;}error="";
        var scope=new NativeHanzoSkillRuntime.Scope(c.player.getUuid(),world,h.generation(),model);var server=c.getServer();
        long sc=s.entries().get("scatter").tick(),dr=s.entries().get("dragon").tick();
        if(lastScatter<0||lastDragon<0){lastScatter=sc;lastDragon=dr;return;}
            if(sc>lastScatter){lastScatter=sc;var parameters=scatterContext.poll(h,model,sc);String launch="hanzo-parent:"+h.generation()+":"+model+":"+sc;
                NativeMuzzleOrigins.thrown(c,h,launch,hero,c.player.getEyePos(),false);server.execute(()->NativeHanzoSkillRuntime.scatter(server,scope,parameters,launch));}
        if(dr>lastDragon){lastDragon=dr;long begin=HanzoControlController.nativeBegin();server.execute(()->NativeHanzoSkillRuntime.dragon(server,scope,begin));}
    }
    void resetSession(){HanzoControlController.reset();reader.close();qCast.close();scatterContext.close();lastScatter=lastDragon=-1;frame=frameWall=0;scopeSource=scopeModel=scopeWorld=0;error="";}
    @Override public void close(){resetSession();}
}
