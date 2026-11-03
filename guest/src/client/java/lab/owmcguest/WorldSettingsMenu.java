package lab.owmcguest;

import com.google.gson.JsonObject;
import java.util.Objects;
import java.util.UUID;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.text.Text;

/** F7 世界设置菜单：1 白天 2 黑夜 3 黄昏 4 永远白天 5 取消永远白天 6 永久夜视 7 取消永久夜视。
 * 与 F8/F9 共用原版窗口内的 HUD 平面与数字键选择。 */
final class WorldSettingsMenu {
    private static final TwilightBossMenu.User32 user=com.sun.jna.Native.load("user32",TwilightBossMenu.User32.class);
    private static final PortalMenuKeys keys=new PortalMenuKeys();
    private record Identity(UUID owner,Object world,long source,long model){}
    private static Identity identity;
    private static long epoch;
    private static boolean pending;
    private static String message="";
    static volatile String status="{}";
    static boolean visible(){return keys.open();}
    static long epoch(){return epoch;}
    static void closeMenu(){if(keys.open()){keys.close();epoch++;}pending=false;}
    static void reset(){closeMenu();keys.reset();identity=null;message="";}
    static void tick(MinecraftClient c){
        var host=HostPoseReader.INSTANCE.latest();var pid=new com.sun.jna.ptr.IntByReference();user.GetWindowThreadProcessId(user.GetForegroundWindow(),pid);
        int down=(user.GetAsyncKeyState(0x76)&0x8000)!=0?1:0; // F7
        for(int i=0;i<10;i++){int digit=i==9?0:i+1;if((user.GetAsyncKeyState(0x30+digit)&0x8000)!=0||(user.GetAsyncKeyState(0x60+digit)&0x8000)!=0)down|=2<<i;}
        boolean valid=host!=null&&host.flags()==1&&host.inputActive()&&pid.getValue()==host.pid()&&NativeLocomotionController.INSTANCE.modelId()!=0
            &&c.player!=null&&c.player.isAlive()&&c.getServer()!=null&&c.currentScreen==null;
        var next=host==null||c.player==null?null:new Identity(c.player.getUuid(),c.world,host.generation(),NativeLocomotionController.INSTANCE.modelId());
        if(!Objects.equals(identity,next)){reset();identity=next;}
        boolean was=keys.open();int choice=keys.poll(valid,down,pending,WorldSettingsRuntime.OPTIONS.size());
        if(was!=keys.open()){
            epoch++;
            if(keys.open()){PortalMenu.closePortal();SummonMenu.closeMenu();TwilightBossMenu.closeMenu();SurvivalMenu.closeMenu();keys.firstPage();message="";}
        }
        if(choice>0&&valid){
            String option=WorldSettingsRuntime.OPTIONS.get(choice-1);var server=c.getServer();var owner=c.player.getUuid();pending=true;epoch++;
            server.execute(()->{
                String error=WorldSettingsRuntime.apply(server,owner,option);
                c.execute(()->{pending=false;message=error.isEmpty()?MenuText.get("world.done",MenuText.get("world."+option)):Text.translatableWithFallback(error,error).getString();epoch++;});
            });
        }
        var out=new JsonObject();out.addProperty("open",keys.open());out.addProperty("ready",valid);out.addProperty("pending",pending);out.addProperty("message",message);
        out.add("runtime",com.google.gson.JsonParser.parseString(WorldSettingsRuntime.status));status=out.toString();
    }
    static void draw(DrawContext context){
        var c=MinecraftClient.getInstance();double scale=c.getWindow().getScaleFactor();int center=c.getWindow().getScaledWidth()/2;
        int half=(int)(Math.min(1024,c.getWindow().getFramebufferWidth())/scale/2),available=(int)(Math.min(192,c.getWindow().getFramebufferHeight())/scale);float fit=Math.min(1f,available/73f);
        context.getMatrices().push();context.getMatrices().translate(center,0,0);context.getMatrices().scale(fit,fit,1);int hw=(int)(half/fit);context.fill(-hw,0,hw,73,0xee111827);
        context.drawCenteredTextWithShadow(c.textRenderer,MenuText.get("world.title"),0,6,0xff7ce7ff);
        var options=WorldSettingsRuntime.OPTIONS;
        for(int i=0;i<options.size()&&i<8;i++){
            String name=MenuText.get("world."+options.get(i));
            context.drawTextWithShadow(c.textRenderer,c.textRenderer.trimToWidth((i+1)+"  "+name,hw-14),i%2==0?-hw+8:6,16+i/2*11,pending?0xff8b95a6:0xfff3f4f6);
        }
        String footer=message.isEmpty()?MenuText.get(pending?"world.pending":"world.footer"):message;
        context.drawCenteredTextWithShadow(c.textRenderer,c.textRenderer.trimToWidth(footer,hw*2-12),0,64,0xffffd479);context.getMatrices().pop();
    }
}
