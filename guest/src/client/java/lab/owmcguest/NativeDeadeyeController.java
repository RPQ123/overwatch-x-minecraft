package lab.owmcguest;

import net.minecraft.client.MinecraftClient;
import net.minecraft.util.math.Vec3d;

/** Read the actual scoped Q/targeting/fire action. No input button admits Q damage. */
public final class NativeDeadeyeController implements AutoCloseable {
    static final NativeDeadeyeController INSTANCE=new NativeDeadeyeController();
    private record Context(HostPoseReader.Pose host,long model,long world,long session,long wall,net.minecraft.server.MinecraftServer server,java.util.UUID owner){}
    private record Candidate(Context context,long observed,long begin,boolean admitted,boolean tracking,boolean fire,boolean firing,long script,long logger,double[] geometry){}
    private volatile Context context;private volatile Candidate candidate;
    private final java.util.concurrent.ArrayBlockingQueue<Candidate> fires=new java.util.concurrent.ArrayBlockingQueue<>(8);
    private final NativeDeadeyeFinish finish=new NativeDeadeyeFinish();
    private volatile long session;private volatile boolean running=true;private Thread worker;
    private long lastPresentationWrite;
    static volatile boolean active;static volatile String error="";
    static volatile String lastFailure="";static volatile long presentationIoFailures;
    void tick(MinecraftClient client){
        finish.releaseDue();
        MccreeVoice.INSTANCE.tick(client);
        DeadeyeShotSound.INSTANCE.tick(client);
        var host=HostPoseReader.INSTANCE.latest();var p=client.player;
        if(host==null||host.flags()!=1||p==null||!p.isAlive()||client.world==null||client.getServer()==null||NativeLocomotionController.INSTANCE.hero()!=NativeDeadeyeRuntime.HERO){context=null;candidate=null;active=false;return;}
        long world=NativeWorldIdentity.of(client.getServer(),client.world.getRegistryKey()),model=NativeLocomotionController.INSTANCE.modelId();
        var c=new Context(host,model,world,session,System.currentTimeMillis(),client.getServer(),p.getUuid());context=c;
        if(worker==null){worker=new Thread(this::run,"owmc-native-deadeye");worker.setDaemon(true);worker.start();}
        Candidate firing;while((firing=fires.poll())!=null)send(client,c,firing);
        send(client,c,candidate);
        var v=candidate;if(v!=null&&v.context().session()==session&&v.context().model()==model&&v.context().world()==world&&v.context().host().generation()==host.generation())finish.complete(client,host,model,world,v.begin(),v.observed(),active);
    }
    private void send(MinecraftClient client,Context c,Candidate v){
        var host=c.host();var p=client.player;long world=c.world(),model=c.model();
        if(v==null||v.context().session()!=session||v.context().model()!=model||v.context().world()!=world||v.context().host().generation()!=host.generation()||System.currentTimeMillis()-v.observed()>150)return;
        var f=new org.joml.Vector3f(0,0,-1).rotate(host.rotation());var forward=new Vec3d(f.x,f.y,f.z);var g=v.geometry();
        var frame=new NativeDeadeyeRuntime.Frame(p.getUuid(),world,host.generation(),model,v.begin(),System.currentTimeMillis(),v.admitted(),v.tracking(),v.fire(),g[0],g[1],g[2],g[3],g[4],p.getEyePos(),forward);
        if(v.admitted())MccreeVoice.INSTANCE.deadeye(client,host.generation(),model,world,v.begin());
        var server=client.getServer();server.execute(()->{NativeDeadeyeRuntime.refresh(frame);if(frame.fire())NativeDeadeyeRuntime.tick(server);});
    }
    private void run(){
        var events=new NativeDeadeyeEvents();boolean admitted=false;long accepted=0,scope=-1,lastGood=0;
        try(var skills=new NativeSkillReader();var meter=new NativeMeterReader()){
            while(running){try{
                var c=context;long now=System.currentTimeMillis();
                if(c!=null&&now-c.wall()>150&&now-c.wall()<=1000){Thread.sleep(20);continue;}
                if(c==null||now-c.wall()>150){skills.close();events.reset();admitted=false;candidate=null;active=false;lastGood=0;Thread.sleep(20);continue;}
                if(scope!=c.session()){scope=c.session();events.reset();admitted=false;accepted=0;lastGood=0;}
                var s=skills.poll(c.host(),c.model(),NativeDeadeyeRuntime.HERO);var g=s==null?null:skills.deadeyeGeometry();
                if(s==null||g==null){
                    error=skills.error;
                    // A two-read snapshot can overlap the actual native fire
                    // transition. Retain admission for at most one second;
                    // every damage/receipt still requires a fresh150ms frame.
                    if(now-lastGood>1000){active=false;candidate=null;events.reset();admitted=false;fires.clear();}
                    Thread.sleep(15);continue;
                }
                if(context==null||session!=c.session())continue;
                now=System.currentTimeMillis();
                if(lastGood!=0&&now-lastGood>1000){events.reset();admitted=false;fires.clear();}
                lastGood=now;
                var inputBinding=skills.deadeyeInputBinding();
                long begin=s.entries().get("ultimate").tick(),fire=s.entries().get("fire").tick();
                active=s.active("ultimate");var e=events.observe(c.host().generation(),c.model(),c.world(),begin,active,fire);
                if(e.started()){admitted=true;accepted=begin;}if(!active)admitted=false;
                long observed=System.currentTimeMillis();
                if(e.fire()){
                    var charge=meter.poll(c.host(),c.model(),NativeDeadeyeRuntime.HERO);
                    if(charge==null||!meter.consumeDeadeye(charge,s))throw new IllegalStateException("Deadeye confirmed-fire charge consumption failed: "+meter.error);
                    if(!fires.offer(new Candidate(c,observed,accepted,admitted,s.active("tracking"),true,events.firing(),inputBinding[0],inputBinding[1],g)))throw new IllegalStateException("Deadeye native fire queue full");
                }
                // Windows can briefly refuse atomic file replacement while the
                // other process reads it. That transport failure is not an
                // original Q cancellation. Retry without losing its admission.
                try{animate(c,skills,accepted,admitted);}
                catch(java.io.IOException io){presentationIoFailures++;lastFailure=io.toString();}
                candidate=new Candidate(c,observed,accepted,admitted,s.active("tracking"),false,events.firing(),inputBinding[0],inputBinding[1],g);error="";
            }catch(Exception e){candidate=null;active=false;events.reset();admitted=false;error=lastFailure=e.toString();}Thread.sleep(15);}
        }catch(InterruptedException e){Thread.currentThread().interrupt();}
    }
    private void animate(Context c,NativeSkillReader skills,long begin,boolean admitted)throws java.io.IOException{
        var request=NativeDeadeyeRuntime.presentation;if(!admitted||request==null||request.begin()!=begin||request.source()!=c.host().generation()||request.world()!=c.world()||request.model()!=c.model()||!request.owner().equals(c.owner()))return;
        String directory=System.getProperty("owmc.nativeEventsDirectory","");if(directory.isBlank())throw new IllegalStateException("Native Deadeye presentation directory missing");
        long now=System.currentTimeMillis();byte[] packet=skills.deadeyePresentation(request.sequence(),request.world(),begin,request.ordinal());
        var dir=java.nio.file.Path.of(directory);var path=dir.resolve("deadeye-presentation-request-"+c.host().pid()+".bin");
        if(now-lastPresentationWrite>=30){var temp=path.resolveSibling(path.getFileName()+".tmp");java.nio.file.Files.write(temp,packet);java.nio.file.Files.move(temp,path,java.nio.file.StandardCopyOption.REPLACE_EXISTING,java.nio.file.StandardCopyOption.ATOMIC_MOVE);lastPresentationWrite=now;}
        var response=dir.resolve("deadeye-presentation-ack-"+c.host().pid()+".bin");if(!java.nio.file.Files.isRegularFile(response)||java.nio.file.Files.size(response)!=88)return;
        byte[] raw=java.nio.file.Files.readAllBytes(response);if(raw.length!=88)return;var b=java.nio.ByteBuffer.wrap(raw).order(java.nio.ByteOrder.LITTLE_ENDIAN);var sent=java.nio.ByteBuffer.wrap(packet).order(java.nio.ByteOrder.LITTLE_ENDIAN);
        if(!new String(raw,0,8,java.nio.charset.StandardCharsets.US_ASCII).equals("OWDEYE01")||b.getInt(8)!=1||b.getInt(12)!=c.host().pid()||b.getLong(16)!=sent.getLong(16)
            ||b.getLong(24)!=request.sequence()||b.getLong(40)!=request.source()||b.getLong(48)!=request.world()||b.getLong(56)!=request.model()||b.getLong(64)!=begin||b.getInt(84)!=request.ordinal())return;
        int phase=b.getInt(80);long wall=b.getLong(32),tick=b.getLong(72);if(phase<1||phase>3||wall>now+50||now-wall>150||tick<=0)return;
        // The server owns receipt admission/idempotence. Do not mark a receipt
        // consumed here: a queued refresh may still be stale when it executes.
        var receipt=new NativeDeadeyeRuntime.Receipt(request.source(),request.world(),request.model(),begin,request.sequence(),request.ordinal(),phase,wall,tick);
        c.server().execute(()->NativeDeadeyeRuntime.receipt(c.server(),receipt));
    }
    boolean acceptsCue(MinecraftClient client,NativeDeadeyeRuntime.ShotCue cue){
        var c=context;var v=candidate;var host=HostPoseReader.INSTANCE.latest();long now=System.currentTimeMillis();
        return c!=null&&v!=null&&host!=null&&host.inputActive()&&client.player!=null&&client.world!=null&&client.getServer()!=null
            &&cue.owner().equals(client.player.getUuid())&&cue.source()==host.generation()&&cue.source()==c.host().generation()
            &&cue.model()==c.model()&&cue.world()==c.world()&&cue.world()==NativeWorldIdentity.of(client.getServer(),client.world.getRegistryKey())
            &&cue.begin()==v.begin()&&v.context().session()==session&&now-v.observed()<=150&&now-c.wall()<=150&&now-cue.wall()<=150&&now>=cue.wall()-50
            &&NativeLocomotionController.INSTANCE.hero()==NativeDeadeyeRuntime.HERO&&NativeLocomotionController.INSTANCE.modelId()==cue.model();
    }
    float gradeStrength(){
        var c=context;var v=candidate;var h=HostPoseReader.INSTANCE.latest();long now=System.currentTimeMillis();
        var client=MinecraftClient.getInstance();
        if(c==null||v==null||h==null||!h.inputActive()||!v.admitted()||!active||v.begin()<=0||v.context().session()!=session
            ||v.context().model()!=c.model()||v.context().world()!=c.world()||v.context().host().generation()!=c.host().generation()
            ||h.generation()!=c.host().generation()||now-c.wall()>150||now-v.observed()>150
            ||client.player==null||!client.player.isAlive()||client.world==null||client.getServer()!=c.server()
            ||!client.player.getUuid().equals(c.owner())||NativeWorldIdentity.of(client.getServer(),client.world.getRegistryKey())!=c.world()
            ||NativeLocomotionController.INSTANCE.hero()!=NativeDeadeyeRuntime.HERO||NativeLocomotionController.INSTANCE.modelId()!=c.model())return 0;
        return 1;
    }
    /** A fresh admitted original Q phase, rather than the Q key or meter value. */
    public static boolean jumpLocked(){return INSTANCE.gradeStrength()>0;}
    NativeDeadeyeInputLock inputLock(){
        var c=context;var v=candidate;var h=HostPoseReader.INSTANCE.latest();
        // New guest + old compositor must never partially freeze MC while the
        // original native camera can still turn. DEY1 is required on both ends.
        if(c==null||v==null||h==null||!h.deadeyeInputGuard()||!v.firing()||gradeStrength()==0||c!=context||v!=candidate)return null;
        var lock=new NativeDeadeyeInputLock(c.host().generation(),c.model(),c.world(),v.begin(),v.script(),v.logger(),v.observed());
        return lock.matches(h.generation(),NativeLocomotionController.INSTANCE.modelId(),c.world(),System.currentTimeMillis())?lock:null;
    }
    /** Charging can still walk/look; only actual confirmed fire locks motion. */
    public static boolean movementLocked(){return INSTANCE.inputLock()!=null;}
    void resetSession(){session++;context=null;candidate=null;fires.clear();finish.reset();MccreeVoice.INSTANCE.reset();DeadeyeShotSound.INSTANCE.reset();active=false;error="";}
    @Override public void close(){running=false;resetSession();if(worker!=null)worker.interrupt();}
}
