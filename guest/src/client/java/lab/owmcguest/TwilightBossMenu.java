package lab.owmcguest;

import com.google.gson.JsonParser;
import com.sun.jna.*;
import com.sun.jna.win32.StdCallLibrary;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.DrawContext;
import net.fabricmc.loader.api.FabricLoader;

/** Native-window keys only; renders through the existing unwarped HUD pixel plane. */
final class TwilightBossMenu {
    interface User32 extends StdCallLibrary {
        Pointer GetForegroundWindow();
        int GetWindowThreadProcessId(Pointer window,com.sun.jna.ptr.IntByReference pid);
        short GetAsyncKeyState(int key);
    }
    static final String[] IDS={"naga","lich","minoshroom","hydra","knight_phantom","ur_ghast","alpha_yeti","snow_queen","random","aether"};
    private static final String[] NAMES={"娜迦 · 庭院","巫妖 · 高塔","米诺菇 · 迷宫","九头蛇 · 巢穴","幻影骑士 · 要塞","暮色恶魂 · 黑塔","雪怪首领 · 洞穴","冰雪女王 · 极光宫殿","随机Boss · 已接入维度","天堂 · 随机原生地牢"};
    private static final User32 user=Native.load("user32",User32.class);
    private static final BossTravelMenuKeys keys=new BossTravelMenuKeys();
    private static long epoch,opened,choices,requestBase,busyBase;
    private record Identity(java.util.UUID player,Object world,long source,long model){}
    private static Identity identity;
    private static volatile long admissionEpoch,admissionWall;
    private static volatile boolean eligible;
    private static long lastAction;
    private static boolean requesting,progressionDisabled;
    private static String message="",boss="";
    private static int menuPage;
    private static final String[] AETHER_IDS={"bronze_dungeon","silver_dungeon","gold_dungeon"};
    private static final String[] AETHER_NAMES={"滑行魔石 · 铜地牢","女武神女王 · 银地牢","烈阳巨灵 · 金地牢"};
    static volatile String status="{}";
    private static boolean aoa(){return net.minecraft.registry.Registries.ENTITY_TYPE.containsId(net.minecraft.util.Identifier.of("aoa3:smash"));}
    static boolean visible(){return keys.open();}
    static long epoch(){return epoch;}
    static void closeMenu(){if(keys.open()){keys.close();epoch++;}}
    static void reset(){if(keys.open())epoch++;keys.reset();identity=null;requesting=false;menuPage=0;message="";eligible=false;admissionEpoch++;}
    static void tick(MinecraftClient client){
        var host=HostPoseReader.INSTANCE.latest();var pid=new com.sun.jna.ptr.IntByReference();
        user.GetWindowThreadProcessId(user.GetForegroundWindow(),pid);
        int down=(user.GetAsyncKeyState(0x79)&0x8000)!=0?1:0; // F10
        for(int i=0;i<10;i++){int digit=i==9?0:i+1;if((user.GetAsyncKeyState(0x30+digit)&0x8000)!=0||(user.GetAsyncKeyState(0x60+digit)&0x8000)!=0)down|=2<<i;}
        boolean valid=Boolean.getBoolean("owmc.twilightTrial")&&(aoa()||FabricLoader.getInstance().isModLoaded("twilightforest")||FabricLoader.getInstance().isModLoaded("aether"))
            &&System.getProperty("owmc.worldName","").startsWith("Overwatch Twilight ")
            &&host!=null&&host.flags()==1&&host.inputActive()&&pid.getValue()==host.pid()
            &&client.player!=null&&client.player.isAlive()&&SurvivalRuntime.permitted(client.player)
            &&client.getServer()!=null&&client.currentScreen==null;
        try{var data=JsonParser.parseString(TwilightBossTravel.status).getAsJsonObject();progressionDisabled=data.has("progressionDisabled")&&data.get("progressionDisabled").getAsBoolean();}
        catch(RuntimeException ignored){progressionDisabled=false;}
        var next=host==null||client.player==null?null:new Identity(client.player.getUuid(),client.world,host.generation(),NativeLocomotionController.INSTANCE.modelId());
        if(!java.util.Objects.equals(identity,next)){
            reset();identity=next;
        }
        long now=System.currentTimeMillis();boolean action=false;
        for(int key:new int[]{0x51,0x45,0x10,0x56,0x01,0x02,0x52,0x48})if((user.GetAsyncKeyState(key)&0x8000)!=0)action=true;
        boolean casting=NativeUltimateController.active||NativeDeadeyeController.active||NativeRecallController.rewinding()
            ||NativeWraithController.active()||NativeShadowController.casting()||NativeReaperController.active();
        try{var meter=JsonParser.parseString(NativeChargeController.status).getAsJsonObject();
            if(meter.has("modelId")&&meter.get("modelId").getAsLong()==NativeLocomotionController.INSTANCE.modelId()
                &&meter.has("active")&&meter.get("active").getAsBoolean())casting=true;
        }catch(RuntimeException ignored){}
        if(action||casting){lastAction=now;admissionEpoch++;}
        // A later return to the window cannot resurrect an already cancelled request.
        if(!valid)admissionEpoch++;
        eligible=valid&&!casting&&!action&&now-lastAction>=750;admissionWall=now;
        if(requesting){
            try{
                var result=JsonParser.parseString(travelStatus()).getAsJsonObject();
                if(result.has("busyRequests")&&result.get("busyRequests").getAsLong()>busyBase
                    &&result.has("requestId")&&result.get("requestId").getAsLong()<=requestBase){
                    requesting=false;message=MenuText.get("boss.busy");epoch++;
                }else if(result.has("requestId")&&result.get("requestId").getAsLong()>requestBase){
                    boolean busy=result.has("busy")&&result.get("busy").getAsBoolean();
                    if(!busy){requesting=false;message=result.has("error")?result.get("error").getAsString():"";epoch++;
                        BossHudTravelScope.finish(message.isEmpty());if(message.isEmpty())keys.close();}
                }
            }catch(RuntimeException ignored){message=MenuText.get("boss.waiting_server");}
        }
        boolean was=keys.open();int selected=keys.poll(valid,down,requesting);
        if(was!=keys.open()){epoch++;if(keys.open()){PortalMenu.closeMenu();opened++;message="";}}
        if(selected==10){menuPage=1-menuPage;epoch++;message="";selected=0;}
        if(selected>0&&selected<=8&&(menuPage==0?!aoa()&&!FabricLoader.getInstance().isModLoaded("twilightforest"):selected>3||!FabricLoader.getInstance().isModLoaded("aether"))){
            message=MenuText.get("boss.unavailable");epoch++;selected=0;
        }
        if(selected>0&&(AoABossTravel.busy()||RandomBossTravel.busy())){message=MenuText.get("boss.locating");epoch++;selected=0;}
        if(selected!=0&&!eligible){message=MenuText.get("boss.wait");epoch++;}
        if(selected!=0&&eligible){
            var server=client.getServer();var owner=client.player.getUuid();boss=selected<=8?(menuPage==1?"aether:"+AETHER_IDS[selected-1]:aoa()?"aoa:"+AoABossTravel.IDS[selected-1]:IDS[selected-1]):"random";
            try{var result=JsonParser.parseString(travelStatus()).getAsJsonObject();requestBase=result.has("requestId")?result.get("requestId").getAsLong():0;busyBase=result.has("busyRequests")?result.get("busyRequests").getAsLong():0;}
            catch(RuntimeException ignored){requestBase=0;busyBase=0;}
            requesting=true;choices++;message=MenuText.get("boss.request");epoch++;
            String destination=boss;long token=admissionEpoch,model=NativeLocomotionController.INSTANCE.modelId(),generation=host.generation();
            BossHudTravelScope.begin(((lab.owmcguest.mixin.BossBarHudAccessor)client.inGameHud.getBossBarHud()).owmc$bars().keySet());
            server.execute(()->{java.util.function.BooleanSupplier fresh=()->eligible&&admissionEpoch==token&&System.currentTimeMillis()-admissionWall<=250;
                // Delayed author-owned summoning has separate owner checks after the
                // committed dimension transfer. This grants no native attack permission.
                java.util.function.BooleanSupplier sameNative=()->{var h=HostPoseReader.INSTANCE.latest();return h!=null&&h.flags()==1&&h.generation()==generation&&NativeLocomotionController.INSTANCE.modelId()==model&&client.currentScreen==null;};
                if(destination.startsWith("aoa:"))AoABossTravel.request(server,owner,destination.substring(4),fresh,sameNative);
                else if(destination.startsWith("aether:"))RandomBossTravel.requestAether(server,owner,java.util.Arrays.asList(AETHER_IDS).indexOf(destination.substring(7)),fresh);
                else if(destination.equals("random")||destination.equals("aether"))RandomBossTravel.request(server,owner,destination.equals("aether"),fresh,sameNative);
                else TwilightBossTravel.request(server,owner,destination,fresh);});
        }
        var out=new com.google.gson.JsonObject();out.addProperty("open",keys.open());out.addProperty("ready",valid);
        out.addProperty("requesting",requesting);out.addProperty("opens",opened);out.addProperty("choices",choices);
        out.addProperty("page",menuPage);out.addProperty("boss",boss);out.addProperty("message",message);out.addProperty("progressionDisabled",progressionDisabled);status=out.toString();
    }
    private static String travelStatus(){return boss.startsWith("aoa:")?AoABossTravel.status:boss.equals("random")||boss.startsWith("aether")?RandomBossTravel.status:TwilightBossTravel.status;}
    static void draw(DrawContext context){
        BossMenuPresentation.draw(context,menuPage,aoa(),requesting,message);
    }
}
