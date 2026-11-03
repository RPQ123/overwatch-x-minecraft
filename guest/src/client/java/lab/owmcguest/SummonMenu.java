package lab.owmcguest;

import com.google.gson.*;
import java.util.*;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.text.Text;

/** F9 uses the existing native HUD plane through PortalMenu; no extra render hook. */
final class SummonMenu {
    private static final TwilightBossMenu.User32 user=com.sun.jna.Native.load("user32",TwilightBossMenu.User32.class);
    private static final PortalMenuKeys keys=new PortalMenuKeys();
    private record Identity(UUID owner,Object world,long source,long model){}
    private static Identity identity;
    private static List<SummonMenuRuntime.Entry> catalog=List.of();
    private static boolean singles,pending,loading;
    private static long epoch;
    private static volatile long token,wall;
    private static volatile boolean eligible;
    private static String message="";
    static volatile String status="{}";
    static boolean visible(){return keys.open();}
    static long epoch(){return epoch;}
    static void closeMenu(){if(keys.open()){keys.close();epoch++;}token++;eligible=false;}
    static void reset(){closeMenu();keys.reset();identity=null;catalog=List.of();singles=pending=loading=false;message="";}
    static void tick(MinecraftClient c){
        var host=HostPoseReader.INSTANCE.latest();var pid=new com.sun.jna.ptr.IntByReference();user.GetWindowThreadProcessId(user.GetForegroundWindow(),pid);
        int down=(user.GetAsyncKeyState(0x78)&0x8000)!=0?1:0;
        for(int i=0;i<10;i++){int digit=i==9?0:i+1;if((user.GetAsyncKeyState(0x30+digit)&0x8000)!=0||(user.GetAsyncKeyState(0x60+digit)&0x8000)!=0)down|=2<<i;}
        boolean valid=host!=null&&host.flags()==1&&host.inputActive()&&pid.getValue()==host.pid()&&NativeLocomotionController.INSTANCE.modelId()!=0&&c.player!=null&&c.player.isAlive()&&SurvivalRuntime.permitted(c.player)&&c.getServer()!=null&&c.currentScreen==null;
        var next=host==null||c.player==null?null:new Identity(c.player.getUuid(),c.world,host.generation(),NativeLocomotionController.INSTANCE.modelId());
        if(!Objects.equals(identity,next)){reset();identity=next;}
        boolean action=false;for(int key:new int[]{0x51,0x45,0x10,0x56,0x01,0x02,0x52,0x48})if((user.GetAsyncKeyState(key)&0x8000)!=0)action=true;
        boolean casting=NativeUltimateController.active||NativeDeadeyeController.active||NativeRecallController.rewinding()||NativeWraithController.active()||NativeShadowController.casting()||NativeReaperController.active();
        try{var meter=JsonParser.parseString(NativeChargeController.status).getAsJsonObject();if(meter.has("modelId")&&meter.get("modelId").getAsLong()==NativeLocomotionController.INSTANCE.modelId()&&meter.has("active")&&meter.get("active").getAsBoolean())casting=true;}catch(RuntimeException ignored){}
        if(!valid||action||casting){token++;if(pending||loading){pending=loading=false;message=MenuText.get("summon.cancelled");epoch++;}}
        eligible=valid&&!action&&!casting;wall=System.currentTimeMillis();
        boolean was=keys.open();int beforePage=keys.page();int selected=keys.poll(valid,down,pending||loading,singles?catalog.size():SummonMenuOptions.ROOT.size());
        if(was!=keys.open()){
            epoch++;
            if(keys.open()){PortalMenu.closePortal();TwilightBossMenu.closeMenu();WorldSettingsMenu.closeMenu();SurvivalMenu.closeMenu();singles=false;keys.firstPage();message="";load(c);}
            else{token++;pending=loading=false;}
        }
        if(beforePage!=keys.page())epoch++;
        if(selected>0&&!singles&&SummonMenuOptions.ROOT.get(selected-1).selection().equals(SummonMenuOptions.ALL)){singles=true;keys.firstPage();message="";epoch++;}
        else if(selected>0){
            if(!eligible){message=MenuText.get("summon.wait");epoch++;}
            else{
                String selection=singles?catalog.get(selected-1).id():SummonMenuOptions.ROOT.get(selected-1).selection();
                var server=c.getServer();var owner=c.player.getUuid();long world=NativeWorldIdentity.of(server,c.world.getRegistryKey()),accepted=token;
                pending=true;message="";epoch++;
                server.execute(()->{
                    var result=SummonMenuRuntime.summon(server,owner,world,selection,()->eligible&&token==accepted&&System.currentTimeMillis()-wall<=250);
                    c.execute(()->{if(token!=accepted)return;pending=false;message=result.success()?MenuText.get("summon.success"):Text.translatableWithFallback(result.error(),result.error()).getString();epoch++;});
                });
            }
        }
        var out=new JsonObject();out.addProperty("open",keys.open());out.addProperty("ready",valid);out.addProperty("pending",pending);out.addProperty("loading",loading);
        out.addProperty("singles",singles);out.addProperty("page",keys.page());out.addProperty("entities",catalog.size());out.addProperty("message",message);var runtime=JsonParser.parseString(SummonMenuRuntime.status).getAsJsonObject();runtime.add("lifecycle",JsonParser.parseString(SummonedMobLifecycle.status));out.add("runtime",runtime);status=out.toString();
    }
    private static void load(MinecraftClient c){
        var server=c.getServer();var owner=c.player.getUuid();long world=NativeWorldIdentity.of(server,c.world.getRegistryKey()),accepted=token;loading=true;
        server.execute(()->{
            try{
                var rows=SummonMenuRuntime.catalog(server,owner,world,()->token==accepted);
                c.execute(()->{if(token!=accepted)return;catalog=rows;loading=false;epoch++;});
            }catch(RuntimeException failure){c.execute(()->{if(token!=accepted)return;loading=false;message=MenuText.get("summon.catalog_failed");epoch++;});}
        });
    }
    static void draw(DrawContext context){
        var c=MinecraftClient.getInstance();double scale=c.getWindow().getScaleFactor();int center=c.getWindow().getScaledWidth()/2;
        int half=(int)(Math.min(1024,c.getWindow().getFramebufferWidth())/scale/2),available=(int)(Math.min(192,c.getWindow().getFramebufferHeight())/scale);float fit=Math.min(1f,available/73f);
        context.getMatrices().push();context.getMatrices().translate(center,0,0);context.getMatrices().scale(fit,fit,1);int hw=(int)(half/fit);context.fill(-hw,0,hw,73,0xee111827);
        int pages=Math.max(1,((singles?catalog.size():SummonMenuOptions.ROOT.size())+7)/8);context.drawCenteredTextWithShadow(c.textRenderer,MenuText.get(singles?"summon.single_title":"summon.title",keys.page()+1,pages,catalog.size()),0,6,0xff7ce7ff);
        for(int i=0;i<8;i++){
            int index=keys.page()*8+i;if(index>=(singles?catalog.size():SummonMenuOptions.ROOT.size()))break;
            String name=singles?Text.translatableWithFallback(catalog.get(index).translationKey(),catalog.get(index).id()).getString():MenuText.get("summon."+SummonMenuOptions.ROOT.get(index).label());
            context.drawTextWithShadow(c.textRenderer,c.textRenderer.trimToWidth((i+1)+"  "+name,hw-14),i%2==0?-hw+8:6,16+i/2*11,pending||loading?0xff8b95a6:0xfff3f4f6);
        }
        String footer=message.isEmpty()?MenuText.get(loading?"summon.loading":pending?"summon.pending":singles?"summon.single_footer":"summon.footer"):message;
        context.drawCenteredTextWithShadow(c.textRenderer,c.textRenderer.trimToWidth(footer,hw*2-12),0,64,0xffffd479);context.getMatrices().pop();
    }
}
