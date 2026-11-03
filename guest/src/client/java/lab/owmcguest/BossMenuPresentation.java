package lab.owmcguest;

import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.DrawContext;

/** Localized F10 presentation; the existing Boss travel admission/protocol remains its owner. */
final class BossMenuPresentation {
    private BossMenuPresentation(){}
    static void draw(DrawContext context,int page,boolean aoa,boolean requesting,String message){
        var c=MinecraftClient.getInstance();double scale=c.getWindow().getScaleFactor();
        int center=c.getWindow().getScaledWidth()/2,half=(int)(Math.min(1024,c.getWindow().getFramebufferWidth())/scale/2);
        int available=(int)(Math.min(192,c.getWindow().getFramebufferHeight())/scale);float fit=Math.min(1f,available/78f);
        context.getMatrices().push();context.getMatrices().translate(center,0,0);context.getMatrices().scale(fit,fit,1);
        int hw=(int)(half/fit);context.fill(-hw,0,hw,78,0xee111827);
        boolean twilight=FabricLoader.getInstance().isModLoaded("twilightforest"),aether=FabricLoader.getInstance().isModLoaded("aether");
        String group=page==1?"aether":aoa?"aoa":"twilight";
        context.drawCenteredTextWithShadow(c.textRenderer,MenuText.get("boss.title",MenuText.get("boss.group."+group)),0,6,0xff7ce7ff);
        for(int i=0;i<10;i++){
            if(page==1&&i>=3&&i<8)continue;
            boolean installed=i<8?(page==0?aoa||twilight:i<3&&aether):true;
            String label=MenuText.get(i==9?(page==0?"boss.next":"boss.previous"):i==8?"boss.random":"boss."+group+"."+i);
            if(!installed)label+=MenuText.get("boss.missing");
            context.drawTextWithShadow(c.textRenderer,c.textRenderer.trimToWidth((i==9?0:i+1)+"  "+label,hw-14),i%2==0?-hw+8:6,18+i/2*10,requesting||!installed?0xff8b95a6:0xfff3f4f6);
        }
        String footer=requesting?MenuText.get("boss.pending"):message.isEmpty()?MenuText.get("boss.footer"):message;
        context.drawCenteredTextWithShadow(c.textRenderer,c.textRenderer.trimToWidth(footer,hw*2-12),0,68,0xffffd479);context.getMatrices().pop();
    }
}
