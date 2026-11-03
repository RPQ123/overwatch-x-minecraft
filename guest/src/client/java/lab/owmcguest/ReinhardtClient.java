package lab.owmcguest;

import java.util.*;
import net.minecraft.client.MinecraftClient;
import net.minecraft.entity.MovementType;
import net.minecraft.util.math.Vec3d;

/** Native evidence only. B/E phases are leases, not two casts. An attach, stale
 * source, identity change, lost read or reversed logger clock rebuilds baselines.
 * Shift110 merely records an animation attempt: movement6 must start separately.
 * MC 适配值: charge16m/s, capped3.6s, steering30deg/s, no pin/slam damage without
 * an observed damage node. Actual Entity.move owns world collision as Grapple does.
 * Integration (Claude only): if(ReinhardtClient.INSTANCE.travel(client)){ci.cancel();return;}
 * Place before Grapple/Flight travel ownership checks; do not change the mixin here. */
public final class ReinhardtClient implements HeroClientModule {
    static {
        NativeSkillReader.register("reinhardtHammer",new NativeSkillReader.Spec(ReinhardtServer.HERO,0x0580000000000048L,Map.of("left",9,"right",10)));
        NativeSkillReader.register("reinhardtBarrier",new NativeSkillReader.Spec(ReinhardtServer.HERO,0x0580000000000095L,Map.of("pet",58)));
        NativeSkillReader.register("reinhardtCharge",new NativeSkillReader.Spec(ReinhardtServer.HERO,0x058000000000007dL,Map.of("anim",110,"movement",6,"slam",11,"damage31",31,"damage38",38,"damage63",63,"damage128",128)));
        NativeSkillReader.register("reinhardtFire",new NativeSkillReader.Spec(ReinhardtServer.HERO,0x05800000000000e2L,Map.of("volley",3)));
        NativeSkillReader.register("reinhardtShatter",new NativeSkillReader.Spec(ReinhardtServer.HERO,0x05800000000000beL,Map.of("shockwave",1,"damage",3,"aura",13)));
    }
    public static final ReinhardtClient INSTANCE=new ReinhardtClient();
    private final NativeSkillReader[] readers={new NativeSkillReader("reinhardtHammer"),new NativeSkillReader("reinhardtBarrier"),new NativeSkillReader("reinhardtCharge"),new NativeSkillReader("reinhardtFire"),new NativeSkillReader("reinhardtShatter")};
    private final Map<String,NativeSkillReader.Entry> previous=new HashMap<>();
    private final Set<String> admitted=new HashSet<>();
    private final TanksNodeEvidence evidence=new TanksNodeEvidence();
    private static final String[] PURPOSES={"hammer","barrier","charge","fire","shatter"};
    private ReinhardtServer.Scope scope;
    private net.minecraft.server.MinecraftServer lastServer;
    private long frame,frameWall,observedSource,travelWall,chargeWall,lastTravelTick=-1;
    private Vec3d direction;
    private String failure="";
    private boolean renderRegistered;
    private static final double CHARGE_STEP=16/20.0;

    private boolean fresh(String name,NativeSkillReader.Entry e){
        var old=previous.put(name,e);
        if(old==null){admitted.remove(name);return false;}
        if(e.tick()<old.tick()){admitted.remove(name);return false;}
        if(e.tick()==old.tick())return false;
        if(e.active())admitted.add(name);else admitted.remove(name);
        return true;
    }
    private NativeSkillReader.State poll(int index,HostPoseReader.Pose h,long model){
        var s=readers[index].poll(h,model,ReinhardtServer.HERO);
        String prefix=PURPOSES[index]+".";
        if(s==null)evidence.unavailable(prefix);
        else s.entries().forEach((name,e)->evidence.observe(prefix+name,e.tick(),e.active()));
        if(s==null){failure+=readers[index].error+"; ";
            String[] names=switch(index){case 0->new String[]{"left","right"};case 1->new String[]{"pet"};case 2->new String[]{"anim","movement","slam"};case 3->new String[]{"volley"};default->new String[]{"shockwave"};};
            for(var name:names){previous.remove(name);admitted.remove(name);}}
        return s;
    }
    @Override public void tick(MinecraftClient c){
        var h=HostPoseReader.INSTANCE.latest();long model=NativeLocomotionController.INSTANCE.modelId();
        if(h==null||h.flags()!=1||!h.inputActive()||c.player==null||!c.player.isAlive()||c.player.hasVehicle()||c.world==null||c.getServer()==null
            ||NativeLocomotionController.INSTANCE.hero()!=ReinhardtServer.HERO||model==0){resetSession();return;}
        long now=System.currentTimeMillis();
        if(frame!=h.frame()||observedSource!=h.generation()){frame=h.frame();observedSource=h.generation();frameWall=now;}
        if(now-frameWall>150){resetSession();return;}
        var next=new ReinhardtServer.Scope(c.player.getUuid(),NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey()),h.generation(),model);
        if(!next.equals(scope)){resetSession();scope=next;}
        lastServer=c.getServer();failure="";long[] events=new long[6];
        var hammer=poll(0,h,model);
        if(hammer!=null)for(int i=0;i<2;i++){String name=i==0?"left":"right";var e=hammer.entries().get(name);if(fresh(name,e)&&e.active())events[i]=e.tick();}
        var barrier=poll(1,h,model);if(barrier!=null)fresh("pet",barrier.entries().get("pet"));
        var charge=poll(2,h,model);
        if(charge!=null){
            var anim=charge.entries().get("anim");if(fresh("anim",anim)&&anim.active())events[2]=anim.tick();
            var movement=charge.entries().get("movement");
            if(fresh("movement",movement)&&movement.active()&&admitted.contains("anim")){
                events[5]=movement.tick();chargeWall=now;direction=flat(c.player.getRotationVec(1));lastTravelTick=-1;}
            fresh("slam",charge.entries().get("slam"));
            if(!admitted.contains("movement")||!admitted.contains("anim")||admitted.contains("slam"))stopTravel(c);
        }else stopTravel(c);
        // These definitions have no successful cast evidence. Observe candidates only.
        for(int i=3;i<5;i++){var s=poll(i,h,model);if(s!=null){String name=i==3?"volley":"shockwave";var e=s.entries().get(name);
            var old=previous.get(name);if(fresh(name,e)&&(e.active()||old!=null&&!old.active()))events[i]=e.tick();}}
        boolean left=admitted.contains("left"),right=admitted.contains("right"),raised=admitted.contains("pet");
        boolean moving=direction!=null;travelWall=now;var server=c.getServer();var current=scope;
        var diagnostics=evidence.snapshot();
        server.execute(()->{ReinhardtServer.INSTANCE.sample(server,current,now,events,left,right,raised,moving);
            ReinhardtServer.INSTANCE.observeCandidates(current,now,diagnostics);});
    }
    private static Vec3d flat(Vec3d v){var f=v.multiply(1,0,1);return f.lengthSquared()<1e-6?null:f.normalize();}
    private void stopTravel(MinecraftClient c){if(direction!=null&&c.player!=null)c.player.setVelocity(0,c.player.getVelocity().y,0);direction=null;}
    /** The existing movement mixin must call this; this module adds no mixins. */
    public boolean travel(MinecraftClient c){
        var p=c.player;var h=HostPoseReader.INSTANCE.latest();long now=System.currentTimeMillis();
        if(direction==null)return false;
        if(p==null||!p.isAlive()||p.hasVehicle()||c.world==null||c.getServer()==null||scope==null||h==null||h.flags()!=1||!h.inputActive()
            ||now-travelWall>150||now-frameWall>150||now-chargeWall>3600||h.generation()!=scope.source()
            ||!p.getUuid().equals(scope.owner())||NativeLocomotionController.INSTANCE.hero()!=ReinhardtServer.HERO
            ||NativeLocomotionController.INSTANCE.modelId()!=scope.model()
            ||NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey())!=scope.world()){stopTravel(c);return false;}
        if(lastTravelTick==p.age)return true;lastTravelTick=p.age;
        var desired=flat(p.getRotationVec(1));
        if(desired!=null){double angle=Math.atan2(direction.x*desired.z-direction.z*desired.x,direction.dotProduct(desired));
            angle=Math.max(-Math.toRadians(1.5),Math.min(Math.toRadians(1.5),angle));
            direction=new Vec3d(direction.x*Math.cos(angle)-direction.z*Math.sin(angle),0,direction.x*Math.sin(angle)+direction.z*Math.cos(angle));}
        var before=p.getPos();double dy=Math.max(-1.5,p.getVelocity().y-.08);
        p.setVelocity(Vec3d.ZERO);p.move(MovementType.SELF,direction.multiply(CHARGE_STEP).add(0,dy,0));
        var moved=p.getPos().subtract(before);p.setVelocity(moved);
        if(p.horizontalCollision||moved.multiply(1,0,1).lengthSquared()<.01){stopTravel(c);admitted.remove("movement");}
        return true;
    }
    @Override public void resetSession(){
        var server=lastServer;var old=scope;
        if(server!=null&&old!=null)server.execute(()->ReinhardtServer.INSTANCE.invalidate(server,old));
        stopTravel(MinecraftClient.getInstance());for(var r:readers)r.close();previous.clear();admitted.clear();evidence.clear();
        scope=null;lastServer=null;travelWall=chargeWall=0;lastTravelTick=-1;failure="";
        // A reset must never make an unchanged/frozen host frame fresh again.
    }
    /** Original barrier/charge/hammer remain in OW. No substitute mesh is invented. */
    @Override public void registerRender(){if(renderRegistered)return;renderRegistered=true;}
    @Override public String errorKey(){return "reinhardtError";}
    @Override public String error(){return failure;}
}
