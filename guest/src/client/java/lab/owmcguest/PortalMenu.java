package lab.owmcguest;

import com.google.gson.*;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.DrawContext;

/** F8 plus top-row/numpad digits, only in the exact native offline first-person window. */
final class PortalMenu {
    private static final TwilightBossMenu.User32 user=com.sun.jna.Native.load("user32",TwilightBossMenu.User32.class);
    private static final PortalMenuKeys keys=new PortalMenuKeys();
    private static long epoch,base;
    private static volatile long token,wall;
    private static volatile boolean eligible;
    private static boolean pending;
    private static String message="";
    private record Identity(java.util.UUID player,Object world,long source,long model){}
    private static Identity identity;
    static volatile String status="{}";
    // Keep the existing HUD exporter/session hooks for both local menus.
    static boolean visible(){return keys.open()||SummonMenu.visible()||WorldSettingsMenu.visible()||SurvivalMenu.visible();}
    static long epoch(){return epoch+SummonMenu.epoch()+WorldSettingsMenu.epoch()+SurvivalMenu.epoch();}
    static void closePortal(){if(keys.open()){keys.close();epoch++;}}
    static void closeMenu(){closePortal();SummonMenu.closeMenu();WorldSettingsMenu.closeMenu();SurvivalMenu.closeMenu();}
    static void reset(){closeMenu();keys.reset();SummonMenu.reset();WorldSettingsMenu.reset();SurvivalMenu.reset();identity=null;eligible=false;pending=false;token++;message="";}
    static void tick(MinecraftClient c){
        SurvivalMenu.tick(c);
        SummonMenu.tick(c);
        WorldSettingsMenu.tick(c);
        var host=HostPoseReader.INSTANCE.latest();var pid=new com.sun.jna.ptr.IntByReference();user.GetWindowThreadProcessId(user.GetForegroundWindow(),pid);
        int down=(user.GetAsyncKeyState(0x77)&0x8000)!=0?1:0;
        for(int i=0;i<10;i++){int digit=i==9?0:i+1;if((user.GetAsyncKeyState(0x30+digit)&0x8000)!=0||(user.GetAsyncKeyState(0x60+digit)&0x8000)!=0)down|=2<<i;}
        boolean valid=host!=null&&host.flags()==1&&host.inputActive()&&pid.getValue()==host.pid()&&NativeLocomotionController.INSTANCE.modelId()!=0&&c.player!=null&&c.player.isAlive()&&SurvivalRuntime.permitted(c.player)&&c.getServer()!=null&&c.currentScreen==null;
        var next=host==null||c.player==null?null:new Identity(c.player.getUuid(),c.world,host.generation(),NativeLocomotionController.INSTANCE.modelId());
        if(!java.util.Objects.equals(identity,next)){reset();identity=next;}
        boolean action=false;for(int key:new int[]{0x51,0x45,0x10,0x56,0x01,0x02,0x52,0x48})if((user.GetAsyncKeyState(key)&0x8000)!=0)action=true;
        boolean casting=NativeUltimateController.active||NativeDeadeyeController.active||NativeRecallController.rewinding()||NativeWraithController.active()||NativeShadowController.casting()||NativeReaperController.active();
        try{var meter=JsonParser.parseString(NativeChargeController.status).getAsJsonObject();if(meter.has("modelId")&&meter.get("modelId").getAsLong()==NativeLocomotionController.INSTANCE.modelId()&&meter.has("active")&&meter.get("active").getAsBoolean())casting=true;}catch(RuntimeException ignored){}
        if(!valid||action||casting)token++;eligible=valid&&!action&&!casting;wall=System.currentTimeMillis();
        if(pending){var result=JsonParser.parseString(PortalBuildRuntime.status).getAsJsonObject();if(result.has("requests")&&result.get("requests").getAsLong()>base){pending=false;message=result.get("error").getAsString();epoch++;if(message.isEmpty())keys.close();}}
        boolean was=keys.open();int page=keys.page();int choice=keys.poll(valid,down,pending,PortalCatalog.entries.size());
        if(was!=keys.open()){epoch++;if(keys.open()){TwilightBossMenu.closeMenu();SummonMenu.closeMenu();WorldSettingsMenu.closeMenu();SurvivalMenu.closeMenu();message="";}}
        if(page!=keys.page())epoch++;
        if(choice>0&&eligible){
            var entry=PortalCatalog.entries.get(choice-1);var old=JsonParser.parseString(PortalBuildRuntime.status).getAsJsonObject();base=old.has("requests")?old.get("requests").getAsLong():0;
            var server=c.getServer();var owner=c.player.getUuid();var direction=c.player.getRotationVec(1f);long accepted=token;pending=true;epoch++;
            server.execute(()->PortalBuildRuntime.build(server,owner,entry.id(),direction,()->eligible&&token==accepted&&System.currentTimeMillis()-wall<=250));
        }else if(choice>0){message=MenuText.get("portal.wait");epoch++;}
        var out=new JsonObject();out.addProperty("open",keys.open());out.addProperty("ready",valid);out.addProperty("pending",pending);out.addProperty("page",keys.page());out.addProperty("message",message);out.add("entries",new Gson().toJsonTree(PortalCatalog.entries));out.add("summonMenu",JsonParser.parseString(SummonMenu.status));status=out.toString();
    }
    static void draw(DrawContext context){
        if(SurvivalMenu.visible()){SurvivalMenu.draw(context);return;}
        if(SummonMenu.visible()){SummonMenu.draw(context);return;}
        if(WorldSettingsMenu.visible()){WorldSettingsMenu.draw(context);return;}
        var c=MinecraftClient.getInstance();double scale=c.getWindow().getScaleFactor();int center=c.getWindow().getScaledWidth()/2,half=(int)(Math.min(1024,c.getWindow().getFramebufferWidth())/scale/2),available=(int)(Math.min(192,c.getWindow().getFramebufferHeight())/scale);float fit=Math.min(1f,available/73f);
        context.getMatrices().push();context.getMatrices().translate(center,0,0);context.getMatrices().scale(fit,fit,1);int hw=(int)(half/fit);context.fill(-hw,0,hw,73,0xee111827);
        int pages=Math.max(1,(PortalCatalog.entries.size()+7)/8);context.drawCenteredTextWithShadow(c.textRenderer,MenuText.get("portal.title",keys.page()+1,pages),0,6,0xff7ce7ff);
        for(int i=0;i<8;i++){int index=keys.page()*8+i;if(index>=PortalCatalog.entries.size())break;var entry=PortalCatalog.entries.get(index);String name=net.minecraft.text.Text.translatableWithFallback("menu.owmcguest.portal."+entry.id().replace(':','.'),entry.name()).getString();context.drawTextWithShadow(c.textRenderer,c.textRenderer.trimToWidth((i+1)+"  "+name,hw-14),i%2==0?-hw+8:6,16+i/2*11,pending?0xff8b95a6:0xfff3f4f6);}
        String footer=message.isEmpty()?MenuText.get(pending?"portal.pending":"portal.footer"):c.textRenderer.trimToWidth(message,hw*2-12);context.drawCenteredTextWithShadow(c.textRenderer,footer,0,64,0xffffd479);context.getMatrices().pop();
    }
}
