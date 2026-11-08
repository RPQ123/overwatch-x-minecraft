package lab.owmcguest;

import java.util.Map;
import net.minecraft.client.MinecraftClient;
import net.minecraft.util.math.Vec3d;

/** Read-only binding to original committed states. No key/ammo-derived casts. */
public final class WinstonClient implements HeroClientModule {
    static {
        NativeSkillReader.register("winstonJump",new NativeSkillReader.Spec(WinstonRules.HERO,0x058000000000010aL,Map.of("cast",32,"movement",14,"ability",58)));
        NativeSkillReader.register("winstonBarrier",new NativeSkillReader.Spec(WinstonRules.HERO,0x05800000000000faL,Map.of("cast",20,"pet",22,"ability",26)));
        NativeSkillReader.register("winstonPrimal",new NativeSkillReader.Spec(WinstonRules.HERO,0x0580000000000109L,Map.of("rage",10,"pool",7)));
        NativeSkillReader.register("winstonFists",new NativeSkillReader.Spec(WinstonRules.HERO,0x05800000000000feL,Map.of("left",69,"right",70,"leftSwing",63,"rightSwing",62)));
    }
    public static final WinstonClient INSTANCE=new WinstonClient();
    private final NativeSkillReader[] readers={new NativeSkillReader("winstonJump"),new NativeSkillReader("winstonBarrier"),new NativeSkillReader("winstonPrimal"),new NativeSkillReader("winstonFists")};
    private final WinstonFistPhase jump=new WinstonFistPhase();
    private final WinstonCastPhase barrier=new WinstonCastPhase(),barrierEffect=new WinstonCastPhase();
    private final WinstonRules.Phase rage=new WinstonRules.Phase();
    private final WinstonPrimalStrike left=new WinstonPrimalStrike(),right=new WinstonPrimalStrike();
    private final WinstonNativeAction jumpAction=new WinstonNativeAction(5),barrierAction=new WinstonNativeAction(6);
    private final WinstonJumpFlight flight=new WinstonJumpFlight();
    private final WinstonJumpLaunch launch=new WinstonJumpLaunch();
    private final WinstonJumpInput jumpInput=new WinstonJumpInput();
    private WinstonServer.Scope scope;private net.minecraft.server.MinecraftServer server;
    private long frame,source,frameWall,lastWall,lastRageWall,rageToken,jumpNativeToken;private String failure="";
    private static volatile long primalUntil;
    static volatile WinstonAudioGate.NativeSample nativeAudio;
    private WinstonClient(){}
    public static boolean primalLease(){return System.currentTimeMillis()<=primalUntil;}
    @Override public String errorKey(){return "winstonError";}
    @Override public String error(){return failure;}
    private static long phase(WinstonRules.Phase p,NativeSkillReader.State state,String name){var e=state.entries().get(name);return p.observe(e.tick(),e.active());}
    @Override public void tick(MinecraftClient c){
        var h=HostPoseReader.INSTANCE.latest();var loc=NativeLocomotionController.INSTANCE;long now=System.currentTimeMillis();
        if(h==null||h.flags()!=1||loc.hero()!=WinstonRules.HERO||loc.modelId()==0||c.player==null||!c.player.isAlive()
            ||c.player.hasVehicle()||c.world==null||c.getServer()==null){resetSession();return;}
        WinstonDiagnostics.increment("eligibleTicks");WinstonDiagnostics.value("pid",h.pid());WinstonDiagnostics.value("hero",loc.hero());WinstonDiagnostics.value("model",loc.modelId());WinstonDiagnostics.value("generation",h.generation());WinstonDiagnostics.value("inputActive",h.inputActive());
        // A slow MC tick is not a new native pawn. Keep cast baselines so a
        // completed cast during that gap is recovered, rather than baselined
        // away after OW already consumed its cooldown. Identity/frame guards
        // below still revoke genuinely stale/recreated native sessions.
        lastWall=now;
        if(frame!=h.frame()||source!=h.generation()){frame=h.frame();source=h.generation();frameWall=now;}
        if(now-frameWall>150){resetSession();failure="native Winston frame stale";WinstonDiagnostics.stage("frame-rejected",failure);return;}
        var next=new WinstonServer.Scope(c.player.getUuid(),NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey()),h.generation(),loc.modelId());
        if(!next.equals(scope)){resetSession();scope=next;server=c.getServer();lastWall=now;}
        var j=readers[0].poll(h,loc.modelId(),WinstonRules.HERO);var b=readers[1].poll(h,loc.modelId(),WinstonRules.HERO);
        var q=readers[2].poll(h,loc.modelId(),WinstonRules.HERO);var f=readers[3].poll(h,loc.modelId(),WinstonRules.HERO);
        long jt=0,bt=0,lt=0,rt=0;failure="";
        for(int i=0;i<4;i++){boolean ready=new NativeSkillReader.State[]{j,b,q,f}[i]!=null;WinstonDiagnostics.value(new String[]{"jumpReader","barrierReader","rageReader","fistsReader"}[i],ready?"ready":readers[i].error);}
        if(j!=null){
            observeJump(j,now);
            long receipt=jumpAction.tick(readers[0],h,next.world(),jumpNativeToken);
            if(receipt>0)launch.confirm(receipt,jumpAction.confirmedToken(),now);
            applyJump(c,h,now);jt=launch.takeCommit();
        }else failure+=readers[0].error+"; ";
        if(b!=null){
            var cast=b.entries().get("cast");var effect=b.entries().get("pet");long a=barrier.observe(cast.tick(),cast.active()),e=barrierEffect.observe(effect.tick(),effect.active());
            WinstonDiagnostics.value("barrierCastTick",cast.tick());WinstonDiagnostics.value("barrierCastActive",cast.active());WinstonDiagnostics.value("barrierPetTick",effect.tick());
            bt=barrierAction.tick(readers[1],h,next.world(),h.inputActive()?(a>0?a:e):0);
        }else failure+=readers[1].error+"; ";
        // 0109:25 starts both StateStack10 (the real transform flag) and
        // HealthPool7. The absent OW server need not instantiate pool7.
        if(q!=null){rageToken=phase(rage,q,"rage");lastRageWall=now;
            WinstonDiagnostics.value("rageNativeActive",q.active("rage"));WinstonDiagnostics.value("ragePoolActive",q.active("pool"));}
        else if(now-lastRageWall>150)rageToken=0;
        long qt=rageToken;primalUntil=qt>0?now+150:0;
        if(f!=null){var l=f.entries().get("left");var r=f.entries().get("right");var la=f.entries().get("leftSwing");var ra=f.entries().get("rightSwing");
            lt=left.observe(l.tick(),l.active(),la.tick(),la.active(),now);rt=right.observe(r.tick(),r.active(),ra.tick(),ra.active(),now);
            if(!h.inputActive()){lt=rt=0;}}
        var s=scope;var srv=server;var sample=new WinstonServer.Sample(jt,bt,qt,lt,rt,launch.intent());
        srv.execute(()->WinstonServer.INSTANCE.refresh(srv,s,now,sample));
        nativeAudio=new WinstonAudioGate.NativeSample(new WinstonAudioGate.Scope(s.owner(),s.world(),s.source(),s.model()),now,
            jumpAction.confirmedSequence(),jumpAction.confirmedToken(),j==null?-1:readers[0].winstonEffectTick(37),j==null?-1:readers[0].winstonEffectTick(17),
            barrierAction.confirmedSequence(),barrierAction.confirmedToken(),b==null?-1:readers[1].winstonEffectTick(7),b==null?-1:b.entries().get("pet").tick());
        if(!jumpAction.error.isEmpty())failure+=jumpAction.error+"; ";if(!barrierAction.error.isEmpty())failure+=barrierAction.error+"; ";
        WinstonDiagnostics.stage(jt>0?"jump-receipt":bt>0?"barrier-receipt":failure.isEmpty()?"watching-native-casts":"partial-reader-failure",failure);
    }
    private void observeJump(NativeSkillReader.State j,long now){
        var cast=j.entries().get("cast");long token=jump.observe(cast.tick(),cast.active());
        WinstonDiagnostics.value("jumpCastTick",cast.tick());WinstonDiagnostics.value("jumpCastActive",cast.active());WinstonDiagnostics.value("jumpMovementTick",j.entries().get("movement").tick());
        if(token>0){
            jumpNativeToken=token;WinstonDiagnostics.increment("jumpNativeWindows");
            if(launch.nativeCast(token,now))WinstonDiagnostics.increment("jumpNativeLaunchFallbacks");
        }
    }
    private boolean movementScope(MinecraftClient c,HostPoseReader.Pose h,long now){
        return c.player!=null&&c.player.isAlive()&&!c.player.hasVehicle()&&c.world!=null&&c.getServer()!=null&&scope!=null&&h!=null&&h.flags()==1
            &&now-lastWall<=200&&now-lastWall>=0&&h.generation()==scope.source()&&c.player.getUuid().equals(scope.owner())
            &&NativeLocomotionController.INSTANCE.hero()==WinstonRules.HERO&&NativeLocomotionController.INSTANCE.modelId()==scope.model()
            &&NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey())==scope.world();
    }
    /** At travel HEAD: read native intent/cast and apply now, without waiting for
     * mailbox IO or the END_CLIENT_TICK -> next travel queue. */
    public void beforeTravel(MinecraftClient c){
        if(scope==null)return;var h=HostPoseReader.INSTANCE.latest();long now=System.currentTimeMillis();
        NativeLocomotionController.INSTANCE.tick(c);
        if(!movementScope(c,h,now)){launch.revokeInput();return;}
        var j=readers[0].poll(h,scope.model(),WinstonRules.HERO);
        double remaining=Double.NaN;
        if(j!=null)try{remaining=readers[0].placementRemaining(5);}catch(RuntimeException unavailable){failure=unavailable.toString();}
        int key=jumpInput.sample(c,h);boolean ready=Double.isFinite(remaining)&&remaining<=0&&!jumpAction.pending();
        if(launch.input(key==1,key>=0,ready,now))WinstonDiagnostics.increment("jumpPredictions");
        if(j!=null)observeJump(j,now);
        applyJump(c,h,now);
    }
    private void applyJump(MinecraftClient c,HostPoseReader.Pose h,long now){
        long appliedAt=System.currentTimeMillis();
        if(!launch.needsLaunch()||!movementScope(c,h,appliedAt))return;
        var d=c.player.getRotationVec(1);var v=WinstonRules.jump(new NativeShotProtocol.Vec(d.x,d.y,d.z));
        c.player.getAbilities().flying=false;c.player.sendAbilitiesUpdate();c.player.setVelocity(v.x(),v.y(),v.z());c.player.setOnGround(false);c.player.fallDistance=0;flight.launch(c.player.age);launch.launched();
        var s=scope;var srv=server;long intent=launch.intent();srv.execute(()->WinstonServer.INSTANCE.observeJump(srv,s,intent,appliedAt));
        WinstonDiagnostics.value("jumpIntentToImpulseMs",appliedAt-launch.created());
        WinstonDiagnostics.increment("jumpImpulsesApplied");WinstonDiagnostics.value("impulseX",v.x());WinstonDiagnostics.value("impulseY",v.y());WinstonDiagnostics.value("impulseZ",v.z());
    }
    /** Native walk import must not erase the admitted horizontal launch.
     * Vanilla still owns all movement, gravity, drag and block collision. */
    Vec3d momentumMovement(MinecraftClient c,Vec3d vanilla){
        var p=c.player;var h=HostPoseReader.INSTANCE.latest();
        boolean allowed=p!=null&&p.isAlive()&&!p.hasVehicle()&&!p.getAbilities().flying&&!p.isFallFlying()
            &&scope!=null&&c.world!=null&&c.getServer()!=null&&h!=null&&h.flags()==1&&h.generation()==scope.source()
            &&p.getUuid().equals(scope.owner())&&NativeLocomotionController.INSTANCE.hero()==WinstonRules.HERO
            &&NativeLocomotionController.INSTANCE.modelId()==scope.model()
            &&NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey())==scope.world();
        boolean active=flight.owns(p==null?0:p.age,p!=null&&p.isOnGround(),allowed);WinstonDiagnostics.value("jumpMomentumActive",active);
        if(!active)return null;
        WinstonDiagnostics.increment("jumpMomentumMoves");return vanilla;
    }
    @Override public void resetSession(){
        if(scope!=null&&server!=null){var old=scope;var srv=server;srv.execute(()->WinstonServer.INSTANCE.suspend(srv,old));}
        for(var r:readers)r.close();jump.reset();for(var p:new WinstonCastPhase[]{barrier,barrierEffect})p.reset();rage.reset();left.reset();right.reset();
        jumpAction.reset();barrierAction.reset();flight.reset();launch.reset();nativeAudio=null;scope=null;server=null;lastWall=lastRageWall=rageToken=primalUntil=jumpNativeToken=0;failure="";
    }
    @Override public void revalidateSession(java.util.UUID player,long world,long hero,long model,long source){
        if(scope==null||!scope.matches(player,world,hero,model,source)){resetSession();return;}
        // Revoke key edges while keeping actual casts/receipts and motion.
        // A focus/camera change cannot erase a successfully admitted jump.
        launch.revokeInput();
    }
    @Override public void registerRender(){WinstonRenderer.register();}
}
