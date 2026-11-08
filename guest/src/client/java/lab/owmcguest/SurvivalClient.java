package lab.owmcguest;

import com.google.gson.*;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.*;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.option.Perspective;
import net.minecraft.client.util.InputUtil;

/** The only continuous native HP writer. It never calls native death/ability code. */
public final class SurvivalClient implements ClientModInitializer {
    private final NativeHealthMirror mirror=new NativeHealthMirror();
    private long hostFrame,hostProgress,exchangeMaxNanos;
    private long writes,deathAt,respawnAt;private String error="";private boolean unbound;
    public static volatile String status="{}";
    @Override public void onInitializeClient(){
        HeroNpcRenderer.register();
        ClientTickEvents.END_CLIENT_TICK.register(this::tick);
        ClientLifecycleEvents.CLIENT_STOPPING.register(c->mirror.close());
    }
    private void tick(MinecraftClient c){
        if(!Boolean.getBoolean("owmc.frameExport"))return;
        if(!unbound){c.options.togglePerspectiveKey.setBoundKey(InputUtil.UNKNOWN_KEY);net.minecraft.client.option.KeyBinding.updateKeysByCode();unbound=true;}
        c.options.setPerspective(Perspective.FIRST_PERSON);
        while(c.options.togglePerspectiveKey.wasPressed()){} // Drain pre-start queued vanilla F5 presses.
        var host=HostPoseReader.INSTANCE.latest();var p=c.player;long now=System.currentTimeMillis();
        if(p==null||c.world==null||c.getServer()==null||host==null||host.flags()!=1){mirror.clear();return;}
        long model=NativeLocomotionController.INSTANCE.modelId(),hero=NativeLocomotionController.INSTANCE.hero();
        if(host.frame()!=hostFrame){hostFrame=host.frame();hostProgress=now;}
        if(model==0||hero==0||now-hostProgress>250||now<hostProgress){mirror.clear();return;}
        long exchangeStarted=System.nanoTime();
        var context=new NativeHealthMirror.Context(host,p.getUuid(),NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey()),model,hero,now,null);
        var result=mirror.latest(context,now);var state=result==null?null:result.state();
        NativeHealthMirror.Target target=null;
        if(state!=null){
            var server=c.getServer();double baseMaximum=hero==WinstonRules.HERO?WinstonRules.BASE_HP:state.maximum();
            var scope=new SurvivalRuntime.Scope(p.getUuid(),NativeWorldIdentity.of(server,c.world.getRegistryKey()),host.generation(),model,hero,baseMaximum);
            if(host.inputActive())server.execute(()->SurvivalRuntime.refresh(server,scope,now));
            var view=SurvivalRuntime.view;
            if(view!=null&&view.scope().equals(scope)&&now-view.wall()<=250){
                target=new NativeHealthMirror.Target(view.enabled(),view.health(),view.wall());
            }
        }
        mirror.submit(new NativeHealthMirror.Context(host,context.owner(),context.world(),model,hero,now,target));
        writes=mirror.writes;error=mirror.error;exchangeMaxNanos=Math.max(exchangeMaxNanos,System.nanoTime()-exchangeStarted);
        // Use Minecraft's real death/respawn flow. The native view remains the
        // original OW hero; its HP is zero during the visible 1.5-second delay.
        if(!p.isAlive()&&SurvivalRuntime.enabled()){
            if(deathAt==0)deathAt=now;
            if(now-deathAt>=1500&&now-respawnAt>=1000){p.requestRespawn();c.setScreen(null);respawnAt=now;}
        }else deathAt=0;
        var out=new JsonObject();out.addProperty("ready",state!=null);out.addProperty("writes",writes);out.addProperty("error",error);out.add("healthMirror",mirror.diagnostics());out.addProperty("maxMainExchangeMs",exchangeMaxNanos/1_000_000.);
        out.addProperty("perspective",c.options.getPerspective().name());out.addProperty("f5PerspectiveBound",!c.options.togglePerspectiveKey.isUnbound());
        if(state!=null){out.addProperty("nativeHealth",state.current());out.addProperty("nativeMaximum",state.maximum());out.addProperty("model",state.model());out.addProperty("source",state.source());}
        status=out.toString();
    }
}
