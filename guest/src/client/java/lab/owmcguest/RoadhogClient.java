package lab.owmcguest;

import java.util.Map;
import net.minecraft.client.MinecraftClient;

/** Read-only native phase bridge. Gunshots use the existing acknowledged journal,
 * never lossy factoryCalibration snapshots, keys, ammo guesses or a new owner. */
public final class RoadhogClient implements HeroClientModule {
    static {
        NativeSkillReader.register("roadhogWeapon",new NativeSkillReader.Spec(RoadhogRules.HERO,0x05800000000001c6L,Map.of("primary",30,"secondary",34,"wholeHog",37)));
        NativeSkillReader.register("roadhogHook",new NativeSkillReader.Spec(RoadhogRules.HERO,0x05800000000001c8L,Map.of("cast",11,"search",19,"damage",21)));
        NativeSkillReader.register("roadhogHeal",new NativeSkillReader.Spec(RoadhogRules.HERO,0x0580000000000240L,Map.of("heal",23,"cast",12)));
    }
    public static final RoadhogClient INSTANCE=new RoadhogClient();
    private final NativeSkillReader weapon=new NativeSkillReader("roadhogWeapon"),hook=new NativeSkillReader("roadhogHook"),heal=new NativeSkillReader("roadhogHeal");
    private final Phase q=new Phase(),cast=new Phase(),search=new Phase(),breather=new Phase(),breatherCast=new Phase();
    private final RoadhogSplitSound splitSound=new RoadhogSplitSound();
    private RoadhogServer.Scope scope;private net.minecraft.server.MinecraftServer server;
    private long frame,generation,frameWall,lastWall,lastHook;private String error="";
    private static volatile long lockedUntil;
    private RoadhogClient(){}
    @Override public String errorKey(){return "roadhogError";}
    @Override public String error(){return error.isEmpty()?RoadhogRenderer.error:error;}
    /** Baseline an already active window; a reconnect must never replay its Begin. */
    static final class Phase {
        private NativeSkillReader.Entry previous;private long token;
        long update(NativeSkillReader.Entry e){
            if(e==null)throw new IllegalArgumentException("phase absent");
            if(previous==null||e.tick()<previous.tick()){previous=e;token=0;return 0;}
            if(!e.active())token=0;
            else if(!previous.active()&&e.tick()>previous.tick())token=e.tick();
            previous=e;return token;
        }
        void reset(){previous=null;token=0;}
    }
    public static boolean breatherLocked(){return System.currentTimeMillis()<=lockedUntil;}
    @Override public void tick(MinecraftClient c){
        var h=HostPoseReader.INSTANCE.latest();var loc=NativeLocomotionController.INSTANCE;
        long now=System.currentTimeMillis();
        if(h==null||h.flags()!=1||!h.inputActive()||loc.hero()!=RoadhogRules.HERO||loc.modelId()==0
            ||c.player==null||!c.player.isAlive()||c.world==null||c.getServer()==null){resetSession();return;}
        if(lastWall>0&&now-lastWall>150)resetSession();lastWall=now;
        if(h.frame()!=frame||h.generation()!=generation){frame=h.frame();generation=h.generation();frameWall=now;}
        if(now-frameWall>150){resetSession();error="native frame stale";return;}
        long world=NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey());
        var current=new RoadhogServer.Scope(c.player.getUuid(),world,h.generation(),loc.modelId());
        if(!current.equals(scope)){resetSession();scope=current;server=c.getServer();lastWall=now;}
        var w=weapon.poll(h,loc.modelId(),RoadhogRules.HERO);var k=hook.poll(h,loc.modelId(),RoadhogRules.HERO);var b=heal.poll(h,loc.modelId(),RoadhogRules.HERO);
        if(w==null||k==null||b==null){String failure=w==null?weapon.error:k==null?hook.error:heal.error;resetSession();error=failure;return;}
        long whole=q.update(w.entries().get("wholeHog")),hc=cast.update(k.entries().get("cast")),hs=search.update(k.entries().get("search")),hb=breather.update(b.entries().get("heal")),bc=breatherCast.update(b.entries().get("cast"));
        lockedUntil=bc>0?now+150:0;
        if(hc>0&&hc!=lastHook){lastHook=hc;RoadhogRenderer.hookOrigin.begin(RoadhogServer.hookId(scope,hc),now);}
        var s=scope;var srv=server;var sample=new RoadhogServer.Sample(hc,hs,hb,whole,bc);
        srv.execute(()->RoadhogServer.INSTANCE.refresh(srv,s,now,sample));splitSound.tick(c,scope);error="";
    }
    @Override public void resetSession(){
        if(scope!=null&&server!=null){var old=scope;server.execute(()->RoadhogServer.INSTANCE.suspend(old));}
        weapon.close();hook.close();heal.close();q.reset();cast.reset();search.reset();breather.reset();breatherCast.reset();
        RoadhogRenderer.hookOrigin.clear();
        splitSound.reset(MinecraftClient.getInstance());
        scope=null;server=null;lastWall=lastHook=lockedUntil=0;error="";
    }
    @Override public void registerRender(){RoadhogRenderer.register();}
}
