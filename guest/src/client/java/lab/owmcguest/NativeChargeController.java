package lab.owmcguest;
import net.minecraft.client.MinecraftClient;

/** Generic offline-server charge adapter; Genji remains owned by NativeUltimateController. */
final class NativeChargeController implements AutoCloseable {
    static final NativeChargeController INSTANCE=new NativeChargeController();
    private static final long BASTION=0x02e0000000000015L;
    record SkillGate(boolean ready,boolean active){}
    static boolean requiresSkills(long hero){return hero==0x02e0000000000006L||hero==0x02e0000000000008L||hero==NativeVisorRuntime.HERO||hero==NativeDeadeyeRuntime.HERO||hero==NativeReaperRuntime.HERO||hero==BASTION||hero==NativeInfraSightState.HERO||hero==NativeJunkratController.HERO;}
    /** Native form state, never Q input or a guessed ultimate duration. */
    static SkillGate skillGate(long hero,long source,long model,NativeSkillReader.State state,double[] geometry){
        if(hero==0x02e0000000000006L){
            boolean ready=state!=null&&state.hero()==hero&&state.source()==source&&state.model()==model&&state.entries().keySet().equals(java.util.Set.of("ultimate","coreAnimation","coreArmor","coreEffect","coreTimer"))&&state.entries().values().stream().noneMatch(java.util.Objects::isNull);
            return new SkillGate(ready,ready&&state.entries().values().stream().anyMatch(NativeSkillReader.Entry::active));
        }
        if(hero==NativeInfraSightState.HERO){
            boolean ready=state!=null&&state.hero()==hero&&state.source()==source&&state.model()==model&&state.entries().keySet().equals(java.util.Set.of("ultimate","infraAnimation","infraEffect","infraTimer"))&&state.entries().values().stream().noneMatch(java.util.Objects::isNull);
            return new SkillGate(ready,ready&&state.entries().values().stream().anyMatch(NativeSkillReader.Entry::active));
        }
        if(hero==NativeJunkratController.HERO){
            // integrator/builders: independent junkTire binding; missing nodes deny credit.
            boolean ready=state!=null&&state.hero()==hero&&state.source()==source&&state.model()==model
                &&state.entries().keySet().equals(java.util.Set.of("create","control","view","windup"))
                &&state.entries().values().stream().noneMatch(java.util.Objects::isNull);
            return new SkillGate(ready,ready&&(state.active("windup")||state.active("control")||state.active("view")));
        }
        if(hero==BASTION){
            if(state==null||state.source()!=source||state.model()!=model||state.hero()!=hero
                ||!state.entries().keySet().equals(java.util.Set.of("recon","sentry","tank"))||state.entries().values().stream().anyMatch(java.util.Objects::isNull))return new SkillGate(false,false);
            boolean tank=state.active("tank");
            // Empty/conflicting forms include real transformations and missing
            // logger state. They cannot bank damage or passive charge for End.
            boolean known=!NativeMotorIntent.bastionForm(state.active("recon"),state.active("sentry"),tank).equals("transition");
            return new SkillGate(known,tank);
        }
        boolean soldier=hero==NativeVisorRuntime.HERO,mccree=hero==NativeDeadeyeRuntime.HERO,reaper=hero==NativeReaperRuntime.HERO;
        boolean ready=!requiresSkills(hero)||state!=null&&(!(soldier||reaper)||geometry!=null);
        boolean active=state!=null&&(mccree?state.active("ultimate"):soldier?(state.active("ultimate")||state.active("visor")):reaper?(state.active("ultimate")||state.active("firing")||state.active("animation")):(state.active("barrage")||state.active("windup")||state.active("firing")));
        return new SkillGate(ready,active);
    }
    private record Context(HostPoseReader.Pose host,long model,long hero,long world,long wallMs,long session,java.util.UUID owner){
        NativeChargeScope.Sample sample(){return new NativeChargeScope.Sample(new NativeChargeScope.Identity(host.pid(),host.generation(),model,hero,world,session),wallMs);}
    }
    private volatile long session;
    private volatile Context context;private volatile boolean running=true;private Thread worker;
    static volatile String status="{\"ready\":false}";
    private boolean current(Context captured){
        var latest=context;return captured!=null&&latest!=null&&session==captured.session()
            &&NativeChargeScope.current(captured.sample(),latest.sample(),System.currentTimeMillis());
    }
    void tick(MinecraftClient client){
        var host=HostPoseReader.INSTANCE.latest();var p=client.player;
        long hero=NativeLocomotionController.INSTANCE.hero();
        if(host==null||host.flags()!=1||p==null||!p.isAlive()||client.world==null||client.getServer()==null||!NativeChargeEligibility.supported(hero)||NativeChargeEligibility.nativeUltimateOwner(hero)){context=null;NativeVisorRuntime.state=null;return;}
        context=new Context(host,NativeLocomotionController.INSTANCE.modelId(),hero,NativeWorldIdentity.of(client.getServer(),client.world.getRegistryKey()),System.currentTimeMillis(),session,p.getUuid());
        if(worker==null){worker=new Thread(this::run,"owmc-native-charge");worker.setDaemon(true);worker.start();}
    }
    private void run(){
        long hero=0,last=System.nanoTime();var budget=new NativeChargeBudget();
        var visorWindow=new NativeVisorAim.Window();
        // Initialize its registered Spec before constructing the named reader.
        var junkController=NativeJunkratController.INSTANCE;
        try(var meter=new NativeMeterReader();var skills=new NativeSkillReader();var junkTire=new NativeSkillReader("junkTire")){
            while(running){
                try{
                    var c=context;long ns=System.nanoTime();double dt=Math.clamp((ns-last)/1e9,0,.1);last=ns;
                    if(!current(c)){budget.reset();meter.close();skills.close();junkTire.close();visorWindow.reset();NativeVisorRuntime.state=null;status="{\"ready\":false}";Thread.sleep(30);continue;}
                    hero=c.hero();boolean soldier=hero==NativeVisorRuntime.HERO,reaper=hero==NativeReaperRuntime.HERO;
                    boolean junk=hero==NativeJunkratController.HERO;
                    var activeReader=junk?junkTire:skills;
                    var state=requiresSkills(hero)?activeReader.poll(c.host(),c.model(),hero):null;
                    double[] geometry=state==null?null:soldier?skills.visorGeometry():reaper?skills.reaperParameters():null;
                    if(!current(c))continue;
                    long observedWall=System.currentTimeMillis();
                    long begin=soldier&&state!=null?state.entries().get("visor").tick():0;
                    boolean aiming=soldier&&state!=null&&geometry!=null&&state.active("ultimate")&&state.active("visor")&&begin>0;
                    long started=visorWindow.observe(c.host().generation(),c.model(),c.world(),begin,aiming,observedWall);
                    NativeVisorRuntime.state=soldier&&state!=null&&geometry!=null?new NativeVisorAim.Scope(c.host().generation(),c.model(),c.world(),observedWall,begin,aiming,geometry[0],geometry[1],started):null;
                    var gate=skillGate(hero,c.host().generation(),c.model(),state,geometry);
                    boolean skillsReady=gate.ready(),active=gate.active();
                    // MC tire only blocks this exact current owner/world/source/model session.
                    var tire=NativeJunkratTireRuntime.view;
                    if(junk&&tire!=null&&tire.world()==c.world()&&observedWall>=tire.wall()&&observedWall-tire.wall()<=250
                        &&NativeJunkratRuntime.current(new NativeJunkratRuntime.Scope(c.owner(),c.world(),c.host().generation(),c.model())))active=true;
                    budget.observe(c.sample().identity(),NativeUltimateRuntime.chargeCredit,dt,!active&&skillsReady);
                    var value=meter.poll(c.host(),c.model(),hero);
                    if(value==null){status="{\"ready\":false,\"pendingCredit\":"+budget.pending()+",\"error\":"+new com.google.gson.Gson().toJson(meter.error)+"}";Thread.sleep(50);continue;}
                    if(!current(c))continue;
                    if(!active&&skillsReady){
                        double added=budget.offer(value.charge(),value.cost(),value.kind());
                        // Recheck the latest context immediately before the bounded data write.
                        if(added>0&&current(c)&&meter.credit(value,value.charge()+added))budget.accepted(added);
                    }
                    status="{\"ready\":true,\"hero\":"+hero+",\"modelId\":"+c.model()+",\"worldId\":"+c.world()+",\"hostGeneration\":"+c.host().generation()+",\"charge\":"+value.charge()+",\"cost\":"+value.cost()+",\"active\":"+active+",\"skillsReady\":"+skillsReady+",\"visorActive\":"+aiming+",\"visorBegin\":"+begin+",\"visorStartedWallMs\":"+started+",\"skillError\":"+new com.google.gson.Gson().toJson(!skillsReady?activeReader.error:"")+",\"policy\":\"native-meter-plus-offline-credit\"}";
                }catch(Exception failure){budget.reset();visorWindow.reset();NativeVisorRuntime.state=null;status="{\"ready\":false,\"error\":"+new com.google.gson.Gson().toJson(failure.toString())+"}";}
                Thread.sleep(20);
            }
        }catch(InterruptedException stopped){Thread.currentThread().interrupt();}
    }
    void resetSession(){session++;context=null;NativeVisorRuntime.state=null;status="{\"ready\":false}";}
    @Override public void close(){running=false;context=null;if(worker!=null)worker.interrupt();}
}
