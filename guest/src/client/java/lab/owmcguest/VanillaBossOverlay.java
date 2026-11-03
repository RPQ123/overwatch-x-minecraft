package lab.owmcguest;

import net.fabricmc.fabric.api.client.rendering.v1.HudRenderCallback;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gl.SimpleFramebuffer;
import org.lwjgl.opengl.*;

/** Export pixels drawn by the real BossBarHud, independently of world reprojection.
 * HUD callback already has vanilla's GUI projection. Never synthesize a boss bar. */
final class VanillaBossOverlay {
    record Image(int width,int height,byte[] rgba) {}
    static volatile Image latest;
    static volatile String status="{\"bars\":[],\"pixelsReady\":false}";
    private static SimpleFramebuffer target;
    private static Object world;
    private static int pbo,capacity,pendingW,pendingH;
    private static long fence,lastCapture;
    private static long pendingMenuEpoch;
    private static long observedMenuEpoch=Long.MIN_VALUE;
    private static long pendingTravelEpoch,observedTravelEpoch=Long.MIN_VALUE;
    private static Object pendingWorld;
    static void register() {
        HudRenderCallback.EVENT.register((context,tick)->{
            var client=MinecraftClient.getInstance();
            if(client.world!=world){world=client.world;latest=null;}
            long menuEpoch=(TwilightBossMenu.epoch()<<32)^PortalMenu.epoch();
            long travelEpoch=BossHudTravelScope.epoch();
            if(travelEpoch!=observedTravelEpoch){observedTravelEpoch=travelEpoch;latest=null;}
            // Drop an already published menu before throttle/fence-timeout paths.
            if(menuEpoch!=observedMenuEpoch){observedMenuEpoch=menuEpoch;latest=null;}
            if(client.world==null){latest=null;status="{\"bars\":[],\"pixelsReady\":false}";return;}
            var bars=((lab.owmcguest.mixin.BossBarHudAccessor)client.inGameHud.getBossBarHud()).owmc$bars();
            boolean menu=TwilightBossMenu.visible()||PortalMenu.visible();
            if(bars.keySet().stream().noneMatch(BossHudTravelScope::visible)&&!menu){latest=null;status="{\"bars\":[],\"pixelsReady\":false,\"retired\":"+BossHudTravelScope.retired()+",\"trackedCount\":"+bars.size()+"}";return;}
            long now=System.nanoTime();
            if(now-lastCapture<33_333_333L)return;
            lastCapture=now;
            var info=new com.google.gson.JsonObject();var rows=new com.google.gson.JsonArray();
            for(var entry:bars.entrySet()){
                if(!BossHudTravelScope.visible(entry.getKey()))continue;
                var row=new com.google.gson.JsonObject();row.addProperty("id",entry.getKey().toString());row.addProperty("name",entry.getValue().getName().getString());row.addProperty("percent",entry.getValue().getPercent());rows.add(row);
            }
            info.add("bars",rows);info.addProperty("trackedCount",bars.size());info.addProperty("retired",BossHudTravelScope.retired());info.addProperty("menu",menu);info.addProperty("pixelsReady",latest!=null);status=info.toString();
            int oldDraw=GL11.glGetInteger(GL30.GL_DRAW_FRAMEBUFFER_BINDING),oldRead=GL11.glGetInteger(GL30.GL_READ_FRAMEBUFFER_BINDING);
            int oldBuffer=GL11.glGetInteger(GL11.GL_READ_BUFFER),oldPack=GL11.glGetInteger(GL21.GL_PIXEL_PACK_BUFFER_BINDING);
            int[] names={GL11.GL_PACK_ALIGNMENT,GL11.GL_PACK_ROW_LENGTH,GL11.GL_PACK_SKIP_ROWS,GL11.GL_PACK_SKIP_PIXELS,GL11.GL_PACK_SWAP_BYTES};
            int[] values=new int[names.length];for(int i=0;i<names.length;i++)values[i]=GL11.glGetInteger(names[i]);
            try {
                if(fence!=0){
                    int ready=GL32.glClientWaitSync(fence,0,0);
                    if(ready==GL32.GL_TIMEOUT_EXPIRED)return;
                    if(ready==GL32.GL_WAIT_FAILED)throw new IllegalStateException("Boss HUD fence");
                    GL15.glBindBuffer(GL21.GL_PIXEL_PACK_BUFFER,pbo);
                    var bytes=GL30.glMapBufferRange(GL21.GL_PIXEL_PACK_BUFFER,0,pendingW*pendingH*4,GL30.GL_MAP_READ_BIT);
                    if(bytes!=null){byte[] data=new byte[pendingW*pendingH*4];bytes.get(data);if(GL15.glUnmapBuffer(GL21.GL_PIXEL_PACK_BUFFER)&&pendingWorld==client.world&&pendingMenuEpoch==((TwilightBossMenu.epoch()<<32)^PortalMenu.epoch())&&pendingTravelEpoch==BossHudTravelScope.epoch())latest=new Image(pendingW,pendingH,data);}
                    GL32.glDeleteSync(fence);fence=0;
                }
                context.draw();
                int w=client.getWindow().getFramebufferWidth(),h=client.getWindow().getFramebufferHeight();
                if(target==null||target.textureWidth!=w||target.textureHeight!=h){if(target!=null)target.delete();target=new SimpleFramebuffer(w,h,true,MinecraftClient.IS_SYSTEM_MAC);target.setClearColor(0,0,0,0);}
                target.clear(MinecraftClient.IS_SYSTEM_MAC);target.beginWrite(false);
                if(PortalMenu.visible())PortalMenu.draw(context);else if(menu)TwilightBossMenu.draw(context);else client.inGameHud.getBossBarHud().render(context);context.draw();
                int cw=Math.min(1024,w),ch=Math.min(192,h),size=cw*ch*4;
                if(pbo==0)pbo=GL15.glGenBuffers();GL15.glBindBuffer(GL21.GL_PIXEL_PACK_BUFFER,pbo);
                if(capacity!=size){GL15.glBufferData(GL21.GL_PIXEL_PACK_BUFFER,size,GL15.GL_STREAM_READ);capacity=size;}
                GL30.glBindFramebuffer(GL30.GL_READ_FRAMEBUFFER,target.fbo);GL11.glReadBuffer(GL30.GL_COLOR_ATTACHMENT0);
                GL11.glPixelStorei(GL11.GL_PACK_ALIGNMENT,1);for(int i=1;i<names.length;i++)GL11.glPixelStorei(names[i],0);
                GL11.glReadPixels((w-cw)/2,h-ch,cw,ch,GL11.GL_RGBA,GL11.GL_UNSIGNED_BYTE,0L);
                pendingW=cw;pendingH=ch;pendingWorld=client.world;pendingMenuEpoch=(TwilightBossMenu.epoch()<<32)^PortalMenu.epoch();pendingTravelEpoch=BossHudTravelScope.epoch();fence=GL32.glFenceSync(GL32.GL_SYNC_GPU_COMMANDS_COMPLETE,0);
            } finally {
                GL30.glBindFramebuffer(GL30.GL_DRAW_FRAMEBUFFER,oldDraw);GL30.glBindFramebuffer(GL30.GL_READ_FRAMEBUFFER,oldRead);GL11.glReadBuffer(oldBuffer);
                GL15.glBindBuffer(GL21.GL_PIXEL_PACK_BUFFER,oldPack);for(int i=0;i<names.length;i++)GL11.glPixelStorei(names[i],values[i]);
            }
        });
    }
}
