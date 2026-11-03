package lab.owmcguest;

import com.sun.jna.*;
import com.sun.jna.win32.StdCallLibrary;
import net.minecraft.client.MinecraftClient;

/** F9 is owned by SummonMenu, F10 by the Boss menu; F11 refills native resources. */
final class NativeUtilityController implements AutoCloseable {
    interface User32 extends StdCallLibrary {
        Pointer GetForegroundWindow();int GetWindowThreadProcessId(Pointer window,com.sun.jna.ptr.IntByReference pid);short GetAsyncKeyState(int key);
    }
    static final NativeUtilityController INSTANCE=new NativeUtilityController();
    private final User32 user=Native.load("user32",User32.class);
    private final NativeUtilityKeys keys=new NativeUtilityKeys();
    private final NativeMeterReader meter=new NativeMeterReader();
    private long refills,cooldownRefills;private String error="";
    static volatile String status="{}";
    void tick(MinecraftClient client){
        var host=HostPoseReader.INSTANCE.latest();var pid=new com.sun.jna.ptr.IntByReference();user.GetWindowThreadProcessId(user.GetForegroundWindow(),pid);
        int down=(user.GetAsyncKeyState(0x7a)&0x8000)!=0?4:0;
        boolean valid=host!=null&&host.flags()==1&&host.inputActive()&&pid.getValue()==host.pid()&&client.player!=null&&client.player.isAlive()&&SurvivalRuntime.permitted(client.player)&&client.getServer()!=null&&client.currentScreen==null&&!PortalMenu.visible()&&!TwilightBossMenu.visible();
        int edge=keys.poll(valid,down);
        if(valid&&edge!=0){
            if((edge&4)!=0)refill(client);
        }
        var out=new com.google.gson.JsonObject();out.addProperty("ready",valid);out.addProperty("refills",refills);out.addProperty("cooldownRefills",cooldownRefills);out.addProperty("error",error);out.add("cooldowns",com.google.gson.JsonParser.parseString(cooldownStatus));status=out.toString();
    }
    private String cooldownStatus="{}";
    void refill(MinecraftClient client){
        var host=HostPoseReader.INSTANCE.latest();long model=NativeLocomotionController.INSTANCE.modelId(),hero=NativeLocomotionController.INSTANCE.hero();
        if(host==null||host.flags()!=1||client.player==null||!client.player.isAlive()||!SurvivalRuntime.permitted(client.player)||model==0)return;
        if(client.getServer()==null||!client.getServer().isSingleplayer()||client.currentScreen!=null||PortalMenu.visible()||TwilightBossMenu.visible())return;
        if(NativeUltimateController.active||NativeDeadeyeController.active||NativeRecallController.rewinding()||NativeWraithController.active()||NativeShadowController.casting()||NativeReaperController.active()){error=MenuText.get("utility.wait");return;}
        try{var active=com.google.gson.JsonParser.parseString(NativeChargeController.status).getAsJsonObject();if(active.has("modelId")&&active.get("modelId").getAsLong()==model&&active.has("active")&&active.get("active").getAsBoolean()){error=MenuText.get("utility.wait");return;}}catch(RuntimeException ignored){}
        var pid=new com.sun.jna.ptr.IntByReference();user.GetWindowThreadProcessId(user.GetForegroundWindow(),pid);if(pid.getValue()!=host.pid()||!host.inputActive())return;
        for(int key:new int[]{0x51,0x45,0x10,0x56,0x01,0x02,0x52,0x48})if((user.GetAsyncKeyState(key)&0x8000)!=0){error=MenuText.get("utility.wait");return;}
        try{synchronized(NativeMeterWrites.LOCK){
            if(hero==0x02e0000000000029L){try(var reader=new NativeAbilityReader(true)){var value=reader.ultimate(host);if(value==null||value.model()!=model)throw new IllegalStateException(reader.error);reader.charge(value,value.cost());}}
            else {var value=meter.poll(host,model,hero);if(value==null||!meter.credit(value,value.cost()))throw new IllegalStateException(meter.error);}
            refills++;error="";
            var world=client.world;var owner=client.player.getUuid();
            int restored=new NativeCooldownRefill().restore(host,model,hero,()->{var now=HostPoseReader.INSTANCE.latest();var foreground=new com.sun.jna.ptr.IntByReference();user.GetWindowThreadProcessId(user.GetForegroundWindow(),foreground);return now!=null&&now.flags()==1&&now.inputActive()&&now.pid()==host.pid()&&now.generation()==host.generation()&&foreground.getValue()==host.pid()&&client.world==world&&client.player!=null&&client.player.getUuid().equals(owner)&&client.player.isAlive()&&SurvivalRuntime.permitted(client.player)&&NativeLocomotionController.INSTANCE.modelId()==model&&NativeLocomotionController.INSTANCE.hero()==hero;});
            cooldownRefills++;cooldownStatus="{\"restored\":"+restored+",\"modelId\":"+model+",\"hero\":"+hero+"}";
        }}catch(Exception e){error=e.toString();}
    }
    void resetSession(){keys.reset();meter.close();error="";cooldownStatus="{}";}
    @Override public void close(){resetSession();}
}
