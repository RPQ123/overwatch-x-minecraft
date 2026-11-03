package lab.owmcguest;

import java.util.*;
import net.fabricmc.fabric.api.client.rendering.v1.WorldRenderEvents;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.WorldRenderer;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.util.math.BlockPos;

/** Native channel/Volley reader. No keyboard-derived events or energy/ammo writes.
 * A missing read/stale host/world/model transition drops leases and baselines.
 * E TrackTargets is diagnostic only, including a future Aura candidate with no
 * mapped native target. Rendering stays in this hero's file, no shared edits. */
public final class ZaryaClient implements HeroClientModule {
    static {
        NativeSkillReader.register("zaryaPrimary",new NativeSkillReader.Spec(ZaryaServer.HERO,0x0580000000000241L,Map.of("beam",36,"grenade",42)));
        NativeSkillReader.register("zaryaSelf",new NativeSkillReader.Spec(ZaryaServer.HERO,0x0580000000000244L,Map.of("aura",15)));
        NativeSkillReader.register("zaryaProjected",new NativeSkillReader.Spec(ZaryaServer.HERO,0x058000000000025cL,Map.of("search",24,"aura",43,"pet",32)));
        NativeSkillReader.register("zaryaGraviton",new NativeSkillReader.Spec(ZaryaServer.HERO,0x058000000000025fL,Map.of("volley",2)));
    }
    public static final ZaryaClient INSTANCE=new ZaryaClient();
    private final NativeSkillReader[] readers={new NativeSkillReader("zaryaPrimary"),new NativeSkillReader("zaryaSelf"),new NativeSkillReader("zaryaProjected"),new NativeSkillReader("zaryaGraviton")};
    private final Map<String,NativeSkillReader.Entry> previous=new HashMap<>();
    private final Set<String> admitted=new HashSet<>();
    private final TanksNodeEvidence evidence=new TanksNodeEvidence();
    private static final String[] PURPOSES={"primary","self","projected","graviton"};
    private ZaryaServer.Scope scope;
    private net.minecraft.server.MinecraftServer lastServer;
    private long frame,frameWall,observedSource;
    private String failure="";
    private boolean registered;
    private boolean fresh(String name,NativeSkillReader.Entry e){
        var old=previous.put(name,e);
        if(old==null||e.tick()<old.tick()){admitted.remove(name);return false;}
        if(e.tick()==old.tick())return false;
        if(e.active())admitted.add(name);else admitted.remove(name);return true;
    }
    private boolean volley(String name,NativeSkillReader.Entry e){
        var old=previous.get(name);return fresh(name,e)&&(e.active()||old!=null&&!old.active());
    }
    private NativeSkillReader.State poll(int index,HostPoseReader.Pose h,long model){
        var state=readers[index].poll(h,model,ZaryaServer.HERO);
        String prefix=PURPOSES[index]+".";
        if(state==null)evidence.unavailable(prefix);
        else state.entries().forEach((name,e)->evidence.observe(prefix+name,e.tick(),e.active()));
        if(state==null){failure+=readers[index].error+"; ";
            String[] names=switch(index){case 0->new String[]{"beam","grenade"};case 1->new String[]{"self"};case 2->new String[]{"search","projected"};default->new String[]{"volley"};};
            for(var name:names){previous.remove(name);admitted.remove(name);}}
        return state;
    }
    @Override public void tick(MinecraftClient c){
        var h=HostPoseReader.INSTANCE.latest();long model=NativeLocomotionController.INSTANCE.modelId();
        if(h==null||h.flags()!=1||c.player==null||!c.player.isAlive()||c.world==null||c.getServer()==null||model==0
            ||NativeLocomotionController.INSTANCE.hero()!=ZaryaServer.HERO){resetSession();return;}
        long now=System.currentTimeMillis();
        if(frame!=h.frame()||observedSource!=h.generation()){frame=h.frame();observedSource=h.generation();frameWall=now;}
        if(now-frameWall>150){resetSession();return;}
        var next=new ZaryaServer.Scope(c.player.getUuid(),NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey()),h.generation(),model);
        if(!next.equals(scope)){resetSession();scope=next;}
        lastServer=c.getServer();failure="";long[] events=new long[5];
        var primary=poll(0,h,model);
        if(primary!=null){var beam=primary.entries().get("beam");if(fresh("beam",beam)&&beam.active())events[0]=beam.tick();
            var grenade=primary.entries().get("grenade");if(volley("grenade",grenade))events[1]=grenade.tick();}
        var self=poll(1,h,model);
        var selfSignal=new ZaryaServer.SelfSignal(false,0,false,false);
        if(self!=null){var aura=self.entries().get("aura");var old=previous.get("self");
            selfSignal=new ZaryaServer.SelfSignal(true,aura.tick(),aura.active(),old==null||aura.tick()<old.tick());
            if(fresh("self",aura)&&aura.active())events[2]=aura.tick();}
        boolean candidate=false;var projected=poll(2,h,model);
        if(projected!=null){var search=projected.entries().get("search");if(volley("search",search))events[3]=search.tick();
            var aura=projected.entries().get("aura");candidate=fresh("projected",aura)&&aura.active();}
        var q=poll(3,h,model);if(q!=null){var v=q.entries().get("volley");if(volley("volley",v))events[4]=v.tick();}
        boolean beamActive=admitted.contains("beam"),selfActive=admitted.contains("self");
        var server=c.getServer();var current=scope;boolean projectedCandidate=candidate;var nativeSelf=selfSignal;
        var diagnostics=evidence.snapshot();
        server.execute(()->{ZaryaServer.INSTANCE.sample(server,current,now,events,beamActive,selfActive,nativeSelf);
            ZaryaServer.INSTANCE.observeCandidates(current,now,diagnostics);
            if(projectedCandidate)ZaryaServer.INSTANCE.projectedCandidate(server,current,now);});
        if(selfActive&&c.world!=null){var at=c.player.getPos();c.world.addParticle(ParticleTypes.ENCHANT,at.x,at.y+1,at.z,.3,.3,.3);}
    }
    @Override public void resetSession(){
        var server=lastServer;var old=scope;
        if(server!=null&&old!=null)server.execute(()->ZaryaServer.INSTANCE.invalidate(server,old));
        for(var r:readers)r.close();previous.clear();admitted.clear();evidence.clear();scope=null;lastServer=null;failure="";
        // Keep frame/source freshness across resets: a frozen host cannot re-arm by resetting.
    }
    @Override public void registerRender(){
        if(registered)return;registered=true;
        WorldRenderEvents.AFTER_ENTITIES.register(ctx->{
            if(!Boolean.getBoolean("owmc.frameExport"))return;
            var c=MinecraftClient.getInstance();if(c.world==null||c.getServer()==null||ctx.matrixStack()==null)return;
            long world=NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey()),now=System.currentTimeMillis();
            for(var v:ZaryaServer.INSTANCE.views){
                if(v.world()!=world||now-v.wall()>200||!c.world.isChunkLoaded(BlockPos.ofFloored(v.at())))continue;
                // integrator/colors: keep audited 6b4d8661; blue requires native team-condition proof.
                var pack=OriginalMeshPack.get(v.ultimate()?"zarya-graviton":"zarya-grenade");
                if(pack==null){c.world.addParticle(v.ultimate()?ParticleTypes.PORTAL:ParticleTypes.END_ROD,v.at().x,v.at().y,v.at().z,0,0,0);continue;}
                var m=ctx.matrixStack();var cam=ctx.camera().getPos();m.push();m.translate(v.at().x-cam.x,v.at().y-cam.y,v.at().z-cam.z);
                if(v.velocity().lengthSquared()>1e-6){var d=v.velocity().normalize();m.multiply(new org.joml.Quaternionf().rotationTo(0,0,1,(float)d.x,(float)d.y,(float)d.z));}
                pack.draw(c.getBufferBuilders().getEntityVertexConsumers(),m.peek(),WorldRenderer.getLightmapCoordinates(c.world,BlockPos.ofFloored(v.at())));m.pop();
            }
        });
    }
    @Override public String errorKey(){return "zaryaError";}
    @Override public String error(){return failure;}
}
