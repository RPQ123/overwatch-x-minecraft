package lab.owmcguest;

import net.minecraft.client.MinecraftClient;

/** One fresh original throw animation plus Volley admits one MC sticky bomb. */
final class NativePulseController implements AutoCloseable {
    static final NativePulseController INSTANCE=new NativePulseController();
    private final NativeSkillReader reader=new NativeSkillReader("pulse");
    private final NativePulseGate gate=new NativePulseGate();
    private long primes,queued;
    static volatile String error="";
    static volatile String status="{\"ready\":false}";
    /** The exporter calls this immediately after locomotion.tick, before the
     * session guard resets that reader and skips the normal controller pass. */
    void prime(MinecraftClient c,HostPoseReader.Pose h,long world,long hero,long model){
        if(h==null||h.flags()!=1||c.player==null||!c.player.isAlive()||c.world==null||c.getServer()==null
            ||hero!=NativePulseRuntime.HERO||world==0||model==0)return;
        var scope=new NativePulseGate.Scope(c.player.getUuid(),h.generation(),world,model);
        if(gate.bound(scope))return;
        var state=reader.poll(h,model,hero);
        if(state==null){error=reader.error;publish(false,scope,0,0);return;}
        gate.prime(scope,state.entries().get("cast").tick(),state.entries().get("deploy").tick(),System.currentTimeMillis());
        primes++;error="";publish(true,scope,state.entries().get("cast").tick(),state.entries().get("deploy").tick());
    }
    void tick(MinecraftClient c){
        var h=HostPoseReader.INSTANCE.latest();long hero=NativeLocomotionController.INSTANCE.hero(),model=NativeLocomotionController.INSTANCE.modelId();
        if(h==null||h.flags()!=1||c.player==null||!c.player.isAlive()||c.world==null||c.getServer()==null||hero!=NativePulseRuntime.HERO){
            resetSession();if(hero!=0&&hero!=NativePulseRuntime.HERO)gate.reset();return;
        }
        long world=NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey());
        var scope=new NativePulseGate.Scope(c.player.getUuid(),h.generation(),world,model);
        var state=reader.poll(h,model,hero);if(state==null){error=reader.error;publish(false,scope,0,0);return;}
        long now=System.currentTimeMillis();var cast=state.entries().get("cast");var volley=state.entries().get("deploy");error="";
        // A binding can appear between the early prime pass and this poll.
        // Count that safe first baseline too; active first snapshots stay silent.
        if(!gate.bound(scope)){gate.prime(scope,cast.tick(),volley.tick(),now);primes++;}
        boolean admitted=gate.observe(scope,cast.tick(),cast.active(),volley.tick(),now,h.inputActive());
        publish(gate.bound(scope),scope,cast.tick(),volley.tick());if(!admitted)return;
        var forward=c.player.getRotationVec(1);var at=c.player.getEyePos().add(forward.multiply(.35));
        var d=new NativePulseRuntime.Deployment(c.player.getUuid(),world,h.generation(),model,volley.tick(),now,at,forward.multiply(15));
        NativeMuzzleOrigins.thrown(c,h,"pulse:"+h.generation()+":"+model+":"+volley.tick(),NativePulseRuntime.HERO,at,true);
        queued++;publish(true,scope,cast.tick(),volley.tick());var server=c.getServer();server.execute(()->NativePulseRuntime.deploy(server,d));
    }
    private void publish(boolean ready,NativePulseGate.Scope scope,long cast,long deploy){
        var o=new com.google.gson.JsonObject();o.addProperty("ready",ready);o.addProperty("primes",primes);o.addProperty("queued",queued);
        o.addProperty("source",scope==null?0:scope.source());o.addProperty("world",scope==null?0:scope.world());o.addProperty("model",scope==null?0:scope.model());
        o.addProperty("castTick",cast);o.addProperty("deployTick",deploy);status=o.toString();
    }
    // NativeSessionGuard also calls this for same-model input confirmation.
    // Keep the cursor; the next authenticated owner either matches or re-baselines.
    void resetSession(){reader.close();error="";publish(false,null,0,0);}
    @Override public void close(){resetSession();gate.reset();}
}
