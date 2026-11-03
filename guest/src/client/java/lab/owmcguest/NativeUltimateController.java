package lab.owmcguest;

import java.util.concurrent.ArrayBlockingQueue;
import net.minecraft.client.MinecraftClient;
import net.minecraft.util.math.Vec3d;

/** Native reads and charge feedback stay off MC's render thread. Q remains native. */
final class NativeUltimateController implements AutoCloseable {
    static final NativeUltimateController INSTANCE=new NativeUltimateController();
    private record Context(HostPoseReader.Pose host,long wallMs,long session,long world){}
    private record Callout(long source,long model,long session,long world,long wallMs){}
    private record Swing(NativeUltimateEventGate.Scope scope,long tick,int node,double damage,long wallMs){}
    private record SwordVisual(NativeUltimateEventGate.Scope scope,long tick,int node,long wallMs){}
    private volatile Context context;
    private volatile boolean running=true;
    static volatile String error="waiting for native ultimate binding";
    static volatile double charge,cost;
    static volatile boolean active;
    private final ArrayBlockingQueue<Swing> queue=new ArrayBlockingQueue<>(64);
    private final ArrayBlockingQueue<Callout> callouts=new ArrayBlockingQueue<>(4);
    private final ArrayBlockingQueue<SwordVisual> visuals=new ArrayBlockingQueue<>(16);
    private volatile long session;
    private Thread worker;
    void tick(MinecraftClient client){
        GenjiUltimateVoice.INSTANCE.tick(client);
        var host=HostPoseReader.INSTANCE.latest();
        long hero=NativeLocomotionController.INSTANCE.hero();
        // Dragonblade is the only calibrated native ultimate event stream in
        // this beta. Other heroes use NativeChargeController for their typed
        // charge/cost meter; do not poll the Genji graph and report a false
        // hero/ability mismatch while those heroes are selected.
        if(hero!=0x02e0000000000029L||host==null||host.flags()!=1||client.player==null||!client.player.isAlive()||client.world==null||client.getServer()==null){
            context=null;callouts.clear();visuals.clear();GenjiUltimateVoice.INSTANCE.stop(client);active=false;charge=0;cost=0;error="";return;
        }
        long world=NativeWorldIdentity.of(client.getServer(),client.world.getRegistryKey());
        context=new Context(host,System.currentTimeMillis(),session,world);
        if(worker==null){worker=new Thread(this::run,"owmc-native-ultimate");worker.setDaemon(true);worker.start();}
        Callout callout;while((callout=callouts.poll())!=null){
            if(callout.session()==session&&callout.world()==world&&callout.source()==host.generation()&&callout.model()==NativeDashController.INSTANCE.modelId()&&System.currentTimeMillis()-callout.wallMs()<300)GenjiUltimateVoice.INSTANCE.play(client);
        }
        Swing swing;while((swing=queue.poll())!=null){
            var current=new NativeUltimateEventGate.Scope(session,world,host.generation(),NativeDashController.INSTANCE.modelId());
            if(!NativeUltimateEventGate.accepts(swing.scope(),current,swing.wallMs(),System.currentTimeMillis()))continue;
            var event=swing;var p=client.player;var eye=p.getEyePos();var q=host.rotation();var f=new org.joml.Vector3f(0,0,-1).rotate(q);var r=new org.joml.Vector3f(1,0,0).rotate(q);
            var forward=new Vec3d(f.x,f.y,f.z);var right=new Vec3d(r.x,r.y,r.z);var owner=p.getUuid();var server=client.getServer();
            server.execute(()->NativeUltimateRuntime.swing(server,owner,world,event.scope().source(),event.scope().model(),event.tick(),event.node(),eye,forward,right,event.damage(),event.wallMs()));
        }
    }
    /** Render-thread cosmetics only; damage remains on the original tracking event. */
    void presentSword(MinecraftClient client){
        var host=HostPoseReader.INSTANCE.latest();var c=context;
        if(c==null||host==null||host.flags()!=1||client.player==null||!client.player.isAlive()||client.world==null||client.getServer()==null
            ||NativeLocomotionController.INSTANCE.hero()!=0x02e0000000000029L){visuals.clear();return;}
        long world=NativeWorldIdentity.of(client.getServer(),client.world.getRegistryKey());
        var current=new NativeUltimateEventGate.Scope(session,world,host.generation(),NativeDashController.INSTANCE.modelId());
        SwordVisual event;
        while((event=visuals.poll())!=null){
            if(!NativeUltimateEventGate.accepts(event.scope(),current,event.wallMs(),System.currentTimeMillis()))continue;
            GenjiSwordParticles.present(client,host,event.node(),event.tick(),event.wallMs());
        }
    }
    private void run(){
        long source=0,model=0,scope=-1,world=0,begin=0,timer=0,left=0,right=0,leftAnimation=0,rightAnimation=0,deadline=0,last=System.nanoTime();boolean timerSeen=false;double credit=NativeUltimateRuntime.chargeCredit,remainder=0;
        var voiceGate=new UltimateCalloutGate();
        try(var reader=new NativeAbilityReader(true)){
            while(running){
                try{
                    var c=context;long now=System.currentTimeMillis(),ns=System.nanoTime();double dt=Math.min(.1,(ns-last)/1e9);last=ns;
                    if(c==null||now-c.wallMs()>150){active=false;source=0;queue.clear();callouts.clear();visuals.clear();voiceGate.reset();Thread.sleep(20);continue;}
                    var u=reader.ultimate(c.host());if(u==null){error=reader.error;active=false;source=0;Thread.sleep(50);continue;}
                    if(voiceGate.observe(c.session(),u.source(),u.model(),c.world(),u.begin())&&!callouts.offer(new Callout(u.source(),u.model(),c.session(),c.world(),now)))throw new IllegalStateException("native callout queue full");
                    if(source!=u.source()||model!=u.model()||scope!=c.session()||world!=c.world()){
                        queue.clear();visuals.clear();source=u.source();model=u.model();scope=c.session();world=c.world();begin=u.begin();timer=u.timer();left=u.left();right=u.right();leftAnimation=u.leftAnimation();rightAnimation=u.rightAnimation();deadline=u.timerActive()?now+8500:0;timerSeen=u.timerActive();remainder=0;credit=NativeUltimateRuntime.chargeCredit;
                    }else{
                        if(u.begin()>begin){deadline=now+9500;begin=u.begin();timerSeen=false;}
                        if(u.timer()>timer){deadline=now+8500;timer=u.timer();timerSeen=true;}
                    }
                    if(timerSeen&&!u.timerActive())deadline=0;
                    if(context!=c||c.session()!=session)continue;
                    active=deadline>now;
                    if(active){
                        var identity=new NativeUltimateEventGate.Scope(c.session(),c.world(),source,model);
                        if(u.left()>left&&!queue.offer(new Swing(identity,u.left(),57,u.damage(),now)))throw new IllegalStateException("native sword queue full");
                        if(u.right()>right&&!queue.offer(new Swing(identity,u.right(),58,u.damage(),now)))throw new IllegalStateException("native sword queue full");
                        if(u.leftAnimation()>leftAnimation&&!visuals.offer(new SwordVisual(identity,u.leftAnimation(),47,now)))throw new IllegalStateException("native sword visual queue full");
                        if(u.rightAnimation()>rightAnimation&&!visuals.offer(new SwordVisual(identity,u.rightAnimation(),48,now)))throw new IllegalStateException("native sword visual queue full");
                    }
                    left=Math.max(left,u.left());right=Math.max(right,u.right());charge=u.charge();cost=u.cost();
                    leftAnimation=Math.max(leftAnimation,u.leftAnimation());rightAnimation=Math.max(rightAnimation,u.rightAnimation());
                    double total=NativeUltimateRuntime.chargeCredit,earned=Math.max(0,total-credit);credit=total;
                    // Missing offline server policy: 5 native points/sec + actual
                    // shuriken/dash HP dealt. Native graph still owns Q and drain.
                    if(!active&&u.charge()<u.cost()){
                        remainder+=dt*5+earned;double added=u.chargeType()==2?Math.floor(remainder):remainder;
                        if(added>0&&context==c&&c.session()==session){reader.charge(u,Math.min(u.cost(),u.charge()+added));remainder-=added;}
                    }else remainder=0;
                    error="";
                }catch(Exception failure){error=failure.toString();active=false;source=0;}
                Thread.sleep(20);
            }
        }catch(InterruptedException stop){Thread.currentThread().interrupt();}
    }
    @Override public void close(){running=false;context=null;if(worker!=null)worker.interrupt();queue.clear();callouts.clear();visuals.clear();}
    void resetSession(){session++;context=null;queue.clear();callouts.clear();visuals.clear();GenjiUltimateVoice.INSTANCE.stop(MinecraftClient.getInstance());active=false;charge=0;cost=0;error="native session transition";}
}
