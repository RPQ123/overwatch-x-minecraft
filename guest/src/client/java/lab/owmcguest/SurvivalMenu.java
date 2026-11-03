package lab.owmcguest;

import com.google.gson.*;
import java.util.*;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.DrawContext;

/** F5 shares the existing native HUD plane and held/focus-safe digit state machine. */
final class SurvivalMenu {
    private static final TwilightBossMenu.User32 user=com.sun.jna.Native.load("user32",TwilightBossMenu.User32.class);
    private static final PortalMenuKeys keys=new PortalMenuKeys();
    private record Identity(UUID player,Object world,long source,long model){}
    private static Identity identity;private static long epoch;
    private static volatile long token,wall;private static volatile boolean eligible;
    private static boolean singles,pending;private static String message="";
    static volatile String status="{}";
    static boolean visible(){return keys.open();}
    static long epoch(){return epoch;}
    static void closeMenu(){if(keys.open()){keys.close();epoch++;}pending=false;token++;eligible=false;}
    static void reset(){closeMenu();keys.reset();identity=null;singles=false;message="";}
    static void tick(MinecraftClient c){
        var host=HostPoseReader.INSTANCE.latest();var pid=new com.sun.jna.ptr.IntByReference();user.GetWindowThreadProcessId(user.GetForegroundWindow(),pid);
        int down=(user.GetAsyncKeyState(0x74)&0x8000)!=0?1:0;
        for(int i=0;i<10;i++){int digit=i==9?0:i+1;if((user.GetAsyncKeyState(0x30+digit)&0x8000)!=0||(user.GetAsyncKeyState(0x60+digit)&0x8000)!=0)down|=2<<i;}
        boolean valid=host!=null&&host.flags()==1&&host.inputActive()&&pid.getValue()==host.pid()&&NativeLocomotionController.INSTANCE.modelId()!=0
            &&c.player!=null&&c.player.isAlive()&&c.getServer()!=null&&c.currentScreen==null;
        var next=host==null||c.player==null?null:new Identity(c.player.getUuid(),c.world,host.generation(),NativeLocomotionController.INSTANCE.modelId());
        if(!Objects.equals(identity,next)){reset();identity=next;}
        boolean action=false;for(int key:new int[]{0x51,0x45,0x10,0x56,0x01,0x02,0x52,0x48})if((user.GetAsyncKeyState(key)&0x8000)!=0)action=true;
        boolean casting=NativeUltimateController.active||NativeDeadeyeController.active||NativeRecallController.rewinding()||NativeWraithController.active()||NativeShadowController.casting()||NativeReaperController.active();
        if(!valid||action||casting){token++;if(pending){pending=false;epoch++;}}
        eligible=valid&&!action&&!casting;wall=System.currentTimeMillis();
        boolean was=keys.open();int page=keys.page();int choice=keys.poll(valid,down,pending,singles?12:4);
        if(was!=keys.open()){
            epoch++;if(keys.open()){PortalMenu.closePortal();SummonMenu.closeMenu();WorldSettingsMenu.closeMenu();TwilightBossMenu.closeMenu();singles=false;keys.firstPage();message="";}
            else{token++;pending=false;}
        }
        if(page!=keys.page())epoch++;
        if(choice>0&&eligible){
            if(!singles&&choice==1){singles=true;keys.firstPage();epoch++;}
            else{
                var server=c.getServer();var owner=c.player.getUuid();long world=NativeWorldIdentity.of(server,c.world.getRegistryKey()),accepted=token;
                int selection=singles?choice-1:choice==2?-1:-2;boolean toggle=!singles&&choice==4;boolean nextMode=!SurvivalRuntime.enabled();pending=true;
                server.execute(()->{
                    String result="召唤已取消";
                    if(eligible&&token==accepted&&System.currentTimeMillis()-wall<=250){
                        result=toggle?SurvivalRuntime.setEnabled(server,owner,nextMode):HeroSummonRuntime.summon(server,owner,world,selection,()->eligible&&token==accepted&&System.currentTimeMillis()-wall<=250);
                    }
                    String reply=result;c.execute(()->{if(token!=accepted)return;pending=false;message=reply.isEmpty()?"操作成功":reply;epoch++;});
                });
            }
        }else if(choice>0){message="请先松开攻击和技能键";epoch++;}
        var out=new JsonObject();out.addProperty("open",keys.open());out.addProperty("ready",valid);out.addProperty("singles",singles);out.addProperty("page",keys.page());out.addProperty("pending",pending);out.addProperty("message",message);status=out.toString();
    }
    static void draw(DrawContext context){
        var c=MinecraftClient.getInstance();double scale=c.getWindow().getScaleFactor();int center=c.getWindow().getScaledWidth()/2;
        int half=(int)(Math.min(1024,c.getWindow().getFramebufferWidth())/scale/2),available=(int)(Math.min(192,c.getWindow().getFramebufferHeight())/scale);float fit=Math.min(1f,available/73f);
        context.getMatrices().push();context.getMatrices().translate(center,0,0);context.getMatrices().scale(fit,fit,1);int hw=(int)(half/fit);context.fill(-hw,0,hw,73,0xee111827);
        context.drawCenteredTextWithShadow(c.textRenderer,singles?"F5 召唤英雄  "+(keys.page()+1)+" / 2":"F5 英雄召唤 / 生存模式",0,6,0xff7ce7ff);
        var root=List.of("选择一位英雄（共 12 位）","召唤全部英雄","清除我的英雄召唤","生存模式："+(SurvivalRuntime.enabled()?"开（会受伤）":"关（无敌）"));
        for(int i=0;i<8;i++){int index=keys.page()*8+i;if(index>=(singles?12:4))break;String name=singles?HeroNpcCatalog.entry(index).name():root.get(index);
            context.drawTextWithShadow(c.textRenderer,c.textRenderer.trimToWidth((i+1)+"  "+name,hw-14),i%2==0?-hw+8:6,16+i/2*11,pending?0xff8b95a6:0xfff3f4f6);}
        String footer=message.isEmpty()?(pending?"正在处理…":singles?"1–8 / 小键盘选择   9 下一页   0 上一页   F5 关闭":"数字键 / 小键盘选择   F5 关闭（设置自动保存）"):message;
        context.drawCenteredTextWithShadow(c.textRenderer,c.textRenderer.trimToWidth(footer,hw*2-12),0,64,0xffffd479);context.getMatrices().pop();
    }
}
