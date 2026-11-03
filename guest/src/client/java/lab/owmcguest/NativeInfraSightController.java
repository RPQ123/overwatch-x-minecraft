package lab.owmcguest;

import net.minecraft.client.MinecraftClient;
import net.minecraft.entity.Entity;
import net.minecraft.entity.LivingEntity;

/** Actual original Infra-Sight phase -> local loaded MC creature outlines only. */
public final class NativeInfraSightController {
    public static final NativeInfraSightController INSTANCE=new NativeInfraSightController();
    private final NativeSkillReader reader=new NativeSkillReader();
    private final NativeInfraSightState gate=new NativeInfraSightState();
    private NativeInfraSightState.Scope scope;
    private boolean running;
    public static volatile String status="{}";
    private NativeInfraSightController(){}
    public void tick(MinecraftClient c){
        var h=HostPoseReader.INSTANCE.latest();var loc=NativeLocomotionController.INSTANCE;
        if(h==null||h.flags()!=1||!h.inputActive()||loc.hero()!=NativeInfraSightState.HERO||c.player==null||!c.player.isAlive()||c.world==null||c.getServer()==null||c.currentScreen!=null){reset();return;}
        var s=reader.poll(h,loc.modelId(),loc.hero());
        if(s==null){running=false;gate.reset();status="{\"active\":false,\"error\":"+new com.google.gson.Gson().toJson(reader.error)+"}";return;}
        scope=new NativeInfraSightState.Scope(c.player.getUuid(),NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey()),h.generation(),s.model());
        var phase=s.entries().get("infraAnimation");long now=System.currentTimeMillis();
        running=gate.observe(scope,phase.tick(),phase.active()&&s.active("infraEffect")&&s.active("infraTimer"),now,now);
        var out=new com.google.gson.JsonObject();out.addProperty("active",running);out.addProperty("begin",gate.begin());out.addProperty("world",scope.world());out.addProperty("model",scope.model());out.addProperty("nativeAnimationActive",phase.active());out.addProperty("nativeEffectActive",s.active("infraEffect"));out.addProperty("nativeTimerActive",s.active("infraTimer"));out.addProperty("duration",15);
        var rows=new com.google.gson.JsonArray();if(running)for(var e:c.world.getEntities())if(reveals(e)){
            var row=new com.google.gson.JsonObject();row.addProperty("id",e.getId());row.addProperty("outline",c.hasOutline(e));row.addProperty("color",e.getTeamColorValue());rows.add(row);
        }
        out.add("entities",rows);out.addProperty("policy","native-15s-phase-local-loaded-living-nonplayer");status=out.toString();
    }
    public static boolean reveals(Entity entity){
        var self=INSTANCE;var c=MinecraftClient.getInstance();var h=HostPoseReader.INSTANCE.latest();
        if(!self.running||c.player==null||!c.player.isAlive()||c.world==null||c.getServer()==null||c.currentScreen!=null||h==null||!h.inputActive()
            ||!(entity instanceof LivingEntity)||entity instanceof net.minecraft.entity.player.PlayerEntity||entity.getWorld()!=c.world||!entity.isAlive()||entity.isSpectator())return false;
        var loc=NativeLocomotionController.INSTANCE;
        var current=new NativeInfraSightState.Scope(c.player.getUuid(),NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey()),h.generation(),loc.modelId());
        return loc.hero()==NativeInfraSightState.HERO&&self.gate.active(current,System.currentTimeMillis());
    }
    public void reset(){reader.close();gate.reset();scope=null;running=false;status="{\"active\":false}";}
}
