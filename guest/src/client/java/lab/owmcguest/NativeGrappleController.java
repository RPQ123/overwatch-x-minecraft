package lab.owmcguest;

import net.minecraft.client.MinecraftClient;
import net.minecraft.entity.MovementType;
import net.minecraft.util.math.Vec3d;

/** Widowmaker Grappling Hook. Original Shift owns admission, animation, cooldown and HUD;
 * a fresh original fire animation (node61 Begin) triggers one MC hook test and pull.
 * No server exists for the original hook physics, so MC supplies them (WidowGrapplePull). */
public final class NativeGrappleController implements AutoCloseable {
    public static final NativeGrappleController INSTANCE=new NativeGrappleController();
    static final long HERO=0x02e000000000000aL;
    private final NativeSkillReader reader=new NativeSkillReader("grapple");
    private final NativeSkillReader venomReader=new NativeSkillReader("venom");private long lastThrow=-1;
    private WidowGrapplePull.Pull pull,pendingAim;private Vec3d last;
    private final GrappleCastGate gate=new GrappleCastGate();private long pendingStarted;private java.util.UUID scopeOwner;
    private double nativeCooldown;private long nativeReceipts,nativeFailures;
    public record View(java.util.UUID owner,long world,long source,long model,long token,Vec3d anchor,long wall){}
    public static volatile View view;
    private final NativeTorbPlacementInput cancelKeys=new NativeTorbPlacementInput();
    private int previousCancelKeys;private boolean cancelKeysReady,cancelPending,momentum;
    private long momentumStarted,pullToken,cancels;private Vec3d lastLaunch;
    private final NativePlacementActionClient nativeActions=new NativePlacementActionClient(3);
    private long scopeSource,scopeModel,scopeWorld,lastFire=-1,frame,frameWall;
    private int stalled;private long casts,hooks,misses,arrivals,timeouts,blocked;
    static volatile String error="";
    public static volatile String status="{\"pulling\":false}";

    void tick(MinecraftClient c){
        var h=HostPoseReader.INSTANCE.latest();long hero=NativeLocomotionController.INSTANCE.hero(),model=NativeLocomotionController.INSTANCE.modelId();
        if(h==null||h.flags()!=1||c.player==null||!c.player.isAlive()||c.world==null||c.getServer()==null||hero!=HERO){resetSession();return;}
        long now=System.currentTimeMillis();if(h.frame()!=frame){frame=h.frame();frameWall=now;}if(now-frameWall>150){if(pull!=null)end(c.player);cancelKeysReady=false;return;}
        long world=NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey());
        if(scopeSource!=h.generation()||scopeModel!=model||scopeWorld!=world){resetSession();scopeSource=h.generation();scopeModel=model;scopeWorld=world;}
        scopeOwner=c.player.getUuid();
        var state=reader.poll(h,model,hero);if(state==null){error=reader.error;return;}error="";
        try{nativeCooldown=reader.placementRemaining(3);}catch(Exception unavailable){nativeCooldown=Double.NaN;error=unavailable.toString();}
        nativeActions.tick(c,h,reader,new PlacementCooldowns.Scope(c.player.getUuid(),world,h.generation(),model,3));
        var receipt=nativeActions.takeGrappleReceipt();
        if(receipt!=null&&receipt.kind()==4&&receipt.token()==pullToken&&gate.pending()){
            boolean accepted=receipt.phase()==1;gate.receipt(accepted);if(accepted)nativeCooldown=receipt.remaining();nativeReceipts++;
            if(accepted&&pendingAim!=null&&now-pendingStarted<=1000){pull=new WidowGrapplePull.Pull(pendingAim.anchor(),pendingAim.ledge(),now,c.player.getPos());last=null;stalled=0;momentum=false;hooks++;}
            else{if(!accepted)nativeFailures++;else misses++;nativeActions.cancelGrapple(pullToken);}
            pendingAim=null;
        }
        if(gate.pending()&&now-pendingStarted>1000){gate.receipt(false);pendingAim=null;nativeFailures++;nativeActions.cancelGrapple(pullToken);error="native grapple cooldown admission timed out; no MC pull";}
        int keys=cancelKeys.keys(c,h),edge=cancelKeysReady?keys&~previousCancelKeys:0;previousCancelKeys=keys;cancelKeysReady=cancelKeys.permitted();
        if((pull!=null||gate.pending())&&cancelKeys.permitted()&&(edge&(2|8))!=0)cancelPending=true;
        pollVenom(c,h,model,hero,world);
        var fire=state.entries().get("fire");
        if(gate.observe(fire.tick(),state.entries().get("cast").tick(),fire.active(),state.active("window"),cancelKeys.permitted(),nativeCooldown)){
            casts++;pullToken=gate.token();pendingStarted=now;pendingAim=WidowGrapplePull.aim(c.player,now);nativeActions.beginGrapple(pullToken);
        }
        publish();
    }
    /** Venom Mine: a fresh original WeaponVolley1 tick inside the cast admits one MC throw. */
    private void pollVenom(MinecraftClient c,HostPoseReader.Pose h,long model,long hero,long world){
        var v=venomReader.poll(h,model,hero);if(v==null){lastThrow=-1;return;}var t=v.entries().get("throw");
        if(lastThrow<0){lastThrow=t.tick();return;}
        if(t.tick()>lastThrow){lastThrow=t.tick();
            if(v.active("cast")){var server=c.getServer();var scope=new NativeVenomRuntime.Scope(c.player.getUuid(),world,h.generation(),model);String launch="venom:"+h.generation()+":"+model+":"+t.tick();
                NativeMuzzleOrigins.thrown(c,h,launch,hero,c.player.getEyePos().add(c.player.getRotationVec(1).multiply(.5)),true);server.execute(()->NativeVenomRuntime.cast(server,scope,launch));}}
    }
    /** Called from the travel hook; true when the pull owns this tick's movement. */
    public boolean travel(MinecraftClient c){
        var p=c.player;if(pull==null||p==null)return false;
        if(!p.isAlive()||p.hasVehicle()||NativeLocomotionController.INSTANCE.hero()!=HERO){end(null);return false;}
        if(cancelPending){
            // A fast second press can precede the first travel tick after the
            // native receipt. Resolve one bounded real collision step first;
            // never invent a launch velocity through an occupied block.
            if(last==null){var step=WidowGrapplePull.step(p,pull,System.currentTimeMillis());if(step!=null){var before=p.getPos();p.setVelocity(Vec3d.ZERO);p.move(MovementType.SELF,step);last=p.getPos().subtract(before);}}
            cancelPending=false;var launch=GrappleCancelMomentum.release(last==null?null:new NativeShotProtocol.Vec(last.x,last.y,last.z));
            requestNativeCancel(c);
            if(launch!=null){lastLaunch=new Vec3d(launch.x(),launch.y(),launch.z());p.setVelocity(lastLaunch);p.setOnGround(false);p.fallDistance=0;momentum=true;momentumStarted=System.currentTimeMillis();cancels++;}
            pull=null;last=null;stalled=0;publish();return false;
        }
        long now=System.currentTimeMillis();var step=WidowGrapplePull.step(p,pull,now);
        if(step==null){if(now-pull.started()>WidowGrapplePull.MAX_MS)timeouts++;else arrivals++;end(p);return false;}
        var before=p.getPos();p.setVelocity(Vec3d.ZERO);p.move(MovementType.SELF,step);var moved=p.getPos().subtract(before);
        stalled=moved.lengthSquared()<.0025?stalled+1:0;
        if(stalled>=3){blocked++;end(p);return true;}
        last=moved;p.setVelocity(moved);p.fallDistance=0;rope(c,p);publish();return true;
    }
    /** Skip the native walk-speed replacement only for this real airborne
     * cancel. Vanilla travel still owns gravity, drag and Entity.move collision. */
    Vec3d momentumMovement(MinecraftClient c,Vec3d vanilla){
        var p=c.player;var h=HostPoseReader.INSTANCE.latest();
        if(!momentum)return null;
        if(p==null||!p.isAlive()||p.isOnGround()||p.hasVehicle()||p.getAbilities().flying||p.isTouchingWater()||p.isInLava()||p.isFallFlying()
            ||c.world==null||c.getServer()==null||h==null||h.generation()!=scopeSource||!p.getUuid().equals(scopeOwner)
            ||NativeLocomotionController.INSTANCE.hero()!=0&&NativeLocomotionController.INSTANCE.hero()!=HERO||NativeLocomotionController.INSTANCE.modelId()!=0&&NativeLocomotionController.INSTANCE.modelId()!=scopeModel
            ||NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey())!=scopeWorld||System.currentTimeMillis()-momentumStarted>6000){momentum=false;return null;}
        var steering=h.inputActive()?NativeLocomotionController.INSTANCE.baseMovement(Vec3d.ZERO).multiply(.06):Vec3d.ZERO;
        double x=vanilla.x+steering.x,z=vanilla.z+steering.z,scale=Math.min(1,GrappleCancelMomentum.MAX_HORIZONTAL/Math.max(1e-7,Math.hypot(x,z)));
        double y=Math.clamp(vanilla.y,-3.92,GrappleCancelMomentum.MAX_UP);if(p.getY()+p.getHeight()>=c.world.getTopY()-1)y=Math.min(0,y);
        var result=new Vec3d(x*scale,y,z*scale);p.setVelocity(result);return result;
    }
    private void requestNativeCancel(MinecraftClient c){
        nativeActions.cancelGrapple(pullToken);
    }
    /** Rendering owns a single left-hand aperture for hook, flash and rope. */
    private void rope(MinecraftClient c,net.minecraft.client.network.ClientPlayerEntity p){
        // No separately anchored right-hand particles.
    }
    private void end(net.minecraft.client.network.ClientPlayerEntity p){
        if(pull!=null){nativeActions.cancelGrapple(pullToken);if(p!=null){p.setVelocity(WidowGrapplePull.release(p,pull,last));p.fallDistance=0;}}
        pull=null;last=null;stalled=0;publish();
    }
    private void publish(){
        var o=new com.google.gson.JsonObject();o.addProperty("pulling",pull!=null);o.addProperty("casts",casts);o.addProperty("hooks",hooks);
        o.addProperty("manualCancels",cancels);o.addProperty("cancelMomentum",momentum);if(lastLaunch!=null){var velocity=new com.google.gson.JsonObject();velocity.addProperty("x",lastLaunch.x);velocity.addProperty("y",lastLaunch.y);velocity.addProperty("z",lastLaunch.z);o.add("lastCancelVelocity",velocity);}
        o.addProperty("misses",misses);o.addProperty("arrivals",arrivals);o.addProperty("timeouts",timeouts);o.addProperty("blocked",blocked);
        o.addProperty("nativeCooldown",Double.isFinite(nativeCooldown)?nativeCooldown:-1);o.addProperty("cooldownSeconds",12);o.addProperty("nativePending",gate.pending());o.addProperty("nativeReceipts",nativeReceipts);o.addProperty("nativeFailures",nativeFailures);o.addProperty("nativeActionError",nativeActions.error);o.addProperty("origin","left-hand/render-camera");
        o.add("render",com.google.gson.JsonParser.parseString(WidowGrappleRenderer.diagnostics()));
        o.addProperty("range",WidowGrapplePull.RANGE);if(pull!=null){o.addProperty("ledge",pull.ledge());o.addProperty("x",pull.anchor().x);o.addProperty("y",pull.anchor().y);o.addProperty("z",pull.anchor().z);}
        
        view=pull==null||scopeOwner==null?null:new View(scopeOwner,scopeWorld,scopeSource,scopeModel,pullToken,pull.anchor(),System.currentTimeMillis());
        status=o.toString();
    }
    void revalidateSession(java.util.UUID player,long world,long hero,long model,long source){
        if(scopeOwner==null||!scopeOwner.equals(player)||scopeWorld!=world||hero!=0&&hero!=HERO||model!=0&&scopeModel!=model||scopeSource!=source){resetSession();return;}
        cancelKeysReady=false;previousCancelKeys=0; // focus/view changes revoke input edges, not admitted momentum
    }
    void resetSession(){nativeActions.close();reader.close();venomReader.close();gate.reset();lastThrow=-1;pull=pendingAim=null;scopeOwner=null;last=null;stalled=0;lastFire=-1;frame=frameWall=0;scopeSource=scopeModel=scopeWorld=0;error="";momentum=cancelPending=cancelKeysReady=false;previousCancelKeys=0;publish();}
    @Override public void close(){resetSession();}
}
