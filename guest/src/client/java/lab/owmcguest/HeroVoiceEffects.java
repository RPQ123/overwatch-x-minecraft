package lab.owmcguest;

import com.google.gson.JsonObject;
import java.util.List;
import net.minecraft.client.MinecraftClient;

/** 语音挂接：补充SFX已退役；只排空旧龙吼通知，不触碰原版技能音效。 */
final class HeroVoiceEffects {
    private long discarded;
    boolean busy(MinecraftClient client){return false;}
    void tick(MinecraftClient client,HeroVoiceRuntime.Binding next,List<HeroVoiceAssets.Clip> clips){
        while(NativeHanzoSkillRuntime.pollDragonRoar()!=null)discarded++;
    }
    JsonObject status(MinecraftClient client){
        var out=new JsonObject();out.addProperty("enabled",false);out.addProperty("dragonRoar",0);
        out.addProperty("playing",false);out.addProperty("discarded",discarded);out.addProperty("error","");return out;
    }
    void reset(MinecraftClient client){}
}
